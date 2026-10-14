#!/bin/bash
# ============================================================
# CT-101 Setup Script - DB Service
# Jalankan di dalam LXC container Proxmox CT-101
# ============================================================

set -e

echo "=== [CT-101] Setup DB Service ==="

# 1. Update & install Python
apt update && apt install -y python3 python3-pip python3-venv curl

# 2. Buat direktori aplikasi
mkdir -p /app /data

# 3. Copy file dari host (jalankan dari Proxmox host):
#    pct push 101 db_service.py /app/db_service.py
#    pct push 101 requirements.txt /app/requirements.txt

# 4. Buat virtual environment dan install dependencies
cd /app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Buat systemd service agar auto-start
cat > /etc/systemd/system/db-service.service << 'EOF'
[Unit]
Description=DB Service - Prediksi Harga Rumah
After=network.target tailscaled.service

[Service]
Type=simple
User=root
WorkingDirectory=/app
Environment="DB_PATH=/data/web1_db.sqlite3"
ExecStart=/app/.venv/bin/uvicorn db_service:app --host 0.0.0.0 --port 9000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable db-service
systemctl start db-service

echo ""
echo "=== DB Service berjalan di port 9000 ==="
echo "Test: curl http://localhost:9000/db/history"


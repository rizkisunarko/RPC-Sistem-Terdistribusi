#!/bin/bash
# ============================================================
# CT-104 Setup Script - Web 2 (Flask Monolitik)
# Jalankan di dalam LXC container Proxmox CT-104
# ============================================================

set -e

echo "=== [CT-104] Setup Web 2 (Flask Monolitik) ==="

# 1. Update & install Python
apt update && apt install -y python3 python3-pip python3-venv curl

# 2. Buat direktori
mkdir -p /app/templates /data

# 3. Copy file dari Proxmox host:
#    pct push 104 app.py /app/app.py
#    pct push 104 requirements.txt /app/requirements.txt
#    pct push 104 templates/index.html /app/templates/index.html

# 4. Install dependencies
cd /app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Buat systemd service
cat > /etc/systemd/system/web2-flask.service << 'EOF'
[Unit]
Description=Web 2 - Flask Monolitik
After=network.target tailscaled.service

[Service]
Type=simple
User=root
WorkingDirectory=/app
Environment="DB_PATH=/data/web2_db.sqlite3"
ExecStart=/app/.venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable web2-flask
systemctl start web2-flask

echo ""
echo "=== Web 2 Flask berjalan di port 5000 ==="
echo "Akses: http://<IP-CT-104>:5000/"


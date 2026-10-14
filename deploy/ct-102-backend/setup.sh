#!/bin/bash
# ============================================================
# CT-102 Setup Script - Web 1 Backend (ML Server)
# Jalankan di dalam LXC container Proxmox CT-102
# PENTING: Isi TAILSCALE_DB_IP setelah Tailscale CT-101 aktif
# ============================================================

set -e

echo "=== [CT-102] Setup Web 1 Backend (ML Server) ==="

# Ganti dengan Tailscale IP dari CT-101!
TAILSCALE_DB_IP="100.x.x.x"   # <-- isi setelah CT-101 join Tailscale

# 1. Update & install Python
apt update && apt install -y python3 python3-pip python3-venv curl

# 2. Buat direktori aplikasi
mkdir -p /app

# 3. Copy file dari Proxmox host:
#    pct push 102 rpc_server.py /app/rpc_server.py
#    pct push 102 requirements.txt /app/requirements.txt

# 4. Install dependencies
cd /app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Buat systemd service
cat > /etc/systemd/system/rpc-server.service << EOF
[Unit]
Description=Web 1 Backend - RPC ML Server
After=network.target tailscaled.service

[Service]
Type=simple
User=root
WorkingDirectory=/app
Environment="DB_SERVICE_URL=http://${TAILSCALE_DB_IP}:9000"
ExecStart=/app/.venv/bin/uvicorn rpc_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rpc-server
systemctl start rpc-server

echo ""
echo "=== Backend berjalan di port 8000 ==="
echo "Test: curl http://localhost:8000/rpc/history"


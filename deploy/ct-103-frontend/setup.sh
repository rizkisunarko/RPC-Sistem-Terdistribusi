#!/bin/bash
# ============================================================
# CT-103 Setup Script - Web 1 Frontend (React → Nginx)
# Jalankan di PC development dulu untuk build, lalu di CT-103
# ============================================================

set -e

echo "=== [CT-103] Setup Web 1 Frontend ==="

# LANGKAH 1: Di PC kamu (Windows), build dulu:
#   cd web1-terdistribusi/frontend-react
#   npm run build
# Lalu copy folder dist ke Proxmox host

# LANGKAH 2: Push ke CT-103 dari Proxmox host:
#   pct push 103 dist.tar.gz /tmp/dist.tar.gz

# ============ Di dalam CT-103 ============

# Install nginx
apt update && apt install -y nginx

# Extract dan deploy
mkdir -p /var/www/prediksi-rumah
tar -xzf /tmp/dist.tar.gz -C /var/www/prediksi-rumah --strip-components=1

# Konfigurasi Nginx
# PENTING: Ganti TAILSCALE_BACKEND_IP dengan Tailscale IP CT-102
TAILSCALE_BACKEND_IP="100.x.x.x"   # <-- isi setelah CT-102 join Tailscale

cat > /etc/nginx/sites-available/prediksi-rumah << EOF
server {
    listen 80;
    server_name _;

    root /var/www/prediksi-rumah;
    index index.html;

    # Serve React SPA
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API ke CT-102 Backend via Tailscale
    location /rpc/ {
        proxy_pass http://${TAILSCALE_BACKEND_IP}:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Aktifkan konfigurasi
ln -sf /etc/nginx/sites-available/prediksi-rumah /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
systemctl enable nginx

echo ""
echo "=== Frontend berjalan di port 80 ==="
echo "Akses: http://<IP-CT-103>/"


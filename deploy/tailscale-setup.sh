#!/bin/bash
# ============================================================
# Tailscale Setup Script - Jalankan di SETIAP container
# (CT-101, CT-102, CT-103, CT-104)
# ============================================================

set -e

CT_NAME=${1:-"container"}   # Parameter: nama container (ct-101, ct-102, dll)

echo "=== [Tailscale] Setup di $CT_NAME ==="

# 1. Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Enable IP forwarding (opsional, untuk subnet routing)
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' >> /etc/sysctl.conf
sysctl -p

# 3. Aktifkan dan start tailscaled
systemctl enable tailscaled
systemctl start tailscaled

# 4. Login ke Tailscale (akan muncul URL untuk auth)
echo ""
echo "=== Login ke Tailscale ==="
echo "Jalankan perintah berikut dan ikuti URL yang muncul:"
echo ""
echo "  tailscale up --hostname=$CT_NAME --accept-routes"
echo ""
echo "Setelah login, cek IP Tailscale dengan:"
echo "  tailscale ip -4"
echo ""
echo "Catat IP Tailscale tiap container untuk konfigurasi service!"


#!/bin/bash
# ============================================================
# PROXMOX HOST MASTER SCRIPT
# Jalankan di Proxmox HOST (bukan di dalam container)
# Membuat & mengkonfigurasi semua LXC containers
# ============================================================
# 
# PRASYARAT:
#   1. Proxmox VE sudah terinstall
#   2. Template Ubuntu 22.04 sudah didownload:
#      pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
#   3. Storage "local-lvm" tersedia
#
# CARA PAKAI:
#   chmod +x proxmox-create-containers.sh
#   ./proxmox-create-containers.sh
# ============================================================

set -e

TEMPLATE="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
STORAGE="local-lvm"
BRIDGE="vmbr0"
PASSWORD="prediksi123"   # <-- Ganti password sesuai kebutuhan!
GATEWAY="192.168.1.1"    # <-- Sesuaikan dengan gateway network kamu

# IP Address masing-masing container (sesuaikan dengan subnet kamu)
IP_CT101="192.168.1.101/24"   # DB Service
IP_CT102="192.168.1.102/24"   # Web 1 Backend
IP_CT103="192.168.1.103/24"   # Web 1 Frontend
IP_CT104="192.168.1.104/24"   # Web 2 Flask

echo "======================================================"
echo " Membuat LXC Containers untuk Prediksi Harga Rumah"
echo "======================================================"

# ── CT-101: DB Service ──────────────────────────────────────
echo ""
echo "[1/4] Membuat CT-101 - DB Service..."
pct create 101 $TEMPLATE \
    --hostname ct-101-db-service \
    --password $PASSWORD \
    --cores 1 \
    --memory 512 \
    --rootfs ${STORAGE}:8 \
    --net0 name=eth0,bridge=${BRIDGE},ip=${IP_CT101},gw=${GATEWAY} \
    --mp0 ${STORAGE}:2,mp=/data \
    --features nesting=1 \
    --unprivileged 1 \
    --start 1

echo "CT-101 berhasil dibuat."

# ── CT-102: Web 1 Backend ───────────────────────────────────
echo ""
echo "[2/4] Membuat CT-102 - Web 1 Backend..."
pct create 102 $TEMPLATE \
    --hostname ct-102-backend \
    --password $PASSWORD \
    --cores 2 \
    --memory 1024 \
    --rootfs ${STORAGE}:8 \
    --net0 name=eth0,bridge=${BRIDGE},ip=${IP_CT102},gw=${GATEWAY} \
    --features nesting=1 \
    --unprivileged 1 \
    --start 1

echo "CT-102 berhasil dibuat."

# ── CT-103: Web 1 Frontend ──────────────────────────────────
echo ""
echo "[3/4] Membuat CT-103 - Web 1 Frontend (Nginx)..."
pct create 103 $TEMPLATE \
    --hostname ct-103-frontend \
    --password $PASSWORD \
    --cores 1 \
    --memory 512 \
    --rootfs ${STORAGE}:8 \
    --net0 name=eth0,bridge=${BRIDGE},ip=${IP_CT103},gw=${GATEWAY} \
    --features nesting=1 \
    --unprivileged 1 \
    --start 1

echo "CT-103 berhasil dibuat."

# ── CT-104: Web 2 Flask ─────────────────────────────────────
echo ""
echo "[4/4] Membuat CT-104 - Web 2 Flask..."
pct create 104 $TEMPLATE \
    --hostname ct-104-web2 \
    --password $PASSWORD \
    --cores 1 \
    --memory 512 \
    --rootfs ${STORAGE}:8 \
    --net0 name=eth0,bridge=${BRIDGE},ip=${IP_CT104},gw=${GATEWAY} \
    --mp0 ${STORAGE}:2,mp=/data \
    --features nesting=1 \
    --unprivileged 1 \
    --start 1

echo "CT-104 berhasil dibuat."

# ── Push files ke masing-masing container ──────────────────
echo ""
echo "=== Push file aplikasi ke containers ==="

# Tunggu containers siap
sleep 5

# CT-101 - DB Service
echo "Push ke CT-101..."
pct push 101 /path/to/deploy/ct-101-db-service/db_service.py /app/db_service.py
pct push 101 /path/to/deploy/ct-101-db-service/requirements.txt /app/requirements.txt
pct push 101 /path/to/deploy/ct-101-db-service/setup.sh /app/setup.sh
pct push 101 /path/to/deploy/tailscale-setup.sh /app/tailscale-setup.sh

# CT-102 - Backend
echo "Push ke CT-102..."
pct push 102 /path/to/deploy/ct-102-backend/rpc_server.py /app/rpc_server.py
pct push 102 /path/to/deploy/ct-102-backend/requirements.txt /app/requirements.txt
pct push 102 /path/to/deploy/ct-102-backend/setup.sh /app/setup.sh
pct push 102 /path/to/deploy/tailscale-setup.sh /app/tailscale-setup.sh

# CT-103 - Frontend (build dulu di PC!)
echo "Push ke CT-103..."
# PERHATIAN: Build React dulu di PC sebelum push!
# npm run build → hasilnya folder 'dist'
# tar -czf dist.tar.gz dist/
pct push 103 /path/to/dist.tar.gz /tmp/dist.tar.gz
pct push 103 /path/to/deploy/ct-103-frontend/setup.sh /app/setup.sh
pct push 103 /path/to/deploy/tailscale-setup.sh /app/tailscale-setup.sh

# CT-104 - Web 2
echo "Push ke CT-104..."
pct push 104 /path/to/deploy/ct-104-web2/app.py /app/app.py
pct push 104 /path/to/deploy/ct-104-web2/requirements.txt /app/requirements.txt
pct push 104 /path/to/deploy/ct-104-web2/setup.sh /app/setup.sh
pct push 104 /path/to/web2-single-platform/templates/index.html /app/templates/index.html
pct push 104 /path/to/deploy/tailscale-setup.sh /app/tailscale-setup.sh

echo ""
echo "======================================================"
echo " Semua container berhasil dibuat!"
echo " LANGKAH SELANJUTNYA:"
echo ""
echo " 1. Masuk ke tiap container dan jalankan Tailscale:"
echo "    pct exec 101 -- bash /app/tailscale-setup.sh ct-101-db"
echo "    pct exec 102 -- bash /app/tailscale-setup.sh ct-102-backend"
echo "    pct exec 103 -- bash /app/tailscale-setup.sh ct-103-frontend"
echo "    pct exec 104 -- bash /app/tailscale-setup.sh ct-104-web2"
echo ""
echo " 2. Jalankan: tailscale up --hostname=<nama>"
echo "    Catat IP Tailscale (100.x.x.x) masing-masing container"
echo ""
echo " 3. Update IP Tailscale di setup.sh CT-102 dan CT-103"
echo "    lalu jalankan setup.sh di tiap container"
echo "======================================================"


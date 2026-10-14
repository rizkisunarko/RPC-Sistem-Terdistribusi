# Prediksi Harga Rumah

Aplikasi prediksi harga rumah untuk tugas Sistem Terdistribusi. Proyek ini
membandingkan dua pendekatan:

1. **Web 1 — arsitektur terdistribusi**: frontend React, backend FastAPI
   sebagai server machine learning/RPC, dan database service terpisah.
2. **Web 2 — arsitektur monolitik**: frontend HTML, API Flask, model machine
   learning, dan database berada dalam satu aplikasi.

Model yang digunakan adalah **Linear Regression** dari scikit-learn. Prediksi
dihitung berdasarkan:

- ukuran rumah dalam meter persegi;
- usia bangunan dalam tahun;
- jumlah kamar.

Nilai harga yang dihasilkan dinyatakan dalam **juta rupiah**.

## Arsitektur

## Konteks Tugas Sistem Terdistribusi

Proyek ini dibuat untuk tugas UTS mata kuliah Sistem Terdistribusi. Tujuan
utamanya adalah mengubah aplikasi prediksi harga rumah menjadi sistem yang
terdiri dari beberapa service terpisah dan saling berkomunikasi melalui
jaringan.

### 1. Multi Kernel dan Proxmox

Implementasi tugas menggunakan LXC container pada Proxmox. Setiap container
memiliki environment, filesystem, service, dan alamat jaringan sendiri,
meskipun container-container tersebut berbagi kernel dari host Proxmox.

Pendekatan ini digunakan untuk mempelajari:

- virtualisasi berbasis container;
- komunikasi antarservice;
- deployment aplikasi;
- pembagian tanggung jawab sistem; dan
- pengelolaan jaringan antarcontainer.

### 2. Pemisahan Service

Komponen aplikasi dipisahkan ke container yang berbeda:

| Container | Fungsi | Port |
|---|---|---:|
| CT-101 | Database Service Web 1 | 9000 |
| CT-102 | Backend FastAPI dan Machine Learning | 8000 |
| CT-103 | Frontend React dan Nginx | 80 |
| CT-104 | Web 2 Flask monolitik | 5000 |

Web 1 menunjukkan arsitektur terdistribusi:

```text
User Browser
     |
     v
CT-103: React + Nginx
     |
     v
CT-102: FastAPI + Linear Regression
     |
     v
CT-101: DB Service + SQLite
```

Alur Web 1 adalah:

1. Pengguna mengisi data rumah pada frontend React.
2. Frontend mengirim request prediksi ke backend FastAPI.
3. Backend menjalankan model Linear Regression.
4. Backend mengirim hasil prediksi ke DB Service melalui HTTP/RPC.
5. DB Service menyimpan hasil ke database SQLite.
6. Riwayat prediksi dapat diminta kembali melalui backend.

Web 2 digunakan sebagai pembanding monolitik. Pada Web 2, Flask, tampilan
HTML, model machine learning, dan SQLite berada dalam satu aplikasi pada
CT-104.

| Aspek | Web 1 | Web 2 |
|---|---|---|
| Arsitektur | Terdistribusi | Monolitik |
| Frontend | React | HTML/JavaScript |
| Backend | FastAPI | Flask |
| Database | Service terpisah | Terintegrasi dalam Flask |
| Container | CT-101, CT-102, CT-103 | CT-104 |
| Komunikasi | HTTP/RPC antarservice | Pemanggilan internal aplikasi |

### 3. Tunnel dengan Tailscale

Tailscale digunakan untuk membuat jaringan privat antarcontainer. Dengan
demikian, service dapat berkomunikasi menggunakan IP Tailscale tanpa harus
membuka database atau backend secara langsung ke internet publik.

```text
CT-103 Frontend
      |
      | Tailscale Network
      v
CT-102 Backend
      |
      | Tailscale Network
      v
CT-101 DB Service
```

Setelah setiap container masuk ke jaringan Tailscale, IP-nya dapat digunakan
untuk konfigurasi service. Contohnya:

```text
DB_SERVICE_URL=http://<IP-TAILSCALE-CT101>:9000
```

Tailscale membantu menyederhanakan koneksi antarcontainer, mengurangi
kebutuhan port forwarding, dan menjaga agar komunikasi internal tidak perlu
melewati alamat publik.

## Fungsi Folder `deploy`

Folder `deploy` berisi script dan konfigurasi untuk memasang aplikasi ke
Proxmox, memisahkan service ke container, dan menghubungkan container melalui
Tailscale. Folder ini bukan bagian dari logika model prediksi, tetapi
merupakan bagian penting dari deployment sistem terdistribusi.

```text
deploy/
├── proxmox-create-containers.sh
├── tailscale-setup.sh
├── ct-101-db-service/
├── ct-102-backend/
├── ct-103-frontend/
└── ct-104-web2/
```

### `proxmox-create-containers.sh`

Script [proxmox-create-containers.sh](deploy/proxmox-create-containers.sh)
dijalankan pada host Proxmox. Fungsinya:

- membuat CT-101 sampai CT-104;
- mengatur hostname, CPU, RAM, storage, dan jaringan;
- menyalakan container;
- mengirim file aplikasi ke container menggunakan `pct push`.

Script ini dijalankan pada host Proxmox, bukan pada Windows atau di dalam
container.

### `tailscale-setup.sh`

Script [tailscale-setup.sh](deploy/tailscale-setup.sh) dijalankan pada setiap
container. Script ini:

- menginstal Tailscale;
- menjalankan service `tailscaled`;
- membantu proses login container ke jaringan Tailscale;
- mengatur hostname container; dan
- membantu memperoleh IP Tailscale.

Contoh penggunaan di dalam container:

```bash
bash /app/tailscale-setup.sh ct-101-db
tailscale up --hostname=ct-101-db --accept-routes
tailscale ip -4
```

### Konfigurasi Tiap Container

- `ct-101-db-service/` berisi DB Service FastAPI pada port `9000` dengan
  endpoint `/db/save` dan `/db/history`.
- `ct-102-backend/` berisi backend FastAPI dan model Linear Regression pada
  port `8000`, termasuk endpoint prediksi sync dan async.
- `ct-103-frontend/` berisi setup Nginx untuk menyajikan hasil build React
  pada port `80` dan meneruskan request `/rpc/` ke CT-102.
- `ct-104-web2/` berisi setup aplikasi Flask monolitik pada port `5000`.

Secara ringkas, fungsi folder `deploy` berkaitan langsung dengan tugas sebagai
berikut:

```text
Memasukkan aplikasi ke Proxmox
    -> proxmox-create-containers.sh

Memisahkan service ke container
    -> ct-101, ct-102, ct-103, ct-104

Membuat tunnel antarcontainer
    -> tailscale-setup.sh
```

### Web 1 — Terdistribusi

```text
Browser
   |
   v
React + Vite (CT-103, port 80)
   |
   v
FastAPI RPC/ML Server (CT-102, port 8000)
   |
   v
DB Service (CT-101, port 9000)
   |
   v
SQLite: web1_db.sqlite3
```

Backend Web 1 menyediakan mode prediksi sinkron dan asinkron. Hasil prediksi
dikirim ke DB Service melalui HTTP sehingga komponen machine learning dan
penyimpanan data dapat berjalan pada service/container yang berbeda.

### Web 2 — Monolitik

```text
Browser
   |
   v
Flask + HTML + Linear Regression (CT-104, port 5000)
   |
   v
SQLite: web2_db.sqlite3
```

Pada Web 2, Flask menangani tampilan, API, proses prediksi, dan penyimpanan
database dalam satu aplikasi.

## Struktur Folder

```text
.
├── init_db.py                         # Membuat tabel pada database SQLite
├── web1_db.sqlite3                    # Database riwayat Web 1
├── web2_db.sqlite3                    # Database riwayat Web 2
├── web1-terdistribusi/
│   ├── backend-python/
│   │   ├── rpc_server.py              # FastAPI ML/RPC server
│   │   └── requirements.txt
│   └── frontend-react/
│       ├── src/App.jsx                # Antarmuka Web 1
│       ├── package.json
│       └── vite.config.js
├── web2-single-platform/
│   ├── app.py                         # Aplikasi Flask monolitik
│   └── templates/index.html
└── deploy/
    ├── proxmox-create-containers.sh  # Membuat CT-101 sampai CT-104
    ├── tailscale-setup.sh             # Konfigurasi jaringan Tailscale
    └── ct-*/                          # Skrip deployment tiap container
```

## Persyaratan

- Python 3.9 atau lebih baru
- Node.js dan npm (untuk frontend React)
- Git
- Linux/Proxmox dan Tailscale hanya diperlukan untuk deployment terdistribusi

## Menjalankan Secara Lokal

### 1. Membuat atau memperbarui database

Dari folder root proyek:

```powershell
python init_db.py
```

Perintah ini membuat tabel `riwayat_prediksi` pada `web1_db.sqlite3` dan
`web2_db.sqlite3` jika tabel belum tersedia.

### 2. Menjalankan DB Service Web 1

Buka terminal pertama:

```powershell
cd deploy/ct-101-db-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn db_service:app --host 0.0.0.0 --port 9000
```

### 3. Menjalankan Backend Web 1

Buka terminal kedua:

```powershell
cd web1-terdistribusi/backend-python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DB_SERVICE_URL = "http://localhost:9000"
uvicorn rpc_server:app --host 0.0.0.0 --port 8000
```

Endpoint utama backend tersedia di `http://localhost:8000`.

### 4. Menjalankan Frontend Web 1

Buka terminal ketiga:

```powershell
cd web1-terdistribusi/frontend-react
npm install
npm run dev
```

Buka alamat yang ditampilkan Vite, biasanya `http://localhost:5173`.
Frontend akan mengakses backend pada port `8000`.

### 5. Menjalankan Web 2

Buka terminal lain:

```powershell
cd web2-single-platform
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r ..\deploy\ct-104-web2\requirements.txt
python app.py
```

Buka `http://localhost:5000`.

## API

### Web 1 RPC Server

| Method | Endpoint | Keterangan |
|---|---|---|
| `GET` | `/` | Status backend |
| `GET` | `/rpc/history` | Mengambil 10 riwayat prediksi terakhir |
| `POST` | `/rpc/predict-sync` | Prediksi dengan pemrosesan sinkron |
| `POST` | `/rpc/predict-async` | Prediksi dengan pemrosesan asinkron |

Contoh body request:

```json
{
  "ukuran": 60,
  "usia": 5,
  "kamar": 3
}
```

Contoh menggunakan PowerShell:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/rpc/predict-sync `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"ukuran":60,"usia":5,"kamar":3}'
```

### Web 1 DB Service

| Method | Endpoint | Keterangan |
|---|---|---|
| `POST` | `/db/save` | Menyimpan hasil prediksi |
| `GET` | `/db/history` | Mengambil riwayat prediksi |

### Web 2 Flask

| Method | Endpoint | Keterangan |
|---|---|---|
| `GET` | `/` | Halaman utama |
| `GET` | `/api/history` | Mengambil riwayat prediksi |
| `POST` | `/api/predict` | Menghasilkan dan menyimpan prediksi |

## Deployment ke Proxmox

Folder `deploy/` berisi contoh deployment ke empat LXC container:

| Container | Komponen | Port |
|---|---|---:|
| CT-101 | DB Service Web 1 | 9000 |
| CT-102 | Backend FastAPI dan model ML | 8000 |
| CT-103 | Frontend React melalui Nginx | 80 |
| CT-104 | Web 2 Flask | 5000 |

Urutan umum deployment:

1. Siapkan template Ubuntu 22.04 pada Proxmox.
2. Sesuaikan variabel jaringan, storage, dan password pada
   `deploy/proxmox-create-containers.sh`.
3. Jalankan skrip tersebut pada **host Proxmox**, bukan pada Windows atau
   dalam container.
4. Jalankan `deploy/tailscale-setup.sh` pada setiap container dan catat IP
   Tailscale.
5. Masukkan IP Tailscale DB Service ke konfigurasi CT-102.
6. Masukkan IP Tailscale backend ke konfigurasi Nginx CT-103.
7. Build frontend React dengan `npm run build`, lalu kirim folder `dist` ke
   CT-103.
8. Jalankan `setup.sh` pada setiap container sesuai komponennya.

Skrip deployment menggunakan placeholder seperti `100.x.x.x` dan
`/path/to/...`. Nilai tersebut harus diganti sesuai lingkungan deployment.
Jangan memasukkan password, token Tailscale, atau credential lain ke dalam
repository.

## Catatan Database

Database menggunakan SQLite dengan tabel `riwayat_prediksi` yang memiliki
kolom:

```text
id, ukuran, usia, kamar, prediksi_harga, platform, waktu_prediksi
```

Database pada repository merupakan database lokal untuk pengembangan. Dalam
deployment, lokasi database service diatur oleh environment atau konfigurasi
service pada container.

## Pengembangan Frontend

Perintah yang tersedia pada `web1-terdistribusi/frontend-react`:

```powershell
npm run dev      # Menjalankan server development Vite
npm run build    # Membuat build production
npm run lint     # Menjalankan Oxlint
npm run preview  # Menjalankan preview build production
```

## Lisensi

Proyek ini dibuat untuk keperluan pembelajaran mata kuliah Sistem
Terdistribusi.

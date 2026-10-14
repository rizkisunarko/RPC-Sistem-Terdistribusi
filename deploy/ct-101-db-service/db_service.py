"""
CT-101 - DB Service
FastAPI service yang mengelola SQLite untuk Web 1.
Berkomunikasi dengan CT-102 (Backend) via Tailscale.
Port: 9000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

app = FastAPI(title="DB Service - Prediksi Harga Rumah Web 1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database disimpan di volume persistent /data/
DB_PATH = os.environ.get("DB_PATH", "/data/web1_db.sqlite3")


def init_db():
    """Buat tabel jika belum ada."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_prediksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ukuran REAL NOT NULL,
            usia INTEGER NOT NULL,
            kamar INTEGER NOT NULL,
            prediksi_harga REAL NOT NULL,
            platform TEXT NOT NULL,
            waktu_prediksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database siap di: {DB_PATH}")


# Inisialisasi database saat startup
init_db()


@app.get("/")
def root():
    return {"service": "DB Service", "status": "running", "db": DB_PATH}


@app.post("/db/save")
def save_prediction(data: dict):
    """Menerima data prediksi dari ML Server dan menyimpannya ke SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO riwayat_prediksi (ukuran, usia, kamar, prediksi_harga, platform)
            VALUES (?, ?, ?, ?, ?)
        ''', (data["ukuran"], data["usia"], data["kamar"], data["prediksi_harga"], data["platform"]))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Data berhasil disimpan"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/db/history")
def get_history():
    """Mengambil 10 riwayat prediksi terakhir dari SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM riwayat_prediksi ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)


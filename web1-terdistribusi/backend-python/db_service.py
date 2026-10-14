from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path ke database Web 1
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web1_db.sqlite3")

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
    """Mengambil 10 riwayat prediksi terakhir dari SQLite dan mengirimkannya."""
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


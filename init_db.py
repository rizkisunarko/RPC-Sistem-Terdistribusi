import sqlite3
import os

DB_WEB1 = "web1_db.sqlite3"
DB_WEB2 = "web2_db.sqlite3"

def create_table(db_name):
    conn = sqlite3.connect(db_name)
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

def init_db():
    print("Membuat database terpisah untuk Web 1 dan Web 2...")
    create_table(DB_WEB1)
    create_table(DB_WEB2)
    print("Berhasil membuat web1_db.sqlite3 dan web2_db.sqlite3")

if __name__ == "__main__":
    init_db()


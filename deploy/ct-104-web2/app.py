"""
CT-104 - Web 2 (Flask Monolitik)
Flask single-platform dengan SQLite sendiri.
DB path via environment variable untuk fleksibilitas.
Port: 5000
"""
from flask import Flask, render_template, request, jsonify
from sklearn.linear_model import LinearRegression
import numpy as np
import sqlite3
import os

app = Flask(__name__)

# Training Model Linear Regression
X_train = np.array([[36, 10, 2], [45, 5, 2], [60, 2, 3], [72, 8, 3], [90, 1, 4], [120, 15, 4]])
y_train = np.array([300, 420, 550, 620, 850, 950])
model = LinearRegression().fit(X_train, y_train)

# Database path via env var (default ke /data/web2_db.sqlite3)
DB_PATH = os.environ.get("DB_PATH", "/data/web2_db.sqlite3")


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


init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/history', methods=['GET'])
def history():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM riwayat_prediksi ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    features = np.array([[data["ukuran"], data["usia"], data["kamar"]]])
    harga = round(float(model.predict(features)[0]), 2)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO riwayat_prediksi (ukuran, usia, kamar, prediksi_harga, platform)
            VALUES (?, ?, ?, ?, ?)
        ''', (data["ukuran"], data["usia"], data["kamar"], harga, "Web 2 (Monolitik)"))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving to DB:", e)

    return jsonify({
        "status": "success",
        "platform": "Single Platform (Flask)",
        "prediksi_harga_juta": harga
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)


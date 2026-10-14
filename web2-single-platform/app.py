from flask import Flask, render_template, request, jsonify
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)

# Training Model Linear Regression
X_train = np.array([[36, 10, 2], [45, 5, 2], [60, 2, 3], [72, 8, 3], [90, 1, 4], [120, 15, 4]])
y_train = np.array([300, 420, 550, 620, 850, 950])
model = LinearRegression().fit(X_train, y_train)

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web2_db.sqlite3")

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
    predicted_price = model.predict(features)[0]
    harga = round(float(predicted_price), 2)
    
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
    app.run(host='0.0.0.0', port=5000, debug=True)
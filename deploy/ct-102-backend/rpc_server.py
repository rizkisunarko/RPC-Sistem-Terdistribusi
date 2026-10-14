"""
CT-102 - Web 1 Backend (ML Server)
FastAPI RPC server untuk prediksi harga rumah.
Berkomunikasi dengan CT-101 (DB Service) via Tailscale.
Port: 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sklearn.linear_model import LinearRegression
import numpy as np
import asyncio
import requests
import os

app = FastAPI(title="Web 1 Backend - RPC ML Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alamat DB Service (CT-101) via Tailscale — diisi via environment variable
# Contoh: DB_SERVICE_URL=http://100.x.x.x:9000
DB_SERVICE_URL = os.environ.get("DB_SERVICE_URL", "http://localhost:9000")

print(f"DB Service URL: {DB_SERVICE_URL}")

# Training Model Linear Regression
X_train = np.array([
    [36, 10, 2], [45, 5, 2], [60, 2, 3],
    [72, 8, 3], [90, 1, 4], [120, 15, 4]
])
y_train = np.array([300, 420, 550, 620, 850, 950])

model = LinearRegression()
model.fit(X_train, y_train)


def save_to_db(data, harga, mode):
    """Memanggil DB Service (CT-101) via HTTP/RPC untuk menyimpan hasil prediksi."""
    try:
        requests.post(f"{DB_SERVICE_URL}/db/save", json={
            "ukuran": data["ukuran"],
            "usia": data["usia"],
            "kamar": data["kamar"],
            "prediksi_harga": harga,
            "platform": f"Web 1 (Terdistribusi - {mode})"
        }, timeout=5)
    except Exception as e:
        print("Gagal menghubungi DB Service:", e)


@app.get("/")
def root():
    return {"service": "Web 1 Backend", "status": "running", "db_service": DB_SERVICE_URL}


@app.get("/rpc/history")
def get_history():
    """Memanggil DB Service (CT-101) via HTTP/RPC untuk mengambil riwayat."""
    try:
        response = requests.get(f"{DB_SERVICE_URL}/db/history", timeout=5)
        return response.json()
    except Exception as e:
        return {"error": f"Gagal menghubungi DB Service: {str(e)}"}


@app.post("/rpc/predict-sync")
def predict_sync(data: dict):
    features = np.array([[data["ukuran"], data["usia"], data["kamar"]]])
    harga = round(float(model.predict(features)[0]), 2)
    save_to_db(data, harga, "sync")
    return {"status": "success", "mode": "sync", "prediksi_harga_juta": harga}


@app.post("/rpc/predict-async")
async def predict_async(data: dict):
    loop = asyncio.get_event_loop()
    features = np.array([[data["ukuran"], data["usia"], data["kamar"]]])
    predicted_price = await loop.run_in_executor(None, lambda: model.predict(features)[0])
    harga = round(float(predicted_price), 2)
    save_to_db(data, harga, "async")
    return {"status": "success", "mode": "async", "prediksi_harga_juta": harga}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


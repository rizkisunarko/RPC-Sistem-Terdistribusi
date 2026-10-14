from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sklearn.linear_model import LinearRegression
import numpy as np
import asyncio
import requests
import os

app = FastAPI(title="Web 1 Backend - RPC ML Server")

# Mengizinkan akses CORS dari React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alamat DB Service — di lokal: localhost:9000
# Di Proxmox: set env DB_SERVICE_URL=http://<tailscale-ip-ct101>:9000
DB_SERVICE_URL = os.environ.get("DB_SERVICE_URL", "http://localhost:9000")

# Training Model Linear Regression Sederhana
# Dataset: [Ukuran (m2), Usia (tahun), Jumlah Kamar]
X_train = np.array([
    [36, 10, 2], [45, 5, 2], [60, 2, 3],
    [72, 8, 3], [90, 1, 4], [120, 15, 4]
])
# Target: Harga (dalam Juta Rupiah)
y_train = np.array([300, 420, 550, 620, 850, 950])

model = LinearRegression()
model.fit(X_train, y_train)


def validate_payload(data):
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Body request harus berupa JSON object.")

    required_fields = ["ukuran", "usia", "kamar"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Field yang dibutuhkan belum ada: {', '.join(missing)}"
        )

    try:
        return {
            "ukuran": float(data["ukuran"]),
            "usia": float(data["usia"]),
            "kamar": float(data["kamar"]),
        }
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Ukuran, usia, dan kamar harus berupa angka.",
        )


def save_to_db(data, harga, mode):
    """Memanggil DB Service via RPC (HTTP POST) untuk menyimpan hasil prediksi."""
    try:
        response = requests.post(
            f"{DB_SERVICE_URL}/db/save",
            json={
                "ukuran": data["ukuran"],
                "usia": data["usia"],
                "kamar": data["kamar"],
                "prediksi_harga": harga,
                "platform": f"Web 1 (Terdistribusi - {mode})",
            },
            timeout=5,
        )
        response.raise_for_status()
    except Exception as e:
        print("Gagal menghubungi DB Service:", e)


@app.get("/")
def root():
    return {"service": "Web 1 Backend", "status": "running", "db_service": DB_SERVICE_URL}


@app.get("/rpc/history")
def get_history():
    """Memanggil DB Service via RPC (HTTP GET) untuk mengambil riwayat prediksi."""
    try:
        response = requests.get(f"{DB_SERVICE_URL}/db/history", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Gagal menghubungi DB Service: {str(e)}"}


@app.post("/rpc/predict-sync")
def predict_sync(data: dict):
    payload = validate_payload(data)
    features = np.array([[payload["ukuran"], payload["usia"], payload["kamar"]]])
    predicted_price = model.predict(features)[0]
    harga = round(float(predicted_price), 2)

    save_to_db(payload, harga, "sync")

    return {
        "status": "success",
        "mode": "sync",
        "prediksi_harga_juta": harga
    }


@app.post("/rpc/predict-async")
async def predict_async(data: dict):
    payload = validate_payload(data)
    features = np.array([[payload["ukuran"], payload["usia"], payload["kamar"]]])

    # Menjalankan pemrosesan ML secara non-blocking dan aman di Python 3.11+
    predicted_price = (await asyncio.to_thread(model.predict, features))[0]
    harga = round(float(predicted_price), 2)

    save_to_db(payload, harga, "async")

    return {
        "status": "success",
        "mode": "async",
        "prediksi_harga_juta": harga
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
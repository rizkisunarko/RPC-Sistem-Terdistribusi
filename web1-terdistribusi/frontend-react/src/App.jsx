import React, { useState, useEffect } from 'react';

export default function App() {
  const [form, setForm] = useState({ ukuran: 60, usia: 5, kamar: 3 });
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: Number(e.target.value) });

  const loadHistory = async () => {
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/rpc/history`);
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.log("Gagal memuat riwayat", err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handlePredict = async (mode) => {
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/rpc/predict-${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      const data = await res.json();
      setResult(data);
      loadHistory();
    } catch (err) {
      alert("Gagal terhubung ke RPC Server Python!");
    }
  };

  return (
    <div style={{ padding: 30, fontFamily: 'sans-serif', maxWidth: 500, margin: 'auto' }}>
      <h2>Web 1: Terdistribusi (React + Python RPC)</h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <label>Ukuran (m²):</label>
        <input type="number" name="ukuran" value={form.ukuran} onChange={handleChange} />
        
        <label>Usia Bangunan (Tahun):</label>
        <input type="number" name="usia" value={form.usia} onChange={handleChange} />
        
        <label>Jumlah Kamar:</label>
        <input type="number" name="kamar" value={form.kamar} onChange={handleChange} />
      </div>

      <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
        <button onClick={() => handlePredict('sync')}>Prediksi (RPC Sync)</button>
        <button onClick={() => handlePredict('async')}>Prediksi (RPC Async)</button>
      </div>

      {result && (
        <div style={{ marginTop: 20, padding: 15, background: '#eef2f7', borderRadius: 8 }}>
          <h4>Hasil Prediksi Mode ({result.mode.toUpperCase()}):</h4>
          <p style={{ fontSize: 18, color: '#2c3e50' }}>
            Estimasi Harga: <strong>Rp {result.prediksi_harga_juta} Juta</strong>
          </p>
        </div>
      )}

      <div style={{ marginTop: 40 }}>
        <h3>Riwayat Prediksi (RPC Database)</h3>
        <ul style={{ padding: 0, listStyle: 'none' }}>
          {history.length > 0 ? history.map(item => (
            <li key={item.id} style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>
              <strong>Rp {item.prediksi_harga} Juta</strong> <br/>
              <small>(Ukuran: {item.ukuran}m², Usia: {item.usia}thn, Kamar: {item.kamar})</small> <br/>
              <small style={{ color: '#666' }}>{item.platform}</small>
            </li>
          )) : (
            <li>Belum ada riwayat.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
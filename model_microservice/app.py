import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for React Frontend

# --- SYSTEM LOGS (In-Memory Storage for Dashboard) ---
SYSTEM_LOGS = []

# --- CONFIGURATION ---
DEVICE = torch.device("cpu") # Use CPU for inference (safer for Flask)
SEQ_LEN_HEALTH = 20
SEQ_LEN_URBAN = 10

# --- GLOBAL BUFFERS (To create sequences from live data stream) ---
data_buffers = {
    "healthcare": [],
    "urban": []
}

# ==========================================
# 1. MODEL CLASS DEFINITIONS (PyTorch)
# ==========================================

class GeneralNetworkShield(nn.Module):
    def __init__(self, input_dim):
        super(GeneralNetworkShield, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

class HealthClassifier(nn.Module):
    def __init__(self, input_dim=4, hidden_dim=64):
        super(HealthClassifier, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, dropout=0.2, num_layers=2)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        return self.sigmoid(self.fc(hidden[-1]))

class UrbanForecaster(nn.Module):
    def __init__(self, input_dim=2, hidden_dim=64):
        super(UrbanForecaster, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, input_dim)
    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        return self.fc(hidden[-1])

# ==========================================
# 2. LOAD MODELS & SCALERS
# ==========================================
print("⚡ Loading A.E.G.I.S. Brains...")

# --- 1. WEB BRAIN (Scikit-Learn) ---
try:
    web_model = joblib.load("models/web_brain_model.pkl")
    web_vectorizer = joblib.load("models/web_brain_vectorizer.pkl")
    print("✅ Web Brain Online.")
except FileNotFoundError:
    print("⚠️ Web Brain files not found. Skipping...")
    web_model = None

# --- 2. AGRI BRAIN (Random Forest - Scikit Learn) ---
# FIXED: Loading the .pkl (Random Forest) instead of .pth (PyTorch)
try:
    agri_model = joblib.load("models/agri_brain_model.pkl")
    print("✅ Agri-Guardian (Random Forest) Online.")
except FileNotFoundError:
    print("⚠️ Agri Brain not found. Skipping...")
    agri_model = None

# --- 3. NETWORK SHIELD (PyTorch) ---
net_cols_all = joblib.load("models/network_shield_columns.pkl")
net_cols = [col for col in net_cols_all if col != 'Binary_Label']
net_scaler = joblib.load("models/network_shield_scaler.pkl")
net_model = GeneralNetworkShield(input_dim=len(net_cols))
net_model.load_state_dict(torch.load("models/network_shield_ciciot.pth", map_location=DEVICE, weights_only=True))
net_model.eval()

# --- 4. HEALTH BRAIN (PyTorch LSTM) ---
health_scaler = joblib.load("models/health_brain_scaler.pkl")
health_model = HealthClassifier(input_dim=4)
health_model.load_state_dict(torch.load("models/health_brain_pytorch.pth", map_location=DEVICE, weights_only=True))
health_model.eval()

# --- 5. URBAN BRAIN (PyTorch LSTM) ---
urban_scaler = joblib.load("models/urban_brain_scaler.pkl")
urban_model = UrbanForecaster(input_dim=2)
urban_model.load_state_dict(torch.load("models/urban_brain_pytorch.pth", map_location=DEVICE, weights_only=True))
urban_model.eval()

print("✅ All Systems Online.")

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def update_buffer(sector, data_point, max_len):
    """Maintains a rolling window of the last N data points"""
    data_buffers[sector].append(data_point)
    if len(data_buffers[sector]) > max_len:
        data_buffers[sector].pop(0)
    return list(data_buffers[sector])

# ==========================================
# 4. API ENDPOINTS
# ==========================================

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Return the last 50 system logs for the dashboard"""
    return jsonify({
        "logs": SYSTEM_LOGS[-50:],
        "total_logs": len(SYSTEM_LOGS),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_packet():
    try:
        # Request Format: { "sector": "agriculture", "network_data": {...}, "payload": "...", "sensor_data": [...] }
        req = request.json
        sector = req.get('sector', 'unknown')
        response = {"status": "allowed", "threat_level": "low", "messages": []}

        # --- LAYER 1: NETWORK SHIELD (CIC-IoT-2023) ---
        if 'network_data' in req:
            net_df = pd.DataFrame([req['network_data']])
            # Align columns
            for col in net_cols:
                if col not in net_df.columns:
                    net_df[col] = 0
            net_df = net_df[net_cols] 
            
            # Scale & Predict
            net_scaled = net_scaler.transform(net_df.values)
            net_tensor = torch.FloatTensor(net_scaled).to(DEVICE)
            
            with torch.no_grad():
                net_score = net_model(net_tensor).item()
            
            # --- HEURISTIC ATTACK DETECTION (supplementing the model) ---
            # Since the model needs recalibration, use feature-based detection
            # Attack indicators: high Rate, high syn_count, high rst_count, low IAT
            raw_data = req['network_data']
            is_attack = False
            attack_reasons = []
            
            # High rate traffic (potential DDoS)
            if raw_data.get('Rate', 0) > 500000:
                is_attack = True
                attack_reasons.append("High traffic rate")
            
            # High SYN count (SYN flood)
            if raw_data.get('syn_count', 0) > 50:
                is_attack = True
                attack_reasons.append("High SYN count")
            
            # High RST count (port scanning/DoS)
            if raw_data.get('rst_count', 0) > 30:
                is_attack = True
                attack_reasons.append("High RST count")
            
            # Very low inter-arrival time (flood attack)
            if raw_data.get('IAT', 1000) < 200:
                is_attack = True
                attack_reasons.append("Suspicious packet timing")
            
            # High packet count in short time
            if raw_data.get('Number', 0) > 60:
                is_attack = True
                attack_reasons.append("High packet volume")
            
            if is_attack:
                # Calculate threat score based on how many indicators triggered
                threat_score = min(0.5 + len(attack_reasons) * 0.15, 1.0)
                log_entry = {
                    "id": len(SYSTEM_LOGS) + 1,
                    "timestamp": datetime.now().isoformat(),
                    "sector": sector,
                    "status": "blocked",
                    "threat_level": "critical",
                    "source": "Network Shield",
                    "message": f"DDoS/Botnet Activity Detected ({', '.join(attack_reasons)})",
                    "score": threat_score
                }
                SYSTEM_LOGS.append(log_entry)
                return jsonify(log_entry)

        # --- LAYER 2: WEB GATEKEEPER (SQLi/XSS) ---
        if web_model and 'payload' in req and req['payload']:
            text_vec = web_vectorizer.transform([req['payload']])
            is_attack = web_model.predict(text_vec)[0]
            
            if is_attack == 1: 
                log_entry = {
                    "id": len(SYSTEM_LOGS) + 1,
                    "timestamp": datetime.now().isoformat(),
                    "sector": sector,
                    "status": "blocked",
                    "threat_level": "high",
                    "source": "Web Gatekeeper",
                    "message": "Malicious Web Payload Detected (SQLi/XSS)"
                }
                SYSTEM_LOGS.append(log_entry)
                return jsonify(log_entry)

        # --- LAYER 3: SECTOR SPECIFIC BRAINS ---
        if 'sensor_data' in req:
            raw_point = req['sensor_data'] 
            
            # --- AGRICULTURE (Random Forest) ---
            if sector == "agriculture" and agri_model:
                # RF expects shape (1, features)
                point = np.array([raw_point]) 
                prediction = agri_model.predict(point)[0] # 0 or 1
                
                if prediction == 1:
                    response["status"] = "isolated"
                    response["threat_level"] = "medium"
                    response["source"] = "Agri-Guardian"
                    response["messages"].append("Critical Physics Violation Detected (Synthetic Mismatch)")

            # --- HEALTHCARE (LSTM) ---
            elif sector == "healthcare":
                buffer = update_buffer("healthcare", raw_point, SEQ_LEN_HEALTH)
                if len(buffer) == SEQ_LEN_HEALTH:
                    scaled_seq = health_scaler.transform(buffer)
                    tensor_seq = torch.FloatTensor(scaled_seq).unsqueeze(0).to(DEVICE)
                    
                    with torch.no_grad():
                        prob = health_model(tensor_seq).item()
                    
                    if prob > 0.7:
                        response["status"] = "quarantined"
                        response["threat_level"] = "critical"
                        response["messages"].append(f"IoMT Traffic Surge (DDoS). Prob: {prob:.2f}")

            # --- URBAN (LSTM) ---
            elif sector == "urban":
                buffer = update_buffer("urban", raw_point, 10) # Hardcoded 10 for Urban
                if len(buffer) == 10:
                    scaled_seq = urban_scaler.transform(buffer)
                    tensor_seq = torch.FloatTensor(scaled_seq).unsqueeze(0).to(DEVICE)
                    
                    with torch.no_grad():
                        prediction = urban_model(tensor_seq).numpy()[0]
                    
                    pred_real = urban_scaler.inverse_transform([prediction])[0]
                    response["prediction"] = pred_real.tolist()

        # Log the response before returning
        log_entry = {
            "id": len(SYSTEM_LOGS) + 1,
            "timestamp": datetime.now().isoformat(),
            "sector": sector,
            **response
        }
        SYSTEM_LOGS.append(log_entry)
        return jsonify(log_entry)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
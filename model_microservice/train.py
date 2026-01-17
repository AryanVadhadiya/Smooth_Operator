import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# --- CONFIGURATION ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODELS_DIR = "models"
DATA_DIR = "datasets"

if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

print(f"🚀 A.E.G.I.S. Training System Online. Device: {DEVICE}")

# ==========================================
# 1. MODEL ARCHITECTURES (PyTorch)
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
# 2. TRAINING FUNCTIONS
# ==========================================

def train_web_brain():
    print("\n🌐 --- Training Web Brain (SQLi/XSS) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'payload_full.csv'))
        df['payload'] = df['payload'].astype(str).fillna('')
        # Map labels: 'norm' -> 0, everything else -> 1
        df['binary_label'] = df['label'].apply(lambda x: 0 if x == 'norm' else 1)
        
        # Vectorize (Char-level for SQL patterns)
        vectorizer = TfidfVectorizer(min_df=3, analyzer="char", ngram_range=(2, 4))
        X = vectorizer.fit_transform(df['payload'])
        y = df['binary_label']
        
        # Train
        model = RandomForestClassifier(n_estimators=50, max_depth=20, n_jobs=-1, random_state=42)
        model.fit(X, y)
        
        # Save
        joblib.dump(model, os.path.join(MODELS_DIR, "web_brain_model.pkl"))
        joblib.dump(vectorizer, os.path.join(MODELS_DIR, "web_brain_vectorizer.pkl"))
        print("✅ Web Brain Saved.")
    except Exception as e:
        print(f"❌ Failed to train Web Brain: {e}")

def train_agri_brain():
    print("\n🌽 --- Training Agri Brain (Physics Guardian) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'IoTProcessed_Data.csv'))
        features = ['tempreature', 'humidity', 'water_level', 'N', 'P', 'K']
        
        # 1. Normal Data
        normal_data = df[features].copy()
        normal_data['label'] = 0
        
        # 2. Synthetic Attack Generation
        n_samples = len(normal_data) // 3
        
        # Attack A: High Temp + Low Water (Physics Violation)
        attack_a = pd.DataFrame()
        attack_a['tempreature'] = np.random.randint(50, 100, n_samples)
        attack_a['humidity'] = np.random.randint(0, 10, n_samples)
        attack_a['water_level'] = np.random.randint(0, 20, n_samples)
        attack_a['N'] = np.random.randint(0, 255, n_samples)
        attack_a['P'] = np.random.randint(0, 255, n_samples)
        attack_a['K'] = np.random.randint(0, 255, n_samples)
        attack_a['label'] = 1
        
        # Attack B: Maxed Out Sensors
        attack_b = pd.DataFrame(255, index=range(n_samples), columns=features)
        attack_b['label'] = 1
        
        # Combine
        balanced_df = pd.concat([normal_data, attack_a, attack_b], axis=0).sample(frac=1).reset_index(drop=True)
        
        # Train
        X = balanced_df[features]
        y = balanced_df['label']
        clf = RandomForestClassifier(n_estimators=100)
        clf.fit(X, y)
        
        # Save
        joblib.dump(clf, os.path.join(MODELS_DIR, "agri_brain_model.pkl"))
        print("✅ Agri Brain Saved.")
    except Exception as e:
        print(f"❌ Failed to train Agri Brain: {e}")

def train_health_brain():
    print("\n🏥 --- Training Health Brain (IoMT DDoS) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'UL-ECE-UDP-DDoS-H-IoT2025.csv'))
        cols = ['payload_size', 'total_messages', 'frequency', 'mean_frequency']
        
        X_raw = df[cols].values
        y_raw = df['outcome'].values
        
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X_raw)
        
        # Sequence Creation
        SEQ_LEN = 20
        xs, ys = [], []
        for i in range(len(X_scaled) - SEQ_LEN):
            xs.append(X_scaled[i:i+SEQ_LEN])
            ys.append(y_raw[i+SEQ_LEN])
            
        tensor_x = torch.Tensor(np.array(xs)).to(DEVICE)
        tensor_y = torch.Tensor(np.array(ys)).unsqueeze(1).to(DEVICE)
        
        loader = DataLoader(TensorDataset(tensor_x, tensor_y), batch_size=64, shuffle=True)
        
        model = HealthClassifier(input_dim=4).to(DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.BCELoss()
        
        model.train()
        for epoch in range(5):
            for X_batch, y_batch in loader:
                optimizer.zero_grad()
                out = model(X_batch)
                loss = criterion(out, y_batch)
                loss.backward()
                optimizer.step()
            print(f"   Epoch {epoch+1} Complete")
            
        torch.save(model.state_dict(), os.path.join(MODELS_DIR, "health_brain_pytorch.pth"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, "health_brain_scaler.pkl"))
        print("✅ Health Brain Saved.")
    except Exception as e:
        print(f"❌ Failed to train Health Brain: {e}")

def train_urban_brain():
    print("\n🚦 --- Training Urban Brain (Traffic Forecast) ---")
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'traffic_dataset.csv'))
        # Ensure numeric
        # Depending on CSV format, might need cleaning. Assuming clean for now based on prev steps.
        features = ['Vehicle Count', 'Avg Speed (km/h)']
        data = df[features].values
        
        scaler = MinMaxScaler()
        data_scaled = scaler.fit_transform(data)
        
        SEQ_LEN = 10
        xs, ys = [], []
        for i in range(len(data_scaled) - SEQ_LEN):
            xs.append(data_scaled[i:i+SEQ_LEN])
            ys.append(data_scaled[i+SEQ_LEN]) # Predict next step
            
        tensor_x = torch.Tensor(np.array(xs)).to(DEVICE)
        tensor_y = torch.Tensor(np.array(ys)).to(DEVICE)
        
        loader = DataLoader(TensorDataset(tensor_x, tensor_y), batch_size=32, shuffle=True)
        
        model = UrbanForecaster(input_dim=2).to(DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        model.train()
        for epoch in range(10):
            for X_batch, y_batch in loader:
                optimizer.zero_grad()
                out = model(X_batch)
                loss = criterion(out, y_batch)
                loss.backward()
                optimizer.step()
        
        torch.save(model.state_dict(), os.path.join(MODELS_DIR, "urban_brain_pytorch.pth"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, "urban_brain_scaler.pkl"))
        print("✅ Urban Brain Saved.")
    except Exception as e:
        print(f"❌ Failed to train Urban Brain: {e}")

def train_network_shield():
    print("\n🛡️ --- Training General Network Shield (CIC-IoT-2023) ---")
    # This expects the massive Kaggle dataset.
    csv_path = os.path.join(DATA_DIR, 'Stratified_data.csv')
    if not os.path.exists(csv_path):
        print(f"⚠️  Skipping Network Shield: {csv_path} not found.")
        print("    (Download 'ciciot-2023-stratified-dataset' from Kaggle and unzip it in 'datasets/')")
        return

    try:
        # Load subset to save RAM if needed, or full if capable machine
        df = pd.read_csv(csv_path) # Add nrows=500000 for testing
        
        # Cleaning
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        # Labeling
        target_col = 'Label' if 'Label' in df.columns else 'label'
        df['Binary_Label'] = df[target_col].apply(lambda x: 0 if 'Benign' in str(x) else 1)
        
        # Drop junk
        drop_cols = ['Label', 'label', 'Timestamp', 'Dst_IP', 'Src_IP', 'Src_Port', 'Dst_Port']
        existing_drop = [c for c in drop_cols if c in df.columns]
        df = df.drop(columns=existing_drop)
        
        # Encoding
        encoders = {}
        for col in df.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
            
        X = df.drop(columns=['Binary_Label']).values
        y = df['Binary_Label'].values
        
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)
        
        tensor_x = torch.Tensor(X)
        tensor_y = torch.Tensor(y).unsqueeze(1)
        
        # Train
        train_idx, _ = train_test_split(range(len(tensor_x)), test_size=0.2)
        loader = DataLoader(TensorDataset(tensor_x[train_idx], tensor_y[train_idx]), batch_size=2048, shuffle=True)
        
        model = GeneralNetworkShield(input_dim=X.shape[1]).to(DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.BCELoss()
        
        model.train()
        for epoch in range(3):
            total_loss = 0
            for X_batch, y_batch in loader:
                X_batch, y_batch = X_batch.to(DEVICE), y_batch.to(DEVICE)
                optimizer.zero_grad()
                out = model(X_batch)
                loss = criterion(out, y_batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            print(f"   Epoch {epoch+1} Loss: {total_loss/len(loader):.4f}")
            
        # Save
        torch.save(model.state_dict(), os.path.join(MODELS_DIR, "network_shield_ciciot.pth"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, "network_shield_scaler.pkl"))
        joblib.dump(list(df.drop(columns=['Binary_Label']).columns), os.path.join(MODELS_DIR, "network_shield_columns.pkl"))
        print("✅ Network Shield Saved.")
        
    except Exception as e:
        print(f"❌ Failed to train Network Shield: {e}")

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    train_web_brain()
    train_agri_brain()
    train_health_brain()
    train_urban_brain()
    train_network_shield()
    print("\n🏁 --- ALL TRAINING JOBS COMPLETE ---")
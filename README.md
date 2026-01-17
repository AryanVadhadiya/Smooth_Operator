# Threat_Ops.ai 🛡️

**AI-Powered Threat Detection & Automated Response Platform**

Threat_Ops.ai is a microservices-based security platform that detects, analyzes, and responds to cyber threats in real-time.

## 🚀 Quick Start

The entire platform (Frontend + 5 Backend Services) can be started with a single command.

### 1. Prerequisites
- Node.js & npm
- Python 3.11+
- Virtual environments created for backend services (already done if you followed the setup)

### 2. Install Dependencies
```bash
npm install

### 2.1 Backend Setup (First Time Only)
Install Python dependencies for all microservices:
```bash
for service in ingest-service api-gateway detection-engine alert-manager response-engine; do
  echo "Installing deps for $service..."
  (cd backend/$service && source venv/bin/activate && pip install -r requirements.txt)
done
```
```

### 3. Run Everything
```bash
npm run dev
```
This command starts:
- **Frontend** (http://localhost:5173)
- **Ingest Service** (http://localhost:8001)
- **API Gateway** (http://localhost:3001)
- **Detection Engine** (http://localhost:8002)
- **Alert Manager** (http://localhost:8003)
- **Response Engine** (http://localhost:8004)

---

## 🎮 Demo Guide

### The "Money Moment" 🎯
1. **Open Dashboard**: Go to [http://localhost:5173](http://localhost:5173).
2. **Verify Connection**: Ensure the status indicator says "Connected".
3. **Trigger Attack**:
   - Use the **"Simulate SQL Injection"** button on the frontend.
   - OR use the CLI command below.

### Manual Attack Trigger (CLI)
Run this from a new terminal to simulate a malicious SQL Injection attack:
```bash
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "192.168.1.66",
    "service": "payment-api",
    "event_type": "http_request",
    "payload": {
        "query": "SELECT * FROM users WHERE id = 1 OR 1=1"
    }
}'
```

### What Happens Next (The Pipeline)
1. **Ingest**: Receives the event, saves it, and forwards it to Detection.
2. **Detection**: Flags the `OR 1=1` pattern as a **Critical SQL Injection**.
3. **Alert Manager**: Creates a human-readable alert "🚨 SQL Injection Attack Detected".
4. **Response**: Automatically **Blocks IP 192.168.1.66** and isolates the service.
5. **Frontend**: Instantly displays the Alert, updates the Device Status to "Offline/Isolated", and shows the Blocked IP count increase.

---

## 🌍 Multi-Device Remote Demo (Advanced)

Turn this into a real "Red Team vs Blue Team" wargame using 3 devices.

### Device A: Command Center (Your Mac)
Running `npm run dev`. Find your IP (e.g., `192.168.1.5`).

### Device B: The Victim Server (Monitor Agent)
1. Copy `scripts/monitor_server.py` to this device.
2. Install deps: `pip install flask psutil requests flask-cors`
3. Edit the script: Update `MAIN_SERVER_URL` to point to Device A (e.g., `http://192.168.1.5:8001/ingest`).
4. Run: `python3 monitor_server.py`
   - It will start sending **REAL** CPU/RAM stats to your Dashboard.
   - It also opens port `5050` to listen for attacks.

### Device C: The Attacker (Red Team)
1. Copy `scripts/attacker_ui.html` to any device (phone, laptop, tablet).
2. Open it in a browser.
3. Enter Target IP: `http://<DEVICE_B_IP>:5050`
4. Click **"SQL Injection"** or **"DDoS"**.
5. Watch the Dashboard on Device A light up with alerts!

---

## 🏗️ Architecture

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 5173 | React + Vite Dashboard |
| **API Gateway** | 3001 | Socket.IO Bridge |
| **Ingest** | 8001 | Telemetry Entry Point |
| **Detection** | 8002 | Anomaly Analysis |
| **Alert** | 8003 | Alert Generation |
| **Response** | 8004 | Automated Playbooks |

---

## 🛠️ Development

- **Stop All**: Press `Ctrl+C` in the terminal where `npm run dev` is running.
- **Backend Logs**: All backend service logs stream to the same terminal, color-coded.

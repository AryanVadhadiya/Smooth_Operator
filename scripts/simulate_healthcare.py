import time
import requests
import random
import json
from datetime import datetime

# Configuration
INGEST_URL = "http://localhost:8001/ingest"
DEVICE_ID = "healthcare-server-01"
DEVICE_NAME = "Healthcare Server"

def get_telemetry():
    """Generate realistic server telemetry"""
    return {
        "source_ip": "10.0.0.50",
        "service": DEVICE_ID,
        "event_type": "telemetry",
        "received_at": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "cpu": 30 + random.random() * 20,       # 30-50%
            "memory": 40 + random.random() * 10,    # 40-50%
            "network": 200 + random.random() * 100, # 200-300 Mbps
            "requests": int(50 + random.random() * 50)
        }
    }

def main():
    print(f"🏥 Starting Healthcare Server Simulation ({DEVICE_ID})...")
    print(f"📡 Sending telemetry to {INGEST_URL}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            data = get_telemetry()
            try:
                response = requests.post(INGEST_URL, json=data)
                if response.status_code == 200:
                    print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Heartbeat sent: CPU={int(data['payload']['cpu'])}%")
                else:
                    print(f"❌ Failed to send: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Connection Error: {e}")

            time.sleep(2) # Send every 2 seconds

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped.")

if __name__ == "__main__":
    main()

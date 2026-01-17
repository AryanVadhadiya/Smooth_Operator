import os
import time
import json
import threading
import socket
import psutil
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timezone

config = {
    "MAIN_SERVER_URL": os.environ.get("MAIN_SERVER_URL", "http://localhost:8001/ingest")
}

def get_server_url():
    return config["MAIN_SERVER_URL"]

DEVICE_ID = socket.gethostname()
DEVICE_NAME = f"{DEVICE_ID}-node"
DEVICE_IP = socket.gethostbyname(DEVICE_ID)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception:
        return jsonify({
            "status": "online",
            "device": DEVICE_NAME,
            "message": "Monitoring Agent Active. Template not found."
        })

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "device": DEVICE_NAME,
        "message": "Monitoring Agent Active. Ready to be attacked."
    })

@app.route('/config', methods=['GET', 'POST'])
def server_config():
    if request.method == 'POST':
        data = request.json or {}
        server_ip = data.get('server_ip')
        if server_ip:
            if server_ip.startswith("http"):
                 config['MAIN_SERVER_URL'] = server_ip
            else:
                 config['MAIN_SERVER_URL'] = f"http://{server_ip}/ingest"

            print(f"Server URL updated to: {config['MAIN_SERVER_URL']}")
            return jsonify({"status": "success", "server_url": config['MAIN_SERVER_URL']}), 200
        return jsonify({"error": "Missing server_ip"}), 400

    return jsonify({"server_url": config['MAIN_SERVER_URL']}), 200

@app.route('/login', methods=['POST'])
def protect_login():
    data = request.json or {}
    username = data.get("username", "unknown")
    password = data.get("password", "unknown")

    print(f"Login attempt for user: {username} from {request.remote_addr}")

    if "admin" in username or "OR 1=1" in username:
        send_security_event("auth_failure", {
            "username": username,
            "ip": request.remote_addr,
            "reason": "Suspicious pattern detected"
        })
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"status": "success", "token": "dummy-token"}), 200

@app.route('/data', methods=['POST'])
def protect_data():
    data = request.json or {}
    query = data.get("query", "")

    print(f"Query received: {query}")

    send_security_event("http_request", {
        "path": "/data",
        "query": query,
        "method": "POST",
        "ip": request.remote_addr
    })

    return jsonify({"results": []}), 200

def send_security_event(event_type, payload):
    try:
        event = {
            "source_ip": DEVICE_IP,
            "service": DEVICE_NAME,
            "event_type": event_type,
            "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": payload
        }
        requests.post(get_server_url(), json=event, timeout=1)
    except Exception as e:
        print(f"Failed to send event: {e}")

def telemetry_loop():
    print(f"Telemetry Agent started. Reporting to {get_server_url()}")
    consecutive_failures = 0
    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()

            try:
                disk_info = psutil.disk_usage(os.path.abspath(os.sep))
            except:
                disk_info = psutil.disk_usage('/')

            try:
                network_count = len(psutil.net_connections(kind='inet'))
            except Exception:
                network_count = 0

            telemetry = {
                "source_ip": DEVICE_IP,
                "service": DEVICE_NAME,
                "event_type": "telemetry",
                "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "payload": {
                    "cpu": cpu_percent,
                    "memory": memory_info.percent,
                    "disk": disk_info.percent,
                    "network": network_count,
                    "requests": 0
                }
            }

            requests.post(get_server_url(), json=telemetry, timeout=2)
            consecutive_failures = 0
        except Exception:
            consecutive_failures += 1
            if consecutive_failures == 1:
                print(f"Telemetry connection failed to {get_server_url()}")

        time.sleep(2)

if __name__ == '__main__':
    print(f"Threat_Ops Universal Agent")
    print(f"Device: {DEVICE_NAME}")
    print(f"IP:     {DEVICE_IP}")
    print(f"Server: {get_server_url()}")
    print(f"Attack Listener running on port 5050")

    t = threading.Thread(target=telemetry_loop, daemon=True)
    t.start()

    app.run(host='0.0.0.0', port=5050, threaded=True)

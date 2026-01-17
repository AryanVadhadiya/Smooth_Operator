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

# ==========================================
# CONFIGURATION
# ==========================================
# The Threat_Ops.ai Main Server (Ingest Service)
# REPLACE THIS with your Mac's IP if running on a different device!
# Using a list to make it mutable for updates
config = {
    "MAIN_SERVER_URL": os.environ.get("MAIN_SERVER_URL", "http://10.110.5.98:8001/ingest")
}

def get_server_url():
    return config["MAIN_SERVER_URL"]

# This Device's Identity
DEVICE_ID = socket.gethostname()
DEVICE_NAME = f"{DEVICE_ID}-node"

# Get actual network IP (not localhost)
def get_network_ip():
    """Get the actual network IP address (not 127.0.0.1)"""
    try:
        # Create a socket to determine which interface would be used to connect to the internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        # Doesn't actually connect, just determines the route
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to gethostbyname
        return socket.gethostbyname(socket.gethostname())

DEVICE_IP = get_network_ip()

# ==========================================
# FLASK APP (The "Trap Door" for Attacks)
# ==========================================
app = Flask(__name__)
CORS(app)  # Allow attacks from web UI

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "device": DEVICE_NAME,
        "message": "Monitoring Agent Active. Ready to be attacked."
    })

@app.route('/health')
def health():
    """Get current system health metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = int(time.time() - psutil.boot_time())
        
        # Network I/O stats
        net_io = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        # CPU info
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()
        cpu_threads = psutil.cpu_count(logical=True)
        
        # Load average (Unix-like systems)
        try:
            load_avg = psutil.getloadavg()
            load_1min = round(load_avg[0], 2)
        except (AttributeError, OSError):
            load_1min = None
        
        return jsonify({
            "cpu": round(cpu_percent, 1),
            "memory": round(memory_info.percent, 1),
            "disk": round(disk_info.percent, 1),
            "device_ip": DEVICE_IP,
            "total_memory_gb": round(memory_info.total / (1024**3), 1),
            "total_disk_gb": round(disk_info.total / (1024**3), 1),
            "cpu_cores": cpu_count,
            "cpu_threads": cpu_threads,
            "processes": process_count,
            "uptime_seconds": uptime_seconds,
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "network_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
            "network_recv_mb": round(net_io.bytes_recv / (1024**2), 1),
            "load_avg": load_1min,
            "platform": socket.gethostname()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def server_config():
    """Get or update server configuration"""
    if request.method == 'POST':
        data = request.json or {}
        server_ip = data.get('server_ip')
        if server_ip:
            # Update the server URL
            config['MAIN_SERVER_URL'] = f"http://{server_ip}/ingest"
            print(f"✅ Server URL updated to: {config['MAIN_SERVER_URL']}")
            return jsonify({"status": "success", "server_url": config['MAIN_SERVER_URL']}), 200
        return jsonify({"error": "Missing server_ip"}), 400
    
    # GET request - return current configuration
    return jsonify({"server_url": config['MAIN_SERVER_URL']}), 200

@app.route('/login', methods=['POST'])
def protect_login():
    """Simulates a login endpoint that logs attacks"""
    data = request.json or {}
    username = data.get("username", "unknown")

    # 1. Log the local event
    print(f"⚠️  [SECURITY] Login attempt for user: {username} from {request.remote_addr}")

    # 2. Forward suspicious activity to Main Server
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
    """Simulates a data endpoint vulnerable to SQLi"""
    data = request.json or {}
    query = data.get("query", "")

    print(f"⚠️  [SECURITY] Query received: {query}")

    # Forward to Main Server as a "Log"
    send_security_event("http_request", {
        "path": "/data",
        "query": query,
        "method": "POST",
        "ip": request.remote_addr
    })

    return jsonify({"results": []}), 200

# ==========================================
# TELEMETRY SENDER (Background Thread)
# ==========================================
def send_security_event(event_type, payload):
    """Forward a security log to the Threat_Ops Main Server"""
    try:
        event = {
            "source_ip": DEVICE_IP,
            "service": DEVICE_NAME,
            "event_type": event_type,
            "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": payload
        }
        res = requests.post(get_server_url(), json=event, timeout=2)
        print(f"📡 Forwarded alert to Main Server: {res.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection refused or network unreachable: {type(e).__name__}")
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout to {get_server_url()}")
    except Exception as e:
        print(f"❌ Failed to reach Main Server: {type(e).__name__} - {str(e)}")

def telemetry_loop():
    """Constantly reports system health"""
    print(f"🚑 Telemetry Agent started. Reporting to {get_server_url()}")
    consecutive_failures = 0
    while True:
        try:
            # Gather Real System Stats
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # Get network connections (may require sudo on macOS)
            try:
                network_count = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                network_count = 0  # Fallback if permission denied

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
                    "requests": 0  # Placeholder
                }
            }

            requests.post(get_server_url(), json=telemetry, timeout=2)
            if consecutive_failures > 0:
                print(f"✅ Telemetry connection restored")
            consecutive_failures = 0
        except requests.exceptions.ConnectionError:
            consecutive_failures += 1
            if consecutive_failures == 1:
                print(f"❌ Telemetry connection failed: Connection refused to {get_server_url()}")
                print(f"   Server may not be running or port is blocked. Will retry silently...")
        except requests.exceptions.Timeout:
            consecutive_failures += 1
            if consecutive_failures == 1:
                print(f"❌ Telemetry timeout: Cannot reach {get_server_url()}")
        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures == 1:
                print(f"❌ Telemetry error: {type(e).__name__} - {str(e)}")

        time.sleep(2)

# ==========================================
# RUNNER
# ==========================================
if __name__ == '__main__':
    print(f"╔══════════════════════════════════════════╗")
    print(f"║  🛡️  Threat_Ops Universal Agent           ║")
    print(f"║──────────────────────────────────────────║")
    print(f"║  Device: {DEVICE_NAME:<24}        ║")
    print(f"║  IP:     {DEVICE_IP:<24}        ║")
    print(f"║  Server: {get_server_url():<24}  ║")
    print(f"╚══════════════════════════════════════════╝")

    # Start Telemetry in Background
    t = threading.Thread(target=telemetry_loop, daemon=True)
    t.start()

    # Start Attack Listener Web Server
    app.run(host='0.0.0.0', port=5050)
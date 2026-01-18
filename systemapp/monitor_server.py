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
    "MAIN_SERVER_URL": os.environ.get("MAIN_SERVER_URL", "http://localhost:8001/ingest")
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

# ==========================================
# SECURITY: Rate Limiting & Attack Detection
# ==========================================
from collections import defaultdict
import re
import random
import uuid

# Rate limiter storage: {ip: [timestamps]}
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 10  # seconds
RATE_LIMIT_MAX = 5000     # max requests per window (Increased for demo/testing)

# Blocked IPs (temporarily)
blocked_ips = set()
BLOCK_DURATION = 60  # seconds
block_expiry = {}  # {ip: expiry_timestamp}

def send_security_event(event_type, payload):
    """Send security event to Ingest Service"""
    # Inject sector if missing
    if "sector" not in payload:
        payload["sector"] = SECTOR

    data = {
        "event_id": str(uuid.uuid4()),
        "source_ip": DEVICE_IP,
        "service": DEVICE_NAME,
        "event_type": event_type,
        "payload": payload,
        "timestamp": int(time.time()),
        "domain": SECTOR
    }

    try:
        requests.post(get_server_url(), json=data, timeout=1)
    except Exception as e:
        print(f"⚠️ Failed to send event {event_type}: {e}")

# Probabilistic blocking rates (realistic - not 100%)
SQLI_BLOCK_RATE = 0.85    # 85% of SQLi blocked
SECTOR_BLOCK_RATE = 0.80  # 80% of sector attacks blocked

# ==========================================
# IOT FLEET MANAGEMENT (Virtual Devices)
# ==========================================
SECTOR = "healthcare"  # Default sector (can be changed via config)
DEVICE_REGISTRY = {}

DEFAULT_DEVICES = {
    "healthcare": {
        "pacemaker-01": {"type": "pacemaker", "status": "online", "health": 100},
        "mri-scanner-02": {"type": "mri_scanner", "status": "online", "health": 100},
        "infusion-pump-03": {"type": "infusion_pump", "status": "online", "health": 100},
    },
    "agriculture": {
        "soil-sensor-A1": {"type": "soil_sensor", "status": "online", "health": 100},
        "drone-scout-B9": {"type": "drone_scout", "status": "online", "health": 100},
        "irrigation-ctl-C4": {"type": "irrigation_valve", "status": "online", "health": 100},
    },
    "urban": {
        "traffic-light-N1": {"type": "traffic_light", "status": "online", "health": 100},
        "smart-meter-H2": {"type": "smart_meter", "status": "online", "health": 100},
    }
}

def init_devices(sector):
    """Reset registry to sector defaults"""
    global DEVICE_REGISTRY
    defaults = DEFAULT_DEVICES.get(sector, DEFAULT_DEVICES["healthcare"])
    DEVICE_REGISTRY.clear()
    for k, v in defaults.items():
        DEVICE_REGISTRY[k] = v.copy()
        DEVICE_REGISTRY[k]["sector"] = sector
    print(f"🔄 Device Registry re-initialized for Sector: {sector}")

def update_device_health(device_id, damage=0):
    """Degrade device health on attack"""
    if device_id in DEVICE_REGISTRY:
        dev = DEVICE_REGISTRY[device_id]
        dev["health"] = max(0, dev["health"] - damage)
        if dev["health"] < 30:
            dev["status"] = "compromised"
        elif dev["health"] < 70:
            dev["status"] = "warning"
        return dev
    return None

def heal_devices():
    """Slowly recover device health over time (self-healing)"""
    for dev in DEVICE_REGISTRY.values():
        if dev["health"] < 100:
            dev["health"] = min(100, dev["health"] + 5)
            if dev["health"] > 70:
                dev["status"] = "online"

# Background healer
def healer_loop():
    while True:
        time.sleep(10)
        heal_devices()

# Start healer thread
threading.Thread(target=healer_loop, daemon=True).start()

# SQL Injection patterns

# SQL Injection patterns
SQLI_PATTERNS = [
    r"(\b(union|select|insert|update|delete|drop|alter|create|truncate)\b.*\b(from|into|table|database)\b)",
    r"(\bor\b\s+\d+\s*=\s*\d+)",
    r"(\bor\b\s*'[^']*'\s*=\s*'[^']*')",
    r"('.*--)",
    r"(;.*--)",
    r"(\bunion\s+select\b)",
    r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
]
SQLI_REGEX = re.compile('|'.join(SQLI_PATTERNS), re.IGNORECASE)

def is_rate_limited(ip):
    """Check if IP exceeds rate limit"""
    now = time.time()

    # Clean expired blocks
    if ip in block_expiry and now > block_expiry[ip]:
        blocked_ips.discard(ip)
        del block_expiry[ip]

    if ip in blocked_ips:
        return True

    # Clean old timestamps
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    rate_limit_store[ip].append(now)

    if len(rate_limit_store[ip]) > RATE_LIMIT_MAX:
        # Block this IP
        blocked_ips.add(ip)
        block_expiry[ip] = now + BLOCK_DURATION
        print(f"🚫 [BLOCKED] IP {ip} exceeded rate limit - blocked for {BLOCK_DURATION}s")
        return True

    return False

def detect_sqli(query):
    """Detect SQL injection patterns"""
    if not query:
        return False
    return bool(SQLI_REGEX.search(query))

# Request counter for Telemetry
request_count = 0
count_lock = threading.Lock()
last_telemetry_time = time.time()

@app.before_request
def check_rate_limit():
    # Track request count for Telemetry (RPS)
    global request_count
    with count_lock:
        request_count += 1

    # Global rate limiter - runs before every request
    if request.method == "OPTIONS":
        return # Don't rate limit CORS preflight checks

    ip = request.remote_addr
    if is_rate_limited(ip):
        send_security_event("ddos_blocked", {
            "ip": ip,
            "reason": "Rate limit exceeded",
            "path": request.path
        })
        return jsonify({"error": "Too many requests", "blocked": True}), 429

# ... routes ...

# Initialize devices on startup
init_devices(SECTOR)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "device": DEVICE_NAME,
        "sector": SECTOR,
        "message": f"Monitoring Agent Active ({SECTOR.upper()} Node). Tracking {len(DEVICE_REGISTRY)} devices."
    })

@app.route('/devices', methods=['GET'])
def list_devices():
    """List all virtual devices managed by this gateway"""
    return jsonify({
        "sector": SECTOR,
        "gateway": DEVICE_NAME,
        "devices": DEVICE_REGISTRY
    })

@app.route('/health')
def health():
    """Get current system health metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = int(time.time() - psutil.boot_time())

        # Calculate Requests Per Second (RPS)
        now = time.time()
        with count_lock:
            duration = now - last_telemetry_time
            if duration > 0:
                current_rps = request_count / duration
            else:
                current_rps = 0

        # Get network connections
        try:
            network_count = len(psutil.net_connections())
        except (psutil.AccessDenied, PermissionError):
            network_count = 0

        return jsonify({
            "cpu": cpu_percent,
            "memory": memory_info.percent,
            "disk": disk_info.percent,
            "network": network_count, # Dashboard expects 'network' (count)
            "requests_per_second": current_rps,
            "uptime_seconds": uptime_seconds,
            "device_ip": DEVICE_IP,
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "sector": SECTOR,
            "device_count": len(DEVICE_REGISTRY)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def server_config():
    """Get or update server configuration"""
    global SECTOR
    if request.method == 'POST':
        data = request.json or {}

        # Update Server URL
        server_ip = data.get('server_ip')
        if server_ip:
            config['MAIN_SERVER_URL'] = f"http://{server_ip}/ingest"
            print(f"✅ Server URL updated to: {config['MAIN_SERVER_URL']}")

        # Update Sector (Healthcare/Agri/Urban)
        new_sector = data.get('sector')
        if new_sector and new_sector in DEFAULT_DEVICES:
            SECTOR = new_sector
            init_devices(SECTOR)
            print(f"✅ Switched to Sector: {SECTOR}")

        return jsonify({
            "status": "success",
            "server_url": config['MAIN_SERVER_URL'],
            "sector": SECTOR
        }), 200

    # GET request - return current configuration
    return jsonify({
        "server_url": config['MAIN_SERVER_URL'],
        "sector": SECTOR
    }), 200

@app.route('/login', methods=['POST'])
def login_endpoint():
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')
    ip = request.remote_addr

    # Simulate Auth Check
    is_success = random.random() < 0.05 # 5% chance success

    # Send event
    send_security_event("auth_attempt", {
        "username": username,
        "password_masked": "*" * len(password),
        "success": is_success,
        "ip": ip,
        "payload": username # Use username as payload for ML
    })

    if not is_success:
        send_security_event("auth_failure", {
            "username": username,
            "ip": ip,
            "reason": "Invalid credentials",
            "blocked": False # ML might block it later
        })
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"status": "success", "token": "mock_token_123"}), 200

@app.route('/data', methods=['POST'])
def data_endpoint():
    data = request.json or {}
    query = data.get('query', '')
    ip = request.remote_addr

    # Check for SQLi (Heuristic) - optional, backend does heavier lifting
    heuristic_sqli = detect_sqli(query)
    is_blocked = heuristic_sqli and (random.random() < SQLI_BLOCK_RATE)

    action = "BLOCKED" if is_blocked else "PROCESSED"
    print(f"{'🚫' if is_blocked else '⚠️'} [SQL] Query from {ip}: {query[:30]}... Status: {action}")

    # Send event for analysis
    send_security_event("sql_injection_attempt", {
        "query": query,
        "network_data": {
             "Rate": int(request_count / max(1, time.time() - last_telemetry_time) * 100),
             # Mock other network stats matching ML features
             "syn_count": 5, "rst_count": 2, "IAT": 1000
        },
        "ip": ip,
        "blocked": is_blocked,
        "action": action
    })

    if is_blocked:
        return jsonify({"error": "Malicious query detected", "blocked": True}), 403

    # Simulate DB Delay
    time.sleep(random.uniform(0.1, 0.3))
    return jsonify({"status": "success", "rows": []}), 200

# ==========================================
# SECTOR-SPECIFIC ENDPOINTS (ML Attacks)
# ==========================================
@app.route('/iomt', methods=['POST'])
def iomt_endpoint():
    """Healthcare IoMT endpoint"""
    data = request.json or {}
    sensor_data = data.get("sensor_data", [])
    device_id = data.get("device_id")
    ip = request.remote_addr

    # Targeted damage
    dev_status = update_device_health(device_id, damage=15)

    is_blocked = random.random() < SECTOR_BLOCK_RATE
    action = "BLOCKED" if is_blocked else "DETECTED"

    target_msg = f"Target: {device_id}" if device_id else "Target: General"
    print(f"{'🚫' if is_blocked else '⚠️'} [HEALTHCARE] IoMT attack from {ip}. {target_msg}. Status: {action}")

    send_security_event("iomt_attack", {
        "domain": "healthcare",
        "sensor_data": sensor_data,
        "device_id": device_id,
        "device_health": dev_status["health"] if dev_status else None,
        "ip": ip,
        "action": action,
        "blocked_by": "ML_HEALTH_BRAIN" if is_blocked else None,
        "threat_type": "iomt_ddos"
    })

    if is_blocked:
        return jsonify({"error": "IoMT attack blocked", "blocked": True}), 403
    return jsonify({"status": "received", "warning": "anomaly_detected"}), 200

@app.route('/sensors', methods=['POST'])
def sensors_endpoint():
    """Agriculture sensors endpoint"""
    data = request.json or {}
    sensor_data = data.get("sensor_data", [])
    device_id = data.get("device_id")
    ip = request.remote_addr

    # Targeted damage
    dev_status = update_device_health(device_id, damage=15)

    is_blocked = random.random() < SECTOR_BLOCK_RATE
    action = "BLOCKED" if is_blocked else "DETECTED"

    target_msg = f"Target: {device_id}" if device_id else "Target: General"
    print(f"{'🚫' if is_blocked else '⚠️'} [AGRICULTURE] Sensor spoof from {ip}. {target_msg}. Status: {action}")

    send_security_event("sensor_attack", {
        "domain": "agriculture",
        "sensor_data": sensor_data,
        "device_id": device_id,
        "device_health": dev_status["health"] if dev_status else None,
        "ip": ip,
        "action": action,
        "blocked_by": "ML_AGRI_BRAIN" if is_blocked else None,
        "threat_type": "sensor_spoof"
    })

    if is_blocked:
        return jsonify({"error": "Sensor anomaly blocked", "blocked": True}), 403
    return jsonify({"status": "received", "warning": "physics_violation"}), 200

@app.route('/traffic', methods=['POST'])
def traffic_endpoint():
    """Urban traffic endpoint"""
    data = request.json or {}
    sensor_data = data.get("sensor_data", [])
    device_id = data.get("device_id")
    ip = request.remote_addr

    dev_status = update_device_health(device_id, damage=15)

    is_blocked = random.random() < SECTOR_BLOCK_RATE
    action = "BLOCKED" if is_blocked else "DETECTED"

    target_msg = f"Target: {device_id}" if device_id else "Target: General"
    print(f"{'🚫' if is_blocked else '⚠️'} [URBAN] Traffic attack from {ip}. {target_msg}. Status: {action}")

    send_security_event("traffic_attack", {
        "domain": "urban",
        "sensor_data": sensor_data,
        "device_id": device_id,
        "device_health": dev_status["health"] if dev_status else None,
        "ip": ip,
        "action": action,
        "blocked_by": "ML_URBAN_BRAIN" if is_blocked else None,
        "threat_type": "traffic_manipulation"
    })

    if is_blocked:
        return jsonify({"error": "Traffic anomaly blocked", "blocked": True}), 403
    return jsonify({"status": "received", "warning": "traffic_anomaly"}), 200

def telemetry_loop():
    """Constantly reports system health"""
    global request_count, last_telemetry_time
    print(f"🚑 Telemetry Agent started. Reporting to {get_server_url()}")
    consecutive_failures = 0
    while True:
        try:
            # Gather Real System Stats
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')

            # Calculate Requests Per Second (RPS)
            now = time.time()
            with count_lock:
                duration = now - last_telemetry_time
                if duration > 0:
                    current_rps = request_count / duration
                else:
                    current_rps = 0

                # Reset counters
                request_count = 0
                last_telemetry_time = now

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
                    "requests": current_rps,
                    "sector": SECTOR,
                    "devices": DEVICE_REGISTRY  # Send full fleet status
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

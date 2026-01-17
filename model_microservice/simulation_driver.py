"""
╔═══════════════════════════════════════════════════════════════╗
║           PROJECT A.E.G.I.S. - SIMULATION DRIVER             ║
║         Nervous System for Cybersecurity AI Dashboard         ║
╚═══════════════════════════════════════════════════════════════╝

This script simulates realistic IoT traffic across three sectors:
- Healthcare (IoMT devices)
- Agriculture (Smart farming sensors)  
- Urban (Smart city infrastructure)

80% normal traffic, 20% attack scenarios for demo purposes.
"""

import requests
import random
import time
import json
from datetime import datetime

# Try to import colorama for cross-platform colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    print("⚠️  Install colorama for colored output: pip install colorama")

# Configuration
API_URL = "http://127.0.0.1:5000/api/analyze"
DELAY_BETWEEN_REQUESTS = 1.5  # seconds

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def print_status(sector, status, message, response_data):
    """Print colorful terminal logs"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if HAS_COLOR:
        if status in ["blocked", "quarantined", "isolated"]:
            color = Fore.RED
            icon = "🚨 BLOCKED"
        else:
            color = Fore.GREEN
            icon = "✅ ALLOWED"
        
        sector_colors = {
            "healthcare": Fore.CYAN,
            "agriculture": Fore.YELLOW,
            "urban": Fore.MAGENTA
        }
        sector_color = sector_colors.get(sector, Fore.WHITE)
        
        print(f"{Fore.WHITE}[{timestamp}] {sector_color}[{sector.upper():^12}] {color}{icon:^12}{Style.RESET_ALL} │ {message}")
        if response_data.get("score"):
            print(f"{Fore.WHITE}           └─ Threat Score: {Fore.RED}{response_data['score']:.2%}{Style.RESET_ALL}")
    else:
        icon = "🚨 BLOCKED" if status in ["blocked", "quarantined", "isolated"] else "✅ ALLOWED"
        print(f"[{timestamp}] [{sector.upper():^12}] {icon:^12} │ {message}")


def generate_network_data(is_attack=False):
    """
    Generate network packet data for Network Shield
    
    Backend uses heuristic detection based on these thresholds:
    - Rate > 500000 → attack
    - syn_count > 50 → attack
    - rst_count > 30 → attack
    - IAT < 200 → attack  
    - Number > 60 → attack
    
    Normal traffic should stay BELOW these thresholds.
    Attack traffic should EXCEED these thresholds.
    """
    if is_attack:
        # DDoS Attack signature: triggers heuristic detection
        return {
            "Header_Length": random.uniform(40, 60),
            "Protocol Type": random.randint(0, 10),
            "Time_To_Live": random.randint(1, 30),
            "Rate": random.uniform(600000, 8000000),      # > 500000 triggers detection
            "fin_flag_number": random.randint(0, 1),
            "syn_flag_number": random.randint(0, 1),
            "rst_flag_number": random.randint(0, 1),
            "psh_flag_number": random.randint(0, 1),
            "ack_flag_number": random.randint(0, 1),
            "ece_flag_number": 0,
            "cwr_flag_number": 0,
            "ack_count": random.randint(0, 10),
            "syn_count": random.randint(60, 100),         # > 50 triggers detection
            "fin_count": random.randint(0, 10),
            "rst_count": random.randint(40, 100),         # > 30 triggers detection
            "HTTP": 0,
            "HTTPS": 0,
            "DNS": 0,
            "Telnet": 0,
            "SMTP": 0,
            "SSH": 0,
            "IRC": 0,
            "TCP": 1,
            "UDP": 0,
            "DHCP": 0,
            "ARP": 0,
            "ICMP": 0,
            "IGMP": 0,
            "IPv": 1,
            "LLC": 0,
            "Tot sum": random.randint(200000, 315024),
            "Min": random.uniform(42, 100),
            "Max": random.uniform(10000, 36266),
            "AVG": random.uniform(2000, 7831),
            "Std": random.uniform(5000, 11306),
            "Tot size": random.uniform(3000, 7831),
            "IAT": random.uniform(10, 150),               # < 200 triggers detection
            "Number": random.randint(70, 100),            # > 60 triggers detection
            "Variance": random.uniform(50000000, 127834924)
        }
    else:
        # Normal traffic - stays BELOW all detection thresholds
        return {
            "Header_Length": random.uniform(20, 40),
            "Protocol Type": random.randint(0, 5),
            "Time_To_Live": random.randint(64, 128),
            "Rate": random.uniform(1000, 100000),         # Well below 500000
            "fin_flag_number": random.randint(0, 1),
            "syn_flag_number": random.randint(0, 1),
            "rst_flag_number": 0,
            "psh_flag_number": random.randint(0, 1),
            "ack_flag_number": 1,
            "ece_flag_number": 0,
            "cwr_flag_number": 0,
            "ack_count": random.randint(10, 50),
            "syn_count": random.randint(0, 20),           # Well below 50
            "fin_count": random.randint(0, 5),
            "rst_count": random.randint(0, 10),           # Well below 30
            "HTTP": random.choice([0, 1]),
            "HTTPS": random.choice([0, 1]),
            "DNS": random.choice([0, 1]),
            "Telnet": 0,
            "SMTP": 0,
            "SSH": 0,
            "IRC": 0,
            "TCP": 1,
            "UDP": 0,
            "DHCP": 0,
            "ARP": 0,
            "ICMP": 0,
            "IGMP": 0,
            "IPv": 1,
            "LLC": 0,
            "Tot sum": random.randint(120, 10000),
            "Min": random.uniform(42, 200),
            "Max": random.uniform(100, 2000),
            "AVG": random.uniform(46, 500),
            "Std": random.uniform(0, 500),
            "Tot size": random.uniform(46, 1000),
            "IAT": random.uniform(500, 78612),            # Well above 200
            "Number": random.randint(2, 40),              # Well below 60
            "Variance": random.uniform(0, 10000)
        }


# ═══════════════════════════════════════════════════════════════
# SECTOR SIMULATORS
# ═══════════════════════════════════════════════════════════════

def simulate_healthcare():
    """
    Healthcare IoMT simulation
    - Normal: Heart rate 60-100bpm, stable vitals
    - Attack: DDoS on medical devices
    """
    is_attack = random.random() < 0.60  # 20% attack probability
    
    if is_attack:
        # DDoS Attack on healthcare network
        return {
            "sector": "healthcare",
            "network_data": generate_network_data(is_attack=True),
            "sensor_data": [
                random.uniform(60, 100),    # Heart rate
                random.uniform(36, 38),     # Temperature
                random.uniform(95, 100),    # SpO2
                random.uniform(110, 140)    # Blood pressure systolic
            ]
        }, "DDoS Attack on IoMT Network"
    else:
        # Normal healthcare telemetry
        return {
            "sector": "healthcare",
            "network_data": generate_network_data(is_attack=False),
            "sensor_data": [
                random.uniform(60, 100),    # Heart rate
                random.uniform(36.5, 37.5), # Temperature
                random.uniform(96, 99),     # SpO2
                random.uniform(110, 130)    # Blood pressure systolic
            ]
        }, "Normal IoMT Telemetry"


def simulate_agriculture():
    """
    Agriculture IoT simulation
    - Normal: Reasonable soil/weather readings
    - Attack: Physics violation (impossible sensor readings)
    """
    is_attack = random.random() < 0.60  # 20% attack probability
    
    if is_attack:
        # Physics Violation: High temperature + Zero moisture = impossible
        return {
            "sector": "agriculture",
            "network_data": generate_network_data(is_attack=False),
            "sensor_data": [
                random.uniform(45, 60),     # Temperature (very high)
                0.0,                         # Moisture (zero - impossible with high temp)
                random.uniform(6.5, 7.5),   # pH
                random.uniform(100, 200)    # Nitrogen
            ]
        }, "⚡ Physics Violation: Synthetic Data Injection"
    else:
        # Normal agriculture readings
        return {
            "sector": "agriculture",
            "network_data": generate_network_data(is_attack=False),
            "sensor_data": [
                random.uniform(20, 35),     # Temperature
                random.uniform(30, 70),     # Moisture
                random.uniform(6.0, 7.5),   # pH
                random.uniform(50, 150)     # Nitrogen
            ]
        }, "Normal Soil Telemetry"


def simulate_urban():
    """
    Urban smart city simulation
    - Normal: Traffic flow data
    - Attack: SQL Injection in payload
    """
    is_attack = random.random() < 0.60  # 20% attack probability
    
    sql_injection_payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "'; SELECT * FROM passwords; --",
        "1; DELETE FROM traffic_logs WHERE 1=1; --",
        "' UNION SELECT username, password FROM users --",
        "<script>alert('XSS')</script>",
        "'; INSERT INTO admin VALUES('hacker','pwned'); --"
    ]
    
    if is_attack:
        # SQL Injection Attack
        return {
            "sector": "urban",
            "network_data": generate_network_data(is_attack=False),
            "payload": random.choice(sql_injection_payloads),
            "sensor_data": [
                random.uniform(50, 200),    # Vehicle count
                random.uniform(20, 60)      # Average speed
            ]
        }, "💉 SQL Injection Attack Attempt"
    else:
        # Normal traffic data
        return {
            "sector": "urban",
            "network_data": generate_network_data(is_attack=False),
            "sensor_data": [
                random.uniform(50, 150),    # Vehicle count
                random.uniform(30, 50)      # Average speed
            ]
        }, "Normal Traffic Flow"


# ═══════════════════════════════════════════════════════════════
# MAIN SIMULATION LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    """Main simulation loop"""
    print("\n" + "═" * 65)
    print("║" + " " * 10 + "PROJECT A.E.G.I.S. SIMULATION DRIVER" + " " * 10 + "║")
    print("║" + " " * 15 + "Nervous System Online" + " " * 21 + "║")
    print("═" * 65)
    print(f"\n🎯 Target: {API_URL}")
    print(f"⏱️  Delay: {DELAY_BETWEEN_REQUESTS}s between requests")
    print(f"📊 Attack Probability: 20%\n")
    print("─" * 65)
    print(f"{'TIMESTAMP':<15} {'SECTOR':<14} {'STATUS':<14} │ MESSAGE")
    print("─" * 65)
    
    simulators = [simulate_healthcare, simulate_agriculture, simulate_urban]
    request_count = 0
    
    while True:
        try:
            # Pick a random sector
            simulator = random.choice(simulators)
            payload, description = simulator()
            
            # Send request to API
            try:
                response = requests.post(API_URL, json=payload, timeout=5)
                result = response.json()
                
                status = result.get("status", "unknown")
                threat = result.get("threat_level", "low")
                message = result.get("message", description)
                
                print_status(payload["sector"], status, message, result)
                
            except requests.exceptions.ConnectionError:
                if HAS_COLOR:
                    print(f"{Fore.RED}❌ CONNECTION ERROR: Flask server not running at {API_URL}{Style.RESET_ALL}")
                else:
                    print(f"❌ CONNECTION ERROR: Flask server not running at {API_URL}")
                print("   Start the server with: python app.py")
                time.sleep(5)
                continue
            except requests.exceptions.Timeout:
                print(f"⏰ Request timeout - retrying...")
                continue
            
            request_count += 1
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except KeyboardInterrupt:
            print(f"\n\n{'═' * 65}")
            print(f"║ SIMULATION TERMINATED - {request_count} requests sent")
            print(f"{'═' * 65}\n")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()

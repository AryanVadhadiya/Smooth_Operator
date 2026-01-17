import time
import requests
import random
from datetime import datetime

# Configuration
INGEST_URL = "http://localhost:8001/ingest"
TARGET_DEVICE = "healthcare-server-01"
ATTACKER_IP = "192.168.1.66"

ATTACKS = [
    {
        "name": "SQL Injection",
        "payload": {"query": "SELECT * FROM patients WHERE id = 1 OR 1=1"},
        "event_type": "http_request"
    },
    {
        "name": "Brute Force",
        "payload": {"action": "login", "username": "admin", "attempts": 50},
        "event_type": "auth_log"
    }
]

def send_attack(attack_type):
    """Send a malicious packet"""
    attack = ATTACKS[attack_type]
    data = {
        "source_ip": ATTACKER_IP,
        "service": TARGET_DEVICE,
        "event_type": attack["event_type"],
        "received_at": datetime.utcnow().isoformat() + "Z",
        "payload": attack["payload"]
    }

    print(f"⚔️  Launching {attack['name']} against {TARGET_DEVICE}...")
    try:
        response = requests.post(INGEST_URL, json=data)
        if response.status_code == 200:
            print(f"✅ Attack payload delivered!")
        else:
            print(f"❌ Attack failed to deliver: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def main():
    print("☠️  Cyber Attack Simulator initialized")
    print("1. SQL Injection")
    print("2. Brute Force")

    while True:
        choice = input("\nSelect attack (1-2) or 'q' to quit: ")
        if choice == 'q':
            break

        if choice == '1':
            send_attack(0)
        elif choice == '2':
            send_attack(1)
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()

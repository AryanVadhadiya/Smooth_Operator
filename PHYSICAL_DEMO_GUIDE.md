# 3-Machine Physical Demo Setup Guide

This guide explains how to set up the **Red Team vs Blue Team** physical capability you requested.

## 🖥️ The Setup

| Machine | Role | IP Address (Example) | What to do |
|:---|:---|:---|:---|
| **Machine A** | **The Monitor (Blue Team)** | `192.168.1.10` | Runs the Dashboard & API. Detects threats. |
| **Machine B** | **The Target (Victim)** | `192.168.1.50` | The device being protected. Running a simple web server. |
| **Machine C** | **The Attacker (Red Team)** | `192.168.1.99` | Runs the attack script to flood the Target. |

---

## 🚀 Step 1: Configure Machine B (The Target)
We need Machine B to have an "Open Door" (Port) for the system to monitor and for the attacker to hit.

1.  Open a terminal on **Machine B**.
2.  Run this simple command to start a web server on Port 8000:
    ```bash
    # This comes built-in with Python
    python3 -m http.server 8000
    ```
    *(If you don't have Python, just ensure the machine is on and reachable)*.

---

## 🛡️ Step 2: Configure Machine A (The Monitor)
Set up the dashboard to watch Machine B.

1.  **Start CyberThreat_Ops** on Machine A (you already have this running).
2.  Open the **Dashboard** (`http://localhost:8000` or file path).
3.  Click **"➕ Add Device"**.
4.  Fill in the details:
    *   **Device ID**: `TARGET-PC-01`
    *   **Sector**: `Urban Systems` (or Healthcare)
    *   **IP Address**: `192.168.1.50` (<- **IMPORTANT**: Use Machine B's Real IP)
    *   **Port**: `8000` (optional metadata)
5.  Click **Register**.

✅ **Verification**: Watch the dashboard. The Active Monitor is now pinging Machine B every 10 seconds. You should see it listed as "Active".

---

## ⚔️ Step 3: Configure Machine C (The Attacker)
Now, we launch the attack from the third machine.

1.  **Copy the Attack Script**:
    Take the file `src/utils/network_stress_test.py` from Machine A and copy it to Machine C.
    *(You can copy-paste the code into a new file named `attack.py` on Machine C)*.

2.  **Launch the Attack**:
    On Machine C, run:
    ```bash
    # Flood Machine B on Port 8000 with 500 threads
    python3 attack.py 192.168.1.50 8000 500
    ```

---

## 🍿 The Show (What will happen)

1.  **The Attack Begins**: Machine C sends 500 requests/second to Machine B.
2.  **The Congestion**: Machine B's network card gets overwhelmed processing these requests.
3.  **The Detection**:
    *   Machine A (Monitor) pings Machine B.
    *   "Hey, you there?" -> ... ... ... (High Latency or Timeout).
    *   Machine A notices the Latency spike (e.g., >200ms).
4.  **The Alert**:
    *   The Dashboard on Machine A turns **Alert State**.
    *   "🚨 Anomaly Detected on TARGET-PC-01 (High Network Latency)".

You have now successfully demonstrated a physical network attack detection system!

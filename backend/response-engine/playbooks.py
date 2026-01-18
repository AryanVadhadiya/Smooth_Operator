"""
Threat_Ops.ai - Response Engine Playbooks
Automated response actions for security incidents
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import subprocess
import platform
import os


class ActionType(str, Enum):
    BLOCK_IP = "block_ip"
    ISOLATE_SERVICE = "isolate_service"
    THROTTLE = "throttle"
    ALERT_ONLY = "alert_only"
    KILL_PROCESS = "kill_process"
    RESTART_SERVICE = "restart_service"


class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ActionResult:
    """Result of executing an action"""
    action_id: str
    action_type: str
    status: str
    target: str
    message: str
    executed_at: str
    details: Dict[str, Any] = None


# ============================================
# In-Memory State (Demo)
# ============================================
blocked_ips: set = set()
isolated_services: set = set()
throttled_ips: Dict[str, int] = {}  # IP -> requests per minute limit
action_log: List[ActionResult] = []

# System-level blocking enabled (requires sudo/root for real blocking)
SYSTEM_BLOCKING_ENABLED = os.environ.get("ENABLE_SYSTEM_BLOCKING", "false").lower() == "true"


# ============================================
# System-Level Blocking Functions
# ============================================
def _system_block_ip(ip: str) -> bool:
    """Block IP at system level using iptables (Linux) or pfctl (macOS)"""
    if not SYSTEM_BLOCKING_ENABLED:
        print(f"[SYSTEM BLOCK] System blocking disabled. Would block: {ip}")
        return False

    system = platform.system()

    try:
        if system == "Linux":
            # Use iptables to block incoming traffic from IP
            cmd = ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[SYSTEM BLOCK] ✅ Blocked {ip} via iptables")
                return True
            else:
                print(f"[SYSTEM BLOCK] ❌ iptables failed: {result.stderr}")

        elif system == "Darwin":  # macOS
            # Use pfctl to block IP
            # First, add rule to pf.conf
            rule = f"block drop from {ip} to any\\n"
            cmd = f'echo "{rule}" | sudo pfctl -a "threatops" -f -'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Enable the anchor
                subprocess.run(["sudo", "pfctl", "-e"], capture_output=True)
                print(f"[SYSTEM BLOCK] ✅ Blocked {ip} via pfctl")
                return True
            else:
                print(f"[SYSTEM BLOCK] ❌ pfctl failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        print(f"[SYSTEM BLOCK] ⏱️ Timeout blocking {ip}")
    except Exception as e:
        print(f"[SYSTEM BLOCK] ❌ Error blocking {ip}: {e}")

    return False


def _system_unblock_ip(ip: str) -> bool:
    """Unblock IP at system level"""
    if not SYSTEM_BLOCKING_ENABLED:
        print(f"[SYSTEM BLOCK] System blocking disabled. Would unblock: {ip}")
        return False

    system = platform.system()

    try:
        if system == "Linux":
            cmd = ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[SYSTEM BLOCK] ✅ Unblocked {ip} via iptables")
                return True

        elif system == "Darwin":
            # Remove rule from pfctl
            cmd = f'sudo pfctl -a "threatops" -F rules'
            subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            print(f"[SYSTEM BLOCK] ✅ Cleared pfctl rules (unblocked {ip})")
            return True

    except Exception as e:
        print(f"[SYSTEM BLOCK] ❌ Error unblocking {ip}: {e}")

    return False


# ============================================
# Playbook Mapping
# ============================================
RULE_PLAYBOOKS = {
    "sql_injection": [ActionType.BLOCK_IP, ActionType.ALERT_ONLY],
    "brute_force": [ActionType.BLOCK_IP, ActionType.THROTTLE],
    "rate_spike": [ActionType.THROTTLE],
    "high_cpu": [ActionType.ALERT_ONLY],
    "high_memory": [ActionType.ISOLATE_SERVICE],
    "high_network": [ActionType.THROTTLE],
    # ML-triggered rules
    "ml_web_gatekeeper": [ActionType.BLOCK_IP, ActionType.ALERT_ONLY],
    "ml_network_shield": [ActionType.THROTTLE, ActionType.ALERT_ONLY],
    "ml_agri_guardian": [ActionType.ISOLATE_SERVICE, ActionType.ALERT_ONLY],
    "ml_health_sentinel": [ActionType.ISOLATE_SERVICE, ActionType.ALERT_ONLY],
    # Manual response (default block)
    "manual_response": [ActionType.BLOCK_IP, ActionType.THROTTLE],
}


# ============================================
# Action Executors
# ============================================

# IPs that should NEVER be blocked (local machine, localhost, etc.)
PROTECTED_IPS = set()

def _get_local_ips():
    """Get all local machine IPs to protect from accidental blocking"""
    import socket
    local_ips = {"127.0.0.1", "localhost", "::1"}
    try:
        # Get hostname-based IP
        hostname = socket.gethostname()
        local_ips.add(socket.gethostbyname(hostname))
        # Get all network interfaces
        for info in socket.getaddrinfo(hostname, None):
            local_ips.add(info[4][0])
    except:
        pass
    # Common local network prefixes to protect
    return local_ips

# Initialize protected IPs on module load
PROTECTED_IPS = _get_local_ips()
print(f"[PLAYBOOK] Protected IPs (will not be blocked): {PROTECTED_IPS}")

def _is_valid_ip(ip: str) -> bool:
    """Check if string looks like a valid IP address"""
    if not ip:
        return False
    # Skip obvious non-IPs
    if ip in ["unknown", "Unknown", "gateway", "", None]:
        return False
    # Check if it looks like an IP (has dots and numbers)
    parts = ip.split(".")
    if len(parts) == 4:
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False
    return False

def _is_protected_ip(ip: str) -> bool:
    """Check if IP should be protected from blocking"""
    if ip in PROTECTED_IPS:
        return True
    # Don't block localhost ranges
    if ip.startswith("127."):
        return True
    return False

def _extract_ip(alert: Dict[str, Any]) -> str:
    """Extract REAL ATTACKER IP from alert - NOT the local machine IP"""
    evidence = alert.get("evidence", {})

    # Priority order for attacker IP extraction:
    # 1. Explicit attacker_ip field
    # 2. sourceIP (camelCase - from frontend)
    # 3. source_ip from evidence (usually the attacker for attack events)
    # 4. ip field from evidence
    # 5. ml_response source_ip

    candidates = [
        evidence.get("attacker_ip"),
        evidence.get("sourceIP"),  # Frontend sends camelCase
        evidence.get("source_ip"),
        evidence.get("ip"),
        evidence.get("ml_response", {}).get("source_ip"),
    ]

    # DO NOT use alert.source as it's often the victim/local service, not attacker

    print(f"[PLAYBOOK DEBUG] Extracting IP for alert: {alert.get('title')}")
    print(f"[PLAYBOOK DEBUG] Evidence: {evidence}")
    print(f"[PLAYBOOK DEBUG] Candidates: {candidates}")

    for ip in candidates:
        if _is_valid_ip(ip):
            # CRITICAL: Don't return local machine IP as attacker!
            if _is_protected_ip(ip):
                print(f"[PLAYBOOK DEBUG] Skipping protected IP: {ip}")
                continue
            print(f"[PLAYBOOK DEBUG] Found valid attacker IP: {ip}")
            return ip

    print(f"[PLAYBOOK DEBUG] No valid attacker IP found. Returning 'unknown'")
    return "unknown"

def execute_block_ip(alert: Dict[str, Any]) -> ActionResult:
    """Block an IP address - with real system-level blocking"""
    ip = _extract_ip(alert)

    # Skip if no real attacker IP found (telemetry alerts)
    if ip == "unknown":
        return ActionResult(
            action_id="",
            action_type=ActionType.BLOCK_IP,
            status=ActionStatus.SKIPPED,
            target="N/A",
            message="No attacker IP to block (telemetry alert or local IP)",
            executed_at=datetime.utcnow().isoformat() + "Z"
        )

    # Double-check: don't block protected IPs
    if _is_protected_ip(ip):
        return ActionResult(
            action_id="",
            action_type=ActionType.BLOCK_IP,
            status=ActionStatus.SKIPPED,
            target=ip,
            message=f"⚠️ Refusing to block protected IP: {ip}",
            executed_at=datetime.utcnow().isoformat() + "Z"
        )

    if ip in blocked_ips:
        return ActionResult(
            action_id="",
            action_type=ActionType.BLOCK_IP,
            status=ActionStatus.SKIPPED,
            target=ip,
            message=f"IP {ip} already blocked",
            executed_at=datetime.utcnow().isoformat() + "Z"
        )

    # Execute system-level block
    system_blocked = _system_block_ip(ip)
    blocked_ips.add(ip)

    return ActionResult(
        action_id="",
        action_type=ActionType.BLOCK_IP,
        status=ActionStatus.SUCCESS,
        target=ip,
        message=f"✅ IP {ip} blocked {'(system-level)' if system_blocked else '(application-level)'}",
        executed_at=datetime.utcnow().isoformat() + "Z",
        details={
            "blocked_ips_count": len(blocked_ips),
            "duration": "permanent",
            "system_level": system_blocked,
        }
    )


def execute_isolate_service(alert: Dict[str, Any]) -> ActionResult:
    """Isolate a service from the network"""
    source = alert.get("source", "unknown")
    evidence = alert.get("evidence", {})
    service = evidence.get("service", source)

    if service in isolated_services:
        return ActionResult(
            action_id="",
            action_type=ActionType.ISOLATE_SERVICE,
            status=ActionStatus.SKIPPED,
            target=service,
            message=f"Service {service} already isolated",
            executed_at=datetime.utcnow().isoformat() + "Z"
        )

    # Execute isolation (simulated)
    isolated_services.add(service)

    return ActionResult(
        action_id="",
        action_type=ActionType.ISOLATE_SERVICE,
        status=ActionStatus.SUCCESS,
        target=service,
        message=f"🔒 Service {service} isolated from network",
        executed_at=datetime.utcnow().isoformat() + "Z",
        details={
            "isolated_services": list(isolated_services),
            "network_access": "blocked",
        }
    )


def execute_throttle(alert: Dict[str, Any]) -> ActionResult:
    """Apply rate limiting to an IP - only if from actual attack"""
    ip = _extract_ip(alert)

    # Skip if no real attacker IP found (telemetry alerts)
    if ip == "unknown":
        return ActionResult(
            action_id="",
            action_type=ActionType.THROTTLE,
            status=ActionStatus.SKIPPED,
            target="N/A",
            message="No attacker IP to throttle (telemetry alert or local IP)",
            executed_at=datetime.utcnow().isoformat() + "Z"
        )

    # Don't throttle protected IPs
    if _is_protected_ip(ip):
        return ActionResult(
            action_id="",
            action_type=ActionType.THROTTLE,
            status=ActionStatus.SKIPPED,
            target=ip,
            message=f"⚠️ Refusing to throttle protected IP: {ip}",
            executed_at=datetime.utcnow().isoformat() + "Z"
        )

    # Apply rate limit (simulated)
    limit = 10  # requests per minute
    throttled_ips[ip] = limit

    return ActionResult(
        action_id="",
        action_type=ActionType.THROTTLE,
        status=ActionStatus.SUCCESS,
        target=ip,
        message=f"⏱️ Rate limit applied to {ip}: {limit} req/min",
        executed_at=datetime.utcnow().isoformat() + "Z",
        details={
            "rate_limit": limit,
            "unit": "requests_per_minute",
        }
    )


def execute_alert_only(alert: Dict[str, Any]) -> ActionResult:
    """No action, alert only"""
    return ActionResult(
        action_id="",
        action_type=ActionType.ALERT_ONLY,
        status=ActionStatus.SUCCESS,
        target="operators",
        message="📢 Alert sent to operators (no automated action)",
        executed_at=datetime.utcnow().isoformat() + "Z",
        details={
            "action": "notification_only",
            "escalation": "manual_review",
        }
    )


# ============================================
# Action Executor Registry
# ============================================
ACTION_EXECUTORS = {
    ActionType.BLOCK_IP: execute_block_ip,
    ActionType.ISOLATE_SERVICE: execute_isolate_service,
    ActionType.THROTTLE: execute_throttle,
    ActionType.ALERT_ONLY: execute_alert_only,
}


def run_playbook(alert: Dict[str, Any]) -> List[ActionResult]:
    """Run the appropriate playbook for an alert"""
    rule_id = alert.get("rule_id", "")
    actions = RULE_PLAYBOOKS.get(rule_id, [ActionType.ALERT_ONLY])

    results = []
    for action_type in actions:
        executor = ACTION_EXECUTORS.get(action_type)
        if executor:
            result = executor(alert)

            # Don't log/return actions that were skipped due to missing IP (reduce noise for telemetry)
            if result.status == ActionStatus.SKIPPED and "telemetry alert" in result.message:
                continue

            results.append(result)
            action_log.append(result)

            # Keep only last 100 actions
            if len(action_log) > 100:
                action_log.pop(0)

    return results


def get_blocked_ips() -> List[str]:
    """Get list of blocked IPs"""
    return list(blocked_ips)


def get_isolated_services() -> List[str]:
    """Get list of isolated services"""
    return list(isolated_services)


def get_action_log() -> List[ActionResult]:
    """Get action log"""
    return action_log


def clear_all_actions():
    """Reset all actions (for testing) - also clears system-level blocks"""
    global blocked_ips, isolated_services, throttled_ips, action_log

    # Unblock all IPs at system level
    for ip in blocked_ips:
        _system_unblock_ip(ip)

    blocked_ips = set()
    isolated_services = set()
    throttled_ips = {}
    action_log = []


def unblock_ip(ip: str) -> bool:
    """Unblock a specific IP"""
    if ip in blocked_ips:
        _system_unblock_ip(ip)
        blocked_ips.discard(ip)
        return True
    return False

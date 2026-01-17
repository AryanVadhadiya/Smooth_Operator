"""
Threat_Ops.ai - Response Engine Playbooks
Automated response actions for security incidents
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json


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
}


# ============================================
# Action Executors
# ============================================
def execute_block_ip(alert: Dict[str, Any]) -> ActionResult:
    """Block an IP address"""
    evidence = alert.get("evidence", {})
    ip = evidence.get("source_ip", "unknown")

    if ip == "unknown":
        return ActionResult(
            action_id="",
            action_type=ActionType.BLOCK_IP,
            status=ActionStatus.SKIPPED,
            target=ip,
            message="No source IP to block",
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

    # Execute block (simulated)
    blocked_ips.add(ip)

    return ActionResult(
        action_id="",
        action_type=ActionType.BLOCK_IP,
        status=ActionStatus.SUCCESS,
        target=ip,
        message=f"✅ IP {ip} blocked successfully",
        executed_at=datetime.utcnow().isoformat() + "Z",
        details={
            "blocked_ips_count": len(blocked_ips),
            "duration": "permanent",
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
    """Apply rate limiting to an IP"""
    evidence = alert.get("evidence", {})
    ip = evidence.get("source_ip", "unknown")

    if ip == "unknown":
        return ActionResult(
            action_id="",
            action_type=ActionType.THROTTLE,
            status=ActionStatus.SKIPPED,
            target=ip,
            message="No source IP to throttle",
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
    """Reset all actions (for testing)"""
    global blocked_ips, isolated_services, throttled_ips, action_log
    blocked_ips = set()
    isolated_services = set()
    throttled_ips = {}
    action_log = []

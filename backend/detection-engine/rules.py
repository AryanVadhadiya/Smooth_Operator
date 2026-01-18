"""
Threat_Ops.ai - Detection Engine Rules
Rule-based anomaly detection patterns
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import time


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalySignal:
    """Output of a detection rule"""
    anomaly_id: str
    rule_id: str
    rule_name: str
    severity: str
    confidence: float
    description: str
    evidence: Dict[str, Any]
    source_event: Dict[str, Any]
    recommendation: str = ""


# ============================================
# SQL Injection Detection
# ============================================
SQL_INJECTION_PATTERNS = [
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",  # Basic SQL meta-characters
    r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",  # SQL injection attempts
    r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",  # 'or' pattern
    r"((\%27)|(\'))union",  # Union select
    r"exec(\s|\+)+(s|x)p\w+",  # Stored procedure
    r"UNION(\s+)SELECT",  # UNION SELECT
    r"SELECT.*FROM",  # Basic SELECT
    r"INSERT(\s+)INTO",  # INSERT
    r"DELETE(\s+)FROM",  # DELETE
    r"DROP(\s+)TABLE",  # DROP TABLE
    r"UPDATE(\s+)\w+(\s+)SET",  # UPDATE
    r"--",  # SQL comment
    r"1=1",  # Always true
    r"1\s*=\s*1",  # Always true with spaces
    r"OR\s+1=1",  # OR 1=1
    r";\s*DROP",  # Chained DROP
]


def detect_sql_injection(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect SQL injection patterns in event payload"""
    payload = event.get("payload", {})
    event_type = event.get("event_type", "")

    # Extract source IP from multiple possible locations
    def get_source_ip():
        # Priority order for IP extraction
        candidates = [
            event.get("source_ip"),
            payload.get("source_ip"),
            payload.get("ip"),
            payload.get("attacker_ip"),
        ]
        for ip in candidates:
            if ip and ip not in ("unknown", "Unknown", "127.0.0.1", "localhost"):
                return ip
        # Fallback to event source_ip even if localhost (for local testing)
        return event.get("source_ip") or "unknown"

    # If already identified as SQLi or blocked
    if event_type in ["sqli_attack", "sqli_blocked", "sql_injection_attempt"]:
        source_ip = get_source_ip()

        return AnomalySignal(
            anomaly_id="",
            rule_id="sql_injection",
            rule_name="SQL Injection Attempt",
            severity=Severity.CRITICAL,
            confidence=1.0,
            description=f"SQL Injection attempt detected on {payload.get('path', 'unknown endpoint')}",
            evidence={
                "query": payload.get("query"),
                "action": payload.get("action", "DETECTED"),
                "blocked_by": payload.get("blocked_by"),
                "source_ip": source_ip,
                "ip": source_ip,  # Also add 'ip' for frontend compatibility
            },
            source_event=event,
            recommendation="Already neutralized" if payload.get("action") == "BLOCKED" else "Immediate IP Block"
        )

    # Check all string values in payload
    suspicious_values = []
    for key, value in payload.items():
        if isinstance(value, str):
            for pattern in SQL_INJECTION_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    suspicious_values.append({
                        "field": key,
                        "value": value[:100],  # Truncate for safety
                        "pattern": pattern
                    })
                    break

    if suspicious_values:
        # Get source_ip using same robust extraction
        source_ip = get_source_ip()

        return AnomalySignal(
            anomaly_id="",  # Will be assigned by caller
            rule_id="sql_injection",
            rule_name="SQL Injection Detection",
            severity=Severity.CRITICAL,
            confidence=0.85,
            description=f"SQL injection pattern detected in {len(suspicious_values)} field(s)",
            evidence={
                "matched_fields": suspicious_values,
                "source_ip": source_ip,
                "ip": source_ip,  # Also add 'ip' for frontend compatibility
                "service": event.get("service"),
            },
            source_event=event,
            recommendation="Block source IP, review and sanitize input parameters"
        )
    return None


def detect_sector_attack(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect sector-specific attacks (IoMT, Sensors, Traffic)"""
    event_type = event.get("event_type", "")
    payload = event.get("payload", {})

    if event_type in ["iomt_attack", "sensor_attack", "traffic_attack"]:
        # Determine specific type
        attack_name = "Sector Attack"
        if event_type == "iomt_attack": attack_name = "IoMT Device Compromise"
        elif event_type == "sensor_attack": attack_name = "IoT Sensor Spoofing"
        elif event_type == "traffic_attack": attack_name = "Smart City Traffic Hack"

        # Check if it was blocked by ML
        blocked_by = payload.get("blocked_by", "")
        is_ml = "ML" in blocked_by

        return AnomalySignal(
            anomaly_id="",
            rule_id=f"ml_{event_type}" if is_ml else f"rule_{event_type}", # vital for ML tab filter
            rule_name=f"🧠 ML: {attack_name}" if is_ml else f"⚠️ {attack_name}",
            severity=Severity.CRITICAL,
            confidence=0.95 if is_ml else 1.0,
            description=f"{attack_name} detected targeting {payload.get('domain', 'unknown')} sector.",
            evidence={
                "action": payload.get("action", "DETECTED"),
                "blocked_by": blocked_by,
                "sensor_data": payload.get("sensor_data"),
                "threat_type": payload.get("threat_type")
            },
            source_event=event,
            recommendation="Isolate compromised devices immediately"
        )
    return None


# ============================================
# Rate Spike Detection
# ============================================
# Track request counts per IP (in-memory, resets on restart)
request_counts: Dict[str, List[float]] = defaultdict(list)
RATE_WINDOW_SECONDS = 60
RATE_THRESHOLD = 500 # Increased threshold to reduce noise


def detect_rate_spike(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect abnormal request rates from a single IP"""
    source_ip = event.get("source_ip", "")
    event_type = event.get("event_type", "")

    # Skip rate check for events that are already attack reports
    if event_type in ["sqli_attack", "sqli_blocked", "iomt_attack", "sensor_attack", "traffic_attack"]:
        return None

    if not source_ip:
        return None

    current_time = time.time()

    # Add current request timestamp
    request_counts[source_ip].append(current_time)

    # Clean old entries
    cutoff = current_time - RATE_WINDOW_SECONDS
    request_counts[source_ip] = [
        t for t in request_counts[source_ip] if t > cutoff
    ]

    # Check rate
    count = len(request_counts[source_ip])
    if count > RATE_THRESHOLD:
        return AnomalySignal(
            anomaly_id="",
            rule_id="rate_spike",
            rule_name="Abnormal Request Rate",
            severity=Severity.WARNING,
            confidence=0.75,
            description=f"Abnormal request rate detected: {count} requests from {source_ip} in the last minute. This could indicate a DDoS attack or aggressive scraping.",
            evidence={
                "source_ip": source_ip,
                "request_count": count,
                "window_seconds": RATE_WINDOW_SECONDS,
                "threshold": RATE_THRESHOLD,
            },
            source_event=event,
            recommendation="Consider rate limiting or blocking this IP"
        )
    return None


# ============================================
# Metric Threshold Detection
# ============================================
def detect_high_cpu(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect high CPU usage"""
    payload = event.get("payload", {})
    cpu = payload.get("cpu")

    if cpu is not None and cpu > 85:
        return AnomalySignal(
            anomaly_id="",
            rule_id="high_cpu",
            rule_name="High CPU Usage",
            severity=Severity.WARNING if cpu < 95 else Severity.CRITICAL,
            confidence=0.95,
            description=f"CPU usage at {cpu:.1f}% exceeds 85% threshold",
            evidence={
                "cpu_percent": cpu,
                "threshold": 85,
                "service": event.get("service"),
            },
            source_event=event,
            recommendation="Investigate process causing high CPU, consider scaling"
        )
    return None


def detect_high_memory(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect high memory usage"""
    payload = event.get("payload", {})
    memory = payload.get("memory")

    if memory is not None and memory > 90:
        return AnomalySignal(
            anomaly_id="",
            rule_id="high_memory",
            rule_name="High Memory Usage",
            severity=Severity.CRITICAL,
            confidence=0.95,
            description=f"Memory usage at {memory:.1f}% exceeds 90% threshold",
            evidence={
                "memory_percent": memory,
                "threshold": 90,
                "service": event.get("service"),
            },
            source_event=event,
            recommendation="Check for memory leaks, consider restarting service"
        )
    return None


def detect_high_network(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect abnormal network traffic"""
    payload = event.get("payload", {})
    network = payload.get("network")

    if network is not None and network > 900:
        return AnomalySignal(
            anomaly_id="",
            rule_id="high_network",
            rule_name="Network Traffic Spike",
            severity=Severity.WARNING,
            confidence=0.80,
            description=f"Network traffic at {network:.0f} KB/s exceeds 900 KB/s threshold",
            evidence={
                "network_kbps": network,
                "threshold": 900,
                "service": event.get("service"),
            },
            source_event=event,
            recommendation="Investigate traffic source, possible data exfiltration"
        )
    return None


# ============================================
# Suspicious Authentication Detection
# ============================================
failed_auth_counts: Dict[str, List[float]] = defaultdict(list)
AUTH_WINDOW_SECONDS = 300  # 5 minutes
AUTH_THRESHOLD = 5


# Cooldown tracker for brute force alerts to prevent spam
brute_force_cooldown = {}

def detect_brute_force(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect potential brute force attacks"""
    event_type = event.get("event_type", "")
    payload = event.get("payload", {})

    # Check if this is a failed auth attempt
    if event_type not in ["auth_attempt", "auth_failure"]:
        return None

    # For auth_failure event, it is already a failure
    if event_type == "auth_failure" or not payload.get("success", True):
        source_ip = event.get("source_ip", "")
        current_time = time.time()

        failed_auth_counts[source_ip].append(current_time)

        # Clean old entries
        cutoff = current_time - AUTH_WINDOW_SECONDS
        failed_auth_counts[source_ip] = [
            t for t in failed_auth_counts[source_ip] if t > cutoff
        ]

        count = len(failed_auth_counts[source_ip])
        if count >= AUTH_THRESHOLD:
            # Check cooldown (30s)
            last_alert = brute_force_cooldown.get(source_ip, 0)
            if current_time - last_alert < 30:
                return None

            brute_force_cooldown[source_ip] = current_time

            return AnomalySignal(
                anomaly_id="",
                rule_id="brute_force",
                rule_name="Brute Force Attack",
                severity=Severity.CRITICAL,
                confidence=0.90,
                description=f"Multiple failed auth attempts: {count} in {AUTH_WINDOW_SECONDS}s",
                evidence={
                    "source_ip": source_ip,
                    "failed_attempts": count,
                    "window_seconds": AUTH_WINDOW_SECONDS,
                    "username": payload.get("username", "unknown"),
                    "action": payload.get("action", "DETECTED"), # Ensure Blocked tab sees it
                    "blocked_by": payload.get("blocked_by")
                },
                source_event=event,
                recommendation="Block source IP, review account security"
            )
    return None

# ============================================
# Rate Spike Detection
# ============================================
# Track request counts per IP (in-memory, resets on restart)
request_counts: Dict[str, List[float]] = defaultdict(list)
RATE_THRESHOLD = 500  # requests per minute
RATE_WINDOW = 60      # seconds

def detect_rate_spike(event: Dict[str, Any]) -> Optional[AnomalySignal]:
    """Detect abnormal request volume from a single IP"""
    source_ip = event.get("source_ip")
    if not source_ip:
        return None

    event_type = event.get("event_type", "")

    # Skip checking rate for known attack events (reduces noise)
    if event_type in ["sqli_attack", "sqli_blocked", "sql_injection_attempt", "iomt_attack", "sensor_attack", "traffic_attack", "auth_failure", "ddos_blocked"]:
        return None


# ============================================
# Rule Registry
# ============================================
DETECTION_RULES = [
    ("sql_injection", detect_sql_injection),
    ("sector_attack", detect_sector_attack),
    ("rate_spike", detect_rate_spike),
    ("high_cpu", detect_high_cpu),
    ("high_memory", detect_high_memory),
    ("high_network", detect_high_network),
    ("brute_force", detect_brute_force),
]


def run_all_rules(event: Dict[str, Any]) -> List[AnomalySignal]:
    """Run all detection rules against an event"""
    anomalies = []

    for rule_id, rule_func in DETECTION_RULES:
        try:
            result = rule_func(event)
            if result:
                anomalies.append(result)
        except Exception as e:
            print(f"❌ Rule {rule_id} error: {e}")

    return anomalies

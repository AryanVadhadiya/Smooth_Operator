"""
Threat_Ops.ai - IP Manager Module
Centralized IP blocking, rate limiting, and threat tracking
"""

import time
import asyncio
import threading
from typing import Dict, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import json


class ThreatSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BlockReason(str, Enum):
    FLOODING = "flooding"
    SQL_INJECTION = "sql_injection"
    BRUTE_FORCE = "brute_force"
    RATE_LIMIT = "rate_limit"
    MANUAL = "manual"
    ML_DETECTED = "ml_detected"
    ABUSE = "abuse"


@dataclass
class IPBlockRecord:
    """Record of a blocked IP"""
    ip: str
    reason: BlockReason
    severity: ThreatSeverity
    blocked_at: float  # timestamp
    expires_at: float  # timestamp (0 = permanent)
    block_count: int = 1  # How many times blocked
    details: Dict = field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.expires_at == 0:
            return False  # Permanent block
        return time.time() > self.expires_at

    def remaining_seconds(self) -> int:
        if self.expires_at == 0:
            return -1  # Permanent
        remaining = self.expires_at - time.time()
        return max(0, int(remaining))

    def to_dict(self) -> Dict:
        return {
            "ip": self.ip,
            "reason": self.reason.value,
            "severity": self.severity.value,
            "blocked_at": datetime.fromtimestamp(self.blocked_at).isoformat() + "Z",
            "expires_at": datetime.fromtimestamp(self.expires_at).isoformat() + "Z" if self.expires_at > 0 else "permanent",
            "remaining_seconds": self.remaining_seconds(),
            "block_count": self.block_count,
            "details": self.details
        }


@dataclass
class RateLimitRecord:
    """Rate limit tracking for an IP"""
    ip: str
    requests: List[float] = field(default_factory=list)  # timestamps
    limit: int = 100  # requests per window
    window: int = 60  # window in seconds
    throttled: bool = False

    def add_request(self) -> bool:
        """Add request and return True if rate exceeded"""
        now = time.time()
        cutoff = now - self.window
        # Clean old requests
        self.requests = [t for t in self.requests if t > cutoff]
        self.requests.append(now)

        if len(self.requests) > self.limit:
            self.throttled = True
            return True
        return False

    def get_rate(self) -> float:
        """Get current request rate (req/sec)"""
        if not self.requests:
            return 0
        now = time.time()
        cutoff = now - self.window
        recent = [t for t in self.requests if t > cutoff]
        if len(recent) < 2:
            return len(recent)
        elapsed = now - min(recent)
        return len(recent) / max(elapsed, 0.1)


@dataclass
class AuditLogEntry:
    """Audit log for IP actions"""
    timestamp: str
    action: str  # block, unblock, rate_limit, alert
    ip: str
    reason: str
    severity: str
    duration: Optional[int]  # seconds
    triggered_by: str  # rule_id, manual, etc.
    details: Dict = field(default_factory=dict)


@dataclass
class DroppedPacketRecord:
    """Record of a dropped/blocked request"""
    timestamp: str
    source_ip: str
    attack_type: str  # sql_injection, brute_force, flooding, blocked_ip
    reason: str  # rate-limited, blocked, threat-detected
    endpoint: str
    method: str
    severity: str
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "source_ip": self.source_ip,
            "attack_type": self.attack_type,
            "reason": self.reason,
            "endpoint": self.endpoint,
            "method": self.method,
            "severity": self.severity,
            "details": self.details
        }


@dataclass
class BruteForceTracker:
    """Track authentication attempts for an IP"""
    ip: str
    failed_attempts: List[float] = field(default_factory=list)  # timestamps
    usernames_tried: Set[str] = field(default_factory=set)
    last_attempt: float = 0

    # Thresholds
    MAX_ATTEMPTS = 5  # Max failed attempts
    TIME_WINDOW = 60  # seconds
    MIN_INTERVAL = 1.0  # Min seconds between attempts (detect automation)

    def add_attempt(self, username: str) -> Dict:
        """Record failed attempt and return analysis"""
        now = time.time()

        # Calculate interval since last attempt
        interval = now - self.last_attempt if self.last_attempt > 0 else float('inf')
        self.last_attempt = now

        # Clean old attempts
        cutoff = now - self.TIME_WINDOW
        self.failed_attempts = [t for t in self.failed_attempts if t > cutoff]
        self.failed_attempts.append(now)
        self.usernames_tried.add(username)

        attempt_count = len(self.failed_attempts)
        unique_users = len(self.usernames_tried)

        # Analyze threat
        is_brute_force = False
        confidence = 0
        severity = "low"

        if attempt_count >= self.MAX_ATTEMPTS:
            is_brute_force = True
            confidence = min(95, 60 + (attempt_count - self.MAX_ATTEMPTS) * 5)
            severity = "high" if attempt_count >= 10 else "medium"

        # Rapid-fire attempts (automated)
        if interval < self.MIN_INTERVAL and attempt_count >= 3:
            is_brute_force = True
            confidence = max(confidence, 85)
            severity = "high"

        # Multiple usernames = enumeration
        if unique_users >= 5:
            is_brute_force = True
            confidence = max(confidence, 80)
            severity = "high"

        return {
            "is_brute_force": is_brute_force,
            "attempt_count": attempt_count,
            "unique_users": unique_users,
            "interval": interval,
            "confidence": confidence,
            "severity": severity
        }


@dataclass
class FloodingTracker:
    """Track request rate for flooding detection"""
    ip: str
    request_times: List[float] = field(default_factory=list)

    # Thresholds (tunable)
    FLOOD_THRESHOLD = 50  # requests per 10 seconds
    SPIKE_THRESHOLD = 3.0  # multiplier for sudden increase
    TIME_WINDOW = 10  # seconds

    # Historical rate for spike detection
    baseline_rate: float = 0

    def add_request(self) -> Dict:
        """Record request and detect flooding"""
        now = time.time()

        # Clean old requests
        cutoff = now - self.TIME_WINDOW
        self.request_times = [t for t in self.request_times if t > cutoff]
        self.request_times.append(now)

        request_count = len(self.request_times)

        # Calculate current rate
        if len(self.request_times) >= 2:
            elapsed = self.request_times[-1] - self.request_times[0]
            current_rate = request_count / max(elapsed, 0.1)
        else:
            current_rate = request_count

        # Detect flooding
        is_flooding = False
        confidence = 0
        severity = "low"

        # Check absolute threshold
        if request_count >= self.FLOOD_THRESHOLD:
            is_flooding = True
            confidence = min(95, 70 + (request_count - self.FLOOD_THRESHOLD) * 2)
            severity = "critical" if request_count >= 100 else "high"

        # Check for sudden spike
        if self.baseline_rate > 0 and current_rate > self.baseline_rate * self.SPIKE_THRESHOLD:
            is_flooding = True
            confidence = max(confidence, 75)
            severity = "high"

        # Update baseline (rolling average)
        self.baseline_rate = (self.baseline_rate * 0.9 + current_rate * 0.1) if self.baseline_rate > 0 else current_rate

        return {
            "is_flooding": is_flooding,
            "request_count": request_count,
            "current_rate": current_rate,
            "baseline_rate": self.baseline_rate,
            "confidence": confidence,
            "severity": severity
        }


class IPManager:
    """
    Centralized IP threat management system.
    Handles blocking, rate limiting, and threat tracking.
    """

    # Default block durations by severity (seconds)
    DEFAULT_DURATIONS = {
        ThreatSeverity.LOW: 60,        # 1 minute
        ThreatSeverity.MEDIUM: 300,    # 5 minutes
        ThreatSeverity.HIGH: 600,      # 10 minutes
        ThreatSeverity.CRITICAL: 900,  # 15 minutes
    }

    # Rate limit thresholds
    RATE_LIMITS = {
        "default": {"limit": 100, "window": 60},
        "api": {"limit": 60, "window": 60},
        "auth": {"limit": 10, "window": 60},
    }

    # Protected IPs (never block)
    PROTECTED_IPS = {"127.0.0.1", "localhost", "::1"}

    def __init__(self):
        # Core state
        self._blocked_ips: Dict[str, IPBlockRecord] = {}
        self._rate_limits: Dict[str, RateLimitRecord] = defaultdict(
            lambda: RateLimitRecord(ip="", limit=100, window=60)
        )
        self._audit_log: List[AuditLogEntry] = []
        self._threat_scores: Dict[str, float] = defaultdict(float)  # IP -> cumulative threat score

        # NEW: Detection trackers
        self._brute_force_trackers: Dict[str, BruteForceTracker] = {}
        self._flooding_trackers: Dict[str, FloodingTracker] = {}

        # NEW: Dropped packet log
        self._dropped_packets: List[DroppedPacketRecord] = []
        self._dropped_count: Dict[str, int] = defaultdict(int)  # attack_type -> count

        # Callbacks for dropped packet events (will be set by middleware)
        self._on_packet_dropped: Optional[callable] = None

        # Lock for thread safety
        self._lock = threading.RLock()

        # Start cleanup task
        self._cleanup_task = None
        self._running = False

    async def start(self):
        """Start background cleanup task"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("[IP Manager] Started with auto-cleanup enabled")

    async def stop(self):
        """Stop background tasks"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        print("[IP Manager] Stopped")

    async def _cleanup_loop(self):
        """Periodically clean up expired blocks"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[IP Manager] Cleanup error: {e}")

    def _cleanup_expired(self):
        """Remove expired blocks"""
        with self._lock:
            expired = [ip for ip, record in self._blocked_ips.items() if record.is_expired()]
            for ip in expired:
                record = self._blocked_ips.pop(ip)
                self._log_action("auto_unblock", ip, record.reason.value,
                               record.severity.value, None, "expiry",
                               {"was_blocked_for": int(time.time() - record.blocked_at)})
                print(f"[IP Manager] Auto-unblocked {ip} (expired)")

    def _is_protected(self, ip: str) -> bool:
        """Check if IP is protected from blocking"""
        if ip in self.PROTECTED_IPS:
            return True
        if ip.startswith("127."):
            return True
        return False

    def _log_action(self, action: str, ip: str, reason: str, severity: str,
                   duration: Optional[int], triggered_by: str, details: Dict = None):
        """Add entry to audit log"""
        entry = AuditLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            action=action,
            ip=ip,
            reason=reason,
            severity=severity,
            duration=duration,
            triggered_by=triggered_by,
            details=details or {}
        )
        with self._lock:
            self._audit_log.append(entry)
            # Keep last 1000 entries
            if len(self._audit_log) > 1000:
                self._audit_log = self._audit_log[-1000:]

    # ==========================================
    # CORE API: block_ip, unblock_ip, is_blocked
    # ==========================================

    def block_ip(
        self,
        ip: str,
        reason: BlockReason,
        severity: ThreatSeverity,
        duration: Optional[int] = None,
        triggered_by: str = "system",
        details: Dict = None
    ) -> Dict:
        """
        Block an IP address.

        Args:
            ip: IP address to block
            reason: Why the IP is being blocked
            severity: Threat severity level
            duration: Block duration in seconds (None = use default for severity)
            triggered_by: What triggered this block (rule_id, manual, etc.)
            details: Additional details for logging

        Returns:
            Dict with block status and details
        """
        if self._is_protected(ip):
            return {
                "success": False,
                "ip": ip,
                "message": f"Cannot block protected IP: {ip}",
                "protected": True
            }

        # Calculate duration
        if duration is None:
            duration = self.DEFAULT_DURATIONS.get(severity, 300)

        now = time.time()
        expires_at = now + duration if duration > 0 else 0

        with self._lock:
            # Check if already blocked
            existing = self._blocked_ips.get(ip)
            if existing and not existing.is_expired():
                # Extend block and increment count
                existing.block_count += 1
                existing.expires_at = max(existing.expires_at, expires_at)
                existing.severity = max(existing.severity, severity, key=lambda s: list(ThreatSeverity).index(s))

                self._log_action("extend_block", ip, reason.value, severity.value,
                               duration, triggered_by, details)

                return {
                    "success": True,
                    "ip": ip,
                    "action": "extended",
                    "message": f"Extended block for {ip} (count: {existing.block_count})",
                    "block_count": existing.block_count,
                    "expires_in": existing.remaining_seconds()
                }

            # Create new block
            record = IPBlockRecord(
                ip=ip,
                reason=reason,
                severity=severity,
                blocked_at=now,
                expires_at=expires_at,
                block_count=1,
                details=details or {}
            )
            self._blocked_ips[ip] = record

            # Update threat score
            self._threat_scores[ip] += self._severity_to_score(severity)

            self._log_action("block", ip, reason.value, severity.value,
                           duration, triggered_by, details)

        print(f"[IP Manager] 🚫 BLOCKED {ip} for {duration}s | Reason: {reason.value} | Severity: {severity.value}")

        return {
            "success": True,
            "ip": ip,
            "action": "blocked",
            "message": f"IP {ip} blocked for {duration}s",
            "reason": reason.value,
            "severity": severity.value,
            "expires_in": duration,
            "blocked_at": datetime.fromtimestamp(now).isoformat() + "Z"
        }

    def unblock_ip(self, ip: str, triggered_by: str = "manual") -> Dict:
        """
        Unblock an IP address.

        Args:
            ip: IP address to unblock
            triggered_by: What triggered this unblock

        Returns:
            Dict with unblock status
        """
        with self._lock:
            if ip not in self._blocked_ips:
                return {
                    "success": False,
                    "ip": ip,
                    "message": f"IP {ip} is not blocked"
                }

            record = self._blocked_ips.pop(ip)
            duration_was = int(time.time() - record.blocked_at)

            self._log_action("unblock", ip, record.reason.value, record.severity.value,
                           None, triggered_by, {"was_blocked_for": duration_was})

        print(f"[IP Manager] ✅ UNBLOCKED {ip} | Was blocked for {duration_was}s")

        return {
            "success": True,
            "ip": ip,
            "action": "unblocked",
            "message": f"IP {ip} unblocked",
            "was_blocked_for": duration_was
        }

    def is_blocked(self, ip: str) -> Dict:
        """
        Check if an IP is blocked.

        Args:
            ip: IP address to check

        Returns:
            Dict with block status and details
        """
        with self._lock:
            if ip not in self._blocked_ips:
                return {
                    "blocked": False,
                    "ip": ip
                }

            record = self._blocked_ips[ip]
            if record.is_expired():
                # Clean up expired record
                self._blocked_ips.pop(ip)
                return {
                    "blocked": False,
                    "ip": ip,
                    "was_blocked": True,
                    "expired": True
                }

            return {
                "blocked": True,
                "ip": ip,
                "reason": record.reason.value,
                "severity": record.severity.value,
                "remaining_seconds": record.remaining_seconds(),
                "block_count": record.block_count
            }

    # ==========================================
    # RATE LIMITING
    # ==========================================

    def check_rate_limit(self, ip: str, endpoint_type: str = "default") -> Dict:
        """
        Check and update rate limit for an IP.

        Args:
            ip: IP address
            endpoint_type: Type of endpoint (default, api, auth)

        Returns:
            Dict with rate limit status
        """
        limits = self.RATE_LIMITS.get(endpoint_type, self.RATE_LIMITS["default"])

        with self._lock:
            if ip not in self._rate_limits:
                self._rate_limits[ip] = RateLimitRecord(
                    ip=ip,
                    limit=limits["limit"],
                    window=limits["window"]
                )

            record = self._rate_limits[ip]
            exceeded = record.add_request()

            if exceeded:
                return {
                    "allowed": False,
                    "ip": ip,
                    "rate": record.get_rate(),
                    "limit": record.limit,
                    "window": record.window,
                    "message": f"Rate limit exceeded: {record.get_rate():.1f} req/s"
                }

            return {
                "allowed": True,
                "ip": ip,
                "rate": record.get_rate(),
                "limit": record.limit,
                "remaining": record.limit - len(record.requests)
            }

    def apply_throttle(self, ip: str, new_limit: int, duration: int = 300) -> Dict:
        """
        Apply throttling to an IP (reduced rate limit).

        Args:
            ip: IP address
            new_limit: New rate limit (requests per minute)
            duration: How long to apply throttle (seconds)

        Returns:
            Dict with throttle status
        """
        with self._lock:
            record = self._rate_limits[ip]
            record.limit = new_limit
            record.throttled = True

            self._log_action("throttle", ip, "rate_limit", "medium",
                           duration, "system", {"new_limit": new_limit})

        print(f"[IP Manager] ⚡ THROTTLED {ip} to {new_limit} req/min")

        return {
            "success": True,
            "ip": ip,
            "action": "throttled",
            "new_limit": new_limit,
            "duration": duration
        }

    # ==========================================
    # BRUTE FORCE DETECTION
    # ==========================================

    def record_auth_attempt(
        self,
        ip: str,
        username: str,
        success: bool,
        endpoint: str = "/login"
    ) -> Dict:
        """
        Record authentication attempt and detect brute force.

        Args:
            ip: Source IP
            username: Username attempted
            success: Whether auth succeeded
            endpoint: Auth endpoint path

        Returns:
            Dict with detection result and any action taken
        """
        if success:
            # Clear tracker on successful auth
            self._brute_force_trackers.pop(ip, None)
            return {"action": "none", "success": True}

        with self._lock:
            if ip not in self._brute_force_trackers:
                self._brute_force_trackers[ip] = BruteForceTracker(ip=ip)

            tracker = self._brute_force_trackers[ip]
            analysis = tracker.add_attempt(username)

        if analysis["is_brute_force"]:
            # Record dropped packet
            severity = ThreatSeverity(analysis["severity"])
            self._record_dropped_packet(
                source_ip=ip,
                attack_type="brute_force",
                reason="blocked",
                endpoint=endpoint,
                method="POST",
                severity=analysis["severity"],
                details={
                    "attempt_count": analysis["attempt_count"],
                    "unique_users": analysis["unique_users"],
                    "confidence": analysis["confidence"]
                }
            )

            # Block the IP
            return self.block_ip(
                ip,
                BlockReason.BRUTE_FORCE,
                severity,
                triggered_by="brute_force_detector",
                details={
                    "attempt_count": analysis["attempt_count"],
                    "unique_usernames": analysis["unique_users"],
                    "confidence": analysis["confidence"]
                }
            )

        return {
            "action": "monitored",
            "ip": ip,
            "attempt_count": analysis["attempt_count"],
            "is_brute_force": False
        }

    def check_brute_force(self, ip: str) -> Dict:
        """Check current brute force status for an IP"""
        with self._lock:
            if ip not in self._brute_force_trackers:
                return {"ip": ip, "tracked": False}

            tracker = self._brute_force_trackers[ip]
            return {
                "ip": ip,
                "tracked": True,
                "attempt_count": len(tracker.failed_attempts),
                "unique_users": len(tracker.usernames_tried),
                "threshold": tracker.MAX_ATTEMPTS
            }

    # ==========================================
    # FLOODING / DDoS DETECTION
    # ==========================================

    def record_request_for_flooding(self, ip: str, endpoint: str = "/") -> Dict:
        """
        Record request and detect flooding behavior.

        Args:
            ip: Source IP
            endpoint: Request endpoint

        Returns:
            Dict with detection result and any action taken
        """
        with self._lock:
            if ip not in self._flooding_trackers:
                self._flooding_trackers[ip] = FloodingTracker(ip=ip)

            tracker = self._flooding_trackers[ip]
            analysis = tracker.add_request()

        if analysis["is_flooding"]:
            severity = ThreatSeverity(analysis["severity"])

            # Record dropped packet
            self._record_dropped_packet(
                source_ip=ip,
                attack_type="flooding",
                reason="rate-limited" if analysis["request_count"] < 100 else "blocked",
                endpoint=endpoint,
                method="*",
                severity=analysis["severity"],
                details={
                    "request_count": analysis["request_count"],
                    "current_rate": analysis["current_rate"],
                    "confidence": analysis["confidence"]
                }
            )

            # Escalation: first rate-limit, then block
            if analysis["request_count"] >= 100:
                return self.block_ip(
                    ip,
                    BlockReason.FLOODING,
                    severity,
                    triggered_by="flooding_detector",
                    details={
                        "request_count": analysis["request_count"],
                        "rate": analysis["current_rate"],
                        "confidence": analysis["confidence"]
                    }
                )
            else:
                # Apply throttle first
                return self.apply_throttle(ip, new_limit=10, duration=120)

        return {
            "action": "allowed",
            "ip": ip,
            "request_count": analysis["request_count"],
            "rate": analysis["current_rate"],
            "is_flooding": False
        }

    def check_flooding(self, ip: str) -> Dict:
        """Check current flooding status for an IP"""
        with self._lock:
            if ip not in self._flooding_trackers:
                return {"ip": ip, "tracked": False}

            tracker = self._flooding_trackers[ip]
            return {
                "ip": ip,
                "tracked": True,
                "request_count": len(tracker.request_times),
                "baseline_rate": tracker.baseline_rate,
                "threshold": tracker.FLOOD_THRESHOLD
            }

    # ==========================================
    # DROPPED PACKET LOGGING
    # ==========================================

    def _record_dropped_packet(
        self,
        source_ip: str,
        attack_type: str,
        reason: str,
        endpoint: str,
        method: str,
        severity: str,
        details: Dict = None
    ):
        """Record a dropped/blocked packet"""
        record = DroppedPacketRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_ip=source_ip,
            attack_type=attack_type,
            reason=reason,
            endpoint=endpoint,
            method=method,
            severity=severity,
            details=details or {}
        )

        with self._lock:
            self._dropped_packets.append(record)
            self._dropped_count[attack_type] += 1

            # Keep last 500 records
            if len(self._dropped_packets) > 500:
                self._dropped_packets = self._dropped_packets[-500:]

        # Trigger callback if set
        if self._on_packet_dropped:
            try:
                self._on_packet_dropped(record.to_dict())
            except Exception as e:
                print(f"[IP Manager] Callback error: {e}")

        print(f"[IP Manager] 📦 DROPPED: {attack_type} from {source_ip} on {endpoint} ({reason})")

    def record_blocked_request(
        self,
        ip: str,
        endpoint: str,
        method: str,
        block_reason: str,
        severity: str
    ):
        """Record when a blocked IP tries to make a request"""
        self._record_dropped_packet(
            source_ip=ip,
            attack_type="blocked_ip",
            reason="blocked",
            endpoint=endpoint,
            method=method,
            severity=severity,
            details={"original_block_reason": block_reason}
        )

    def record_rate_limited_request(
        self,
        ip: str,
        endpoint: str,
        method: str,
        rate: float,
        limit: int
    ):
        """Record when a request is rate-limited"""
        self._record_dropped_packet(
            source_ip=ip,
            attack_type="rate_limit",
            reason="rate-limited",
            endpoint=endpoint,
            method=method,
            severity="medium",
            details={"rate": rate, "limit": limit}
        )

    def record_sql_injection_blocked(
        self,
        ip: str,
        endpoint: str,
        method: str,
        pattern: str,
        severity: str = "high"
    ):
        """Record when SQL injection is detected and blocked"""
        self._record_dropped_packet(
            source_ip=ip,
            attack_type="sql_injection",
            reason="blocked",
            endpoint=endpoint,
            method=method,
            severity=severity,
            details={"pattern_matched": pattern[:50]}
        )

    def get_dropped_packets(self, limit: int = 100, attack_type: str = None) -> List[Dict]:
        """Get recent dropped packets"""
        with self._lock:
            packets = self._dropped_packets[-limit:]
            if attack_type:
                packets = [p for p in packets if p.attack_type == attack_type]
            return [p.to_dict() for p in reversed(packets)]

    def get_dropped_stats(self) -> Dict:
        """Get dropped packet statistics"""
        with self._lock:
            return {
                "total_dropped": sum(self._dropped_count.values()),
                "by_type": dict(self._dropped_count),
                "recent_count": len(self._dropped_packets)
            }

    def set_dropped_callback(self, callback: callable):
        """Set callback for when packets are dropped"""
        self._on_packet_dropped = callback

    # ==========================================
    # THREAT DETECTION HELPERS
    # ==========================================

    def record_suspicious_activity(
        self,
        ip: str,
        activity_type: str,
        score: float,
        details: Dict = None
    ) -> Dict:
        """
        Record suspicious activity and potentially trigger block.

        Args:
            ip: Source IP
            activity_type: Type of suspicious activity
            score: Threat score (0-100)
            details: Additional details

        Returns:
            Dict with action taken
        """
        with self._lock:
            self._threat_scores[ip] += score

            total_score = self._threat_scores[ip]

            # Determine action based on cumulative score
            if total_score >= 100:
                # Critical - full block
                return self.block_ip(
                    ip,
                    BlockReason.ABUSE,
                    ThreatSeverity.CRITICAL,
                    triggered_by=f"score_threshold_{activity_type}",
                    details={"total_score": total_score, "activity": activity_type, **(details or {})}
                )
            elif total_score >= 75:
                # High - block
                return self.block_ip(
                    ip,
                    BlockReason.ABUSE,
                    ThreatSeverity.HIGH,
                    triggered_by=f"score_threshold_{activity_type}",
                    details={"total_score": total_score, "activity": activity_type, **(details or {})}
                )
            elif total_score >= 50:
                # Medium - throttle
                return self.apply_throttle(ip, new_limit=20, duration=300)

            return {
                "action": "monitored",
                "ip": ip,
                "total_score": total_score,
                "threshold": 50
            }

    def _severity_to_score(self, severity: ThreatSeverity) -> float:
        """Convert severity to threat score"""
        scores = {
            ThreatSeverity.LOW: 10,
            ThreatSeverity.MEDIUM: 25,
            ThreatSeverity.HIGH: 50,
            ThreatSeverity.CRITICAL: 100
        }
        return scores.get(severity, 10)

    # ==========================================
    # STATUS & REPORTING
    # ==========================================

    def get_blocked_ips(self) -> List[Dict]:
        """Get list of all currently blocked IPs"""
        with self._lock:
            # Clean expired first
            self._cleanup_expired()
            return [record.to_dict() for record in self._blocked_ips.values()]

    def get_blocked_ip_set(self) -> Set[str]:
        """Get set of blocked IP addresses (for fast lookup)"""
        with self._lock:
            return {ip for ip, record in self._blocked_ips.items() if not record.is_expired()}

    def get_throttled_ips(self) -> List[Dict]:
        """Get list of throttled IPs"""
        with self._lock:
            return [
                {"ip": ip, "limit": record.limit, "rate": record.get_rate()}
                for ip, record in self._rate_limits.items()
                if record.throttled
            ]

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        with self._lock:
            entries = self._audit_log[-limit:]
            return [
                {
                    "timestamp": e.timestamp,
                    "action": e.action,
                    "ip": e.ip,
                    "reason": e.reason,
                    "severity": e.severity,
                    "duration": e.duration,
                    "triggered_by": e.triggered_by,
                    "details": e.details
                }
                for e in reversed(entries)
            ]

    def get_stats(self) -> Dict:
        """Get IP manager statistics"""
        with self._lock:
            return {
                "blocked_count": len(self._blocked_ips),
                "throttled_count": sum(1 for r in self._rate_limits.values() if r.throttled),
                "audit_log_size": len(self._audit_log),
                "high_threat_ips": [
                    {"ip": ip, "score": score}
                    for ip, score in self._threat_scores.items()
                    if score >= 50
                ]
            }

    def clear_all(self) -> Dict:
        """Clear all blocks and throttles (for testing/reset)"""
        with self._lock:
            count = len(self._blocked_ips)
            self._blocked_ips.clear()
            self._rate_limits.clear()
            self._threat_scores.clear()

            self._log_action("clear_all", "ALL", "manual", "info", None, "admin", {})

        print(f"[IP Manager] 🗑️ Cleared {count} blocked IPs")

        return {
            "success": True,
            "cleared_count": count
        }


# Singleton instance
ip_manager = IPManager()

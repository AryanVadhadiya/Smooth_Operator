"""
Threat_Ops.ai - IP Blocking Middleware
FastAPI middleware for request-level IP blocking and rate limiting
Enhanced with brute force and flooding detection
"""

import time
import asyncio
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ip_manager import ip_manager, BlockReason, ThreatSeverity

# Global reference to Socket.IO for emitting events
_sio = None
_event_queue = []


def set_socket_io(sio):
    """Set the Socket.IO server for emitting events"""
    global _sio
    _sio = sio


async def emit_dropped_packet(data: Dict[str, Any]):
    """Emit dropped packet event to frontend"""
    global _sio
    if _sio:
        await _sio.emit('ip:dropped', data)


def queue_dropped_event(data: Dict[str, Any]):
    """Queue dropped packet event for async emission"""
    global _event_queue
    _event_queue.append(data)


async def process_event_queue():
    """Process queued events (call periodically)"""
    global _event_queue, _sio
    if _sio and _event_queue:
        events = _event_queue.copy()
        _event_queue.clear()
        for event in events:
            try:
                await _sio.emit('ip:dropped', event)
            except Exception as e:
                print(f"[Middleware] Failed to emit event: {e}")


class IPBlockingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces IP blocking and rate limiting at the request level.

    Features:
    - Blocks requests from blocked IPs (returns 403)
    - Applies rate limiting (returns 429 when exceeded)
    - Detects flooding/DDoS patterns
    - Extracts real client IP from headers (supports proxies)
    - Adds IP info to request state for downstream use
    - Logs all dropped packets for visualization
    """

    # Endpoints that bypass blocking (health checks, etc.)
    BYPASS_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/ip/dropped", "/ip/stats"}

    # Endpoint rate limit categories
    RATE_LIMIT_CATEGORIES = {
        "/auth": "auth",
        "/login": "auth",
        "/api": "api",
    }

    def __init__(self, app: ASGIApp, bypass_local: bool = True, enable_flooding_detection: bool = True):
        """
        Args:
            app: FastAPI application
            bypass_local: If True, don't block localhost requests
            enable_flooding_detection: Enable flooding/DDoS detection
        """
        super().__init__(app)
        self.bypass_local = bypass_local
        self.enable_flooding_detection = enable_flooding_detection

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process each request through IP blocking logic"""

        # 1. Extract client IP
        client_ip = self._get_client_ip(request)

        # Store IP in request state for downstream use
        request.state.client_ip = client_ip

        # 2. Check bypass conditions
        path = request.url.path
        method = request.method

        if path in self.BYPASS_PATHS:
            return await call_next(request)

        if self.bypass_local and self._is_local_ip(client_ip):
            return await call_next(request)

        # 3. Check if IP is blocked
        block_status = ip_manager.is_blocked(client_ip)

        if block_status.get("blocked"):
            # Record this blocked request
            ip_manager.record_blocked_request(
                ip=client_ip,
                endpoint=path,
                method=method,
                block_reason=block_status.get("reason", "unknown"),
                severity=block_status.get("severity", "high")
            )
            # Queue event for frontend
            queue_dropped_event({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source_ip": client_ip,
                "attack_type": "blocked_ip",
                "reason": "blocked",
                "endpoint": path,
                "method": method,
                "severity": block_status.get("severity", "high"),
                "original_reason": block_status.get("reason", "unknown")
            })
            return self._blocked_response(client_ip, block_status)

        # 4. Check for flooding (if enabled)
        if self.enable_flooding_detection:
            flood_result = ip_manager.record_request_for_flooding(client_ip, path)
            if flood_result.get("action") in ["throttled", "blocked"]:
                queue_dropped_event({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source_ip": client_ip,
                    "attack_type": "flooding",
                    "reason": flood_result.get("action"),
                    "endpoint": path,
                    "method": method,
                    "severity": "high",
                    "rate": flood_result.get("rate", 0)
                })
                if flood_result.get("action") == "blocked":
                    return self._flooding_response(client_ip, flood_result)

        # 5. Check rate limit
        endpoint_type = self._get_rate_limit_category(path)
        rate_status = ip_manager.check_rate_limit(client_ip, endpoint_type)

        if not rate_status.get("allowed"):
            # Record this rate-limited request
            ip_manager.record_rate_limited_request(
                ip=client_ip,
                endpoint=path,
                method=method,
                rate=rate_status.get("rate", 0),
                limit=rate_status.get("limit", 100)
            )
            # Record as suspicious activity
            ip_manager.record_suspicious_activity(
                client_ip,
                "rate_limit_exceeded",
                score=25,
                details={"path": path, "rate": rate_status.get("rate")}
            )
            # Queue event for frontend
            queue_dropped_event({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source_ip": client_ip,
                "attack_type": "rate_limit",
                "reason": "rate-limited",
                "endpoint": path,
                "method": method,
                "severity": "medium",
                "rate": rate_status.get("rate", 0),
                "limit": rate_status.get("limit", 100)
            })
            return self._rate_limited_response(client_ip, rate_status)

        # 6. Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 7. Add headers with rate limit info
        response.headers["X-RateLimit-Limit"] = str(rate_status.get("limit", 100))
        response.headers["X-RateLimit-Remaining"] = str(rate_status.get("remaining", 100))
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract real client IP, handling proxies and load balancers.
        Priority: X-Forwarded-For > X-Real-IP > CF-Connecting-IP > client.host
        """
        # Check X-Forwarded-For (standard proxy header)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP in chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Check Cloudflare header
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip.strip()

        # Fallback to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    def _is_local_ip(self, ip: str) -> bool:
        """Check if IP is localhost or local network"""
        if ip in {"127.0.0.1", "localhost", "::1"}:
            return True
        if ip.startswith("127."):
            return True
        return False

    def _get_rate_limit_category(self, path: str) -> str:
        """Determine rate limit category based on path"""
        for prefix, category in self.RATE_LIMIT_CATEGORIES.items():
            if path.startswith(prefix):
                return category
        return "default"

    def _blocked_response(self, ip: str, block_status: dict) -> JSONResponse:
        """Generate response for blocked IP"""
        return JSONResponse(
            status_code=403,
            content={
                "error": "Access Denied",
                "message": f"IP {ip} is blocked",
                "reason": block_status.get("reason", "unknown"),
                "severity": block_status.get("severity", "unknown"),
                "remaining_seconds": block_status.get("remaining_seconds", 0),
                "blocked": True
            },
            headers={
                "X-Blocked": "true",
                "X-Block-Reason": block_status.get("reason", "unknown"),
                "Retry-After": str(block_status.get("remaining_seconds", 300))
            }
        )

    def _rate_limited_response(self, ip: str, rate_status: dict) -> JSONResponse:
        """Generate response for rate limited IP"""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": rate_status.get("message", "Rate limit exceeded"),
                "ip": ip,
                "rate": rate_status.get("rate"),
                "limit": rate_status.get("limit"),
                "rate_limited": True
            },
            headers={
                "X-RateLimit-Limit": str(rate_status.get("limit", 100)),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "60"
            }
        )

    def _flooding_response(self, ip: str, flood_status: dict) -> JSONResponse:
        """Generate response for flooding detection"""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Flooding Detected",
                "message": f"High request rate detected from {ip}",
                "ip": ip,
                "rate": flood_status.get("rate"),
                "flooding": True
            },
            headers={
                "X-Blocked": "true",
                "X-Block-Reason": "flooding",
                "Retry-After": "120"
            }
        )


class BruteForceDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that detects brute force login attempts.
    Should be placed after IPBlockingMiddleware.
    """

    AUTH_ENDPOINTS = {"/login", "/auth", "/auth/login", "/api/auth", "/api/login"}

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Detect brute force on auth endpoints"""
        path = request.url.path
        method = request.method

        # Only check POST to auth endpoints
        if method != "POST" or not any(path.startswith(ep) for ep in self.AUTH_ENDPOINTS):
            return await call_next(request)

        client_ip = getattr(request.state, 'client_ip', None)
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Process the request
        response = await call_next(request)

        # If auth failed (401/403), record the attempt
        if response.status_code in (401, 403):
            # Try to extract username from request body
            username = "unknown"
            try:
                # Note: In production, you'd need to properly read the body
                # This is a simplified version
                username = request.headers.get("X-Username", "unknown")
            except:
                pass

            result = ip_manager.record_auth_attempt(
                ip=client_ip,
                username=username,
                success=False,
                endpoint=path
            )

            if result.get("action") == "blocked":
                # Emit brute force detection event
                queue_dropped_event({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source_ip": client_ip,
                    "attack_type": "brute_force",
                    "reason": "blocked",
                    "endpoint": path,
                    "method": method,
                    "severity": "high",
                    "attempt_count": result.get("details", {}).get("attempt_count", 0)
                })

                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Brute Force Detected",
                        "message": f"Too many failed login attempts from {client_ip}",
                        "blocked": True,
                        "ip": client_ip
                    }
                )

        return response


class ThreatDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that analyzes requests for suspicious patterns.
    Works alongside IPBlockingMiddleware to detect threats.
    """

    # SQL Injection patterns
    SQL_PATTERNS = [
        "' or ", "' and ", "1=1", "1 = 1",
        "union select", "drop table", "delete from",
        "--", ";--", "/*", "*/",
        "exec(", "execute(",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        "<script", "javascript:", "onerror=",
        "onclick=", "onload=", "eval(",
    ]

    def __init__(self, app: ASGIApp, enable_auto_block: bool = True):
        """
        Args:
            app: FastAPI application
            enable_auto_block: Automatically block IPs with malicious payloads
        """
        super().__init__(app)
        self.enable_auto_block = enable_auto_block

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Analyze request for threats"""

        client_ip = getattr(request.state, 'client_ip', None)
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        path = request.url.path
        method = request.method

        # Skip if already blocked
        if ip_manager.is_blocked(client_ip).get("blocked"):
            return await call_next(request)

        # Analyze query parameters
        threat_detected = False
        threat_type = None
        threat_details = {}
        matched_pattern = None

        # Check query string
        query_string = str(request.url.query)
        if query_string:
            sql_threat, sql_pattern = self._detect_sql_injection(query_string)
            if sql_threat:
                threat_detected = True
                threat_type = "sql_injection"
                threat_details["query_string"] = query_string[:200]
                matched_pattern = sql_pattern

            xss_threat, xss_pattern = self._detect_xss(query_string)
            if xss_threat:
                threat_detected = True
                threat_type = "xss"
                threat_details["query_string"] = query_string[:200]
                matched_pattern = xss_pattern

        # Check path for injection attempts
        sql_in_path, path_pattern = self._detect_sql_injection(path)
        xss_in_path, xss_path_pattern = self._detect_xss(path)

        if sql_in_path or xss_in_path:
            threat_detected = True
            threat_type = threat_type or "path_injection"
            threat_details["path"] = path
            matched_pattern = path_pattern or xss_path_pattern

        # If threat detected, record and potentially block
        if threat_detected and self.enable_auto_block:
            # Record SQL injection specifically
            if threat_type == "sql_injection":
                ip_manager.record_sql_injection_blocked(
                    ip=client_ip,
                    endpoint=path,
                    method=method,
                    pattern=matched_pattern or "unknown",
                    severity="high"
                )

            # Emit dropped packet event
            queue_dropped_event({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source_ip": client_ip,
                "attack_type": threat_type,
                "reason": "blocked",
                "endpoint": path,
                "method": method,
                "severity": "high",
                "pattern": matched_pattern
            })

            result = ip_manager.record_suspicious_activity(
                client_ip,
                threat_type,
                score=50,  # SQL/XSS attempts are serious
                details=threat_details
            )

            # If action was block, return 403
            if result.get("action") == "blocked":
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Threat Detected",
                        "message": f"Malicious {threat_type} pattern detected",
                        "blocked": True,
                        "ip": client_ip
                    }
                )

        return await call_next(request)

    def _detect_sql_injection(self, text: str) -> tuple:
        """Check text for SQL injection patterns, return (detected, pattern)"""
        text_lower = text.lower()
        for pattern in self.SQL_PATTERNS:
            if pattern in text_lower:
                return True, pattern
        return False, None

    def _detect_xss(self, text: str) -> tuple:
        """Check text for XSS patterns, return (detected, pattern)"""
        text_lower = text.lower()
        for pattern in self.XSS_PATTERNS:
            if pattern in text_lower:
                return True, pattern
        return False, None


def setup_ip_middleware(app, sio=None, bypass_local: bool = True, enable_threat_detection: bool = True):
    """
    Convenience function to set up all IP-related middleware.

    Args:
        app: FastAPI application
        sio: Socket.IO server for emitting events
        bypass_local: Don't block localhost requests
        enable_threat_detection: Enable automatic threat detection
    """
    # Set Socket.IO reference for event emission
    if sio:
        set_socket_io(sio)

    # Add brute force detection (innermost - runs last)
    app.add_middleware(BruteForceDetectionMiddleware)

    # Add threat detection
    if enable_threat_detection:
        app.add_middleware(ThreatDetectionMiddleware, enable_auto_block=True)

    # Add IP blocking (outermost - runs first)
    app.add_middleware(IPBlockingMiddleware, bypass_local=bypass_local, enable_flooding_detection=True)

    print("[Middleware] IP blocking, threat detection, and brute force middleware installed")

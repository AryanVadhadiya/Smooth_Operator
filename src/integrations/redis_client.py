"""
Redis Client for CyberThreat_Ops
Provides caching, real-time state management, and pub/sub for alerts
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not installed. Redis integration disabled.")


class RedisClient:
    """
    Client for Redis caching and real-time state management
    Used for:
    - Caching active alerts for fast retrieval
    - Storing device state and health status
    - Real-time pub/sub for alert notifications
    - Rate limiting and deduplication
    """
    
    # Redis key prefixes
    PREFIX_ALERT = "alert:"
    PREFIX_DEVICE = "device:"
    PREFIX_MODEL = "model:"
    PREFIX_RESPONSE = "response:"
    PREFIX_STATS = "stats:"
    
    # TTL values (in seconds)
    TTL_ALERT = 86400  # 24 hours
    TTL_DEVICE = 300   # 5 minutes
    TTL_STATS = 3600   # 1 hour
    
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 db: int = 0,
                 password: str = None):
        """Initialize Redis client"""
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', '6379'))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')
        
        self.client = None
        self.pubsub = None
        self.connected = False
        
        if REDIS_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """Establish connection to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            
            # Test connection
            self.client.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
            # Initialize pub/sub
            self.pubsub = self.client.pubsub()
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
    
    # ==================== Alert Management ====================
    
    def cache_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Cache an alert in Redis
        
        Args:
            alert: Alert dictionary with alert_id
        """
        if not self.connected or not REDIS_AVAILABLE:
            return False
        
        try:
            alert_id = alert.get('alert_id')
            if not alert_id:
                return False
            
            key = f"{self.PREFIX_ALERT}{alert_id}"
            self.client.setex(key, self.TTL_ALERT, json.dumps(alert, default=str))
            
            # Add to sector-specific sorted set for quick filtering
            sector = alert.get('sector', 'unknown')
            severity = alert.get('severity', 'P4')
            score = self._severity_to_score(severity)
            timestamp = datetime.utcnow().timestamp()
            
            self.client.zadd(
                f"{self.PREFIX_ALERT}sector:{sector}",
                {alert_id: score * 1e10 + timestamp}
            )
            
            # Add to active alerts set
            self.client.sadd(f"{self.PREFIX_ALERT}active", alert_id)
            
            # Publish alert for real-time listeners
            self.publish_alert(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching alert: {e}")
            return False
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get a specific alert by ID"""
        if not self.connected or not REDIS_AVAILABLE:
            return None
        
        try:
            key = f"{self.PREFIX_ALERT}{alert_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting alert: {e}")
            return None
    
    def get_active_alerts(self, 
                         sector: str = None,
                         severity: str = None,
                         limit: int = 100) -> List[Dict]:
        """Get active alerts, optionally filtered by sector/severity"""
        if not self.connected or not REDIS_AVAILABLE:
            return []
        
        try:
            if sector:
                # Get from sector-specific set
                alert_ids = self.client.zrevrange(
                    f"{self.PREFIX_ALERT}sector:{sector}",
                    0, limit - 1
                )
            else:
                # Get from active alerts set
                alert_ids = list(self.client.smembers(f"{self.PREFIX_ALERT}active"))[:limit]
            
            alerts = []
            for alert_id in alert_ids:
                alert = self.get_alert(alert_id)
                if alert:
                    if severity and alert.get('severity') != severity:
                        continue
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str, user: str = "admin") -> bool:
        """Mark an alert as acknowledged"""
        if not self.connected or not REDIS_AVAILABLE:
            return False
        
        try:
            alert = self.get_alert(alert_id)
            if alert:
                alert['status'] = 'acknowledged'
                alert['acknowledged_by'] = user
                alert['acknowledged_at'] = datetime.utcnow().isoformat()
                self.cache_alert(alert)
                return True
            return False
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    def resolve_alert(self, alert_id: str, notes: str = "") -> bool:
        """Mark an alert as resolved"""
        if not self.connected or not REDIS_AVAILABLE:
            return False
        
        try:
            alert = self.get_alert(alert_id)
            if alert:
                alert['status'] = 'resolved'
                alert['resolved_at'] = datetime.utcnow().isoformat()
                alert['resolution_notes'] = notes
                
                # Update cache
                key = f"{self.PREFIX_ALERT}{alert_id}"
                self.client.setex(key, self.TTL_ALERT, json.dumps(alert, default=str))
                
                # Remove from active set
                self.client.srem(f"{self.PREFIX_ALERT}active", alert_id)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    # ==================== Device State ====================
    
    def update_device_state(self, device_id: str, state: Dict[str, Any]) -> bool:
        """Update device state/health information"""
        if not self.connected or not REDIS_AVAILABLE:
            return False
        
        try:
            key = f"{self.PREFIX_DEVICE}{device_id}"
            state['last_seen'] = datetime.utcnow().isoformat()
            self.client.setex(key, self.TTL_DEVICE, json.dumps(state, default=str))
            return True
        except Exception as e:
            logger.error(f"Error updating device state: {e}")
            return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict]:
        """Get current device state"""
        if not self.connected or not REDIS_AVAILABLE:
            return None
        
        try:
            key = f"{self.PREFIX_DEVICE}{device_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting device state: {e}")
            return None
    
    # ==================== Statistics ====================
    
    def increment_stat(self, stat_name: str, value: int = 1) -> int:
        """Increment a counter statistic"""
        if not self.connected or not REDIS_AVAILABLE:
            return 0
        
        try:
            key = f"{self.PREFIX_STATS}{stat_name}"
            return self.client.incrby(key, value)
        except Exception as e:
            logger.error(f"Error incrementing stat: {e}")
            return 0
    
    def get_stat(self, stat_name: str) -> int:
        """Get a counter statistic"""
        if not self.connected or not REDIS_AVAILABLE:
            return 0
        
        try:
            key = f"{self.PREFIX_STATS}{stat_name}"
            value = self.client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Error getting stat: {e}")
            return 0
    
    def get_all_stats(self) -> Dict[str, int]:
        """Get all statistics"""
        if not self.connected or not REDIS_AVAILABLE:
            return {}
        
        try:
            keys = self.client.keys(f"{self.PREFIX_STATS}*")
            stats = {}
            for key in keys:
                stat_name = key.replace(self.PREFIX_STATS, "")
                value = self.client.get(key)
                stats[stat_name] = int(value) if value else 0
            return stats
        except Exception as e:
            logger.error(f"Error getting all stats: {e}")
            return {}
    
    # ==================== Pub/Sub ====================
    
    def publish_alert(self, alert: Dict[str, Any]) -> bool:
        """Publish alert to subscribers"""
        if not self.connected or not REDIS_AVAILABLE:
            return False
        
        try:
            channel = f"alerts:{alert.get('sector', 'general')}"
            self.client.publish(channel, json.dumps(alert, default=str))
            
            # Also publish to severity-specific channel
            severity = alert.get('severity', 'P4')
            if severity in ['P0', 'P1']:
                self.client.publish("alerts:critical", json.dumps(alert, default=str))
            
            return True
        except Exception as e:
            logger.error(f"Error publishing alert: {e}")
            return False
    
    def subscribe_alerts(self, sectors: List[str] = None, callback=None):
        """Subscribe to alert channels"""
        if not self.connected or not REDIS_AVAILABLE:
            return None
        
        try:
            channels = []
            if sectors:
                channels = [f"alerts:{sector}" for sector in sectors]
            else:
                channels = ["alerts:*"]
            
            self.pubsub.psubscribe(*channels)
            
            if callback:
                for message in self.pubsub.listen():
                    if message['type'] == 'pmessage':
                        alert = json.loads(message['data'])
                        callback(alert)
            
            return self.pubsub
        except Exception as e:
            logger.error(f"Error subscribing to alerts: {e}")
            return None
    
    # ==================== Rate Limiting ====================
    
    def check_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Check if an action is within rate limit
        
        Args:
            key: Unique identifier for the rate limit (e.g., "alert:device_id")
            limit: Maximum allowed actions in the window
            window: Time window in seconds
        
        Returns:
            True if within limit, False if exceeded
        """
        if not self.connected or not REDIS_AVAILABLE:
            return True  # Allow if Redis unavailable
        
        try:
            rate_key = f"ratelimit:{key}"
            current = self.client.get(rate_key)
            
            if current is None:
                self.client.setex(rate_key, window, 1)
                return True
            
            if int(current) >= limit:
                return False
            
            self.client.incr(rate_key)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True
    
    # ==================== Helpers ====================
    
    def _severity_to_score(self, severity: str) -> int:
        """Convert severity to numeric score for sorting"""
        scores = {'P0': 5, 'P1': 4, 'P2': 3, 'P3': 2, 'P4': 1}
        return scores.get(severity, 0)
    
    def close(self):
        """Close the Redis connection"""
        if self.client:
            self.client.close()
            self.connected = False

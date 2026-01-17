"""
Alert manager - Handles alert routing and notification
"""
import json
import logging
import math
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    P0 = "Critical"
    P1 = "High"
    P2 = "Medium"
    P3 = "Low"
    P4 = "Informational"


class AlertManager:
    """Manages alert generation, routing, and notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_levels = config.get('alert_levels', {})
        self.alert_history = []
        self.active_alerts = {}
        
        # Notification settings
        self.smtp_config = {
            'host': config.get('SMTP_HOST', 'localhost'),
            'port': config.get('SMTP_PORT', 587),
            'user': config.get('SMTP_USER', ''),
            'password': config.get('SMTP_PASSWORD', ''),
        }
        self.email_to = config.get('ALERT_EMAIL_TO', 'admin@example.com')
        self.slack_webhook = config.get('SLACK_WEBHOOK_URL', '')
        
    def create_alert(self, detection_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an alert from detection result"""
        if not detection_result.get('is_anomaly', False):
            return None
        
        # Check for existing active (unresolved) alert for this device
        for aid, a in self.active_alerts.items():
            if a['device_id'] == detection_result['device_id'] and not a['resolved']:
                # Update existing alert instead of creating new one
                last_seen = datetime.fromisoformat(a['timestamp'])
                now = datetime.utcnow()
                
                a['timestamp'] = now.isoformat()
                a['anomaly_score'] = detection_result['anomaly_score']
                a['detector_votes'] = detection_result['detector_votes']
                
                # If recurrence after quiet period (60s), un-acknowledge it
                time_diff = (now - last_seen).total_seconds()
                if time_diff > 60 and a.get('acknowledged'):
                    a['acknowledged'] = False
                    logger.info(f"Re-activating acknowledged alert {aid} due to recurrence")
                a['description'] = self._generate_description(detection_result)
                # Keep existing severity unless new one is higher priority (lower P value)
                current_severity_val = int(a['severity'][1:])
                new_severity_val = int(detection_result.get('severity', 'P4')[1:])
                if new_severity_val < current_severity_val:
                    a['severity'] = detection_result.get('severity', 'P4')
                    a['severity_name'] = AlertSeverity[a['severity']].value
                
                logger.info(f"Updated existing alert {aid} for device {detection_result['device_id']}")
                return a

        alert_id = f"{detection_result['device_id']}_{datetime.utcnow().timestamp()}"
        severity = detection_result.get('severity', 'P4')
        
        alert = {
            'alert_id': alert_id,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'severity_name': AlertSeverity[severity].value,
            'device_id': detection_result['device_id'],
            'device_type': detection_result['device_type'],
            'sector': detection_result['sector'],
            'anomaly_score': detection_result['anomaly_score'],
            'detector_votes': detection_result['detector_votes'],
            'description': self._generate_description(detection_result),
            'status': 'active',
            'acknowledged': False,
            'resolved': False,
            'response_actions': []
        }
        
        # Store alert
        self.alert_history.append(alert)
        self.active_alerts[alert_id] = alert
        
        logger.info(f"Created alert {alert_id}: {severity} - {alert['description']}")
        
        return alert
    
    def _generate_description(self, detection_result: Dict[str, Any]) -> str:
        """Generate human-readable alert description"""
        device_id = detection_result['device_id']
        device_type = detection_result['device_type']
        sector = detection_result['sector']
        score = detection_result['anomaly_score']
        
        description = f"Anomaly detected on {sector} device {device_id} ({device_type}). "
        description += f"Anomaly score: {score:.2f}. "
        
        # Add detector information
        votes = detection_result.get('detector_votes', {})
        if votes:
            detecting_algos = [name for name, vote in votes.items() if vote == 1]
            if detecting_algos:
                description += f"Detected by: {', '.join(detecting_algos)}."
        
        return description
    
    def route_alert(self, alert: Dict[str, Any]) -> bool:
        """Route alert to appropriate notification channels"""
        severity = alert['severity']
        config = self.alert_levels.get(severity, {})
        channels = config.get('notification_channels', ['email'])
        
        success = True
        
        for channel in channels:
            try:
                if channel == 'email':
                    self._send_email_notification(alert)
                elif channel == 'slack':
                    self._send_slack_notification(alert)
                elif channel == 'sms':
                    logger.info(f"SMS notification for alert {alert['alert_id']} (not implemented)")
                elif channel == 'voice':
                    logger.info(f"Voice notification for alert {alert['alert_id']} (not implemented)")
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
                success = False
        
        return success
    
    def _send_email_notification(self, alert: Dict[str, Any]):
        """Send email notification"""
        try:
            subject = f"[{alert['severity']}] Security Alert: {alert['device_id']}"
            
            body = f"""
Security Alert Notification
==========================

Alert ID: {alert['alert_id']}
Severity: {alert['severity_name']} ({alert['severity']})
Timestamp: {alert['timestamp']}

Device Information:
- Device ID: {alert['device_id']}
- Device Type: {alert['device_type']}
- Sector: {alert['sector']}

Detection Details:
{alert['description']}

Anomaly Score: {alert['anomaly_score']:.3f}

Detector Votes:
{json.dumps(alert['detector_votes'], indent=2)}

Action Required:
Please investigate this alert immediately.

---
CyberThreat_Ops Monitoring System
"""
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['user']
            msg['To'] = self.email_to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (only if SMTP is configured)
            if self.smtp_config['user'] and self.smtp_config['password']:
                with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                    server.starttls()
                    server.login(self.smtp_config['user'], self.smtp_config['password'])
                    server.send_message(msg)
                logger.info(f"Email sent for alert {alert['alert_id']}")
            else:
                logger.info(f"Email notification prepared for alert {alert['alert_id']} (SMTP not configured)")
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    def _send_slack_notification(self, alert: Dict[str, Any]):
        """Send Slack notification"""
        if not self.slack_webhook:
            logger.info(f"Slack notification for alert {alert['alert_id']} (webhook not configured)")
            return
        
        try:
            # Determine color based on severity
            color_map = {
                'P0': '#ff0000',  # Red
                'P1': '#ff6600',  # Orange
                'P2': '#ffcc00',  # Yellow
                'P3': '#3399ff',  # Blue
                'P4': '#999999',  # Gray
            }
            color = color_map.get(alert['severity'], '#999999')
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"[{alert['severity']}] Security Alert",
                    'text': alert['description'],
                    'fields': [
                        {'title': 'Device ID', 'value': alert['device_id'], 'short': True},
                        {'title': 'Device Type', 'value': alert['device_type'], 'short': True},
                        {'title': 'Sector', 'value': alert['sector'], 'short': True},
                        {'title': 'Anomaly Score', 'value': f"{alert['anomaly_score']:.3f}", 'short': True},
                    ],
                    'footer': 'CyberThreat_Ops',
                    'ts': int(datetime.utcnow().timestamp())
                }]
            }
            
            response = requests.post(self.slack_webhook, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Slack notification sent for alert {alert['alert_id']}")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            raise
    
    def acknowledge_alert(self, alert_id: str, user: str = 'system') -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['acknowledged'] = True
            self.active_alerts[alert_id]['acknowledged_by'] = user
            self.active_alerts[alert_id]['acknowledged_at'] = datetime.utcnow().isoformat()
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution_notes: str = '', user: str = 'system') -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['resolved'] = True
            self.active_alerts[alert_id]['resolved_by'] = user
            self.active_alerts[alert_id]['resolved_at'] = datetime.utcnow().isoformat()
            self.active_alerts[alert_id]['resolution_notes'] = resolution_notes
            self.active_alerts[alert_id]['status'] = 'resolved'
            logger.info(f"Alert {alert_id} resolved by {user}")
            return True
        return False
    
    def get_active_alerts(self, severity: Optional[str] = None, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active alerts with optional filtering"""
        # Exclude resolved AND acknowledged alerts from active list
        alerts = [alert for alert in self.active_alerts.values() 
                  if not alert['resolved'] and not alert.get('acknowledged', False)]
        
        # Sanitize NaNs to prevent JSON errors
        for alert in alerts:
            if isinstance(alert.get('anomaly_score'), float) and (math.isnan(alert['anomaly_score']) or math.isinf(alert['anomaly_score'])):
                alert['anomaly_score'] = 0.0
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        if sector:
            alerts = [a for a in alerts if a['sector'] == sector]
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def get_acknowledged_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get acknowledged/closed alerts"""
        alerts = [alert for alert in self.active_alerts.values() if alert.get('acknowledged', False)]
        
        # Sanitize NaNs to prevent JSON errors
        for alert in alerts:
            if isinstance(alert.get('anomaly_score'), float) and (math.isnan(alert['anomaly_score']) or math.isinf(alert['anomaly_score'])):
                alert['anomaly_score'] = 0.0
        
        return sorted(alerts, key=lambda x: x.get('acknowledged_at', x['timestamp']), reverse=True)[:limit]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_count = len([a for a in self.active_alerts.values() if not a['resolved']])
        resolved_count = len([a for a in self.active_alerts.values() if a['resolved']])
        
        # Count by severity
        severity_counts = {}
        for severity in ['P0', 'P1', 'P2', 'P3', 'P4']:
            count = len([a for a in self.alert_history if a['severity'] == severity])
            severity_counts[severity] = count
        
        # Count by sector
        sector_counts = {}
        for alert in self.alert_history:
            sector = alert['sector']
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        # Calculate mean time to acknowledge and resolve
        acknowledged_alerts = [a for a in self.alert_history if a.get('acknowledged')]
        resolved_alerts = [a for a in self.alert_history if a.get('resolved')]
        
        mtta = 0  # Mean Time To Acknowledge
        mttr = 0  # Mean Time To Resolve
        
        if acknowledged_alerts:
            ack_times = []
            for alert in acknowledged_alerts:
                if 'acknowledged_at' in alert:
                    created = datetime.fromisoformat(alert['timestamp'])
                    acked = datetime.fromisoformat(alert['acknowledged_at'])
                    ack_times.append((acked - created).total_seconds())
            if ack_times:
                mtta = sum(ack_times) / len(ack_times)
        
        if resolved_alerts:
            resolve_times = []
            for alert in resolved_alerts:
                if 'resolved_at' in alert:
                    created = datetime.fromisoformat(alert['timestamp'])
                    resolved = datetime.fromisoformat(alert['resolved_at'])
                    resolve_times.append((resolved - created).total_seconds())
            if resolve_times:
                mttr = sum(resolve_times) / len(resolve_times)
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'resolved_alerts': resolved_count,
            'severity_counts': severity_counts,
            'sector_counts': sector_counts,
            'mean_time_to_acknowledge_seconds': mtta,
            'mean_time_to_resolve_seconds': mttr
        }

#!/usr/bin/env python
"""
RabbitMQ Alert Consumer Worker
Demonstrates async processing of security alerts

This worker runs in the background and processes alerts from the queue,
allowing the main API to respond quickly without waiting for:
- Email notifications
- SMS alerts
- Slack messages
- Response action execution
"""
import json
import time
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import pika
except ImportError:
    logger.error("pika not installed. Run: pip install pika")
    sys.exit(1)


class AlertWorker:
    """
    Background worker that processes alerts from RabbitMQ queue
    
    In production, you would run multiple instances of this worker
    for high availability and throughput.
    """
    
    def __init__(self, host='localhost', port=5672):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        self.alerts_processed = 0
        self.start_time = time.time()
    
    def connect(self):
        """Connect to RabbitMQ"""
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Ensure queue exists
        self.channel.queue_declare(queue='cyberops.alerts', durable=True)
        
        # Fair dispatch - don't give more work to busy workers
        self.channel.basic_qos(prefetch_count=1)
        
        logger.info(f"✅ Connected to RabbitMQ at {self.host}:{self.port}")
    
    def process_alert(self, ch, method, properties, body):
        """
        Process a single alert from the queue
        
        This is where you would:
        - Send email notifications
        - Send SMS/voice calls for critical alerts
        - Post to Slack/Teams
        - Trigger PagerDuty incidents
        - Log to SIEM systems
        - Execute automated responses
        """
        try:
            alert = json.loads(body)
            
            self.alerts_processed += 1
            severity = alert.get('severity', 'P4')
            device_id = alert.get('device_id', 'unknown')
            sector = alert.get('sector', 'unknown')
            anomaly_score = alert.get('anomaly_score', 0)
            
            # Simulate different processing based on severity
            if severity == 'P0':
                self._handle_critical_alert(alert)
            elif severity == 'P1':
                self._handle_high_alert(alert)
            elif severity == 'P2':
                self._handle_medium_alert(alert)
            else:
                self._handle_low_alert(alert)
            
            # Acknowledge the message (remove from queue)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            logger.info(f"✅ Processed alert #{self.alerts_processed}: [{severity}] {device_id} ({sector}) - Score: {anomaly_score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error processing alert: {e}")
            # Negative ack - requeue the message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _handle_critical_alert(self, alert):
        """Handle P0 critical alerts - immediate action required"""
        logger.warning(f"🚨 CRITICAL ALERT: {alert.get('device_id')}")
        
        # Simulate sending notifications (in production, these would be real calls)
        logger.info("  → Sending SMS to on-call team...")
        time.sleep(0.5)  # Simulate API call
        
        logger.info("  → Triggering PagerDuty incident...")
        time.sleep(0.3)
        
        logger.info("  → Sending Slack notification to #security-critical...")
        time.sleep(0.2)
        
        logger.info("  → Creating JIRA incident ticket...")
        time.sleep(0.4)
    
    def _handle_high_alert(self, alert):
        """Handle P1 high alerts"""
        logger.warning(f"⚠️  HIGH ALERT: {alert.get('device_id')}")
        
        logger.info("  → Sending email to security team...")
        time.sleep(0.3)
        
        logger.info("  → Posting to Slack #security-alerts...")
        time.sleep(0.2)
    
    def _handle_medium_alert(self, alert):
        """Handle P2 medium alerts"""
        logger.info(f"📌 MEDIUM ALERT: {alert.get('device_id')}")
        
        logger.info("  → Logging to SIEM...")
        time.sleep(0.1)
    
    def _handle_low_alert(self, alert):
        """Handle P3/P4 low alerts"""
        logger.info(f"📝 LOW ALERT: {alert.get('device_id')}")
        # Just log, no external notifications
    
    def start(self):
        """Start consuming alerts from the queue"""
        logger.info("🐰 Alert Worker starting...")
        logger.info("📥 Waiting for alerts on queue: cyberops.alerts")
        logger.info("   Press CTRL+C to stop\n")
        
        self.channel.basic_consume(
            queue='cyberops.alerts',
            on_message_callback=self.process_alert
        )
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the worker gracefully"""
        runtime = time.time() - self.start_time
        logger.info(f"\n🛑 Worker stopped")
        logger.info(f"   Alerts processed: {self.alerts_processed}")
        logger.info(f"   Runtime: {runtime:.1f}s")
        
        if self.connection:
            self.connection.close()


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           CyberThreat_Ops - RabbitMQ Alert Worker                ║
║          Async Processing for Security Notifications             ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    worker = AlertWorker()
    
    try:
        worker.connect()
        worker.start()
    except pika.exceptions.AMQPConnectionError:
        logger.error("❌ Could not connect to RabbitMQ. Is it running?")
        logger.error("   Start it with: docker compose up -d rabbitmq")
        sys.exit(1)


if __name__ == '__main__':
    main()

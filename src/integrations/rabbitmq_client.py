"""
RabbitMQ Client for CyberThreat_Ops
Provides async message processing for alerts and response actions
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import threading

logger = logging.getLogger(__name__)

try:
    import pika
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    logger.warning("pika not installed. RabbitMQ integration disabled.")


class RabbitMQClient:
    """
    Client for RabbitMQ message queue
    Used for:
    - Async alert processing and distribution
    - Response action queuing
    - Event-driven architecture
    - Decoupling components for scalability
    """
    
    # Queue names
    QUEUE_ALERTS = "cyberops.alerts"
    QUEUE_RESPONSES = "cyberops.responses"
    QUEUE_METRICS = "cyberops.metrics"
    QUEUE_NOTIFICATIONS = "cyberops.notifications"
    
    # Exchange names
    EXCHANGE_ALERTS = "cyberops.alerts.exchange"
    EXCHANGE_EVENTS = "cyberops.events.exchange"
    
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 virtual_host: str = "/"):
        """Initialize RabbitMQ client"""
        self.host = host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = port or int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = username or os.getenv('RABBITMQ_USER', 'guest')
        self.password = password or os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.virtual_host = virtual_host
        
        self.connection = None
        self.channel = None
        self.connected = False
        self.consumers = {}
        
        if RABBITMQ_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchanges and queues
            self._setup_infrastructure()
            
            self.connected = True
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self.connected = False
    
    def _setup_infrastructure(self):
        """Set up exchanges and queues"""
        try:
            # Declare exchanges
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_ALERTS,
                exchange_type='topic',
                durable=True
            )
            
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_EVENTS,
                exchange_type='fanout',
                durable=True
            )
            
            # Declare queues
            queues = [
                self.QUEUE_ALERTS,
                self.QUEUE_RESPONSES,
                self.QUEUE_METRICS,
                self.QUEUE_NOTIFICATIONS
            ]
            
            for queue in queues:
                self.channel.queue_declare(queue=queue, durable=True)
            
            # Bind queues to exchanges
            self.channel.queue_bind(
                exchange=self.EXCHANGE_ALERTS,
                queue=self.QUEUE_ALERTS,
                routing_key="alert.#"
            )
            
            self.channel.queue_bind(
                exchange=self.EXCHANGE_ALERTS,
                queue=self.QUEUE_NOTIFICATIONS,
                routing_key="alert.critical.#"
            )
            
            logger.info("RabbitMQ infrastructure setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up RabbitMQ infrastructure: {e}")
    
    # ==================== Publishing ====================
    
    def publish_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Publish an alert to the message queue
        
        Args:
            alert: Alert dictionary with severity and sector
        """
        if not self.connected or not RABBITMQ_AVAILABLE:
            return False
        
        try:
            severity = alert.get('severity', 'P4')
            sector = alert.get('sector', 'general')
            routing_key = f"alert.{severity.lower()}.{sector}"
            
            message = json.dumps(alert, default=str)
            
            self.channel.basic_publish(
                exchange=self.EXCHANGE_ALERTS,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json',
                    timestamp=int(datetime.utcnow().timestamp())
                )
            )
            
            logger.debug(f"Published alert to {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing alert: {e}")
            self._reconnect()
            return False
    
    def publish_response(self, response: Dict[str, Any]) -> bool:
        """Publish a response action to the queue"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return False
        
        try:
            message = json.dumps(response, default=str)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.QUEUE_RESPONSES,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.debug(f"Published response action: {response.get('action')}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing response: {e}")
            self._reconnect()
            return False
    
    def publish_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Publish metrics data to the queue"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return False
        
        try:
            message = json.dumps(metrics, default=str)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.QUEUE_METRICS,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=1,  # Non-persistent for metrics
                    content_type='application/json'
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")
            return False
    
    def publish_notification(self, notification: Dict[str, Any]) -> bool:
        """Publish a notification to the queue"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return False
        
        try:
            message = json.dumps(notification, default=str)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.QUEUE_NOTIFICATIONS,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                    priority=self._get_priority(notification)
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing notification: {e}")
            return False
    
    # ==================== Consuming ====================
    
    def consume_alerts(self, callback: Callable[[Dict], None], auto_ack: bool = False):
        """
        Start consuming alerts from the queue
        
        Args:
            callback: Function to call for each alert
            auto_ack: Whether to auto-acknowledge messages
        """
        if not self.connected or not RABBITMQ_AVAILABLE:
            return
        
        def wrapper(ch, method, properties, body):
            try:
                alert = json.loads(body)
                callback(alert)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        try:
            self.channel.basic_qos(prefetch_count=10)
            consumer_tag = self.channel.basic_consume(
                queue=self.QUEUE_ALERTS,
                on_message_callback=wrapper,
                auto_ack=auto_ack
            )
            self.consumers['alerts'] = consumer_tag
            logger.info("Started consuming alerts")
            
        except Exception as e:
            logger.error(f"Error starting alert consumer: {e}")
    
    def consume_responses(self, callback: Callable[[Dict], None], auto_ack: bool = False):
        """Start consuming response actions from the queue"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return
        
        def wrapper(ch, method, properties, body):
            try:
                response = json.loads(body)
                callback(response)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing response: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        try:
            self.channel.basic_qos(prefetch_count=5)
            consumer_tag = self.channel.basic_consume(
                queue=self.QUEUE_RESPONSES,
                on_message_callback=wrapper,
                auto_ack=auto_ack
            )
            self.consumers['responses'] = consumer_tag
            logger.info("Started consuming responses")
            
        except Exception as e:
            logger.error(f"Error starting response consumer: {e}")
    
    def start_consuming(self):
        """Start the consuming loop (blocking)"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return
        
        try:
            logger.info("Starting message consumption...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()
        except Exception as e:
            logger.error(f"Error in consuming loop: {e}")
    
    def start_consuming_async(self):
        """Start consuming in a background thread"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return None
        
        thread = threading.Thread(target=self.start_consuming, daemon=True)
        thread.start()
        return thread
    
    def stop_consuming(self):
        """Stop all consumers"""
        if self.channel:
            try:
                self.channel.stop_consuming()
                logger.info("Stopped consuming messages")
            except Exception as e:
                logger.error(f"Error stopping consumers: {e}")
    
    # ==================== Queue Management ====================
    
    def get_queue_stats(self) -> Dict[str, Dict]:
        """Get statistics for all queues"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return {}
        
        try:
            stats = {}
            queues = [
                self.QUEUE_ALERTS,
                self.QUEUE_RESPONSES,
                self.QUEUE_METRICS,
                self.QUEUE_NOTIFICATIONS
            ]
            
            for queue in queues:
                result = self.channel.queue_declare(queue=queue, passive=True)
                stats[queue] = {
                    'message_count': result.method.message_count,
                    'consumer_count': result.method.consumer_count
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}
    
    def purge_queue(self, queue_name: str) -> int:
        """Purge all messages from a queue"""
        if not self.connected or not RABBITMQ_AVAILABLE:
            return 0
        
        try:
            result = self.channel.queue_purge(queue=queue_name)
            return result.method.message_count
        except Exception as e:
            logger.error(f"Error purging queue: {e}")
            return 0
    
    # ==================== Helpers ====================
    
    def _get_priority(self, notification: Dict) -> int:
        """Get message priority based on severity"""
        severity = notification.get('severity', 'P4')
        priorities = {'P0': 10, 'P1': 8, 'P2': 5, 'P3': 3, 'P4': 1}
        return priorities.get(severity, 1)
    
    def _reconnect(self):
        """Attempt to reconnect to RabbitMQ"""
        logger.info("Attempting to reconnect to RabbitMQ...")
        self.close()
        self._connect()
    
    def close(self):
        """Close the RabbitMQ connection"""
        try:
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            self.connected = False
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

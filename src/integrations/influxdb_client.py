"""
InfluxDB Client for CyberThreat_Ops
Stores time-series metrics data for monitoring and analytics
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    from influxdb_client import InfluxDBClient as InfluxDB, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    logger.warning("influxdb-client not installed. InfluxDB integration disabled.")


class InfluxDBClient:
    """
    Client for storing and querying time-series data in InfluxDB
    Used for:
    - Storing device metrics (CPU, memory, network, etc.)
    - Storing detection results and anomaly scores
    - Storing alert and response metrics for analytics
    """
    
    def __init__(self, 
                 url: str = None,
                 token: str = None,
                 org: str = None,
                 bucket: str = None):
        """Initialize InfluxDB client"""
        self.url = url or os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = token or os.getenv('INFLUXDB_TOKEN', 'cyberops-token-2026')
        self.org = org or os.getenv('INFLUXDB_ORG', 'cyberops')
        self.bucket = bucket or os.getenv('INFLUXDB_BUCKET', 'monitoring')
        
        self.client = None
        self.write_api = None
        self.query_api = None
        self.connected = False
        
        if INFLUXDB_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """Establish connection to InfluxDB"""
        try:
            self.client = InfluxDB(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            # Test connection
            health = self.client.health()
            if health.status == "pass":
                self.connected = True
                logger.info(f"Connected to InfluxDB at {self.url}")
            else:
                logger.warning(f"InfluxDB health check failed: {health.message}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            self.connected = False
    
    def write_device_metrics(self, data: Dict[str, Any]):
        """
        Write device metrics to InfluxDB
        
        Args:
            data: Dictionary containing device metrics
                Required: device_id, sector
                Optional: cpu_usage, memory_usage, network_traffic_mbps, etc.
        """
        if not self.connected or not INFLUXDB_AVAILABLE:
            return False
        
        try:
            point = Point("device_metrics") \
                .tag("device_id", data.get('device_id', 'unknown')) \
                .tag("device_type", data.get('device_type', 'unknown')) \
                .tag("sector", data.get('sector', 'unknown')) \
                .tag("location", data.get('location', 'unknown'))
            
            # Add numeric fields
            numeric_fields = [
                'cpu_usage', 'memory_usage', 'network_traffic_mbps',
                'disk_io_ops', 'authentication_success', 'authentication_failure',
                'api_calls', 'active_sessions', 'query_rate', 'failed_logins'
            ]
            
            for field in numeric_fields:
                if field in data and data[field] is not None:
                    point = point.field(field, float(data[field]))
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            logger.error(f"Error writing device metrics: {e}")
            return False
    
    def write_detection_result(self, result: Dict[str, Any]):
        """
        Write anomaly detection result to InfluxDB
        
        Args:
            result: Detection result from AnomalyDetectionEngine
        """
        if not self.connected or not INFLUXDB_AVAILABLE:
            return False
        
        try:
            point = Point("detection_results") \
                .tag("device_id", result.get('device_id', 'unknown')) \
                .tag("device_type", result.get('device_type', 'unknown')) \
                .tag("sector", result.get('sector', 'unknown')) \
                .tag("severity", result.get('severity', 'unknown')) \
                .tag("is_anomaly", str(result.get('is_anomaly', False))) \
                .field("anomaly_score", float(result.get('anomaly_score', 0)))
            
            # Add detector scores
            detector_scores = result.get('detector_scores', {})
            for detector, score in detector_scores.items():
                point = point.field(f"score_{detector}", float(score))
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            logger.error(f"Error writing detection result: {e}")
            return False
    
    def write_alert(self, alert: Dict[str, Any]):
        """Write alert to InfluxDB"""
        if not self.connected or not INFLUXDB_AVAILABLE:
            return False
        
        try:
            point = Point("alerts") \
                .tag("alert_id", alert.get('alert_id', 'unknown')) \
                .tag("device_id", alert.get('device_id', 'unknown')) \
                .tag("sector", alert.get('sector', 'unknown')) \
                .tag("severity", alert.get('severity', 'unknown')) \
                .tag("status", alert.get('status', 'active')) \
                .field("anomaly_score", float(alert.get('anomaly_score', 0))) \
                .field("count", 1)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            logger.error(f"Error writing alert: {e}")
            return False
    
    def write_response(self, response: Dict[str, Any]):
        """Write response action to InfluxDB"""
        if not self.connected or not INFLUXDB_AVAILABLE:
            return False
        
        try:
            point = Point("responses") \
                .tag("response_id", response.get('response_id', 'unknown')) \
                .tag("action", response.get('action', 'unknown')) \
                .tag("target", response.get('target', 'unknown')) \
                .tag("status", response.get('status', 'unknown')) \
                .tag("sector", response.get('sector', 'unknown')) \
                .field("execution_time_ms", float(response.get('execution_time_ms', 0))) \
                .field("count", 1)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            logger.error(f"Error writing response: {e}")
            return False
    
    def query_metrics(self, 
                     measurement: str,
                     time_range: str = "-1h",
                     filters: Dict[str, str] = None) -> List[Dict]:
        """
        Query metrics from InfluxDB
        
        Args:
            measurement: Measurement name (device_metrics, detection_results, alerts, responses)
            time_range: Time range (e.g., "-1h", "-24h", "-7d")
            filters: Optional tag filters
        
        Returns:
            List of records
        """
        if not self.connected or not INFLUXDB_AVAILABLE:
            return []
        
        try:
            filter_str = ""
            if filters:
                filter_parts = [f'r["{k}"] == "{v}"' for k, v in filters.items()]
                filter_str = " and ".join(filter_parts)
                filter_str = f" |> filter(fn: (r) => {filter_str})"
            
            query = f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {time_range})
                    |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                    {filter_str}
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        'time': record.get_time(),
                        'value': record.get_value(),
                        'field': record.get_field(),
                        'tags': {k: v for k, v in record.values.items() if not k.startswith('_')}
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying metrics: {e}")
            return []
    
    def get_aggregated_metrics(self,
                               measurement: str,
                               field: str,
                               time_range: str = "-1h",
                               window: str = "5m",
                               aggregate: str = "mean") -> List[Dict]:
        """Get aggregated metrics with windowing"""
        if not self.connected or not INFLUXDB_AVAILABLE:
            return []
        
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {time_range})
                    |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                    |> filter(fn: (r) => r["_field"] == "{field}")
                    |> aggregateWindow(every: {window}, fn: {aggregate}, createEmpty: false)
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        'time': record.get_time().isoformat(),
                        'value': record.get_value()
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting aggregated metrics: {e}")
            return []
    
    def close(self):
        """Close the InfluxDB connection"""
        if self.client:
            self.client.close()
            self.connected = False

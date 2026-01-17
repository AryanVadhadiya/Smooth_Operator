"""
FastAPI Backend for CyberThreat_Ops Dashboard
Integrated with InfluxDB, Redis, and RabbitMQ for production-ready infrastructure
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import yaml
import os
import logging

# Import our modules
from ..simulators import HealthcareSimulator, AgricultureSimulator, UrbanSimulator
from ..detection import AnomalyDetectionEngine
from ..alerting import AlertManager
from ..response import AutomatedResponseSystem
from ..utils.scanner import NetworkScanner

# Import integration modules
try:
    from ..integrations import InfluxDBClient, RedisClient, RabbitMQClient
    INTEGRATIONS_AVAILABLE = True
except ImportError as e:
    INTEGRATIONS_AVAILABLE = False
    logging.warning(f"Integration modules not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CyberThreat_Ops API",
    description="Cyber-Resilient Infrastructure Monitoring API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.warning(f"Could not load config: {e}. Using defaults.")
    config = {}

# Global state
class AppState:
    def __init__(self):
        self.simulators = {
            'healthcare': HealthcareSimulator(num_devices=5),
            'agriculture': AgricultureSimulator(num_devices=5),
            'urban': UrbanSimulator(num_devices=5)
        }
        self.detection_engines = {}
        self.alert_manager = AlertManager(config)
        self.response_system = AutomatedResponseSystem(config)
        self.is_training = False
        self.is_monitoring = False
        self.websocket_clients = set()
        
        # Initialize detection engines for each sector
        for sector in ['healthcare', 'agriculture', 'urban']:
            self.detection_engines[sector] = AnomalyDetectionEngine(config)
        
        # Initialize integration clients
        self.influxdb = None
        self.redis = None
        self.rabbitmq = None
        
        if INTEGRATIONS_AVAILABLE:
            try:
                self.influxdb = InfluxDBClient()
                logger.info(f"InfluxDB connected: {self.influxdb.connected}")
            except Exception as e:
                logger.warning(f"InfluxDB not available: {e}")
            
            try:
                self.redis = RedisClient()
                logger.info(f"Redis connected: {self.redis.connected}")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
            
            try:
                self.rabbitmq = RabbitMQClient()
                logger.info(f"RabbitMQ connected: {self.rabbitmq.connected}")
            except Exception as e:
                logger.warning(f"RabbitMQ not available: {e}")

state = AppState()

# ==================== Device Persistence ====================
DEVICES_FILE = os.path.join(os.path.dirname(__file__), '../../data/devices.json')

def load_registered_devices() -> Dict[str, Dict[str, Any]]:
    """Load devices from JSON file"""
    if not os.path.exists(DEVICES_FILE):
        return {}
    try:
        import json
        with open(DEVICES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load devices: {e}")
        return {}

def save_registered_devices(devices: Dict[str, Dict[str, Any]]):
    """Save devices to JSON file"""
    try:
        import json
        os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
        with open(DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save devices: {e}")

# Load devices on startup
registered_devices: Dict[str, Dict[str, Any]] = load_registered_devices()

# Store historical metrics for graphs (Keep last 20 points)
device_metrics_history: Dict[str, List[Dict[str, Any]]] = {}


# Background Task for Active Monitoring
async def active_monitoring_loop():
    """
    Background task that actively polls real registered devices with IPs.
    This turns the system from a pure simulator into a real monitoring tool.
    """
    logger.info("🚀 Active Monitoring Loop Started")
    while True:
        try:
            # 1. Filter for devices with real IP addresses
            real_ip_devices = [
                d for d in registered_devices.values() 
                if d.get('ip_address') and not d.get('is_simulated', True)
            ]
            
            for device in real_ip_devices:
                ip = device['ip_address']
                device_id = device['id']
                sector = device['sector']
                
                # 2. Perform Active Network Scan (Ping/Ports)
                # logger.info(f"📡 Polling device {device_id} at {ip}...")
                metrics = await NetworkScanner.get_device_metrics(ip)
                
                # 3. Create a metrics payload consistent with our system
                # We map real network stats to our model (Latency -> Network Traffic heuristic)
                data_point = {
                    "device_id": device_id,
                    "device_type": device.get('type', 'unknown'),
                    "sector": sector,
                    "timestamp": datetime.utcnow().isoformat(),
                    
                    # Real Metrics
                    "network_latency": metrics["network_latency_ms"],
                    "packet_loss": metrics.get("packet_loss_percent", 0.0),
                    "is_reachable": metrics["availability"] > 0,
                    
                    # Heuristics (Using scans to estimate load)
                    # High latency = higher simulated CPU load
                    # Adjusted sensitivity: Latency spikes (DoS) should drastically increase CPU metric
                    "cpu_usage": 10.0 + (metrics["network_latency_ms"] * 0.5) if metrics["availability"] > 0 else 0.0,
                    
                    # More open ports = higher risk/traffic profile
                    "network_traffic_mbps": metrics.get("network_traffic_estimation", 0.0),
                    
                    # Memory usage placeholder (can't guess from ping)
                    "memory_usage": 40.0, 
                    
                    "disk_io_ops": 100
                }

                # STORE HISTORY (Real Data for Charts)
                if device_id not in device_metrics_history:
                    device_metrics_history[device_id] = []
                device_metrics_history[device_id].append(data_point)
                # Keep last 20 points
                if len(device_metrics_history[device_id]) > 20:
                    device_metrics_history[device_id].pop(0)
                
                # 4. Integrate with Detection Engine
                # If latency is anomalously high (e.g. DDOS), this will trigger an alert!
                engine = state.detection_engines.get(sector)
                
                # Check if trained, if not, bootstrap training with dummy data
                if engine and not any(d.is_trained for d in engine.detectors.values()):
                    logger.info(f"✨ Bootstrapping training for {sector} to enable detection...")
                    sim = state.simulators.get(sector)
                    if sim:
                        train_data = [sim.generate_normal_data(device['id']) for _ in range(50)]
                        engine.train(train_data, sector=sector)
                
                if engine and any(d.is_trained for d in engine.detectors.values()):
                    results = engine.detect([data_point])
                    
                    for result in results:
                        if result['is_anomaly']:
                            logger.warning(f"🚨 ACTIVE MONITOR DETECTED ANOMALY ON {ip} ({device_id})")
                            alert = state.alert_manager.create_alert(result)
                            if alert:
                                state.alert_manager.route_alert(alert)
                                # Trigger response (e.g., if we had an agent, we'd block IP)
            
            # Wait before next cycle
            await asyncio.sleep(10)  # Poll every 10 seconds
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup and restore device state"""
    
    # Restore registered devices to simulators
    logger.info(f"Restoring {len(registered_devices)} devices...")
    for device_id, device in registered_devices.items():
        try:
            sector = device.get('sector')
            if sector in state.simulators:
                # Avoid duplicates if simulator initialized defaults
                existing_ids = [d['id'] for d in state.simulators[sector].devices]
                if device_id not in existing_ids:
                    state.simulators[sector].devices.append(device)
                    logger.info(f"Restored device {device_id} to {sector}")
        except Exception as e:
            logger.error(f"Error restoring devise {device_id}: {e}")

    asyncio.create_task(active_monitoring_loop())

# Pydantic models
class TrainingRequest(BaseModel):
    sector: str
    num_samples: int = 1000

class DetectionRequest(BaseModel):
    sector: str
    data: List[Dict[str, Any]]

class AttackSimulationRequest(BaseModel):
    sector: str
    attack_type: str
    num_samples: int = 10

class ResponseApprovalRequest(BaseModel):
    response_id: str
    approver: str = "admin"

class DeviceRegistration(BaseModel):
    """Model for registering a new device"""
    device_id: str
    device_type: str
    sector: str  # healthcare, agriculture, or urban
    location: str = "Unknown"
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MetricsSubmission(BaseModel):
    """Model for submitting device metrics"""
    device_id: str
    sector: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    network_traffic_mbps: Optional[float] = None
    disk_io_ops: Optional[int] = None
    custom_metrics: Optional[Dict[str, Any]] = None

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CyberThreat_Ops API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring_active": state.is_monitoring,
        "sectors": list(state.simulators.keys())
    }

@app.post("/train/{sector}")
async def train_model(sector: str, num_samples: int = 1000):
    """Train detection models for a sector"""
    if sector not in state.simulators:
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    
    if state.is_training:
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    try:
        state.is_training = True
        logger.info(f"Training detection engine for {sector}")
        
        # Generate training data
        simulator = state.simulators[sector]
        training_data = []
        for _ in range(num_samples):
            device = simulator.devices[_ % len(simulator.devices)]
            data = simulator.generate_normal_data(device['id'])
            training_data.append(data)
        
        # Train detection engine
        engine = state.detection_engines[sector]
        engine.train(training_data, sector=sector)
        
        # Save models
        models_dir = f"models/{sector}"
        engine.save_models(models_dir)
        
        state.is_training = False
        
        return {
            "status": "success",
            "sector": sector,
            "samples_trained": num_samples,
            "detectors": list(engine.detectors.keys())
        }
    
    except Exception as e:
        state.is_training = False
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect/{sector}")
async def detect_anomalies(sector: str, data: List[Dict[str, Any]]):
    """Detect anomalies in provided data"""
    if sector not in state.detection_engines:
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    
    engine = state.detection_engines[sector]
    
    if not any(d.is_trained for d in engine.detectors.values()):
        raise HTTPException(status_code=400, detail=f"Models not trained for {sector}")
    
    try:
        results = engine.detect(data)
        
        # Create alerts for anomalies
        for result in results:
            if result['is_anomaly']:
                alert = state.alert_manager.create_alert(result)
                if alert:
                    # Route alert (sync - fast)
                    state.alert_manager.route_alert(alert)
                    
                    # Publish to RabbitMQ for async processing (notifications, logging, etc)
                    if state.rabbitmq and state.rabbitmq.connected:
                        state.rabbitmq.publish_alert(alert)
                        logger.info(f"📤 Alert {alert['alert_id']} queued for async processing")
                    
                    # Determine and execute responses
                    actions = state.response_system.determine_response_actions(alert)
                    for action in actions:
                        response = state.response_system.execute_response(action, alert)
                        alert['response_actions'].append(response)
        
        return {
            "status": "success",
            "total_samples": len(results),
            "anomalies_detected": sum(1 for r in results if r['is_anomaly']),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate-attack")
async def simulate_attack(request: AttackSimulationRequest):
    """Simulate an attack scenario"""
    sector = request.sector
    attack_type = request.attack_type
    num_samples = request.num_samples
    
    if sector not in state.simulators:
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    
    simulator = state.simulators[sector]
    attack_data = []
    
    for _ in range(num_samples):
        device = simulator.devices[_ % len(simulator.devices)]
        data = simulator.generate_anomalous_data(device['id'], attack_type)
        attack_data.append(data)
    
    # Detect anomalies in attack data
    engine = state.detection_engines[sector]
    if any(d.is_trained for d in engine.detectors.values()):
        results = engine.detect(attack_data)
        
        # Process alerts
        alerts_created = []
        for result in results:
            if result['is_anomaly']:
                alert = state.alert_manager.create_alert(result)
                if alert:
                    alerts_created.append(alert)
                    state.alert_manager.route_alert(alert)
                    
                    # Queue for async processing
                    if state.rabbitmq and state.rabbitmq.connected:
                        state.rabbitmq.publish_alert(alert)
                    
                    # Execute responses
                    actions = state.response_system.determine_response_actions(alert)
                    for action in actions:
                        response = state.response_system.execute_response(action, alert)
                        alert['response_actions'].append(response)
        
        return {
            "status": "success",
            "sector": sector,
            "attack_type": attack_type,
            "samples_generated": num_samples,
            "anomalies_detected": sum(1 for r in results if r['is_anomaly']),
            "alerts_created": len(alerts_created),
            "detection_results": results
        }
    else:
        return {
            "status": "warning",
            "message": f"Models not trained for {sector}. Attack data generated but not detected.",
            "attack_data": attack_data
        }

@app.get("/alerts")
async def get_alerts(severity: Optional[str] = None, sector: Optional[str] = None, limit: int = 100):
    """Get active alerts"""
    alerts = state.alert_manager.get_active_alerts(severity=severity, sector=sector)
    return {
        "status": "success",
        "count": len(alerts),
        "alerts": alerts[:limit]
    }

@app.get("/alerts/statistics")
async def get_alert_statistics():
    """Get alert statistics"""
    stats = state.alert_manager.get_alert_statistics()
    return {
        "status": "success",
        "statistics": stats
    }

@app.get("/alerts/acknowledged")
async def get_acknowledged_alerts(limit: int = 50):
    """Get acknowledged/closed alerts"""
    alerts = state.alert_manager.get_acknowledged_alerts(limit=limit)
    return {
        "status": "success",
        "count": len(alerts),
        "alerts": alerts
    }

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: str = "admin"):
    """Acknowledge an alert"""
    success = state.alert_manager.acknowledge_alert(alert_id, user)
    if success:
        return {"status": "success", "alert_id": alert_id, "acknowledged_by": user}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, notes: str = "", user: str = "admin"):
    """Resolve an alert"""
    success = state.alert_manager.resolve_alert(alert_id, notes, user)
    if success:
        return {"status": "success", "alert_id": alert_id, "resolved_by": user}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.get("/responses")
async def get_responses(limit: int = 100):
    """Get response history"""
    responses = state.response_system.response_history[-limit:]
    return {
        "status": "success",
        "count": len(responses),
        "responses": responses
    }

@app.get("/responses/pending")
async def get_pending_responses():
    """Get pending response approvals"""
    pending = list(state.response_system.pending_approvals.values())
    return {
        "status": "success",
        "count": len(pending),
        "pending_approvals": pending
    }

@app.post("/responses/{response_id}/approve")
async def approve_response(response_id: str, approver: str = "admin"):
    """Approve a pending response"""
    try:
        result = state.response_system.approve_response(response_id, approver)
        return {"status": "success", "response": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/responses/{response_id}/rollback")
async def rollback_response(response_id: str):
    """Rollback a completed response"""
    try:
        result = state.response_system.rollback_response(response_id)
        return {"status": "success", "response": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/responses/statistics")
async def get_response_statistics():
    """Get response statistics"""
    stats = state.response_system.get_response_statistics()
    return {
        "status": "success",
        "statistics": stats
    }

@app.get("/system/status")
async def get_system_status():
    """Get overall system status including infrastructure"""
    active_alerts = state.alert_manager.get_active_alerts()
    alert_stats = state.alert_manager.get_alert_statistics()
    response_stats = state.response_system.get_response_statistics()
    
    # Get device counts
    device_counts = {
        sector: len(sim.devices) 
        for sector, sim in state.simulators.items()
    }
    
    # Check model training status
    trained_models = {}
    for sector, engine in state.detection_engines.items():
        trained_models[sector] = any(d.is_trained for d in engine.detectors.values())
    
    # Get infrastructure status
    infrastructure = {
        "influxdb": {
            "connected": state.influxdb.connected if state.influxdb else False,
            "url": state.influxdb.url if state.influxdb else None
        },
        "redis": {
            "connected": state.redis.connected if state.redis else False,
            "host": f"{state.redis.host}:{state.redis.port}" if state.redis else None
        },
        "rabbitmq": {
            "connected": state.rabbitmq.connected if state.rabbitmq else False,
            "host": f"{state.rabbitmq.host}:{state.rabbitmq.port}" if state.rabbitmq else None,
            "queues": state.rabbitmq.get_queue_stats() if state.rabbitmq and state.rabbitmq.connected else {}
        }
    }
    
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "monitoring_active": state.is_monitoring,
            "training_active": state.is_training,
        },
        "devices": device_counts,
        "models_trained": trained_models,
        "alerts": {
            "active": len(active_alerts),
            "total": alert_stats['total_alerts'],
            "by_severity": alert_stats['severity_counts']
        },
        "responses": {
            "total": response_stats['total_responses'],
            "pending": response_stats['pending_approval'],
            "success_rate": response_stats['success_rate']
        },
        "infrastructure": infrastructure
    }

@app.get("/devices/{sector}")
async def get_devices(sector: str):
    """Get devices for a sector"""
    if sector not in state.simulators:
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    
    devices = state.simulators[sector].devices
    return {
        "status": "success",
        "sector": sector,
        "count": len(devices),
        "devices": devices
    }

@app.get("/metrics/{sector}")
async def get_sector_metrics(sector: str, num_samples: int = 10):
    """Get current metrics for a sector"""
    if sector not in state.simulators:
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    
    simulator = state.simulators[sector]
    metrics = []
    
    for _ in range(num_samples):
        device = simulator.devices[_ % len(simulator.devices)]
        data = simulator.generate_normal_data(device['id'])
        metrics.append(data)
    
    return {
        "status": "success",
        "sector": sector,
        "count": len(metrics),
        "metrics": metrics
    }

# ==================== Device Management ====================

# Store for custom registered devices (in addition to simulated ones)
# registered_devices is defined globally above

@app.post("/devices/register")
async def register_device(device: DeviceRegistration):
    """
    Register a new device for monitoring.
    
    This adds a custom device that can send real metrics to the system.
    The device will be monitored alongside the simulated devices.
    """
    if device.sector not in state.simulators:
        raise HTTPException(status_code=400, detail=f"Invalid sector: {device.sector}. Must be: healthcare, agriculture, or urban")
    
    # Create device record
    device_record = {
        "id": device.device_id,
        "type": device.device_type,
        "sector": device.sector,
        "location": device.location,
        "ip_address": device.ip_address,
        "firmware_version": device.firmware_version,
        "metadata": device.metadata or {},
        "status": "active",
        "registered_at": datetime.utcnow().isoformat(),
        "is_simulated": False
    }
    
    # Add to registered devices
    registered_devices[device.device_id] = device_record
    save_registered_devices(registered_devices)
    
    # Also add to the simulator's device list for detection
    state.simulators[device.sector].devices.append(device_record)
    
    # Update Redis if available
    if state.redis and state.redis.connected:
        state.redis.update_device_state(device.device_id, device_record)
    
    logger.info(f"Registered new device: {device.device_id} ({device.device_type}) in {device.sector}")
    
    return {
        "status": "success",
        "message": f"Device {device.device_id} registered successfully",
        "device": device_record
    }

@app.post("/devices/metrics")
async def submit_device_metrics(metrics: MetricsSubmission):
    """
    Submit metrics from a registered device.
    
    This endpoint allows real devices to send their metrics
    for anomaly detection and monitoring.
    """
    if metrics.sector not in state.simulators:
        raise HTTPException(status_code=400, detail=f"Invalid sector: {metrics.sector}")
    
    # Build metrics data point
    data_point = {
        "device_id": metrics.device_id,
        "sector": metrics.sector,
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_usage": metrics.cpu_usage or 0,
        "memory_usage": metrics.memory_usage or 0,
        "network_traffic_mbps": metrics.network_traffic_mbps or 0,
        "disk_io_ops": metrics.disk_io_ops or 0,
    }
    
    # Add custom metrics
    if metrics.custom_metrics:
        data_point.update(metrics.custom_metrics)
    
    # Get device info if registered
    if metrics.device_id in registered_devices:
        device = registered_devices[metrics.device_id]
        data_point["device_type"] = device.get("type", "unknown")
        data_point["location"] = device.get("location", "unknown")
    
    # Store in InfluxDB if available
    if state.influxdb and state.influxdb.connected:
        state.influxdb.write_device_metrics(data_point)
    
    # Run anomaly detection if model is trained
    engine = state.detection_engines.get(metrics.sector)
    detection_result = None
    
    if engine and any(d.is_trained for d in engine.detectors.values()):
        results = engine.detect([data_point])
        if results:
            detection_result = results[0]
            
            # Create alert if anomaly detected
            if detection_result.get('is_anomaly'):
                alert = state.alert_manager.create_alert(detection_result)
                if alert:
                    state.alert_manager.route_alert(alert)
                    
                    # Execute automated responses
                    actions = state.response_system.determine_response_actions(alert)
                    for action in actions:
                        state.response_system.execute_response(action, alert)
    
    return {
        "status": "success",
        "device_id": metrics.device_id,
        "metrics_stored": True,
        "anomaly_detected": detection_result.get('is_anomaly', False) if detection_result else None,
        "anomaly_score": detection_result.get('anomaly_score') if detection_result else None
    }

@app.delete("/devices/{device_id}")
async def deregister_device(device_id: str):
    """Remove a registered device from monitoring"""
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    device = registered_devices.pop(device_id)
    save_registered_devices(registered_devices)
    sector = device.get('sector')
    
    # Remove from simulator's device list
    if sector in state.simulators:
        state.simulators[sector].devices = [
            d for d in state.simulators[sector].devices 
            if d.get('id') != device_id
        ]
    
    logger.info(f"Deregistered device: {device_id}")
    
    return {
        "status": "success",
        "message": f"Device {device_id} removed from monitoring"
    }

@app.get("/devices-registered")
async def get_registered_devices():
    """Get all custom registered devices (not simulated)"""
    return {
        "status": "success",
        "count": len(registered_devices),
        "devices": list(registered_devices.values())
    }

@app.get("/devices-all")
async def get_all_devices():
    """Get all devices across all sectors (simulated and registered)"""
    all_devices = {}
    for sector, simulator in state.simulators.items():
        all_devices[sector] = {
            "count": len(simulator.devices),
            "devices": simulator.devices
        }
    
    return {
        "status": "success",
        "total_devices": sum(len(sim.devices) for sim in state.simulators.values()),
        "by_sector": all_devices
    }

@app.get("/devices/{device_id}/history")
async def get_device_history(device_id: str):
    """Get historical metrics for a device (real data)"""
    if device_id in device_metrics_history:
        return {
            "status": "success",
            "device_id": device_id,
            "history": device_metrics_history[device_id]
        }
    return {"status": "success", "history": []}

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    state.websocket_clients.add(websocket)
    
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            
            # Get current status
            active_alerts = state.alert_manager.get_active_alerts()
            
            update = {
                "timestamp": datetime.utcnow().isoformat(),
                "active_alerts": len(active_alerts),
                "recent_alerts": active_alerts[:5] if active_alerts else []
            }
            
            await websocket.send_json(update)
            
    except WebSocketDisconnect:
        state.websocket_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

"""
Urban systems simulator - Generates mock data for smart city infrastructure
"""
import random
from datetime import datetime
from typing import Dict, List, Any
from .base_simulator import BaseSimulator


class UrbanSimulator(BaseSimulator):
    """Simulates urban infrastructure including SCADA, traffic, and utilities"""
    
    DEVICE_TYPES = [
        "traffic_controller",
        "water_treatment_scada",
        "power_grid_monitor",
        "smart_streetlight",
        "emergency_system",
        "subway_controller",
        "smart_meter",
        "waste_management"
    ]
    
    def __init__(self, num_devices: int = 10):
        super().__init__("urban", num_devices)
        
    def _initialize_devices(self) -> List[Dict[str, Any]]:
        """Initialize urban infrastructure devices"""
        devices = []
        for i in range(self.num_devices):
            device = {
                "id": f"URB-{i:04d}",
                "type": random.choice(self.DEVICE_TYPES),
                "location": random.choice(["Zone-A", "Zone-B", "Downtown", "Suburbs", "Industrial"]),
                "status": "active",
                "firmware_version": f"{random.randint(2,6)}.{random.randint(0,12)}.{random.randint(0,25)}",
                "criticality": random.choice(["high", "medium", "low"]),
                "last_maintenance": datetime.utcnow().isoformat()
            }
            devices.append(device)
        return devices
    
    def generate_normal_data(self, device_id: str = None) -> Dict[str, Any]:
        """Generate normal urban system data"""
        if device_id is None:
            device = random.choice(self.devices)
        else:
            device = next((d for d in self.devices if d['id'] == device_id), self.devices[0])
        
        base_metrics = self.get_base_metrics()
        
        device_metrics = {
            "device_id": device['id'],
            "device_type": device['type'],
            "location": device['location'],
            "sector": "urban",
            "criticality": device.get('criticality', 'medium'),
        }
        
        # Add type-specific data
        if device['type'] == "traffic_controller":
            device_metrics.update({
                "active_signals": random.randint(8, 16),
                "vehicle_count": random.randint(100, 500),
                "average_speed": self.add_noise(45.0, 10),  # km/h
                "congestion_level": random.uniform(20, 60),  # percentage
                "signal_timing": self.add_noise(60.0, 5),  # seconds
                "emergency_override_count": random.randint(0, 2),
            })
        elif device['type'] == "water_treatment_scada":
            device_metrics.update({
                "water_flow_rate": self.add_noise(1000.0, 5),  # cubic meters/hour
                "chlorine_level": self.add_noise(2.0, 10),  # ppm
                "ph_level": self.add_noise(7.5, 2),
                "turbidity": self.add_noise(0.5, 10),  # NTU
                "pump_pressure": self.add_noise(80.0, 5),  # psi
                "tank_level": self.add_noise(75.0, 5),  # percentage
                "pump_status": random.choice(["running", "standby"]),
            })
        elif device['type'] == "power_grid_monitor":
            device_metrics.update({
                "voltage": self.add_noise(230.0, 2),  # volts
                "current": self.add_noise(150.0, 5),  # amperes
                "frequency": self.add_noise(50.0, 0.5),  # Hz
                "power_factor": self.add_noise(0.95, 2),
                "load_percentage": self.add_noise(65.0, 10),
                "transformer_temperature": self.add_noise(60.0, 5),  # celsius
            })
        elif device['type'] == "smart_streetlight":
            device_metrics.update({
                "light_intensity": random.randint(60, 100),  # percentage
                "energy_consumption": self.add_noise(50.0, 5),  # watts
                "operating_hours": random.randint(10, 14),
                "motion_detected": random.choice([True, False]),
                "bulb_health": random.uniform(80, 100),  # percentage
            })
        elif device['type'] == "emergency_system":
            device_metrics.update({
                "911_calls": random.randint(5, 20),
                "dispatch_time": self.add_noise(3.0, 10),  # minutes
                "active_incidents": random.randint(2, 10),
                "response_units_available": random.randint(15, 30),
                "system_uptime": random.uniform(99.5, 100.0),  # percentage
            })
        elif device['type'] == "subway_controller":
            device_metrics.update({
                "trains_active": random.randint(20, 40),
                "average_delay": self.add_noise(2.0, 50),  # minutes
                "passenger_count": random.randint(5000, 15000),
                "door_malfunctions": random.randint(0, 2),
                "track_temperature": self.add_noise(25.0, 10),
                "signal_system_status": "operational",
            })
        elif device['type'] == "smart_meter":
            device_metrics.update({
                "energy_usage": self.add_noise(15.0, 10),  # kWh
                "peak_demand": self.add_noise(3.5, 10),  # kW
                "voltage_quality": self.add_noise(230.0, 3),
                "power_outages": random.randint(0, 1),
                "meter_health": random.uniform(95, 100),
            })
        elif device['type'] == "waste_management":
            device_metrics.update({
                "bin_fill_level": self.add_noise(45.0, 15),  # percentage
                "collection_route_active": random.choice([True, False]),
                "compaction_cycles": random.randint(5, 15),
                "temperature": self.add_noise(35.0, 10),
                "odor_level": random.uniform(20, 50),
            })
        
        # Common urban system metrics
        device_metrics.update({
            "uptime_percentage": random.uniform(99.0, 100.0),
            "error_count": random.randint(0, 3),
            "maintenance_due_days": random.randint(10, 90),
            # Network metrics for hybrid detection (Real + Sim)
            "network_latency_ms": random.uniform(5.0, 30.0), # Normal latency
            "packet_loss_percent": 0.0, # Normal loss
        })
        
        return {**base_metrics, **device_metrics}
    
    def generate_anomalous_data(self, device_id: str = None, attack_type: str = "scada_attack") -> Dict[str, Any]:
        """Generate anomalous urban system data simulating various attacks"""
        data = self.generate_normal_data(device_id)
        
        if attack_type == "scada_attack":
            # Simulate SCADA system compromise
            if 'pump_pressure' in data:
                data['pump_pressure'] = random.uniform(150, 200)  # Dangerous pressure
                data['chlorine_level'] = random.uniform(10, 20)  # Toxic levels
                data['pump_status'] = "running"
            if 'voltage' in data:
                data['voltage'] = random.uniform(180, 280)  # Unstable voltage
                data['frequency'] = random.uniform(45, 55)  # Out of spec
            
        elif attack_type == "traffic_manipulation":
            # Simulate traffic light system hack
            if 'signal_timing' in data:
                data['signal_timing'] = random.choice([5.0, 200.0])  # Too short or long
                data['emergency_override_count'] = random.randint(50, 200)
                data['congestion_level'] = random.uniform(90, 100)
            
        elif attack_type == "power_grid_attack":
            # Simulate power grid destabilization
            if 'voltage' in data:
                data['voltage'] = random.uniform(150, 300)
                data['current'] = random.uniform(300, 500)  # Overload
                data['frequency'] = random.uniform(40, 60)
                data['transformer_temperature'] = random.uniform(100, 150)
            
        elif attack_type == "water_contamination":
            # Simulate water treatment manipulation
            if 'chlorine_level' in data:
                data['chlorine_level'] = random.choice([0.1, 15.0])  # Too low or high
                data['ph_level'] = random.uniform(4.0, 11.0)  # Dangerous pH
                data['turbidity'] = random.uniform(5.0, 20.0)  # Contaminated
            
        elif attack_type == "subway_disruption":
            # Simulate subway system attack
            if 'trains_active' in data:
                data['trains_active'] = random.randint(0, 5)  # System shutdown
                data['average_delay'] = random.uniform(30, 120)
                data['door_malfunctions'] = random.randint(20, 50)
                data['signal_system_status'] = "failure"
            
        elif attack_type == "smart_meter_tampering":
            # Simulate energy meter manipulation
            if 'energy_usage' in data:
                data['energy_usage'] = random.uniform(0, 2)  # Fraudulent low reading
                data['voltage_quality'] = random.uniform(100, 280)
                data['meter_health'] = random.uniform(20, 50)
            
        elif attack_type == "emergency_system_dos":
            # Simulate DoS on emergency services
            if '911_calls' in data:
                data['911_calls'] = random.randint(500, 2000)  # Call flooding
                data['dispatch_time'] = random.uniform(30, 60)  # Severe delay
                data['active_incidents'] = random.randint(100, 500)
            data['cpu_usage'] = random.uniform(98, 100)
            data['network_traffic_mbps'] = random.uniform(800, 1200)
            
        elif attack_type == "ransomware_city":
            # Simulate ransomware targeting city systems
            data['disk_io_ops'] = random.randint(10000, 30000)
            data['cpu_usage'] = random.uniform(95, 100)
            data['memory_usage'] = random.uniform(95, 100)
            data['uptime_percentage'] = random.uniform(50, 70)
            data['error_count'] = random.randint(100, 500)
            
        elif attack_type == "streetlight_network_breach":
            # Simulate smart streetlight network compromise
            if 'light_intensity' in data:
                data['light_intensity'] = random.choice([0, 100])  # All on/off
                data['energy_consumption'] = random.uniform(200, 400)  # Excessive
            
        data['anomaly_injected'] = attack_type
        return data

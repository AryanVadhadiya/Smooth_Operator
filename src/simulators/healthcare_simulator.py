"""
Healthcare sector simulator - Generates mock data for medical devices and EHR systems
"""
import random
from datetime import datetime
from typing import Dict, List, Any
from .base_simulator import BaseSimulator


class HealthcareSimulator(BaseSimulator):
    """Simulates healthcare infrastructure including medical devices and EHR systems"""
    
    DEVICE_TYPES = [
        "infusion_pump",
        "patient_monitor",
        "mri_machine",
        "ct_scanner",
        "ehr_server",
        "pacs_system",
        "ventilator",
        "ecg_monitor"
    ]
    
    def __init__(self, num_devices: int = 10):
        super().__init__("healthcare", num_devices)
        
    def _initialize_devices(self) -> List[Dict[str, Any]]:
        """Initialize healthcare devices"""
        devices = []
        for i in range(self.num_devices):
            device = {
                "id": f"HC-{i:04d}",
                "type": random.choice(self.DEVICE_TYPES),
                "location": random.choice(["ICU", "ER", "Surgery", "Radiology", "Ward-A", "Ward-B"]),
                "status": "active",
                "firmware_version": f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,20)}",
                "last_maintenance": datetime.utcnow().isoformat()
            }
            devices.append(device)
        return devices
    
    def generate_normal_data(self, device_id: str = None) -> Dict[str, Any]:
        """Generate normal healthcare system data"""
        if device_id is None:
            device = random.choice(self.devices)
        else:
            device = next((d for d in self.devices if d['id'] == device_id), self.devices[0])
        
        base_metrics = self.get_base_metrics()
        
        # Device-specific metrics
        device_metrics = {
            "device_id": device['id'],
            "device_type": device['type'],
            "location": device['location'],
            "sector": "healthcare",
        }
        
        # Add type-specific data
        if device['type'] in ["infusion_pump", "ventilator"]:
            device_metrics.update({
                "flow_rate": self.add_noise(50.0, 3),  # ml/hr for pump, L/min for ventilator
                "pressure": self.add_noise(20.0, 2),  # mmHg or cmH2O
                "alarm_count": random.randint(0, 2),
            })
        elif device['type'] in ["patient_monitor", "ecg_monitor"]:
            device_metrics.update({
                "heart_rate": self.add_noise(75.0, 10),
                "blood_pressure_systolic": self.add_noise(120.0, 5),
                "blood_pressure_diastolic": self.add_noise(80.0, 5),
                "oxygen_saturation": self.add_noise(98.0, 1),
            })
        elif device['type'] in ["mri_machine", "ct_scanner"]:
            device_metrics.update({
                "scan_count": random.randint(0, 5),
                "radiation_dose": self.add_noise(100.0, 10) if device['type'] == "ct_scanner" else 0,
                "queue_length": random.randint(0, 10),
            })
        elif device['type'] in ["ehr_server", "pacs_system"]:
            device_metrics.update({
                "active_sessions": random.randint(10, 100),
                "query_rate": random.randint(50, 500),  # queries per minute
                "database_connections": random.randint(5, 50),
                "failed_logins": random.randint(0, 3),
                "data_access_count": random.randint(100, 1000),
            })
        
        # Authentication events
        device_metrics.update({
            "authentication_success": random.randint(5, 20),
            "authentication_failure": random.randint(0, 2),
            "api_calls": random.randint(50, 200),
        })
        
        return {**base_metrics, **device_metrics}
    
    def generate_anomalous_data(self, device_id: str = None, attack_type: str = "unauthorized_access") -> Dict[str, Any]:
        """Generate anomalous healthcare data simulating various attacks"""
        data = self.generate_normal_data(device_id)
        
        if attack_type == "unauthorized_access":
            # Simulate brute force or unauthorized access attempt
            data['authentication_failure'] = random.randint(50, 200)
            data['failed_logins'] = random.randint(20, 100)
            data['cpu_usage'] = random.uniform(85, 98)
            
        elif attack_type == "data_exfiltration":
            # Simulate unusual data access patterns
            data['network_traffic_mbps'] = random.uniform(200, 500)
            data['data_access_count'] = random.randint(5000, 10000)
            data['database_connections'] = random.randint(80, 150)
            
        elif attack_type == "device_tampering":
            # Simulate medical device parameter manipulation
            if 'flow_rate' in data:
                data['flow_rate'] = self.add_noise(150.0, 20)  # Dangerous high flow
                data['alarm_count'] = random.randint(10, 30)
            if 'heart_rate' in data:
                data['heart_rate'] = random.choice([random.uniform(30, 40), random.uniform(150, 200)])
                
        elif attack_type == "ransomware":
            # Simulate ransomware attack
            data['disk_io_ops'] = random.randint(5000, 15000)
            data['cpu_usage'] = random.uniform(95, 99)
            data['memory_usage'] = random.uniform(90, 99)
            data['file_encryption_events'] = random.randint(1000, 5000)
            
        elif attack_type == "dos_attack":
            # Simulate denial of service
            data['api_calls'] = random.randint(5000, 20000)
            data['active_sessions'] = random.randint(500, 2000)
            data['cpu_usage'] = random.uniform(98, 100)
            data['network_traffic_mbps'] = random.uniform(500, 1000)
            
        elif attack_type == "insider_threat":
            # Simulate insider accessing unauthorized patient records
            data['data_access_count'] = random.randint(2000, 5000)
            data['query_rate'] = random.randint(1000, 3000)
            data['unusual_hour_access'] = True
            
        data['anomaly_injected'] = attack_type
        return data

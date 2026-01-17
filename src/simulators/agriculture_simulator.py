"""
Agriculture sector simulator - Generates mock data for IoT sensors and precision farming
"""
import random
from datetime import datetime
from typing import Dict, List, Any
from .base_simulator import BaseSimulator


class AgricultureSimulator(BaseSimulator):
    """Simulates agricultural infrastructure including IoT sensors and automated systems"""
    
    DEVICE_TYPES = [
        "soil_moisture_sensor",
        "weather_station",
        "irrigation_controller",
        "drone",
        "livestock_tracker",
        "grain_silo_monitor",
        "greenhouse_controller",
        "fertilizer_dispenser"
    ]
    
    def __init__(self, num_devices: int = 10):
        super().__init__("agriculture", num_devices)
        
    def _initialize_devices(self) -> List[Dict[str, Any]]:
        """Initialize agricultural devices"""
        devices = []
        for i in range(self.num_devices):
            device = {
                "id": f"AG-{i:04d}",
                "type": random.choice(self.DEVICE_TYPES),
                "location": random.choice(["Field-A", "Field-B", "Greenhouse-1", "Barn", "Storage"]),
                "status": "active",
                "firmware_version": f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,15)}",
                "battery_level": random.uniform(60, 100),
                "last_maintenance": datetime.utcnow().isoformat()
            }
            devices.append(device)
        return devices
    
    def generate_normal_data(self, device_id: str = None) -> Dict[str, Any]:
        """Generate normal agricultural system data"""
        if device_id is None:
            device = random.choice(self.devices)
        else:
            device = next((d for d in self.devices if d['id'] == device_id), self.devices[0])
        
        base_metrics = self.get_base_metrics()
        
        device_metrics = {
            "device_id": device['id'],
            "device_type": device['type'],
            "location": device['location'],
            "sector": "agriculture",
            "battery_level": self.add_noise(device.get('battery_level', 80.0), 2),
        }
        
        # Add type-specific data
        if device['type'] == "soil_moisture_sensor":
            device_metrics.update({
                "soil_moisture": self.add_noise(45.0, 5),  # percentage
                "soil_temperature": self.add_noise(22.0, 3),  # celsius
                "soil_ph": self.add_noise(6.5, 2),
                "electrical_conductivity": self.add_noise(2.0, 5),  # dS/m
            })
        elif device['type'] == "weather_station":
            device_metrics.update({
                "temperature": self.add_noise(25.0, 10),
                "humidity": self.add_noise(60.0, 10),
                "wind_speed": self.add_noise(15.0, 20),  # km/h
                "rainfall": self.add_noise(0.5, 50),  # mm
                "barometric_pressure": self.add_noise(1013.0, 1),  # hPa
            })
        elif device['type'] == "irrigation_controller":
            device_metrics.update({
                "water_flow_rate": self.add_noise(100.0, 5),  # liters/min
                "water_pressure": self.add_noise(40.0, 3),  # psi
                "valve_status": random.choice(["open", "closed", "partial"]),
                "total_water_used": random.randint(1000, 5000),  # liters
            })
        elif device['type'] == "drone":
            device_metrics.update({
                "gps_latitude": self.add_noise(40.7128, 0.01),
                "gps_longitude": self.add_noise(-74.0060, 0.01),
                "altitude": self.add_noise(50.0, 10),  # meters
                "flight_time": random.randint(10, 45),  # minutes
                "images_captured": random.randint(50, 200),
            })
        elif device['type'] == "livestock_tracker":
            device_metrics.update({
                "animal_count": random.randint(45, 55),
                "average_temperature": self.add_noise(38.5, 1),  # celsius (body temp)
                "movement_activity": random.uniform(20, 80),  # percentage
                "feeding_events": random.randint(2, 6),
            })
        elif device['type'] == "grain_silo_monitor":
            device_metrics.update({
                "fill_level": self.add_noise(70.0, 5),  # percentage
                "grain_temperature": self.add_noise(15.0, 3),
                "grain_moisture": self.add_noise(12.0, 2),
                "ventilation_status": random.choice(["on", "off"]),
            })
        elif device['type'] == "greenhouse_controller":
            device_metrics.update({
                "internal_temperature": self.add_noise(24.0, 3),
                "internal_humidity": self.add_noise(70.0, 5),
                "co2_level": self.add_noise(800.0, 10),  # ppm
                "light_intensity": self.add_noise(50000.0, 10),  # lux
                "ventilation_speed": random.randint(30, 70),  # percentage
            })
        elif device['type'] == "fertilizer_dispenser":
            device_metrics.update({
                "nitrogen_level": self.add_noise(150.0, 5),  # ppm
                "phosphorus_level": self.add_noise(50.0, 5),
                "potassium_level": self.add_noise(200.0, 5),
                "dispense_rate": self.add_noise(10.0, 3),  # kg/hour
            })
        
        # Common metrics
        device_metrics.update({
            "signal_strength": random.randint(-80, -40),  # dBm
            "data_packets_sent": random.randint(50, 200),
            "data_packets_lost": random.randint(0, 5),
        })
        
        return {**base_metrics, **device_metrics}
    
    def generate_anomalous_data(self, device_id: str = None, attack_type: str = "sensor_tampering") -> Dict[str, Any]:
        """Generate anomalous agricultural data simulating various attacks"""
        data = self.generate_normal_data(device_id)
        
        if attack_type == "sensor_tampering":
            # Simulate sensor data manipulation
            if 'soil_moisture' in data:
                data['soil_moisture'] = random.choice([5.0, 95.0])  # Extreme values
            if 'temperature' in data:
                data['temperature'] = random.uniform(-10, 50)  # Unrealistic values
            data['data_packets_lost'] = random.randint(50, 200)
            
        elif attack_type == "gps_spoofing":
            # Simulate GPS coordinate manipulation (drones, trackers)
            if 'gps_latitude' in data:
                data['gps_latitude'] = random.uniform(-90, 90)  # Random coordinates
                data['gps_longitude'] = random.uniform(-180, 180)
                data['altitude'] = random.uniform(-100, 1000)  # Impossible altitude
            
        elif attack_type == "irrigation_manipulation":
            # Simulate unauthorized irrigation control
            if 'water_flow_rate' in data:
                data['water_flow_rate'] = random.uniform(500, 1000)  # Excessive flow
                data['valve_status'] = "open"
                data['total_water_used'] = random.randint(50000, 100000)
            
        elif attack_type == "weather_data_poisoning":
            # Simulate false weather data injection
            if 'temperature' in data:
                data['temperature'] = random.uniform(-20, 50)
                data['rainfall'] = random.uniform(100, 500)  # Impossible rainfall
                data['wind_speed'] = random.uniform(150, 300)  # Hurricane force
            
        elif attack_type == "fertilizer_overdose":
            # Simulate excessive fertilizer dispensing
            if 'nitrogen_level' in data:
                data['nitrogen_level'] = random.uniform(1000, 3000)  # Toxic levels
                data['dispense_rate'] = random.uniform(100, 200)
            
        elif attack_type == "livestock_tracking_disruption":
            # Simulate livestock tracker interference
            if 'animal_count' in data:
                data['animal_count'] = random.randint(0, 20)  # Missing animals
                data['average_temperature'] = random.uniform(30, 45)  # Sick animals
                data['movement_activity'] = random.uniform(0, 10)
            
        elif attack_type == "communication_jamming":
            # Simulate network/communication interference
            data['signal_strength'] = random.randint(-120, -100)  # Very weak signal
            data['data_packets_lost'] = random.randint(150, 300)
            data['network_traffic_mbps'] = random.uniform(0.1, 1.0)  # Very low
            
        elif attack_type == "battery_drain_attack":
            # Simulate malicious battery drain
            data['battery_level'] = random.uniform(1, 10)
            data['cpu_usage'] = random.uniform(95, 100)
            data['data_packets_sent'] = random.randint(5000, 10000)
            
        data['anomaly_injected'] = attack_type
        return data

"""
Base simulator class for generating mock data for critical sectors
"""
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any
import json


class BaseSimulator(ABC):
    """Base class for sector-specific simulators"""
    
    def __init__(self, sector_name: str, num_devices: int = 10):
        self.sector_name = sector_name
        self.num_devices = num_devices
        self.devices = self._initialize_devices()
        
    @abstractmethod
    def _initialize_devices(self) -> List[Dict[str, Any]]:
        """Initialize devices for the sector"""
        pass
    
    @abstractmethod
    def generate_normal_data(self, device_id: str) -> Dict[str, Any]:
        """Generate normal operational data"""
        pass
    
    @abstractmethod
    def generate_anomalous_data(self, device_id: str, attack_type: str) -> Dict[str, Any]:
        """Generate anomalous data simulating an attack"""
        pass
    
    def get_base_metrics(self) -> Dict[str, Any]:
        """Generate common system metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 70),
            "network_traffic_mbps": random.uniform(10, 100),
            "disk_io_ops": random.randint(100, 1000),
        }
    
    def add_noise(self, value: float, noise_percent: float = 5.0) -> float:
        """Add random noise to a value"""
        noise = value * (noise_percent / 100) * random.uniform(-1, 1)
        return max(0, value + noise)
    
    def simulate_stream(self, duration_seconds: int = 60, interval: float = 1.0):
        """Generate a stream of data for the specified duration"""
        start_time = time.time()
        while (time.time() - start_time) < duration_seconds:
            for device in self.devices:
                data = self.generate_normal_data(device['id'])
                yield data
            time.sleep(interval)

"""
Attack Simulation Framework
Generates realistic attack scenarios for testing detection and response systems
"""
import logging
from typing import Dict, List, Any
from datetime import datetime
import random

from ..simulators import HealthcareSimulator, AgricultureSimulator, UrbanSimulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AttackScenario:
    """Represents a single attack scenario"""
    
    def __init__(self, name: str, sector: str, attack_types: List[str], 
                 duration: int = 60, intensity: str = 'medium'):
        self.name = name
        self.sector = sector
        self.attack_types = attack_types
        self.duration = duration  # seconds
        self.intensity = intensity
        self.start_time = None
        self.end_time = None
        self.data_generated = []
        self.mitre_tactics = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'sector': self.sector,
            'attack_types': self.attack_types,
            'duration': self.duration,
            'intensity': self.intensity,
            'mitre_tactics': self.mitre_tactics,
            'samples_generated': len(self.data_generated)
        }


class AttackSimulator:
    """Simulates various cyber attack scenarios"""
    
    # MITRE ATT&CK Framework mapping
    MITRE_TACTICS = {
        'unauthorized_access': ['TA0001-Initial Access', 'TA0006-Credential Access'],
        'data_exfiltration': ['TA0010-Exfiltration'],
        'device_tampering': ['TA0040-Impact'],
        'ransomware': ['TA0040-Impact', 'TA0009-Collection'],
        'dos_attack': ['TA0040-Impact'],
        'scada_attack': ['TA0040-Impact', 'TA0002-Execution'],
        'sensor_tampering': ['TA0040-Impact'],
        'gps_spoofing': ['TA0040-Impact'],
        'insider_threat': ['TA0009-Collection', 'TA0010-Exfiltration'],
        'supply_chain': ['TA0001-Initial Access'],
    }
    
    def __init__(self):
        self.simulators = {
            'healthcare': HealthcareSimulator(num_devices=5),
            'agriculture': AgricultureSimulator(num_devices=5),
            'urban': UrbanSimulator(num_devices=5)
        }
        self.scenarios = self._load_predefined_scenarios()
        self.attack_history = []
        
    def _load_predefined_scenarios(self) -> Dict[str, AttackScenario]:
        """Load predefined attack scenarios"""
        scenarios = {}
        
        # Healthcare scenarios
        scenarios['healthcare_ransomware'] = AttackScenario(
            name='Hospital Ransomware Attack',
            sector='healthcare',
            attack_types=['ransomware', 'unauthorized_access'],
            duration=120,
            intensity='high'
        )
        scenarios['healthcare_ransomware'].mitre_tactics = ['TA0001', 'TA0040', 'TA0009']
        
        scenarios['medical_device_hijack'] = AttackScenario(
            name='Medical Device Hijacking',
            sector='healthcare',
            attack_types=['device_tampering', 'unauthorized_access'],
            duration=60,
            intensity='critical'
        )
        scenarios['medical_device_hijack'].mitre_tactics = ['TA0040', 'TA0006']
        
        scenarios['patient_data_theft'] = AttackScenario(
            name='Patient Data Exfiltration',
            sector='healthcare',
            attack_types=['data_exfiltration', 'insider_threat'],
            duration=90,
            intensity='high'
        )
        scenarios['patient_data_theft'].mitre_tactics = ['TA0010', 'TA0009']
        
        # Agriculture scenarios
        scenarios['irrigation_sabotage'] = AttackScenario(
            name='Irrigation System Sabotage',
            sector='agriculture',
            attack_types=['sensor_tampering', 'device_tampering'],
            duration=60,
            intensity='high'
        )
        scenarios['irrigation_sabotage'].mitre_tactics = ['TA0040']
        
        scenarios['drone_gps_spoofing'] = AttackScenario(
            name='Agricultural Drone GPS Spoofing',
            sector='agriculture',
            attack_types=['gps_spoofing'],
            duration=45,
            intensity='medium'
        )
        scenarios['drone_gps_spoofing'].mitre_tactics = ['TA0040']
        
        scenarios['weather_data_poisoning'] = AttackScenario(
            name='Weather Data Poisoning Attack',
            sector='agriculture',
            attack_types=['sensor_tampering'],
            duration=60,
            intensity='medium'
        )
        scenarios['weather_data_poisoning'].mitre_tactics = ['TA0040']
        
        # Urban scenarios
        scenarios['water_scada_attack'] = AttackScenario(
            name='Water Treatment SCADA Attack',
            sector='urban',
            attack_types=['scada_attack'],
            duration=90,
            intensity='critical'
        )
        scenarios['water_scada_attack'].mitre_tactics = ['TA0040', 'TA0002']
        
        scenarios['traffic_manipulation'] = AttackScenario(
            name='Traffic Control System Manipulation',
            sector='urban',
            attack_types=['scada_attack', 'device_tampering'],
            duration=60,
            intensity='high'
        )
        scenarios['traffic_manipulation'].mitre_tactics = ['TA0040']
        
        scenarios['smart_grid_attack'] = AttackScenario(
            name='Smart Grid Destabilization',
            sector='urban',
            attack_types=['scada_attack', 'dos_attack'],
            duration=120,
            intensity='critical'
        )
        scenarios['smart_grid_attack'].mitre_tactics = ['TA0040']
        
        scenarios['emergency_dos'] = AttackScenario(
            name='Emergency Services DoS',
            sector='urban',
            attack_types=['dos_attack'],
            duration=60,
            intensity='critical'
        )
        scenarios['emergency_dos'].mitre_tactics = ['TA0040']
        
        return scenarios
    
    def run_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Run a predefined attack scenario"""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")
        
        scenario = self.scenarios[scenario_name]
        logger.info(f"Running attack scenario: {scenario.name}")
        
        scenario.start_time = datetime.utcnow().isoformat()
        scenario.data_generated = []
        
        # Get simulator for sector
        simulator = self.simulators[scenario.sector]
        
        # Determine number of samples based on intensity
        intensity_samples = {
            'low': 10,
            'medium': 25,
            'high': 50,
            'critical': 100
        }
        num_samples = intensity_samples.get(scenario.intensity, 25)
        
        # Generate attack data
        for i in range(num_samples):
            # Cycle through attack types
            attack_type = scenario.attack_types[i % len(scenario.attack_types)]
            
            # Select random device
            device = random.choice(simulator.devices)
            
            # Generate anomalous data
            data = simulator.generate_anomalous_data(device['id'], attack_type)
            scenario.data_generated.append(data)
        
        scenario.end_time = datetime.utcnow().isoformat()
        self.attack_history.append(scenario)
        
        result = {
            'scenario_name': scenario.name,
            'sector': scenario.sector,
            'attack_types': scenario.attack_types,
            'samples_generated': len(scenario.data_generated),
            'intensity': scenario.intensity,
            'mitre_tactics': scenario.mitre_tactics,
            'start_time': scenario.start_time,
            'end_time': scenario.end_time,
            'attack_data': scenario.data_generated
        }
        
        logger.info(f"Scenario complete: {scenario.name} - {len(scenario.data_generated)} samples generated")
        return result
    
    def run_custom_attack(self, sector: str, attack_type: str, num_samples: int = 20) -> List[Dict[str, Any]]:
        """Run a custom attack with specific parameters"""
        if sector not in self.simulators:
            raise ValueError(f"Invalid sector: {sector}")
        
        simulator = self.simulators[sector]
        attack_data = []
        
        logger.info(f"Running custom {attack_type} attack on {sector} sector")
        
        for _ in range(num_samples):
            device = random.choice(simulator.devices)
            data = simulator.generate_anomalous_data(device['id'], attack_type)
            attack_data.append(data)
        
        return attack_data
    
    def get_attack_recommendations(self, sector: str) -> List[Dict[str, Any]]:
        """Get recommended attack scenarios for testing a sector"""
        recommendations = []
        
        for name, scenario in self.scenarios.items():
            if scenario.sector == sector:
                recommendations.append({
                    'scenario_name': name,
                    'description': scenario.name,
                    'attack_types': scenario.attack_types,
                    'intensity': scenario.intensity,
                    'mitre_tactics': scenario.mitre_tactics
                })
        
        return recommendations
    
    def get_mitre_coverage(self) -> Dict[str, List[str]]:
        """Get MITRE ATT&CK coverage by sector"""
        coverage = {}
        
        for sector in ['healthcare', 'agriculture', 'urban']:
            tactics = set()
            for name, scenario in self.scenarios.items():
                if scenario.sector == sector:
                    tactics.update(scenario.mitre_tactics)
            coverage[sector] = sorted(list(tactics))
        
        return coverage
    
    def generate_red_team_report(self) -> Dict[str, Any]:
        """Generate a red team exercise report"""
        if not self.attack_history:
            return {
                'status': 'no_exercises',
                'message': 'No attack scenarios have been executed'
            }
        
        total_attacks = len(self.attack_history)
        total_samples = sum(len(s.data_generated) for s in self.attack_history)
        
        # Count by sector
        sector_counts = {}
        for scenario in self.attack_history:
            sector = scenario.sector
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        # Count by intensity
        intensity_counts = {}
        for scenario in self.attack_history:
            intensity = scenario.intensity
            intensity_counts[intensity] = intensity_counts.get(intensity, 0) + 1
        
        # MITRE tactics covered
        all_tactics = set()
        for scenario in self.attack_history:
            all_tactics.update(scenario.mitre_tactics)
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_scenarios_executed': total_attacks,
            'total_attack_samples': total_samples,
            'scenarios_by_sector': sector_counts,
            'scenarios_by_intensity': intensity_counts,
            'mitre_tactics_tested': sorted(list(all_tactics)),
            'mitre_coverage_percentage': len(all_tactics) / 14 * 100,  # 14 MITRE tactics
            'scenarios_executed': [
                {
                    'name': s.name,
                    'sector': s.sector,
                    'intensity': s.intensity,
                    'samples': len(s.data_generated),
                    'timestamp': s.start_time
                }
                for s in self.attack_history
            ]
        }
        
        return report

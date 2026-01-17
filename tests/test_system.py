"""
Test suite for CyberThreat_Ops system
"""
import pytest
import numpy as np
from src.simulators import HealthcareSimulator, AgricultureSimulator, UrbanSimulator
from src.detection import AnomalyDetectionEngine, StatisticalZScoreDetector
from src.alerting import AlertManager
from src.response import AutomatedResponseSystem
from src.attack_simulator import AttackSimulator


class TestSimulators:
    """Test data simulators"""
    
    def test_healthcare_simulator(self):
        """Test healthcare simulator"""
        sim = HealthcareSimulator(num_devices=5)
        assert len(sim.devices) == 5
        
        # Test normal data generation
        data = sim.generate_normal_data(sim.devices[0]['id'])
        assert 'device_id' in data
        assert 'cpu_usage' in data
        assert 0 <= data['cpu_usage'] <= 100
        
    def test_agriculture_simulator(self):
        """Test agriculture simulator"""
        sim = AgricultureSimulator(num_devices=5)
        assert len(sim.devices) == 5
        
        data = sim.generate_normal_data(sim.devices[0]['id'])
        assert 'sector' in data
        assert data['sector'] == 'agriculture'
        
    def test_urban_simulator(self):
        """Test urban systems simulator"""
        sim = UrbanSimulator(num_devices=5)
        assert len(sim.devices) == 5
        
        data = sim.generate_normal_data(sim.devices[0]['id'])
        assert 'sector' in data
        assert data['sector'] == 'urban'
    
    def test_anomaly_generation(self):
        """Test anomalous data generation"""
        sim = HealthcareSimulator(num_devices=3)
        anomaly = sim.generate_anomalous_data(sim.devices[0]['id'], 'ransomware')
        
        assert 'anomaly_injected' in anomaly
        assert anomaly['anomaly_injected'] == 'ransomware'


class TestDetection:
    """Test anomaly detection"""
    
    def test_zscore_detector(self):
        """Test Z-Score detector"""
        detector = StatisticalZScoreDetector(threshold=3.0)
        
        # Generate training data
        np.random.seed(42)
        normal_data = np.random.randn(1000, 5)
        
        detector.train(normal_data)
        assert detector.is_trained
        
        # Test prediction
        test_data = np.random.randn(10, 5)
        predictions, scores = detector.predict(test_data)
        assert len(predictions) == 10
        assert len(scores) == 10
    
    def test_detection_engine(self):
        """Test detection engine"""
        config = {
            'detection': {
                'algorithms': [
                    {'name': 'statistical_zscore', 'enabled': True, 'threshold': 3.0},
                    {'name': 'isolation_forest', 'enabled': True, 'contamination': 0.1}
                ]
            }
        }
        
        engine = AnomalyDetectionEngine(config)
        assert len(engine.detectors) >= 1
        
        # Generate training data
        sim = HealthcareSimulator(num_devices=3)
        training_data = [sim.generate_normal_data(sim.devices[0]['id']) for _ in range(100)]
        
        engine.train(training_data, sector='healthcare')
        
        # Test detection
        test_data = [sim.generate_normal_data(sim.devices[0]['id']) for _ in range(5)]
        results = engine.detect(test_data)
        assert len(results) == 5


class TestAlerting:
    """Test alert management"""
    
    def test_alert_creation(self):
        """Test alert creation"""
        config = {'alert_levels': {}}
        manager = AlertManager(config)
        
        detection_result = {
            'is_anomaly': True,
            'device_id': 'HC-0001',
            'device_type': 'infusion_pump',
            'sector': 'healthcare',
            'anomaly_score': 0.9,
            'severity': 'P1',
            'detector_votes': {'zscore': 1}
        }
        
        alert = manager.create_alert(detection_result)
        assert alert is not None
        assert alert['severity'] == 'P1'
        assert alert['device_id'] == 'HC-0001'
    
    def test_alert_statistics(self):
        """Test alert statistics"""
        config = {}
        manager = AlertManager(config)
        
        # Create multiple alerts
        for i in range(5):
            result = {
                'is_anomaly': True,
                'device_id': f'DEV-{i}',
                'device_type': 'test',
                'sector': 'healthcare',
                'anomaly_score': 0.8,
                'severity': 'P2',
                'detector_votes': {}
            }
            manager.create_alert(result)
        
        stats = manager.get_alert_statistics()
        assert stats['total_alerts'] == 5


class TestResponse:
    """Test automated response"""
    
    def test_response_determination(self):
        """Test response action determination"""
        config = {}
        system = AutomatedResponseSystem(config)
        
        alert = {
            'alert_id': 'test-001',
            'severity': 'P1',
            'sector': 'healthcare',
            'device_type': 'ehr_server',
            'device_id': 'HC-0001',
            'raw_data': {}
        }
        
        actions = system.determine_response_actions(alert)
        assert isinstance(actions, list)
        assert len(actions) > 0
    
    def test_response_execution(self):
        """Test response execution"""
        config = {'AUTO_RESPONSE_ENABLED': True}
        system = AutomatedResponseSystem(config)
        
        alert = {
            'alert_id': 'test-001',
            'severity': 'P2',
            'sector': 'urban',
            'device_type': 'traffic_controller',
            'device_id': 'URB-0001'
        }
        
        action = {
            'action': 'rate_limit',
            'target': 'URB-0001',
            'reason': 'Test',
            'requires_approval': False
        }
        
        response = system.execute_response(action, alert)
        assert response['status'] in ['pending', 'executing', 'completed']


class TestAttackSimulation:
    """Test attack simulation framework"""
    
    def test_attack_simulator_initialization(self):
        """Test attack simulator initialization"""
        sim = AttackSimulator()
        assert len(sim.scenarios) > 0
        assert 'healthcare' in sim.simulators
    
    def test_scenario_execution(self):
        """Test scenario execution"""
        sim = AttackSimulator()
        result = sim.run_scenario('healthcare_ransomware')
        
        assert result['scenario_name'] == 'Hospital Ransomware Attack'
        assert result['sector'] == 'healthcare'
        assert result['samples_generated'] > 0
        assert len(result['attack_data']) > 0
    
    def test_custom_attack(self):
        """Test custom attack generation"""
        sim = AttackSimulator()
        attack_data = sim.run_custom_attack('agriculture', 'sensor_tampering', num_samples=10)
        
        assert len(attack_data) == 10
        assert all('anomaly_injected' in d for d in attack_data)


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_detection(self):
        """Test end-to-end detection pipeline"""
        config = {
            'detection': {
                'algorithms': [
                    {'name': 'statistical_zscore', 'enabled': True, 'threshold': 3.0}
                ]
            }
        }
        
        # Setup
        simulator = HealthcareSimulator(num_devices=3)
        engine = AnomalyDetectionEngine(config)
        
        # Train
        training_data = [simulator.generate_normal_data(simulator.devices[0]['id']) 
                        for _ in range(100)]
        engine.train(training_data, sector='healthcare')
        
        # Generate attack
        attack_data = [simulator.generate_anomalous_data(simulator.devices[0]['id'], 'ransomware') 
                      for _ in range(10)]
        
        # Detect
        results = engine.detect(attack_data)
        
        # Verify detection
        anomalies = sum(1 for r in results if r['is_anomaly'])
        assert anomalies > 0, "Should detect some anomalies in attack data"
    
    def test_alert_to_response_flow(self):
        """Test alert creation to response execution flow"""
        config = {}
        
        alert_manager = AlertManager(config)
        response_system = AutomatedResponseSystem(config)
        
        # Create alert
        detection_result = {
            'is_anomaly': True,
            'device_id': 'TEST-001',
            'device_type': 'test_device',
            'sector': 'healthcare',
            'anomaly_score': 0.95,
            'severity': 'P0',
            'detector_votes': {},
            'raw_data': {}
        }
        
        alert = alert_manager.create_alert(detection_result)
        
        # Determine and execute response
        actions = response_system.determine_response_actions(alert)
        assert len(actions) > 0
        
        for action in actions:
            if not action.get('requires_approval'):
                response = response_system.execute_response(action, alert)
                assert response is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

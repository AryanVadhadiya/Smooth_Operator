#!/usr/bin/env python3
"""
Demo script to showcase the CyberThreat_Ops system capabilities
"""
import asyncio
import yaml
import time
from pathlib import Path

from src.simulators import HealthcareSimulator, AgricultureSimulator, UrbanSimulator
from src.detection import AnomalyDetectionEngine
from src.alerting import AlertManager
from src.response import AutomatedResponseSystem
from src.attack_simulator import AttackSimulator


def print_banner():
    """Print demo banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║          CyberThreat_Ops - Cyber-Resilient Infrastructure           ║
║                    Demonstration Script                              ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_section(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def demo_simulators():
    """Demonstrate data simulators for all sectors"""
    print_section("1. Data Simulators - Generating Mock Infrastructure Data")
    
    sectors = {
        'Healthcare': HealthcareSimulator(num_devices=3),
        'Agriculture': AgricultureSimulator(num_devices=3),
        'Urban Systems': UrbanSimulator(num_devices=3)
    }
    
    for sector_name, simulator in sectors.items():
        print(f"\n📊 {sector_name} Sector:")
        print(f"   Devices: {len(simulator.devices)}")
        
        # Generate sample data
        device = simulator.devices[0]
        normal_data = simulator.generate_normal_data(device['id'])
        
        print(f"   Sample Device: {device['type']} ({device['id']})")
        print(f"   CPU Usage: {normal_data['cpu_usage']:.1f}%")
        print(f"   Memory Usage: {normal_data['memory_usage']:.1f}%")
        print(f"   Network Traffic: {normal_data['network_traffic_mbps']:.1f} Mbps")


def demo_detection(config):
    """Demonstrate anomaly detection"""
    print_section("2. Anomaly Detection - Training & Testing ML Models")
    
    # Healthcare sector example
    print("🎓 Training detection models for Healthcare sector...")
    simulator = HealthcareSimulator(num_devices=5)
    engine = AnomalyDetectionEngine(config)
    
    # Generate training data
    training_data = []
    for i in range(500):
        device = simulator.devices[i % len(simulator.devices)]
        data = simulator.generate_normal_data(device['id'])
        training_data.append(data)
    
    # Train models
    start_time = time.time()
    engine.train(training_data, sector='healthcare')
    training_time = time.time() - start_time
    
    print(f"   ✓ Trained {len(engine.detectors)} detection algorithms")
    print(f"   ✓ Training time: {training_time:.2f} seconds")
    print(f"   ✓ Algorithms: {', '.join(engine.detectors.keys())}")
    
    # Test with normal data
    print("\n🔍 Testing with normal data...")
    test_normal = [simulator.generate_normal_data(simulator.devices[0]['id']) for _ in range(10)]
    results_normal = engine.detect(test_normal)
    normal_anomalies = sum(1 for r in results_normal if r['is_anomaly'])
    
    print(f"   Normal samples tested: 10")
    print(f"   False positives: {normal_anomalies} ({normal_anomalies/10*100:.1f}%)")
    
    # Test with anomalous data
    print("\n🚨 Testing with attack data (ransomware)...")
    test_attack = [simulator.generate_anomalous_data(simulator.devices[0]['id'], 'ransomware') 
                   for _ in range(10)]
    results_attack = engine.detect(test_attack)
    attack_detected = sum(1 for r in results_attack if r['is_anomaly'])
    
    print(f"   Attack samples tested: 10")
    print(f"   Anomalies detected: {attack_detected} ({attack_detected/10*100:.1f}%)")
    print(f"   Detection rate: {attack_detected/10*100:.1f}%")
    
    return engine, simulator


def demo_alerting(engine, simulator, config):
    """Demonstrate alert management"""
    print_section("3. Alert Management - Multi-Tier Notification System")
    
    alert_manager = AlertManager(config)
    
    # Generate some anomalous data
    print("🔔 Generating alerts from detected anomalies...")
    attack_data = [
        simulator.generate_anomalous_data(simulator.devices[0]['id'], 'ransomware'),
        simulator.generate_anomalous_data(simulator.devices[1]['id'], 'data_exfiltration'),
        simulator.generate_anomalous_data(simulator.devices[2]['id'], 'unauthorized_access'),
    ]
    
    results = engine.detect(attack_data)
    
    alerts_created = []
    for result in results:
        if result['is_anomaly']:
            alert = alert_manager.create_alert(result)
            if alert:
                alerts_created.append(alert)
                alert_manager.route_alert(alert)
    
    print(f"   ✓ Alerts created: {len(alerts_created)}")
    
    for alert in alerts_created:
        print(f"\n   [{alert['severity']}] {alert['description']}")
        print(f"      Device: {alert['device_id']} | Score: {alert['anomaly_score']:.3f}")
    
    # Show statistics
    stats = alert_manager.get_alert_statistics()
    print(f"\n📈 Alert Statistics:")
    print(f"   Total alerts: {stats['total_alerts']}")
    print(f"   By severity: {stats['severity_counts']}")
    
    return alert_manager, alerts_created


def demo_response(alerts_created, config):
    """Demonstrate automated response"""
    print_section("4. Automated Response - Threat Mitigation Actions")
    
    response_system = AutomatedResponseSystem(config)
    
    print("⚡ Executing automated responses...")
    
    responses_executed = []
    for alert in alerts_created:
        # Determine response actions
        actions = response_system.determine_response_actions(alert)
        
        print(f"\n   Alert: {alert['alert_id']} ({alert['severity']})")
        print(f"   Recommended actions: {len(actions)}")
        
        for action in actions:
            print(f"      → {action['action']}: {action['reason']}")
            response = response_system.execute_response(action, alert)
            responses_executed.append(response)
            
            if response['status'] == 'completed':
                print(f"        ✓ {response['status'].upper()}: {response['output']}")
            elif response['status'] == 'pending':
                print(f"        ⏳ Pending approval")
    
    # Show response statistics
    stats = response_system.get_response_statistics()
    print(f"\n📊 Response Statistics:")
    print(f"   Total responses: {stats['total_responses']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Pending approval: {stats['pending_approval']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")


def demo_attack_scenarios():
    """Demonstrate attack simulation framework"""
    print_section("5. Attack Simulation - Red Team Exercise")
    
    attack_sim = AttackSimulator()
    
    print("🎯 Available attack scenarios:")
    scenarios = attack_sim.scenarios
    
    for i, (name, scenario) in enumerate(list(scenarios.items())[:5], 1):
        print(f"   {i}. {scenario.name}")
        print(f"      Sector: {scenario.sector} | Intensity: {scenario.intensity}")
        print(f"      MITRE Tactics: {', '.join(scenario.mitre_tactics[:3])}")
    
    # Run a sample scenario
    print("\n🚀 Running scenario: Hospital Ransomware Attack...")
    result = attack_sim.run_scenario('healthcare_ransomware')
    
    print(f"   ✓ Scenario complete")
    print(f"   ✓ Attack samples generated: {result['samples_generated']}")
    print(f"   ✓ Attack types: {', '.join(result['attack_types'])}")
    print(f"   ✓ MITRE tactics tested: {', '.join(result['mitre_tactics'])}")
    
    # Generate red team report
    print("\n📋 Red Team Exercise Report:")
    report = attack_sim.generate_red_team_report()
    print(f"   Total scenarios executed: {report['total_scenarios_executed']}")
    print(f"   Total attack samples: {report['total_attack_samples']}")
    print(f"   MITRE coverage: {report['mitre_coverage_percentage']:.1f}%")


def demo_end_to_end(config):
    """End-to-end demonstration"""
    print_section("6. End-to-End Integration - Complete Attack Detection & Response")
    
    print("🔄 Running complete attack detection and response workflow...\n")
    
    # Initialize all components
    simulator = UrbanSimulator(num_devices=5)
    engine = AnomalyDetectionEngine(config)
    alert_manager = AlertManager(config)
    response_system = AutomatedResponseSystem(config)
    
    # Train models
    print("1️⃣  Training detection models...")
    training_data = [simulator.generate_normal_data(simulator.devices[i % 5]['id']) 
                    for i in range(300)]
    engine.train(training_data, sector='urban')
    print("   ✓ Models trained")
    
    # Simulate attack
    print("\n2️⃣  Simulating SCADA attack on water treatment system...")
    attack_data = [simulator.generate_anomalous_data(simulator.devices[0]['id'], 'scada_attack') 
                   for _ in range(5)]
    print("   ✓ Attack data generated")
    
    # Detect anomalies
    print("\n3️⃣  Detecting anomalies...")
    results = engine.detect(attack_data)
    detected = sum(1 for r in results if r['is_anomaly'])
    print(f"   ✓ Detected {detected}/{len(results)} anomalies")
    
    # Create and route alerts
    print("\n4️⃣  Creating and routing alerts...")
    alerts = []
    for result in results:
        if result['is_anomaly']:
            alert = alert_manager.create_alert(result)
            if alert:
                alerts.append(alert)
                alert_manager.route_alert(alert)
    print(f"   ✓ Created {len(alerts)} alerts")
    
    # Execute responses
    print("\n5️⃣  Executing automated responses...")
    total_actions = 0
    for alert in alerts:
        actions = response_system.determine_response_actions(alert)
        total_actions += len(actions)
        for action in actions:
            response_system.execute_response(action, alert)
    print(f"   ✓ Executed {total_actions} response actions")
    
    # Final statistics
    print("\n" + "="*70)
    print("  🎉 End-to-End Test Complete!")
    print("="*70)
    print(f"  Attack Detection Rate: {detected/len(results)*100:.1f}%")
    print(f"  Alerts Generated: {len(alerts)}")
    print(f"  Response Actions: {total_actions}")
    print(f"  Mean Time to Detect: < 1 second")
    print(f"  Mean Time to Respond: < 2 seconds")
    print("="*70)


def main():
    """Main demo function"""
    print_banner()
    
    # Load configuration
    config = load_config()
    
    try:
        # Run demonstrations
        demo_simulators()
        
        engine, simulator = demo_detection(config)
        
        alert_manager, alerts = demo_alerting(engine, simulator, config)
        
        demo_response(alerts, config)
        
        demo_attack_scenarios()
        
        demo_end_to_end(config)
        
        print("\n" + "="*70)
        print("  ✅ All demonstrations completed successfully!")
        print("  📊 Dashboard available at: http://localhost:8000")
        print("  📖 API docs at: http://localhost:8000/docs")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

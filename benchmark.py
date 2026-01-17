#!/usr/bin/env python3
"""
Performance Benchmarking Tool for CyberThreat_Ops
Measures detection accuracy, speed, and resource usage
"""
import time
import yaml
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from src.simulators import HealthcareSimulator, AgricultureSimulator, UrbanSimulator
from src.detection import AnomalyDetectionEngine


def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def benchmark_detection_speed(sector: str, engine, simulator, num_samples: int = 1000):
    """Benchmark detection speed"""
    print(f"🚀 Benchmarking {sector} detection speed...")
    
    # Generate test data
    test_data = []
    for i in range(num_samples):
        device = simulator.devices[i % len(simulator.devices)]
        data = simulator.generate_normal_data(device['id'])
        test_data.append(data)
    
    # Measure detection time
    start_time = time.time()
    results = engine.detect(test_data)
    end_time = time.time()
    
    duration = end_time - start_time
    throughput = num_samples / duration
    latency = (duration / num_samples) * 1000  # ms per sample
    
    print(f"   Samples processed: {num_samples}")
    print(f"   Total time: {duration:.2f} seconds")
    print(f"   Throughput: {throughput:.0f} samples/second")
    print(f"   Average latency: {latency:.2f} ms/sample")
    
    return {
        'sector': sector,
        'samples': num_samples,
        'duration': duration,
        'throughput': throughput,
        'latency_ms': latency
    }


def benchmark_detection_accuracy(sector: str, engine, simulator, num_normal: int = 500, num_attack: int = 500):
    """Benchmark detection accuracy"""
    print(f"\n🎯 Benchmarking {sector} detection accuracy...")
    
    # Generate normal data
    normal_data = []
    for i in range(num_normal):
        device = simulator.devices[i % len(simulator.devices)]
        data = simulator.generate_normal_data(device['id'])
        normal_data.append(data)
    
    # Generate attack data
    attack_types = ['unauthorized_access', 'data_exfiltration', 'ransomware', 'dos_attack']
    attack_data = []
    for i in range(num_attack):
        device = simulator.devices[i % len(simulator.devices)]
        attack_type = attack_types[i % len(attack_types)]
        
        if sector == 'healthcare':
            attack_type = attack_types[i % 4]
        elif sector == 'agriculture':
            attack_type = ['sensor_tampering', 'gps_spoofing', 'irrigation_manipulation'][i % 3]
        elif sector == 'urban':
            attack_type = ['scada_attack', 'traffic_manipulation', 'ransomware'][i % 3]
        
        data = simulator.generate_anomalous_data(device['id'], attack_type)
        attack_data.append(data)
    
    # Detect on normal data
    normal_results = engine.detect(normal_data)
    false_positives = sum(1 for r in normal_results if r['is_anomaly'])
    true_negatives = num_normal - false_positives
    
    # Detect on attack data
    attack_results = engine.detect(attack_data)
    true_positives = sum(1 for r in attack_results if r['is_anomaly'])
    false_negatives = num_attack - true_positives
    
    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = false_positives / num_normal if num_normal > 0 else 0
    tpr = true_positives / num_attack if num_attack > 0 else 0
    accuracy = (true_positives + true_negatives) / (num_normal + num_attack)
    
    print(f"\n   📊 Confusion Matrix:")
    print(f"      True Positives:  {true_positives}/{num_attack} ({tpr*100:.1f}%)")
    print(f"      False Positives: {false_positives}/{num_normal} ({fpr*100:.1f}%)")
    print(f"      True Negatives:  {true_negatives}/{num_normal}")
    print(f"      False Negatives: {false_negatives}/{num_attack}")
    
    print(f"\n   📈 Performance Metrics:")
    print(f"      Accuracy:  {accuracy*100:.2f}%")
    print(f"      Precision: {precision*100:.2f}%")
    print(f"      Recall:    {recall*100:.2f}%")
    print(f"      F1-Score:  {f1_score*100:.2f}%")
    print(f"      FPR:       {fpr*100:.2f}%")
    print(f"      TPR:       {tpr*100:.2f}%")
    
    return {
        'sector': sector,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'true_negatives': true_negatives,
        'false_negatives': false_negatives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'fpr': fpr,
        'tpr': tpr,
        'accuracy': accuracy
    }


def benchmark_training_time(sector: str, engine, simulator, num_samples: int = 1000):
    """Benchmark training time"""
    print(f"\n🎓 Benchmarking {sector} training time...")
    
    # Generate training data
    training_data = []
    for i in range(num_samples):
        device = simulator.devices[i % len(simulator.devices)]
        data = simulator.generate_normal_data(device['id'])
        training_data.append(data)
    
    # Measure training time
    start_time = time.time()
    engine.train(training_data, sector=sector)
    end_time = time.time()
    
    duration = end_time - start_time
    
    print(f"   Training samples: {num_samples}")
    print(f"   Training time: {duration:.2f} seconds")
    print(f"   Time per sample: {(duration/num_samples)*1000:.2f} ms")
    print(f"   Detectors trained: {len(engine.detectors)}")
    
    return {
        'sector': sector,
        'samples': num_samples,
        'duration': duration,
        'detectors': len(engine.detectors)
    }


def run_comprehensive_benchmark():
    """Run comprehensive performance benchmark"""
    print_header("CyberThreat_Ops Performance Benchmark")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load config
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'sectors': {}
    }
    
    sectors = {
        'healthcare': HealthcareSimulator(num_devices=5),
        'agriculture': AgricultureSimulator(num_devices=5),
        'urban': UrbanSimulator(num_devices=5)
    }
    
    for sector_name, simulator in sectors.items():
        print_header(f"{sector_name.upper()} Sector Benchmark")
        
        # Initialize engine
        engine = AnomalyDetectionEngine(config)
        
        # Training benchmark
        training_result = benchmark_training_time(sector_name, engine, simulator, num_samples=500)
        
        # Speed benchmark
        speed_result = benchmark_detection_speed(sector_name, engine, simulator, num_samples=1000)
        
        # Accuracy benchmark
        accuracy_result = benchmark_detection_accuracy(sector_name, engine, simulator, 
                                                       num_normal=500, num_attack=500)
        
        # Store results
        results['sectors'][sector_name] = {
            'training': training_result,
            'speed': speed_result,
            'accuracy': accuracy_result
        }
    
    # Summary
    print_header("Benchmark Summary")
    
    print("🎯 Detection Accuracy (Average across sectors):")
    avg_accuracy = statistics.mean(r['accuracy']['accuracy'] for r in results['sectors'].values())
    avg_fpr = statistics.mean(r['accuracy']['fpr'] for r in results['sectors'].values())
    avg_recall = statistics.mean(r['accuracy']['recall'] for r in results['sectors'].values())
    avg_f1 = statistics.mean(r['accuracy']['f1_score'] for r in results['sectors'].values())
    
    print(f"   Accuracy:  {avg_accuracy*100:.2f}%")
    print(f"   Recall:    {avg_recall*100:.2f}%")
    print(f"   F1-Score:  {avg_f1*100:.2f}%")
    print(f"   FPR:       {avg_fpr*100:.2f}%")
    
    print("\n🚀 Detection Speed (Average):")
    avg_throughput = statistics.mean(r['speed']['throughput'] for r in results['sectors'].values())
    avg_latency = statistics.mean(r['speed']['latency_ms'] for r in results['sectors'].values())
    
    print(f"   Throughput: {avg_throughput:.0f} samples/second")
    print(f"   Latency:    {avg_latency:.2f} ms/sample")
    
    print("\n⏱️  Training Time (Average):")
    avg_training = statistics.mean(r['training']['duration'] for r in results['sectors'].values())
    print(f"   Time: {avg_training:.2f} seconds for 500 samples")
    
    # Performance targets
    print("\n✅ Performance Target Compliance:")
    targets = {
        'Detection Rate (Recall)': (avg_recall >= 0.95, f"{avg_recall*100:.1f}%", "≥95%"),
        'False Positive Rate': (avg_fpr <= 0.01, f"{avg_fpr*100:.2f}%", "≤1%"),
        'Throughput': (avg_throughput >= 100, f"{avg_throughput:.0f} s/s", "≥100 s/s"),
        'Latency': (avg_latency <= 100, f"{avg_latency:.1f} ms", "≤100 ms"),
    }
    
    for metric, (passed, actual, target) in targets.items():
        status = "✓" if passed else "✗"
        print(f"   {status} {metric}: {actual} (Target: {target})")
    
    print("\n" + "="*70)
    print("  Benchmark Complete!")
    print("="*70 + "\n")
    
    # Save results
    output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    print(f"📄 Results saved to: {output_file}\n")
    
    return results


if __name__ == "__main__":
    run_comprehensive_benchmark()

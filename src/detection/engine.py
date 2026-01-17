"""
Anomaly Detection Engine - Coordinates multiple detection algorithms
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from .detectors import (
    StatisticalZScoreDetector,
    MovingAverageDetector,
    IsolationForestDetector,
    OneClassSVMDetector,
    AutoencoderDetector
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetectionEngine:
    """Main detection engine that coordinates multiple algorithms"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.detectors = {}
        self.feature_names = []
        self.sector = None
        
        # Initialize detectors based on config
        self._initialize_detectors()
        
    def _initialize_detectors(self):
        """Initialize detection algorithms"""
        detection_config = self.config.get('detection', {})
        algorithms = detection_config.get('algorithms', [])
        
        if not algorithms:
            # Default algorithms if none specified in config
            algorithms = [
                {'name': 'statistical_zscore', 'enabled': True},
                {'name': 'moving_average', 'enabled': True},
                {'name': 'isolation_forest', 'enabled': True}
            ]

        for algo in algorithms:
            if not algo.get('enabled', True):
                continue
                
            name = algo['name']
            
            if name == 'statistical_zscore':
                threshold = algo.get('threshold', 3.0)
                self.detectors['zscore'] = StatisticalZScoreDetector(threshold=threshold)
                
            elif name == 'moving_average':
                window_size = algo.get('window_size', 20)
                std_multiplier = algo.get('std_multiplier', 2.5)
                self.detectors['moving_avg'] = MovingAverageDetector(
                    window_size=window_size,
                    std_multiplier=std_multiplier
                )
                
            elif name == 'isolation_forest':
                contamination = algo.get('contamination', 0.1)
                self.detectors['isolation_forest'] = IsolationForestDetector(
                    contamination=contamination
                )
                
            elif name == 'lstm_autoencoder':
                sequence_length = algo.get('sequence_length', 50)
                threshold = algo.get('threshold', 0.8)
                self.detectors['autoencoder'] = AutoencoderDetector(
                    sequence_length=sequence_length,
                    threshold=threshold
                )
        
        logger.info(f"Initialized {len(self.detectors)} detectors: {list(self.detectors.keys())}")
    
    def prepare_features(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numeric features from data"""
        df = pd.DataFrame(data)
        
        # Store feature names on first call
        if not self.feature_names:
            # Select only numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude timestamp-related columns
            self.feature_names = [col for col in numeric_cols 
                                 if col not in ['timestamp', 'device_id']]
        
        # Extract features
        if not self.feature_names:
            raise ValueError("No numeric features found in data")
        
        # Add missing columns with default value of 0
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0
        
        features = df[self.feature_names].fillna(0).values
        return features
    
    def train(self, training_data: List[Dict[str, Any]], sector: str = None):
        """Train all detection algorithms"""
        logger.info(f"Training detection models on {len(training_data)} samples...")
        
        self.sector = sector
        features = self.prepare_features(training_data)
        
        for name, detector in self.detectors.items():
            try:
                logger.info(f"Training {name}...")
                detector.train(features)
                logger.info(f"{name} trained successfully")
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
        
        logger.info("All detectors trained")
    
    def detect(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in data using ensemble of algorithms
        Returns list of detection results with anomaly scores
        """
        features = self.prepare_features(data)
        
        results = []
        all_predictions = {}
        all_scores = {}
        
        # Run each detector
        for name, detector in self.detectors.items():
            if not detector.is_trained:
                logger.warning(f"{name} not trained, skipping")
                continue
                
            try:
                predictions, scores = detector.predict(features)
                all_predictions[name] = predictions
                all_scores[name] = scores
            except Exception as e:
                logger.error(f"Error in {name} prediction: {e}")
                all_predictions[name] = np.zeros(len(features))
                all_scores[name] = np.zeros(len(features))
        
        # Ensemble voting - majority vote
        if all_predictions:
            # Stack predictions
            pred_array = np.vstack(list(all_predictions.values()))
            score_array = np.vstack(list(all_scores.values()))
            
            # Majority vote (at least 50% of detectors agree)
            ensemble_predictions = (np.mean(pred_array, axis=0) >= 0.5).astype(int)
            
            # Average anomaly score
            ensemble_scores = np.mean(score_array, axis=0)
            
            # Normalize scores to 0-1 range
            # Normalize scores to 0-1 range
            score_range = ensemble_scores.max() - ensemble_scores.min()
            if score_range > 0:
                normalized_scores = (ensemble_scores - ensemble_scores.min()) / score_range
            else:
                # If all scores are the same, keep them as is or default to max
                normalized_scores = ensemble_scores if ensemble_scores.max() <= 1.0 else np.ones(len(ensemble_scores))
        else:
            ensemble_predictions = np.zeros(len(features))
            normalized_scores = np.zeros(len(features))
        
        # Create results
        for i, sample in enumerate(data):
            result = {
                'timestamp': sample.get('timestamp', datetime.utcnow().isoformat()),
                'device_id': sample.get('device_id', 'unknown'),
                'device_type': sample.get('device_type', 'unknown'),
                'sector': sample.get('sector', self.sector),
                'is_anomaly': bool(ensemble_predictions[i]),
                'anomaly_score': float(normalized_scores[i]),
                'detector_votes': {
                    name: int(all_predictions[name][i]) 
                    for name in all_predictions.keys()
                },
                'detector_scores': {
                    name: float(all_scores[name][i]) 
                    for name in all_scores.keys()
                },
                'raw_data': sample
            }
            
            # Determine severity based on score
            if result['anomaly_score'] >= 0.9:
                result['severity'] = 'P0'
            elif result['anomaly_score'] >= 0.75:
                result['severity'] = 'P1'
            elif result['anomaly_score'] >= 0.5:
                result['severity'] = 'P2'
            elif result['anomaly_score'] >= 0.3:
                result['severity'] = 'P3'
            else:
                result['severity'] = 'P4'
            
            results.append(result)
        
        return results
    
    def get_performance_metrics(self, true_labels: np.ndarray, predictions: np.ndarray) -> Dict[str, float]:
        """Calculate performance metrics"""
        from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
        
        metrics = {
            'precision': precision_score(true_labels, predictions, zero_division=0),
            'recall': recall_score(true_labels, predictions, zero_division=0),
            'f1_score': f1_score(true_labels, predictions, zero_division=0),
            'false_positive_rate': np.sum((predictions == 1) & (true_labels == 0)) / np.sum(true_labels == 0) if np.sum(true_labels == 0) > 0 else 0,
            'true_positive_rate': np.sum((predictions == 1) & (true_labels == 1)) / np.sum(true_labels == 1) if np.sum(true_labels == 1) > 0 else 0,
        }
        
        # ROC AUC only if we have both classes
        if len(np.unique(true_labels)) > 1:
            try:
                metrics['roc_auc'] = roc_auc_score(true_labels, predictions)
            except:
                metrics['roc_auc'] = 0.0
        else:
            metrics['roc_auc'] = 0.0
        
        return metrics
    
    def save_models(self, directory: str):
        """Save all trained models"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        for name, detector in self.detectors.items():
            if detector.is_trained:
                filepath = os.path.join(directory, f"{name}_model.pkl")
                detector.save_model(filepath)
                logger.info(f"Saved {name} model to {filepath}")
    
    def load_models(self, directory: str):
        """Load trained models"""
        import os
        
        for name, detector in self.detectors.items():
            filepath = os.path.join(directory, f"{name}_model.pkl")
            if os.path.exists(filepath):
                detector.load_model(filepath)
                logger.info(f"Loaded {name} model from {filepath}")

"""
Anomaly detection engine with multiple algorithms
"""
import numpy as np
from typing import Dict, List, Any, Tuple
from abc import ABC, abstractmethod
import joblib
import os


class BaseDetector(ABC):
    """Base class for anomaly detection algorithms"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_trained = False
        self.model = None
        
    @abstractmethod
    def train(self, data: np.ndarray) -> None:
        """Train the detection model"""
        pass
    
    @abstractmethod
    def predict(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies
        Returns: (predictions, scores)
            predictions: 1 for anomaly, 0 for normal
            scores: anomaly scores (higher = more anomalous)
        """
        pass
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({'model': self.model, 'is_trained': self.is_trained}, filepath)
        
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.is_trained = data['is_trained']


class StatisticalZScoreDetector(BaseDetector):
    """Statistical Z-Score based anomaly detection"""
    
    def __init__(self, threshold: float = 3.0):
        super().__init__("StatisticalZScore")
        self.threshold = threshold
        self.mean = None
        self.std = None
        
    def train(self, data: np.ndarray) -> None:
        """Calculate mean and standard deviation from training data"""
        self.mean = np.mean(data, axis=0)
        self.std = np.std(data, axis=0)
        # Avoid division by zero
        self.std = np.where(self.std == 0, 1, self.std)
        self.is_trained = True
        self.model = {'mean': self.mean, 'std': self.std}
        
    def predict(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies using z-score"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        z_scores = np.abs((data - self.mean) / self.std)
        # Max z-score across all features
        max_z_scores = np.max(z_scores, axis=1)
        predictions = (max_z_scores > self.threshold).astype(int)
        
        return predictions, max_z_scores


class MovingAverageDetector(BaseDetector):
    """Moving average with standard deviation for time series"""
    
    def __init__(self, window_size: int = 20, std_multiplier: float = 2.5):
        super().__init__("MovingAverage")
        self.window_size = window_size
        self.std_multiplier = std_multiplier
        self.history = []
        
    def train(self, data: np.ndarray) -> None:
        """Initialize with historical data"""
        self.history = list(data)
        self.is_trained = True
        self.model = {'window_size': self.window_size, 'std_multiplier': self.std_multiplier}
        
    def predict(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies using moving average"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = []
        scores = []
        
        for point in data:
            if len(self.history) < self.window_size:
                # Not enough history, assume normal
                predictions.append(0)
                scores.append(0.0)
                self.history.append(point)
                continue
            
            # Calculate moving statistics
            recent_data = np.array(self.history[-self.window_size:])
            mean = np.mean(recent_data, axis=0)
            std = np.std(recent_data, axis=0)
            std = np.where(std == 0, 1, std)
            
            # Calculate deviation
            deviation = np.abs((point - mean) / std)
            max_deviation = np.max(deviation)
            
            is_anomaly = max_deviation > self.std_multiplier
            predictions.append(int(is_anomaly))
            scores.append(max_deviation)
            
            # Update history
            self.history.append(point)
            if len(self.history) > self.window_size * 10:  # Keep limited history
                self.history = self.history[-self.window_size * 5:]
        
        return np.array(predictions), np.array(scores)


class IsolationForestDetector(BaseDetector):
    """Isolation Forest for anomaly detection"""
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100):
        super().__init__("IsolationForest")
        self.contamination = contamination
        self.n_estimators = n_estimators
        
    def train(self, data: np.ndarray) -> None:
        """Train Isolation Forest model"""
        from sklearn.ensemble import IsolationForest
        
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(data)
        self.is_trained = True
        
    def predict(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies using Isolation Forest"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Predict returns -1 for anomalies, 1 for normal
        predictions = self.model.predict(data)
        # Convert to 1 for anomaly, 0 for normal
        predictions = np.where(predictions == -1, 1, 0)
        
        # Get anomaly scores (lower = more anomalous)
        scores = -self.model.score_samples(data)
        
        return predictions, scores


class OneClassSVMDetector(BaseDetector):
    """One-Class SVM for anomaly detection"""
    
    def __init__(self, nu: float = 0.1, kernel: str = 'rbf'):
        super().__init__("OneClassSVM")
        self.nu = nu
        self.kernel = kernel
        
    def train(self, data: np.ndarray) -> None:
        """Train One-Class SVM model"""
        from sklearn.svm import OneClassSVM
        from sklearn.preprocessing import StandardScaler
        
        self.scaler = StandardScaler()
        scaled_data = self.scaler.fit_transform(data)
        
        self.model = OneClassSVM(nu=self.nu, kernel=self.kernel, gamma='auto')
        self.model.fit(scaled_data)
        self.is_trained = True
        
    def predict(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies using One-Class SVM"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        scaled_data = self.scaler.transform(data)
        
        # Predict returns -1 for anomalies, 1 for normal
        predictions = self.model.predict(scaled_data)
        predictions = np.where(predictions == -1, 1, 0)
        
        # Get decision scores (lower = more anomalous)
        scores = -self.model.decision_function(scaled_data)
        
        return predictions, scores


class AutoencoderDetector(BaseDetector):
    """LSTM Autoencoder for time series anomaly detection"""
    
    def __init__(self, sequence_length: int = 50, threshold: float = 0.8):
        super().__init__("LSTMAutoencoder")
        self.sequence_length = sequence_length
        self.threshold = threshold
        self.scaler = None
        
    def train(self, data: np.ndarray, epochs: int = 50, batch_size: int = 32) -> None:
        """Train LSTM Autoencoder"""
        import tensorflow as tf
        from tensorflow import keras
        from sklearn.preprocessing import StandardScaler
        
        # Scale data
        self.scaler = StandardScaler()
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        sequences = self._create_sequences(scaled_data)
        
        if len(sequences) < 10:
            raise ValueError(f"Not enough data to create sequences. Need at least {self.sequence_length} samples.")
        
        # Build model
        input_dim = data.shape[1]
        
        self.model = keras.Sequential([
            keras.layers.LSTM(64, activation='relu', input_shape=(self.sequence_length, input_dim), 
                            return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32, activation='relu', return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.RepeatVector(self.sequence_length),
            keras.layers.LSTM(32, activation='relu', return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(64, activation='relu', return_sequences=True),
            keras.layers.TimeDistributed(keras.layers.Dense(input_dim))
        ])
        
        self.model.compile(optimizer='adam', loss='mse')
        
        # Train
        self.model.fit(
            sequences, sequences,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            verbose=0
        )
        
        # Calculate threshold based on training data
        train_predictions = self.model.predict(sequences, verbose=0)
        train_mse = np.mean(np.power(sequences - train_predictions, 2), axis=(1, 2))
        self.threshold = np.percentile(train_mse, 95)  # 95th percentile
        
        self.is_trained = True
        
    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for LSTM"""
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:i + self.sequence_length])
        return np.array(sequences)
    
    def predict(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies using Autoencoder"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        scaled_data = self.scaler.transform(data)
        
        # Create sequences
        sequences = self._create_sequences(scaled_data)
        
        if len(sequences) == 0:
            return np.zeros(len(data), dtype=int), np.zeros(len(data))
        
        # Reconstruct
        reconstructions = self.model.predict(sequences, verbose=0)
        
        # Calculate reconstruction error
        mse = np.mean(np.power(sequences - reconstructions, 2), axis=(1, 2))
        
        # Pad scores for points that weren't in sequences
        all_scores = np.zeros(len(data))
        all_scores[-len(mse):] = mse
        
        predictions = (all_scores > self.threshold).astype(int)
        
        return predictions, all_scores

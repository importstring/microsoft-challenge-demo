"""
Anomaly detection module for query processing.
Uses Isolation Forest to detect anomalous queries.
"""

from pyod.models.iforest import IForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import time

class MultiModalAnomalyDetector:
    def __init__(self, config=None):
        self.config = config or {}
        self.contamination = self.config.get('contamination', 0.1)
        self.n_estimators = self.config.get('n_estimators', 100)
        self.detector = IForest(
            contamination=self.contamination, 
            n_estimators=self.n_estimators
        )
        self.fitted = False
        self.scaler = StandardScaler()
        self.detection_history = []
        
    def preprocess_features(self, features_list):
        """Standardize numerical features for better anomaly detection"""
        if not features_list:
            return np.array([])
            
        # Ensure all features are numerical arrays
        numerical_features = []
        for features in features_list:
            if isinstance(features, dict):
                # If features is a dictionary, convert to array
                numerical_features.append([
                    features.get('length', 0),
                    features.get('word_count', 0),
                    features.get('avg_word_length', 0),
                    features.get('special_char_ratio', 0)
                ])
            elif isinstance(features, (list, np.ndarray)):
                numerical_features.append(features)
                
        # Standardize features
        return self.scaler.fit_transform(np.array(numerical_features))
        
    def fit(self, features_list):
        """Train the anomaly detector on historical queries"""
        if len(features_list) < 10:
            # Need minimum data to fit
            self.fitted = False
            return self
            
        preprocessed_features = self.preprocess_features(features_list)
        if len(preprocessed_features) > 0:
            self.detector.fit(preprocessed_features)
            self.fitted = True
            
        return self
        
    def score_anomaly(self, features):
        """Score a query for anomalousness"""
        if not self.fitted:
            # Not enough data to detect anomalies properly
            return 0.0
            
        # Handle both dictionary and array features
        if isinstance(features, dict):
            numerical_features = [
                features.get('length', 0),
                features.get('word_count', 0),
                features.get('avg_word_length', 0),
                features.get('special_char_ratio', 0)
            ]
            # Add TF-IDF features if available
            if 'tfidf' in features and isinstance(features['tfidf'], np.ndarray):
                numerical_features.extend(features['tfidf'])
        else:
            numerical_features = features
            
        # Preprocess single example
        preprocessed = self.scaler.transform([numerical_features])[0].reshape(1, -1)
        
        # Score and record the detection
        score = self.detector.decision_function(preprocessed)[0]
        
        # Record detection for analysis
        self.detection_history.append({
            'timestamp': time.time(),
            'features': numerical_features,
            'score': score
        })
        
        return score 
"""
Feature extraction module for query processing.
Extracts semantic and statistical features from queries.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class FeatureExtractor:
    def __init__(self, config=None):
        self.config = config or {}
        self.max_features = self.config.get('max_features', 50)
        self.stop_words = self.config.get('stop_words', 'english')
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words=self.stop_words
        )
        self._fitted = False
        
    def fit(self, queries):
        """Fit vectorizer on a corpus of queries"""
        self.vectorizer.fit(queries)
        self._fitted = True
        return self
        
    def transform(self, query):
        """Extract features from a single query"""
        features = {}
        
        # Basic features
        features['length'] = len(query)
        features['word_count'] = len(query.split())
        features['avg_word_length'] = sum(len(word) for word in query.split()) / max(1, features['word_count'])
        features['special_char_ratio'] = sum(not c.isalnum() for c in query) / max(1, len(query))
        
        # Semantic features - fit on first transform if not already fitted
        if not self._fitted and hasattr(self, 'vectorizer'):
            self.fit([query])
            
        if hasattr(self, 'vectorizer') and self._fitted:
            features['tfidf'] = self.vectorizer.transform([query]).toarray()[0]
        
        return features
    
    def extract_numerical_features(self, features_dict):
        """Convert feature dictionary to numerical array for anomaly detection"""
        numerical_features = [
            features_dict.get('length', 0),
            features_dict.get('word_count', 0),
            features_dict.get('avg_word_length', 0),
            features_dict.get('special_char_ratio', 0)
        ]
        
        # Add TF-IDF features if available
        if 'tfidf' in features_dict and isinstance(features_dict['tfidf'], np.ndarray):
            numerical_features.extend(features_dict['tfidf'])
            
        return np.array(numerical_features) 
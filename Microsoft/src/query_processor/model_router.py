"""
Model router module for query processing.
Selects the appropriate model based on query features and system metrics.
"""

import time

class SmartModelRouter:
    def __init__(self, model_config=None):
        self.model_config = model_config or {
            'simple': {'model': 'mistral', 'threshold': 0.3, 'min_complexity': 0, 'resource_intensity': 1},
            'technical': {'model': 'llama2', 'threshold': 0.5, 'min_complexity': 10, 'resource_intensity': 3},
            'analytical': {'model': 'codeqwen', 'threshold': 0.6, 'min_complexity': 15, 'resource_intensity': 5}
        }
        self.default_model = 'mistral'
        self.routing_history = []
        
    def select_model(self, query_features, system_metrics=None):
        """
        Select the most appropriate model for a query based on features and system metrics.
        
        Args:
            query_features: Dictionary containing query features
            system_metrics: Optional dict with system metrics like current_load
            
        Returns:
            model_name: String identifier of the selected model
        """
        scores = {}
        
        # Calculate scores for each model
        for model_name, model_config in self.model_config.items():
            scores[model_name] = 0
            
            # Score based on complexity requirements
            if query_features.get('word_count', 0) >= model_config.get('min_complexity', 0):
                scores[model_name] += 1
                
            # Score based on anomaly threshold
            anomaly_score = query_features.get('anomaly_score', 0)
            if anomaly_score >= model_config.get('threshold', 0):
                scores[model_name] += 2
                
            # Consider system load if available
            if system_metrics and 'current_load' in system_metrics:
                load_penalty = model_config.get('resource_intensity', 1) * system_metrics['current_load']
                if load_penalty > 0.8:  # High load situation
                    scores[model_name] -= 3  # Penalize resource-intensive models under load
        
        # Select highest scoring model or fall back to default
        if scores:
            selected_model = max(scores.items(), key=lambda x: x[1])[0]
        else:
            selected_model = self.default_model
        
        # Get actual model name from config
        model_name = self.model_config[selected_model].get('model', selected_model)
        
        # Record selection for analysis
        self.routing_history.append({
            'features': query_features,
            'selected_model': selected_model,
            'scores': scores,
            'timestamp': time.time()
        })
        
        return model_name
        
    def get_routing_stats(self):
        """Return statistics about routing decisions"""
        if not self.routing_history:
            return {}
            
        # Calculate model distribution
        model_counts = {}
        for record in self.routing_history:
            model = record['selected_model']
            if model not in model_counts:
                model_counts[model] = 0
            model_counts[model] += 1
            
        total = len(self.routing_history)
        model_distribution = {model: count/total for model, count in model_counts.items()}
        
        return {
            'total_decisions': total,
            'model_distribution': model_distribution,
            'latest_timestamp': self.routing_history[-1]['timestamp'] if self.routing_history else None
        } 
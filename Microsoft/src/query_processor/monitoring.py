"""
Monitoring module for query processing system.
Tracks performance metrics and system health.
"""

import time
from collections import deque
import threading
import numpy as np
import psutil

class PerformanceMonitor:
    def __init__(self, window_size=100):
        """
        Initialize the performance monitor.
        
        Args:
            window_size: Size of sliding window for metrics (default: 100)
        """
        self.metrics = {
            'response_times': deque(maxlen=window_size),
            'model_usage': {},
            'error_count': 0,
            'total_queries': 0,
            'start_time': time.time(),
            'system_metrics': []
        }
        self.lock = threading.Lock()
        self.monitoring_thread = None
        self.monitoring_active = False
        
    def record_query(self, model_name, response_time, success=True):
        """
        Record metrics for a processed query.
        
        Args:
            model_name: Name of the model used
            response_time: Processing time in seconds
            success: Whether the query was processed successfully
        """
        with self.lock:
            self.metrics['total_queries'] += 1
            self.metrics['response_times'].append(response_time)
            
            # Update model usage counts
            if model_name not in self.metrics['model_usage']:
                self.metrics['model_usage'][model_name] = 0
            self.metrics['model_usage'][model_name] += 1
            
            if not success:
                self.metrics['error_count'] += 1
    
    def get_system_metrics(self):
        """Get current system resource metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': time.time()
        }
        
    def start_monitoring(self, interval=60):
        """
        Start background monitoring thread.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
            
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    metrics = self.get_system_metrics()
                    with self.lock:
                        self.metrics['system_metrics'].append(metrics)
                        
                        # Trim system metrics if too many
                        if len(self.metrics['system_metrics']) > 1000:
                            self.metrics['system_metrics'] = self.metrics['system_metrics'][-1000:]
                            
                except Exception as e:
                    print(f"Error monitoring system metrics: {e}")
                    
                time.sleep(interval)
                
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Stop background monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
    
    def get_summary_stats(self):
        """
        Return summary performance statistics.
        
        Returns:
            Dictionary of performance metrics
        """
        with self.lock:
            uptime_seconds = time.time() - self.metrics['start_time']
            response_times = list(self.metrics['response_times'])
            
            # Calculate model distribution
            model_distribution = {}
            total_queries = self.metrics['total_queries']
            if total_queries > 0:
                for model, count in self.metrics['model_usage'].items():
                    model_distribution[model] = count / total_queries
            
            # Calculate system metrics averages if available
            system_avg = {}
            if self.metrics['system_metrics']:
                metrics_keys = [k for k in self.metrics['system_metrics'][0].keys() if k != 'timestamp']
                for key in metrics_keys:
                    values = [m[key] for m in self.metrics['system_metrics']]
                    system_avg[key] = np.mean(values)
            
            stats = {
                'total_queries': total_queries,
                'queries_per_minute': (total_queries / uptime_seconds) * 60 if uptime_seconds > 0 else 0,
                'error_rate': self.metrics['error_count'] / max(1, total_queries),
                'model_distribution': model_distribution,
                'response_time': {
                    'mean': np.mean(response_times) if response_times else 0,
                    'median': np.median(response_times) if response_times else 0,
                    'p95': np.percentile(response_times, 95) if response_times else 0,
                    'min': min(response_times) if response_times else 0,
                    'max': max(response_times) if response_times else 0
                },
                'uptime_hours': uptime_seconds / 3600,
                'system_metrics': system_avg
            }
            
            return stats 
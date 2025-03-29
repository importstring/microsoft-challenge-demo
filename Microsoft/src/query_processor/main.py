"""
Main module for Microsoft Advanced Query Processor.
Provides the QueryProcessor class and CLI interface.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import ollama
import time
import argparse
import os
import json
import signal
import sys
from datetime import datetime

# Import our modules
from .feature_extraction import FeatureExtractor
from .anomaly_detection import MultiModalAnomalyDetector
from .model_router import SmartModelRouter
from .logging_utils import QueryLogger
from .cache import QueryCache
from .monitoring import PerformanceMonitor

# Optional Azure integration
try:
    from .azure_integration import (
        AzureStorageManager, 
        AzureAnomalyDetection, 
        AzureLogAnalytics, 
        AZURE_AVAILABLE
    )
except ImportError:
    AZURE_AVAILABLE = False

class QueryProcessor:
    def __init__(self, config_path=None):
        """
        Initialize the query processor.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.console = Console()
        self.feature_extractor = FeatureExtractor(self.config.get('feature_extraction', {}))
        self.anomaly_detector = MultiModalAnomalyDetector(self.config.get('anomaly_detection', {}))
        self.model_router = SmartModelRouter(
            self.config.get('models', {
                'simple': {'model': 'mistral', 'threshold': 0.3, 'min_complexity': 0, 'resource_intensity': 1},
                'technical': {'model': 'llama2', 'threshold': 0.5, 'min_complexity': 10, 'resource_intensity': 3},
                'analytical': {'model': 'codeqwen', 'threshold': 0.6, 'min_complexity': 15, 'resource_intensity': 5}
            })
        )
        
        # Support services
        log_dir = self.config.get('logging', {}).get('directory', './logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"query_processor_{datetime.now().strftime('%Y%m%d')}.log")
        
        self.logger = QueryLogger(log_file=log_file)
        self.cache = QueryCache(
            cache_dir=self.config.get('cache', {}).get('directory', './cache'),
            ttl_hours=self.config.get('cache', {}).get('ttl_hours', 24)
        )
        self.monitor = PerformanceMonitor()
        
        # Start monitoring
        self.monitor.start_monitoring(interval=self.config.get('monitoring', {}).get('interval', 60))
        
        # Log startup
        self.logger.log_system_event('startup', 'Query processor initialized', 
                                     {'config': self.config, 'azure_available': AZURE_AVAILABLE})
        
        # Query history for anomaly detection
        self.query_history = []
        
        # Optional Azure integration
        self.azure_enabled = False
        if AZURE_AVAILABLE and self.config.get('azure', {}).get('enabled', False):
            try:
                self.azure_storage = AzureStorageManager(
                    self.config.get('azure', {}).get('storage_connection_string')
                )
                self.azure_anomaly = AzureAnomalyDetection(
                    self.config.get('azure', {}).get('anomaly_endpoint'),
                    self.config.get('azure', {}).get('anomaly_key')
                )
                self.azure_logs = AzureLogAnalytics(
                    self.config.get('azure', {}).get('log_analytics_workspace_id')
                )
                self.azure_enabled = True
                self.logger.log_system_event('info', 'Azure integration enabled')
            except Exception as e:
                self.logger.log_system_event('error', 'Azure integration failed', {'error': str(e)})
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        self.console.print("\n[yellow]Shutting down gracefully...[/]")
        self.shutdown()
        sys.exit(0)
        
    def shutdown(self):
        """Clean shutdown of the processor"""
        self.monitor.stop_monitoring()
        self.logger.log_system_event('shutdown', 'Query processor shutting down', 
                                    {'stats': self.monitor.get_summary_stats()})
        
    def _load_config(self, config_path):
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'feature_extraction': {
                'max_features': 50,
                'stop_words': 'english'
            },
            'anomaly_detection': {
                'contamination': 0.1,
                'n_estimators': 100
            },
            'models': {
                'simple': {'model': 'mistral', 'threshold': 0.3, 'min_complexity': 0, 'resource_intensity': 1},
                'technical': {'model': 'llama2', 'threshold': 0.5, 'min_complexity': 10, 'resource_intensity': 3},
                'analytical': {'model': 'codeqwen', 'threshold': 0.6, 'min_complexity': 15, 'resource_intensity': 5}
            },
            'logging': {
                'directory': './logs',
                'level': 'INFO'
            },
            'cache': {
                'directory': './cache',
                'ttl_hours': 24
            },
            'monitoring': {
                'interval': 60
            },
            'azure': {
                'enabled': False
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            return default_config
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Merge with defaults to ensure all keys exist
            for section in default_config:
                if section not in config:
                    config[section] = default_config[section]
                elif isinstance(default_config[section], dict):
                    for key in default_config[section]:
                        if key not in config[section]:
                            config[section][key] = default_config[section][key]
                            
            return config
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to load config: {str(e)}. Using defaults.[/]")
            return default_config
            
    def process_query(self, query):
        """
        Process a single query through the pipeline.
        
        Args:
            query: The query string
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        error = None
        response = None
        selected_model = None
        is_cached = False
        
        try:
            # Extract features
            features = self.feature_extractor.transform(query)
            
            # Store for anomaly detection
            self.query_history.append(features)
            
            # Detect anomalies if enough history
            if len(self.query_history) >= 20:
                self.anomaly_detector.fit(self.query_history[-100:])
                
            anomaly_score = self.anomaly_detector.score_anomaly(features)
            features['anomaly_score'] = anomaly_score
            
            # Select appropriate model
            selected_model = self.model_router.select_model(features)
            
            # Check cache first
            cached_response = self.cache.get(query, selected_model)
            if cached_response:
                response = cached_response
                is_cached = True
            else:
                # Generate response with the selected model
                ollama_response = ollama.generate(model=selected_model, prompt=query)
                response = ollama_response['response']
                
                # Cache the response
                self.cache.set(query, selected_model, response)
                
            # Azure integration if enabled
            if self.azure_enabled and not is_cached:
                # Upload model to Azure if it was new
                if hasattr(self, 'azure_storage') and hasattr(self.anomaly_detector, 'detector'):
                    model_name = f"anomaly_detector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                    try:
                        self.azure_storage.save_model(
                            self.anomaly_detector.detector, 
                            "query-processor-models", 
                            model_name
                        )
                    except Exception as e:
                        self.logger.log_system_event('error', 'Failed to save model to Azure', {'error': str(e)})
                
        except Exception as e:
            error = e
            response = f"Error processing query: {str(e)}"
            
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        # Log the query
        self.logger.log_query(query, features, selected_model, processing_time, error)
        
        # Send logs to Azure if enabled
        if self.azure_enabled and hasattr(self, 'azure_logs'):
            try:
                log_entry = {
                    'QueryText': query[:100],
                    'SelectedModel': selected_model,
                    'ResponseTime': processing_time,
                    'AnomalyScore': features.get('anomaly_score', 0),
                    'IsError': error is not None,
                    'IsCached': is_cached
                }
                self.azure_logs.send_logs([log_entry])
            except Exception as e:
                self.logger.log_system_event('error', 'Failed to send logs to Azure', {'error': str(e)})
        
        # Update performance metrics
        self.monitor.record_query(selected_model, processing_time, error is None)
        
        # Return results
        return {
            'query': query,
            'features': features,
            'selected_model': selected_model,
            'response': response,
            'processing_time': processing_time,
            'is_cached': is_cached,
            'error': str(error) if error else None
        }
        
    def display_results(self, results):
        """
        Display processing results in a rich table.
        
        Args:
            results: Dictionary with processing results
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value")
        
        # Add rows for metrics
        table.add_row("Query", results['query'][:50] + "..." if len(results['query']) > 50 else results['query'])
        table.add_row("Complexity", f"{results['features'].get('word_count', 0)}")
        table.add_row("Anomaly Score", f"{results['features'].get('anomaly_score', 0):.4f}")
        table.add_row("Selected Model", results['selected_model'])
        table.add_row("Response Time", f"{results['processing_time']:.2f}s")
        table.add_row("Cached", "Yes" if results.get('is_cached', False) else "No")
        
        # Add abbreviated response
        response_text = results['response']
        if len(response_text) > 100:
            response_text = response_text[:100] + "..."
        table.add_row("Response", response_text)
        
        self.console.print(Panel(table, title="Processing Results"))
        
    def display_system_stats(self):
        """Display system performance statistics"""
        stats = self.monitor.get_summary_stats()
        
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Metric", style="cyan")
        table.add_column("Value")
        
        table.add_row("Total Queries", f"{stats['total_queries']}")
        table.add_row("Queries/Minute", f"{stats['queries_per_minute']:.2f}")
        table.add_row("Error Rate", f"{stats['error_rate']:.2%}")
        table.add_row("Avg Response Time", f"{stats['response_time']['mean']:.2f}s")
        table.add_row("P95 Response Time", f"{stats['response_time']['p95']:.2f}s")
        
        # Model distribution
        model_dist = []
        for model, pct in stats.get('model_distribution', {}).items():
            model_dist.append(f"{model}: {pct:.1%}")
        table.add_row("Model Distribution", ", ".join(model_dist) if model_dist else "N/A")
        
        # System metrics if available
        if stats.get('system_metrics'):
            for metric, value in stats['system_metrics'].items():
                table.add_row(f"System {metric.replace('_', ' ').title()}", f"{value:.1f}%")
        
        # Cache stats
        cache_stats = self.cache.get_stats()
        if cache_stats['total_requests'] > 0:
            table.add_row("Cache Hit Rate", f"{cache_stats['hit_rate']:.1%}")
        
        self.console.print(Panel(table, title="System Performance"))
        
    def interactive_mode(self):
        """Run in interactive console mode"""
        self.console.print(Panel("[bold cyan]Microsoft Advanced Query Processor[/]\nProduction-Ready Version", width=80))
        
        if self.azure_enabled:
            self.console.print("[green]✅ Azure integration enabled[/]")
        
        while True:
            try:
                query = self.console.input("\n[bright_white]Enter query (q to exit, stats for system stats): [/]")
                
                if query.lower() == 'q':
                    break
                    
                if query.lower() == 'stats':
                    self.display_system_stats()
                    continue
                    
                results = self.process_query(query)
                self.display_results(results)
                
                # Print full response to console
                self.console.print("\n[bold green]Response:[/]")
                self.console.print(results['response'])
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Session terminated by user.[/]")
                break
                
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/]")
                
        self.shutdown()
        self.console.print("[green]Session ended. Thank you for using Microsoft Advanced Query Processor![/]")

def main():
    """Command-line interface for the query processor"""
    parser = argparse.ArgumentParser(description="Microsoft Advanced Query Processor")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--query", help="Single query to process")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--azure", action="store_true", help="Enable Azure integration")
    
    args = parser.parse_args()
    
    # Create configuration with CLI overrides
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                
            # Override Azure setting if specified
            if args.azure and 'azure' in config:
                config['azure']['enabled'] = True
                
        except Exception as e:
            print(f"Error loading config: {e}")
            config = None
    
    processor = QueryProcessor(config_path=args.config)
    
    if args.query:
        results = processor.process_query(args.query)
        processor.display_results(results)
        print("\nResponse:")
        print(results['response'])
    else:
        processor.interactive_mode()

if __name__ == "__main__":
    main() 
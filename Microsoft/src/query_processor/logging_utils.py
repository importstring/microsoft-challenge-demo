"""
Logging utilities for query processing.
Provides comprehensive logging of query processing events.
"""

import logging
import json
import os
from datetime import datetime

class QueryLogger:
    def __init__(self, log_file=None, log_level=logging.INFO):
        """
        Initialize the query logger.
        
        Args:
            log_file: Path to log file (optional)
            log_level: Logging level (default: INFO)
        """
        # Create logger
        self.logger = logging.getLogger("query_processor")
        self.logger.setLevel(log_level)
        
        # Create formatters
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if log_file provided
        if log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_query(self, query, features, selected_model, response_time, error=None):
        """
        Log query processing details.
        
        Args:
            query: The query string
            features: Dictionary of extracted features
            selected_model: Name of the selected model
            response_time: Processing time in seconds
            error: Error message if any occurred
        
        Returns:
            Dictionary of log data
        """
        # Create log data dictionary
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'query': query[:100],  # Truncate for privacy
            'query_length': len(query),
            'word_count': features.get('word_count', 0),
            'selected_model': selected_model,
            'response_time_ms': int(response_time * 1000),
            'anomaly_score': features.get('anomaly_score', 0),
            'error': str(error) if error else None
        }
        
        # Log appropriate message
        if error:
            self.logger.error(f"Query processing error: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Query processed: {json.dumps(log_data)}")
        
        return log_data
        
    def log_system_event(self, event_type, message, data=None):
        """
        Log system-level events.
        
        Args:
            event_type: Type of event (startup, shutdown, error, etc.)
            message: Event message
            data: Additional event data (optional)
            
        Returns:
            Dictionary of log data
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'data': data
        }
        
        if event_type == 'error':
            self.logger.error(f"System event: {json.dumps(log_data)}")
        else:
            self.logger.info(f"System event: {json.dumps(log_data)}")
            
        return log_data 
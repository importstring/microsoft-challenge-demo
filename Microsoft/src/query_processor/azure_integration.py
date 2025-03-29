"""
Azure integration module for query processing system.
Provides integration with Azure services for storage, anomaly detection, and monitoring.
"""

import os
import pickle
import json
import time
from datetime import datetime
import logging

# Optional dependencies - these will be imported only if available
try:
    from azure.storage.blob import BlobServiceClient
    from azure.ai.anomalydetector import AnomalyDetectorClient
    from azure.core.credentials import AzureKeyCredential
    from azure.monitor.ingestion import LogsIngestionClient
    from azure.monitor.ingestion import LogsIngestionClientAuthenticationPolicy
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    
logger = logging.getLogger("query_processor.azure")

class AzureStorageManager:
    def __init__(self, connection_string=None):
        """
        Initialize Azure Blob Storage manager.
        
        Args:
            connection_string: Azure Storage connection string (optional)
        """
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK packages are not installed. Please install them with: "
                            "pip install azure-storage-blob azure-ai-anomalydetector azure-identity")
            
        self.connection_string = connection_string or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("Azure storage connection string not provided and AZURE_STORAGE_CONNECTION_STRING environment variable not set")
            
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        
    def save_model(self, model, container_name, blob_name):
        """
        Save a model to Azure Blob Storage.
        
        Args:
            model: The model object to save
            container_name: Azure Storage container name
            blob_name: Name for the blob 
            
        Returns:
            URL of the saved model blob
        """
        container_client = self.blob_service_client.get_container_client(container_name)
        
        # Create container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()
            
        # Serialize the model
        model_blob = pickle.dumps(model)
        
        # Upload to blob storage
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(model_blob, overwrite=True)
        
        return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        
    def load_model(self, container_name, blob_name):
        """
        Load a model from Azure Blob Storage.
        
        Args:
            container_name: Azure Storage container name
            blob_name: Name of the blob
            
        Returns:
            The loaded model object
        """
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        try:
            model_blob = blob_client.download_blob().readall()
            model = pickle.loads(model_blob)
            return model
        except Exception as e:
            logger.error(f"Error loading model from Azure: {str(e)}")
            raise
            
    def list_models(self, container_name, prefix=None):
        """
        List available models in storage.
        
        Args:
            container_name: Azure Storage container name
            prefix: Optional prefix filter
            
        Returns:
            List of model blob names
        """
        container_client = self.blob_service_client.get_container_client(container_name)
        
        try:
            blobs = container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Error listing models in Azure: {str(e)}")
            return []


class AzureAnomalyDetection:
    def __init__(self, endpoint=None, key=None):
        """
        Initialize Azure Anomaly Detector client.
        
        Args:
            endpoint: Azure Anomaly Detector endpoint URL (optional)
            key: Azure Anomaly Detector API key (optional)
        """
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK packages are not installed. Please install them with: "
                            "pip install azure-storage-blob azure-ai-anomalydetector azure-identity")
            
        self.endpoint = endpoint or os.environ.get("ANOMALY_DETECTOR_ENDPOINT")
        self.key = key or os.environ.get("ANOMALY_DETECTOR_KEY")
        
        if not (self.endpoint and self.key):
            raise ValueError("Azure Anomaly Detector credentials not provided and environment variables not set")
            
        self.client = AnomalyDetectorClient(AzureKeyCredential(self.key), self.endpoint)
        
    def detect_anomalies(self, time_series_data):
        """
        Use Azure Anomaly Detector to find anomalies in query patterns.
        
        Args:
            time_series_data: List of dicts with timestamp and value keys
            
        Returns:
            Dictionary with anomaly detection results
        """
        if not time_series_data or len(time_series_data) < 12:
            logger.warning("Insufficient data for Azure anomaly detection (minimum 12 points required)")
            return {"is_anomaly": False, "error": "Insufficient data"}
            
        # Format data for Azure API
        request_data = {
            "series": [{"timestamp": item["timestamp"], "value": item["value"]} for item in time_series_data],
            "granularity": "minutely"
        }
        
        try:
            response = self.client.detect_entire_series(request_data)
            
            return {
                "is_anomaly": response.is_anomaly,
                "expected_values": response.expected_values,
                "upper_bounds": response.upper_bounds,
                "lower_bounds": response.lower_bounds
            }
        except Exception as e:
            logger.error(f"Error in Azure anomaly detection: {str(e)}")
            return {"error": str(e)}


class AzureLogAnalytics:
    def __init__(self, log_analytics_workspace_id=None, log_type="QueryProcessorLogs"):
        """
        Initialize Azure Log Analytics integration.
        
        Args:
            log_analytics_workspace_id: Log Analytics workspace ID (optional)
            log_type: Custom log type name
        """
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK packages are not installed. Please install them with: "
                            "pip install azure-storage-blob azure-ai-anomalydetector azure-identity azure-monitor-ingestion")
                            
        self.log_analytics_workspace_id = log_analytics_workspace_id or os.environ.get("LOG_ANALYTICS_WORKSPACE_ID")
        if not self.log_analytics_workspace_id:
            raise ValueError("Log Analytics workspace ID not provided and environment variable not set")
            
        self.log_type = log_type
        self.credential = DefaultAzureCredential()
        self.logs_client = LogsIngestionClient(
            endpoint=f"https://{self.log_analytics_workspace_id}.ods.opinsights.azure.com",
            credential=self.credential,
            authentication_policy=LogsIngestionClientAuthenticationPolicy(credential=self.credential)
        )
        
    def send_logs(self, logs_data):
        """
        Send logs to Azure Log Analytics.
        
        Args:
            logs_data: List of log entry dictionaries
            
        Returns:
            Boolean indicating success
        """
        if not logs_data:
            return False
            
        # Add timestamp if not present
        for entry in logs_data:
            if "TimeGenerated" not in entry:
                entry["TimeGenerated"] = datetime.utcnow().isoformat()
                
        try:
            self.logs_client.upload(
                rule_id=f"{self.log_analytics_workspace_id}/queryprocessor",
                stream_name=self.log_type,
                logs=logs_data
            )
            return True
        except Exception as e:
            logger.error(f"Error sending logs to Azure: {str(e)}")
            return False 
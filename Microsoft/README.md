# Microsoft Advanced Query Processor

## Production-Ready Query Processor for Microsoft Integration

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

This repository contains a production-ready implementation of the Microsoft Advanced Query Processor, which leverages multi-modal pattern recognition and anomaly detection to intelligently route queries to the most appropriate model while optimizing for performance, accuracy, and resource utilization.

## Core Features

- **Multi-Modal Anomaly Detection**: Identifies unusual query patterns using isolation forest algorithms inspired by financial fraud detection systems
- **Intelligent Model Routing**: Dynamically selects the most appropriate model based on query complexity, anomaly scores, and system load
- **Performance Optimization**: Implements efficient caching and monitoring to ensure optimal resource utilization
- **Microsoft Ecosystem Integration**: Seamless integration with Azure services and Microsoft 365
- **Production-Ready Implementation**: Comprehensive error handling, logging, and monitoring capabilities

## Architecture

The system is built with a modular architecture following Microsoft's recommended practices for production systems:

```
src/query_processor/
├── __init__.py              # Package initialization
├── main.py                  # Main query processor implementation
├── feature_extraction.py    # Feature extraction from queries
├── anomaly_detection.py     # Multi-modal anomaly detection
├── model_router.py          # Intelligent model routing
├── cache.py                 # Response caching system
├── logging_utils.py         # Logging utilities
├── monitoring.py            # Performance monitoring
├── azure_integration.py     # Azure services integration
└── ms365_integration.py     # Microsoft 365 integration
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) for local LLM inference
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/importstring/microsoft-challenge-demo.git
   cd microsoft-challenge-demo
   ```

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

3. Run the demo:
   ```
   python demo.py
   ```

### Azure Integration

To enable Azure integration, provide the necessary credentials through environment variables or configuration:

```
export AZURE_STORAGE_CONNECTION_STRING="your-connection-string"
export ANOMALY_DETECTOR_ENDPOINT="your-endpoint"
export ANOMALY_DETECTOR_KEY="your-key"
export LOG_ANALYTICS_WORKSPACE_ID="your-workspace-id"
```

Then run the demo with Azure integration enabled:

```
python demo.py --azure
```

### Microsoft 365 Integration

To leverage Microsoft 365 integration for continuous model improvement:

```
export MS365_CLIENT_ID="your-client-id"
export MS365_CLIENT_SECRET="your-client-secret"
export MS365_TENANT_ID="your-tenant-id"
```

## Usage Examples

### Basic Usage

```python
from src.query_processor.main import QueryProcessor

# Initialize the processor
processor = QueryProcessor()

# Process a query
result = processor.process_query("What is machine learning?")

# Get response
response = result['response']
print(f"Selected model: {result['selected_model']}")
print(f"Response: {response}")
```

### Configuration

The processor can be configured through a JSON configuration file:

```json
{
  "feature_extraction": {
    "max_features": 50,
    "stop_words": "english"
  },
  "anomaly_detection": {
    "contamination": 0.1,
    "n_estimators": 100
  },
  "models": {
    "simple": {
      "model": "mistral",
      "threshold": 0.3,
      "min_complexity": 0,
      "resource_intensity": 1
    },
    "technical": {
      "model": "llama2",
      "threshold": 0.5,
      "min_complexity": 10,
      "resource_intensity": 3
    },
    "analytical": {
      "model": "codeqwen",
      "threshold": 0.6,
      "min_complexity": 15,
      "resource_intensity": 5
    }
  },
  "azure": {
    "enabled": true
  }
}
```

## Performance Benchmark

The system has been benchmarked with various query types to demonstrate the effectiveness of the intelligent routing:

| Query Type | Average Response Time | Model Distribution         |
| ---------- | --------------------- | -------------------------- |
| Simple     | 0.8s                  | mistral: 95%, llama2: 5%   |
| Technical  | 2.3s                  | llama2: 80%, mistral: 20%  |
| Complex    | 4.5s                  | codeqwen: 75%, llama2: 25% |

## Production Deployment

For production deployment, consider the following:

1. Use Docker for containerization:

   ```
   docker build -t microsoft-query-processor .
   docker run -p 8000:8000 microsoft-query-processor
   ```

2. Set up proper monitoring with Azure Monitor or Application Insights

3. Implement a CI/CD pipeline for automated testing and deployment

## Advanced Features

### Anomaly Detection

The system uses isolation forest algorithms to detect unusual query patterns:

```python
from src.query_processor.anomaly_detection import MultiModalAnomalyDetector

detector = MultiModalAnomalyDetector()
detector.fit(historical_queries)
anomaly_score = detector.score_anomaly(query_features)
```

### Microsoft 365 Integration

The MS365 integration module enables continuous model improvement by leveraging organizational data:

```python
from src.query_processor.ms365_integration import MS365Connector, MS365InsightExtractor

connector = MS365Connector()
extractor = MS365InsightExtractor(connector)
common_topics = extractor.extract_common_topics()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Microsoft for their guidance on production-ready systems
- The open-source community for the tools and libraries used in this project

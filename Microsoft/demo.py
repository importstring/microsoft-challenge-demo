#!/usr/bin/env python3
"""
Microsoft Advanced Query Processor Demo
Production-Ready Version for Microsoft Integration

This script demonstrates the production-ready implementation
of the Query Processor with Microsoft Azure and MS365 integration.
"""

import time
import sys
import argparse
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging

# Import the query processor components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.query_processor.main import QueryProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()

def demo_header():
    """Display demo header"""
    console.print("\n")
    console.print(Panel(
        "[bold cyan]Microsoft Advanced Query Processor[/bold cyan]\n"
        "[yellow]Production-Ready Demo for Microsoft Integration[/yellow]\n\n"
        "Multi-modal anomaly detection with intelligent model routing",
        width=80,
        expand=False
    ))
    console.print("\n")

def run_interactive_demo(config_path=None, azure_enabled=False):
    """Run interactive demo with the query processor"""
    demo_header()
    
    # Create config for demo
    config = {
        'azure': {
            'enabled': azure_enabled
        },
        'models': {
            'simple': {'model': 'mistral', 'threshold': 0.3, 'min_complexity': 0, 'resource_intensity': 1},
            'technical': {'model': 'llama2', 'threshold': 0.5, 'min_complexity': 10, 'resource_intensity': 3},
            'analytical': {'model': 'codeqwen', 'threshold': 0.6, 'min_complexity': 15, 'resource_intensity': 5}
        },
        'monitoring': {
            'interval': 30  # More frequent for demo
        }
    }
    
    # Initialize processor
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Initializing query processor...[/cyan]"),
        transient=True
    ) as progress:
        progress.add_task("init", total=None)
        processor = QueryProcessor(config)
        
    console.print("[green]✓[/green] Query processor initialized")
    
    if processor.azure_enabled:
        console.print("[green]✓[/green] Azure integration enabled")
    
    # Example query suggestions
    console.print(
        Panel(
            "[yellow]Suggested Queries for Testing:[/yellow]\n"
            "• What is the weather today?\n"
            "• Explain the process of machine learning as it applies to anomaly detection in financial transactions with specific examples from banking industry use cases.\n"
            "• Can you give me a code snippet for binary search in Python?\n"
            "• stats (to view system performance)",
            title="Query Suggestions",
            expand=False
        )
    )
    
    # Run processor in interactive mode
    processor.interactive_mode()

def run_benchmark_demo(config_path=None, iterations=10):
    """Run benchmark demo with the query processor"""
    demo_header()
    
    console.print("[bold]Running benchmark with various query types...[/bold]\n")
    
    # Set up processor
    processor = QueryProcessor(config_path)
    
    # Define test queries of various complexity levels
    test_queries = {
        "simple": [
            "What time is it?",
            "Hello, how are you?",
            "Tell me a joke",
            "What is 2+2?",
            "Who is the president?"
        ],
        "medium": [
            "Explain the difference between HTTP and HTTPS protocols",
            "What are the main features of Python programming language?",
            "How does cloud computing work?",
            "Summarize the plot of Romeo and Juliet",
            "What's the difference between supervised and unsupervised learning?"
        ],
        "complex": [
            "Explain the process of quantum computing and its potential impact on cryptography and data security in the next decade",
            "Compare and contrast three machine learning approaches for anomaly detection in large time-series datasets, considering both accuracy and computational efficiency",
            "What architectural patterns should be considered when designing a microservices-based system that needs to process millions of financial transactions per hour while maintaining ACID properties?",
            "Explain the mathematical foundations of transformer-based large language models, including attention mechanisms and their computational complexity",
            "Analyze the ethical considerations in implementing facial recognition technology for public surveillance, considering privacy laws in different jurisdictions"
        ]
    }
    
    # Results table
    results_table = Table(title="Benchmark Results")
    results_table.add_column("Query Type", style="cyan")
    results_table.add_column("Avg. Time (s)", justify="right")
    results_table.add_column("Selected Models", style="magenta")
    
    # Run benchmarks
    for complexity, queries in test_queries.items():
        console.print(f"[yellow]Testing {complexity} queries...[/yellow]")
        
        total_time = 0
        model_counts = {}
        
        for i, query in enumerate(queries):
            if i >= iterations:
                break
                
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Processing query {i+1}/{min(iterations, len(queries))}...[/cyan]"),
                transient=True
            ) as progress:
                progress.add_task("processing", total=None)
                result = processor.process_query(query)
            
            total_time += result['processing_time']
            
            # Count model selections
            model = result['selected_model']
            if model not in model_counts:
                model_counts[model] = 0
            model_counts[model] += 1
            
            # Display result
            console.print(
                f"  Query: '{query[:50]}{'...' if len(query) > 50 else ''}'\n"
                f"  [green]→[/green] Selected model: [bold]{result['selected_model']}[/bold], "
                f"Time: [bold]{result['processing_time']:.2f}s[/bold], "
                f"Anomaly score: [bold]{result['features'].get('anomaly_score', 0):.4f}[/bold]\n"
            )
        
        # Calculate averages
        avg_time = total_time / min(iterations, len(queries))
        
        # Format model distribution
        model_dist = []
        for model, count in model_counts.items():
            percentage = (count / min(iterations, len(queries))) * 100
            model_dist.append(f"{model}: {percentage:.0f}%")
        
        # Add row to results table
        results_table.add_row(
            complexity.title(),
            f"{avg_time:.2f}",
            ", ".join(model_dist)
        )
    
    # Display final results
    console.print("\n")
    console.print(results_table)
    
    # Display system statistics
    console.print("\n[bold]System Performance:[/bold]")
    processor.display_system_stats()
    
    console.print("\n[green]Benchmark completed successfully![/green]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Microsoft Advanced Query Processor Demo")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--azure", action="store_true", help="Enable Azure integration")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark demo")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations for benchmark")
    
    args = parser.parse_args()
    
    try:
        if args.benchmark:
            run_benchmark_demo(args.config, args.iterations)
        else:
            run_interactive_demo(args.config, args.azure)
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo terminated by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        logging.exception("Demo error")
        sys.exit(1) 
#!/usr/bin/env python3
"""
Demo script for the Investor Intelligence Metrics System.

This script demonstrates the latency tracking functionality by:
1. Making sample API calls to generate metrics
2. Displaying performance summaries
3. Showing how to use the metrics service
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from investor_intelligence.utils.metrics import (
    get_metrics_collector,
    track_latency,
    LatencyTracker,
)
from investor_intelligence.services.metrics_service import MetricsService
from investor_intelligence.tools.alpha_vantage_tool import (
    get_current_price,
    get_historical_data,
)
from investor_intelligence.services.portfolio_service import PortfolioService


def simulate_api_calls():
    """Simulate various API calls to generate metrics data."""
    print("🔧 Simulating API calls to generate metrics data...")

    # Sample tickers for testing
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"]

    # Simulate stock price lookups
    for ticker in tickers[:4]:  # Use first 4 to avoid API rate limits
        try:
            print(f"  📈 Getting current price for {ticker}...")
            price = get_current_price(ticker)
            if price:
                print(f"     ✅ {ticker}: ${price:.2f}")
            else:
                print(f"     ❌ Failed to get price for {ticker}")
        except Exception as e:
            print(f"     ❌ Error getting price for {ticker}: {e}")

    # Simulate historical data requests
    for ticker in tickers[:2]:  # Use first 2 to avoid API rate limits
        try:
            print(f"  📊 Getting historical data for {ticker}...")
            data = get_historical_data(ticker, interval="1d")
            if data:
                print(f"     ✅ Got {len(data)} data points for {ticker}")
            else:
                print(f"     ❌ Failed to get historical data for {ticker}")
        except Exception as e:
            print(f"     ❌ Error getting historical data for {ticker}: {e}")

    # Simulate portfolio operations
    try:
        print("  📋 Loading portfolio data...")
        portfolio_service = PortfolioService(
            "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q", "Sheet1!A1:D"
        )
        portfolio = portfolio_service.load_portfolio_from_sheets(
            "demo_user", "Demo Portfolio"
        )
        if portfolio:
            print(f"     ✅ Loaded portfolio with {len(portfolio.holdings)} holdings")
        else:
            print("     ❌ Failed to load portfolio")
    except Exception as e:
        print(f"     ❌ Error loading portfolio: {e}")


def demonstrate_metrics_service():
    """Demonstrate the metrics service functionality."""
    print("\n📊 Demonstrating Metrics Service...")

    metrics_service = MetricsService()

    # Get overall performance summary
    print("\n1. Overall Performance Summary (Last 24 hours):")
    summary = metrics_service.get_overall_performance_summary(hours=24)
    if summary:
        print(f"   Total Requests: {summary.get('total_requests', 0)}")
        print(f"   Average Duration: {summary.get('avg_duration_ms', 0):.2f}ms")
        print(f"   Success Rate: {summary.get('success_rate', 0):.2f}%")
        print(f"   Performance Grade: {summary.get('performance_grade', 'N/A')}")
        print(f"   Performance Status: {summary.get('performance_status', 'Unknown')}")
    else:
        print("   No metrics data available")

    # Get service-specific metrics
    print("\n2. Service Performance Report:")
    service_report = metrics_service.get_service_performance_report(hours=24)
    if service_report and service_report.get("services"):
        for service, metrics in service_report["services"].items():
            print(f"   {service}:")
            print(f"     - Avg Duration: {metrics.get('avg_duration_ms', 0):.2f}ms")
            print(f"     - Success Rate: {metrics.get('success_rate', 0):.2f}%")
            print(f"     - Grade: {metrics.get('performance_grade', 'N/A')}")
    else:
        print("   No service metrics available")

    # Get performance alerts
    print("\n3. Performance Alerts:")
    alerts = metrics_service.get_performance_alerts(hours=24)
    if alerts:
        for alert in alerts:
            print(
                f"   🚨 {alert['type'].replace('_', ' ').upper()}: {alert['message']}"
            )
            print(f"      Service: {alert['service']}, Severity: {alert['severity']}")
    else:
        print("   No performance alerts")

    # Get recommendations
    print("\n4. Performance Recommendations:")
    recommendations = metrics_service.get_performance_recommendations(hours=24)
    if recommendations:
        for rec in recommendations:
            print(f"   💡 {rec['title']}")
            print(f"      Priority: {rec['priority'].upper()}")
            print(f"      Description: {rec['description']}")
    else:
        print("   No recommendations available")


def demonstrate_latency_tracking():
    """Demonstrate different ways to track latency."""
    print("\n⏱️  Demonstrating Latency Tracking Methods...")

    # Method 1: Using decorator
    @track_latency("demo_function", "demo_service")
    def demo_function():
        """A demo function that simulates some work."""
        time.sleep(random.uniform(0.1, 0.5))  # Simulate work
        if random.random() < 0.1:  # 10% chance of failure
            raise ValueError("Simulated error")
        return "Success"

    # Method 2: Using context manager
    def demo_with_context_manager():
        """Demonstrate using the LatencyTracker context manager."""
        with LatencyTracker(
            "context_demo", "demo_service", {"method": "context_manager"}
        ):
            time.sleep(random.uniform(0.05, 0.3))
            if random.random() < 0.05:  # 5% chance of failure
                raise RuntimeError("Simulated context error")

    # Run demonstrations
    print("  Running decorated function...")
    for i in range(5):
        try:
            result = demo_function()
            print(f"    ✅ Call {i+1}: {result}")
        except Exception as e:
            print(f"    ❌ Call {i+1}: {e}")

    print("  Running context manager demo...")
    for i in range(3):
        try:
            demo_with_context_manager()
            print(f"    ✅ Context call {i+1}: Success")
        except Exception as e:
            print(f"    ❌ Context call {i+1}: {e}")


def cleanup_old_metrics():
    """Clean up old metrics data."""
    print("\n🧹 Cleaning up old metrics data...")
    collector = get_metrics_collector()
    collector.cleanup_old_metrics(days=7)
    print("   Cleanup completed")


def main():
    """Main demo function."""
    print("🚀 Investor Intelligence Metrics Demo")
    print("=" * 50)

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Run demonstrations
    simulate_api_calls()
    demonstrate_latency_tracking()
    demonstrate_metrics_service()
    cleanup_old_metrics()

    print("\n" + "=" * 50)
    print("✅ Demo completed!")
    print("\n📈 To view the metrics dashboard:")
    print("   1. Start the web app: python -m src.investor_intelligence.web_app.app")
    print("   2. Open your browser to: http://localhost:5000/metrics")
    print("\n📊 The dashboard will show:")
    print("   - Overall performance metrics")
    print("   - Service-specific performance")
    print("   - Performance alerts and recommendations")
    print("   - Interactive charts and trends")


if __name__ == "__main__":
    main()

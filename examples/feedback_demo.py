#!/usr/bin/env python3
"""
Demonstration of the alert relevance feedback collection system.

This script shows how to:
1. Create alerts with relevance scores
2. Collect user feedback on alerts
3. Train the relevance model with feedback data
4. Analyze feedback patterns and model performance
"""

import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from investor_intelligence.models.alert import Alert
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.services.alert_feedback_service import AlertFeedbackService
from investor_intelligence.ml.relevance_model import RelevanceModel


def create_sample_alerts(alert_service, user_id, portfolio_id):
    """Create sample alerts for demonstration."""
    print("Creating sample alerts...")

    alerts = [
        Alert(
            user_id=user_id,
            portfolio_id=portfolio_id,
            alert_type="price_gain",
            symbol="AAPL",
            message="AAPL stock price increased by 3.2% today",
            triggered_at=datetime.now(),
            relevance_score=0.8,
        ),
        Alert(
            user_id=user_id,
            portfolio_id=portfolio_id,
            alert_type="news_sentiment",
            symbol="MSFT",
            message="Positive news: Microsoft announces new AI partnership",
            triggered_at=datetime.now(),
            relevance_score=0.7,
        ),
        Alert(
            user_id=user_id,
            portfolio_id=portfolio_id,
            alert_type="earnings_report",
            symbol="GOOGL",
            message="Google earnings report scheduled for next week",
            triggered_at=datetime.now(),
            relevance_score=0.9,
        ),
        Alert(
            user_id=user_id,
            portfolio_id=portfolio_id,
            alert_type="price_drop",
            symbol="TSLA",
            message="Tesla stock dropped by 1.5%",
            triggered_at=datetime.now(),
            relevance_score=0.6,
        ),
    ]

    saved_alerts = []
    for alert in alerts:
        saved_alert = alert_service.create_alert(alert)
        saved_alerts.append(saved_alert)
        print(
            f"  Created alert {saved_alert.id}: {alert.alert_type} for {alert.symbol}"
        )

    return saved_alerts


def simulate_user_interactions(alert_service, alerts, user_id):
    """Simulate various user interactions with alerts."""
    print("\nSimulating user interactions...")

    # Alert 1: User finds this very relevant
    alert_service.track_alert_view(alerts[0].id, user_id, 0.8)
    alert_service.track_alert_click(alerts[0].id, user_id, 8.0)  # Long interaction
    alert_service.record_relevance_rating(
        alerts[0].id, user_id, 5, "Very useful for my AAPL position"
    )
    alert_service.record_relevance_mark(alerts[0].id, user_id, True)
    print(f"  User highly engaged with alert {alerts[0].id} (AAPL price gain)")

    # Alert 2: User finds this moderately relevant
    alert_service.track_alert_view(alerts[1].id, user_id, 0.7)
    alert_service.track_alert_click(alerts[1].id, user_id, 3.0)
    alert_service.record_relevance_rating(alerts[1].id, user_id, 4, "Interesting news")
    print(f"  User moderately engaged with alert {alerts[1].id} (MSFT news)")

    # Alert 3: User finds this highly relevant
    alert_service.track_alert_view(alerts[2].id, user_id, 0.9)
    alert_service.track_alert_click(
        alerts[2].id, user_id, 10.0
    )  # Very long interaction
    alert_service.record_relevance_rating(
        alerts[2].id, user_id, 5, "Critical for my GOOGL holdings"
    )
    alert_service.record_relevance_mark(alerts[2].id, user_id, True)
    print(f"  User highly engaged with alert {alerts[2].id} (GOOGL earnings)")

    # Alert 4: User dismisses this as not relevant
    alert_service.track_alert_view(alerts[3].id, user_id, 0.6)
    alert_service.track_alert_dismiss(
        alerts[3].id, user_id, "Not relevant to my portfolio"
    )
    alert_service.record_relevance_rating(alerts[3].id, user_id, 2, "Don't own TSLA")
    print(f"  User dismissed alert {alerts[3].id} (TSLA price drop)")


def analyze_engagement_scores(alert_service, alerts):
    """Analyze engagement scores for all alerts."""
    print("\nAnalyzing engagement scores...")

    for alert in alerts:
        engagement_score = alert_service.get_alert_engagement_score(alert.id)
        print(
            f"  Alert {alert.id} ({alert.symbol} {alert.alert_type}): {engagement_score:.3f}"
        )


def train_model_with_feedback(alert_service, relevance_model):
    """Train the relevance model with collected feedback."""
    print("\nTraining relevance model with feedback data...")

    # Get training data from the last 90 days
    training_data = alert_service.get_relevance_training_data(days_back=90)
    print(f"  Collected {len(training_data)} training examples")

    # Train the model
    training_result = relevance_model.train_with_feedback(training_data)

    print(f"  Training status: {training_result['status']}")
    if training_result["status"] == "success":
        print(f"  Training samples: {training_result['training_samples']}")
        print(f"  Model accuracy: {training_result['performance']['accuracy']:.3f}")


def show_feedback_insights(relevance_model):
    """Show insights from the feedback data."""
    print("\nFeedback insights:")

    insights = relevance_model.get_feedback_insights()

    if "message" in insights:
        print(f"  {insights['message']}")
    else:
        print(f"  Total samples: {insights['total_samples']}")
        print(f"  Average relevance: {insights['average_relevance']:.3f}")

        if "alert_type_statistics" in insights:
            print("  Relevance by alert type:")
            for alert_type, stats in insights["alert_type_statistics"].items():
                print(
                    f"    {alert_type}: {stats['avg_relevance']:.3f} ({stats['count']} samples)"
                )


def show_user_feedback_summary(alert_service, user_id):
    """Show a summary of user feedback patterns."""
    print(f"\nUser feedback summary for {user_id}:")

    summary = alert_service.get_user_feedback_summary(user_id, days_back=30)

    print(f"  Total interactions: {summary['total_interactions']}")
    print(f"  Average rating: {summary['average_rating']:.2f}")
    print(f"  Engagement trend: {summary['engagement_trend']}")

    if summary["feedback_types"]:
        print("  Feedback type breakdown:")
        for feedback_type, count in summary["feedback_types"].items():
            print(f"    {feedback_type}: {count}")


def demonstrate_model_prediction(relevance_model):
    """Demonstrate the model making predictions on new alerts."""
    print("\nDemonstrating model predictions on new alerts...")

    # Sample new alerts
    new_alerts = [
        {
            "type": "price_gain",
            "symbol": "AAPL",
            "change": 2.5,
            "sentiment": "positive",
        },
        {"type": "news_sentiment", "symbol": "UNKNOWN", "sentiment": "negative"},
        {"type": "earnings_report", "symbol": "MSFT"},
    ]

    user_preferences = {"min_price_change_alert": 1.0, "risk_profile": "moderate"}

    portfolio_context = {
        "symbols_held": ["AAPL", "MSFT"],
        "holding_quantities": {"AAPL": 100, "MSFT": 50},
        "portfolio_value": 10000,
    }

    for i, alert in enumerate(new_alerts, 1):
        score = relevance_model.predict_relevance(
            alert, user_preferences, portfolio_context
        )
        print(
            f"  Alert {i} ({alert['type']} for {alert.get('symbol', 'N/A')}): {score:.3f}"
        )


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("Alert Relevance Feedback Collection System Demo")
    print("=" * 60)

    # Initialize services
    alert_service = AlertService()
    feedback_service = AlertFeedbackService()
    relevance_model = RelevanceModel()

    # Test user and portfolio
    user_id = "demo_user_123"
    portfolio_id = "demo_portfolio_123"

    try:
        # Step 1: Create sample alerts
        alerts = create_sample_alerts(alert_service, user_id, portfolio_id)

        # Step 2: Simulate user interactions
        simulate_user_interactions(alert_service, alerts, user_id)

        # Step 3: Analyze engagement
        analyze_engagement_scores(alert_service, alerts)

        # Step 4: Train the model
        train_model_with_feedback(alert_service, relevance_model)

        # Step 5: Show insights
        show_feedback_insights(relevance_model)

        # Step 6: Show user summary
        show_user_feedback_summary(alert_service, user_id)

        # Step 7: Demonstrate predictions
        demonstrate_model_prediction(relevance_model)

        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

from typing import List
from datetime import datetime, date
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.tools.alpha_vantage_tool import (
    get_current_price,
    get_earnings_calendar,
)
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.models.alert import Alert


class MonitoringService:
    """Service for monitoring stock prices and generating alerts."""

    def __init__(self, alert_service: AlertService):
        self.alert_service = alert_service

    def monitor_earnings_reports(self, user_id: str, portfolio: Portfolio):
        """Monitors upcoming earnings reports for stocks in a given portfolio and generates alerts."""
        print(
            f"\nMonitoring earnings reports for portfolio {portfolio.name} (User: {user_id})..."
        )
        earnings_calendar = get_earnings_calendar(horizon="3month")

        if not earnings_calendar:
            print("  Could not retrieve earnings calendar data.")
            return

        for holding in portfolio.holdings:
            print(f"  - Checking earnings for {holding.symbol}...")
            for event in earnings_calendar:
                if event.get("symbol", "").upper() == holding.symbol.upper():
                    report_date_str = event.get("reportDate", "")
                    try:
                        report_date = datetime.strptime(
                            report_date_str, "%Y-%m-%d"
                        ).date()
                        if (
                            report_date >= datetime.now().date()
                        ):  # Only alert for future earnings
                            days_until = (report_date - datetime.now().date()).days
                            message = f"ALERT: Earnings report for {holding.symbol} is scheduled for {report_date_str} ({days_until} days from now)."

                            # Check if we already have an alert for this earnings event
                            existing_alerts = self.alert_service.get_alerts_for_user(
                                user_id, active_only=True
                            )
                            alert_exists = any(
                                alert.alert_type == "earnings_report"
                                and alert.symbol == holding.symbol
                                and report_date_str in alert.message
                                for alert in existing_alerts
                            )

                            if not alert_exists:
                                self.alert_service.create_alert(
                                    Alert(
                                        user_id=user_id,
                                        portfolio_id=portfolio.user_id,
                                        alert_type="earnings_report",
                                        symbol=holding.symbol,
                                        message=message,
                                        triggered_at=datetime.now(),
                                    )
                                )
                                print(f"    {message}")
                            else:
                                print(
                                    f"    Alert already exists for {holding.symbol} earnings on {report_date_str}"
                                )
                    except ValueError:
                        print(
                            f"    Invalid report date format for {holding.symbol}: {report_date_str}"
                        )

    def generate_earnings_summary(self, user_id: str, portfolio: Portfolio) -> str:
        """Generates a summary of upcoming earnings reports for the portfolio."""
        summary_lines = [f"Earnings Summary for {portfolio.name} (User: {user_id}):\n"]
        earnings_calendar = get_earnings_calendar(horizon="3month")

        if not earnings_calendar:
            summary_lines.append("  Could not retrieve earnings calendar data.\n")
            return "\n".join(summary_lines)

        found_earnings = False
        for holding in portfolio.holdings:
            for event in earnings_calendar:
                if event.get("symbol", "").upper() == holding.symbol.upper():
                    report_date_str = event.get("reportDate", "")
                    try:
                        report_date = datetime.strptime(
                            report_date_str, "%Y-%m-%d"
                        ).date()
                        if report_date >= datetime.now().date():
                            days_until = (report_date - datetime.now().date()).days
                            fiscal_date = event.get("fiscalDateEnding", "N/A")
                            summary_lines.append(
                                f"  - {holding.symbol}: Report due on {report_date_str} ({days_until} days) - Fiscal Date Ending: {fiscal_date}\n"
                            )
                            found_earnings = True
                    except ValueError:
                        pass  # Skip invalid dates

        if not found_earnings:
            summary_lines.append(
                "  No upcoming earnings reports found for your portfolio holdings.\n"
            )

        return "\n".join(summary_lines)

    def analyze_sentiment(self, text: str) -> str:
        """Performs basic sentiment analysis on a given text."""
        text_lower = text.lower()
        positive_keywords = [
            "gain",
            "rise",
            "growth",
            "strong",
            "up",
            "beat",
            "exceed",
            "success",
            "optimistic",
            "bullish",
        ]
        negative_keywords = [
            "drop",
            "fall",
            "decline",
            "weak",
            "down",
            "miss",
            "below",
            "loss",
            "pessimistic",
            "bearish",
        ]
        positive_score = sum(
            1 for keyword in positive_keywords if keyword in text_lower
        )
        negative_score = sum(
            1 for keyword in negative_keywords if keyword in text_lower
        )
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"

    def monitor_news_sentiment(self, user_id: str, portfolio: Portfolio):
        """Monitors news sentiment for stocks in a given portfolio and generates alerts."""
        print(
            f"\nMonitoring news sentiment for portfolio {portfolio.name} (User: {user_id})..."
        )
        from datetime import timedelta
        from investor_intelligence.tools.news_tool import get_news_articles

        for holding in portfolio.holdings:
            print(f"  - Checking news for {holding.symbol}...")
            # Fetch news for the last 24 hours
            from_date = (datetime.now() - timedelta(days=1)).isoformat()
            to_date = datetime.now().isoformat()
            articles = get_news_articles(
                holding.symbol, from_date=from_date, to_date=to_date, page_size=5
            )
            if not articles:
                print(f"    No recent news found for {holding.symbol}.")
                continue
            for article in articles:
                title = article.get("title", "")
                description = article.get("description", "")
                content = f"{title}. {description}"
                sentiment = self.analyze_sentiment(content)
                if sentiment != "neutral":
                    message = f"NEWS ALERT: {holding.symbol} - {sentiment.upper()} sentiment detected in news: \"{title}\". URL: {article.get('url')}"
                    # Prevent duplicate alerts for the same article/sentiment
                    existing_alerts = self.alert_service.get_alerts_for_user(
                        user_id, active_only=True
                    )
                    alert_exists = any(
                        alert.alert_type == "news_sentiment"
                        and alert.symbol == holding.symbol
                        and alert.message == message
                        for alert in existing_alerts
                    )
                    if not alert_exists:
                        self.alert_service.create_alert(
                            Alert(
                                user_id=user_id,
                                portfolio_id=portfolio.user_id,
                                alert_type="news_sentiment",
                                symbol=holding.symbol,
                                message=message,
                                triggered_at=datetime.now(),
                            )
                        )
                        print(f"    {message}")
                    else:
                        print(
                            f"    Duplicate news sentiment alert for {holding.symbol} already exists."
                        )


if __name__ == "__main__":
    from investor_intelligence.services.portfolio_service import PortfolioService
    from investor_intelligence.services.alert_service import AlertService
    from investor_intelligence.models.portfolio import Portfolio, StockHolding
    from datetime import date

    # Initialize services
    alert_service = AlertService()
    monitoring_service = MonitoringService(alert_service)

    # Create a test portfolio
    test_holdings = [
        StockHolding(
            symbol="AAPL", quantity=10, purchase_price=150.0, purchase_date=date.today()
        ),
        StockHolding(
            symbol="MSFT", quantity=5, purchase_price=300.0, purchase_date=date.today()
        ),
        StockHolding(
            symbol="GOOG", quantity=8, purchase_price=140.0, purchase_date=date.today()
        ),
    ]

    test_portfolio = Portfolio(
        user_id="test_user", name="Test News Portfolio", holdings=test_holdings
    )

    user_id = "test_user_news"

    print("Testing news sentiment monitoring...")
    monitoring_service.monitor_news_sentiment(user_id, test_portfolio)

    print("\nChecking created news alerts...")
    alerts = alert_service.get_alerts_for_user(user_id, active_only=True)
    for alert in alerts:
        if alert.alert_type == "news_sentiment":
            print(f"  - {alert.alert_type} for {alert.symbol}: {alert.message}")

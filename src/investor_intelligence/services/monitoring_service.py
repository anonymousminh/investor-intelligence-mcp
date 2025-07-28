from typing import List
from datetime import datetime, date
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.tools.alpha_vantage_tool import (
    get_current_price,
    get_earnings_calendar,
)
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.models.alert import Alert
from investor_intelligence.ml.relevance_model import RelevanceModel
from investor_intelligence.services.user_config_service import UserConfigService


class MonitoringService:
    """Service for monitoring stock prices and generating alerts."""

    def __init__(self, alert_service: AlertService, relevance_model: RelevanceModel):
        self.alert_service = alert_service
        self.relevance_model = RelevanceModel()
        self.user_config_service = UserConfigService()

    def monitor_earnings_reports(self, user_id: str, portfolio: Portfolio):
        """Monitors upcoming earnings reports for stocks in a given portfolio and generates alerts."""
        print(
            f"\nMonitoring earnings reports for portfolio {portfolio.name} (User: {user_id})..."
        )
        earnings_calendar = get_earnings_calendar(horizon="3month")

        if not earnings_calendar:
            print(
                "Could not retrieve earnings calendar data. Skipping earnings monitoring."
            )
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
                                # Calculate relevance score
                                user_preferences = self.alert_service.user_config_service.get_user_config(
                                    user_id
                                )
                                alert_dict = {
                                    "type": "earnings_report",
                                    "symbol": holding.symbol,
                                    "report_date": report_date_str,
                                }
                                relevance_score = (
                                    self.relevance_model.predict_relevance(
                                        alert_dict, user_preferences
                                    )
                                )
                                new_alert = Alert(
                                    user_id=user_id,
                                    portfolio_id=portfolio.user_id,
                                    alert_type="earnings_report",
                                    symbol=holding.symbol,
                                    message=message,
                                    triggered_at=datetime.now(),
                                    relevance_score=relevance_score,
                                )
                                # Filter the alert before creating
                                filtered = self.alert_service.filter_alerts(
                                    [new_alert], user_id
                                )
                                if filtered:
                                    self.alert_service.create_alert(filtered[0])
                                    print(f"    {message}")
                                else:
                                    print(
                                        f"    Alert for {holding.symbol} filtered out by user preferences."
                                    )
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
                        # Calculate relevance score
                        user_preferences = (
                            self.alert_service.user_config_service.get_user_config(
                                user_id
                            )
                        )
                        alert_dict = {
                            "type": "news_sentiment",
                            "symbol": holding.symbol,
                            "sentiment": sentiment,
                            "title": title,
                        }
                        relevance_score = self.relevance_model.predict_relevance(
                            alert_dict, user_preferences
                        )
                        new_alert = Alert(
                            user_id=user_id,
                            portfolio_id=portfolio.user_id,
                            alert_type="news_sentiment",
                            symbol=holding.symbol,
                            message=message,
                            triggered_at=datetime.now(),
                            relevance_score=relevance_score,
                        )
                        # Filter the alert before creating
                        filtered = self.alert_service.filter_alerts(
                            [new_alert], user_id
                        )
                        if filtered:
                            self.alert_service.create_alert(filtered[0])
                            print(f"    {message}")
                        else:
                            print(
                                f"    News sentiment alert for {holding.symbol} filtered out by user preferences."
                            )
                    else:
                        print(
                            f"    Duplicate news sentiment alert for {holding.symbol} already exists."
                        )

    def monitor_price_changes(self, user_id: str, portfolio: Portfolio):
        """Monitors price changes for stocks in a given portfolio and generates alerts.

        Args:
            user_id (str): The ID of the user.
            portfolio (Portfolio): The portfolio to monitor.
            threshold (float): The percentage change threshold to trigger an alert (e.g., 1.0 for 1%).
        """
        print(
            f"\nMonitoring price changes for portfolio {portfolio.name} (User: {user_id})..."
        )
        for holding in portfolio.holdings:
            print(f"  - Checking price for {holding.symbol}...")
            current_price = get_current_price(holding.symbol)
            if current_price is None:
                print(
                    f"Could not retrieve current price for {holding.symbol}. Skipping price change for this holding."
                )
                continue

            # For simplicity, let's assume we have a way to get the previous price.
            # In a real system, you would store historical prices in a database.
            # For now, let's simulate a previous price or fetch a historical one.
            # This part needs to be more robust for production.
            previous_price = (
                holding.purchase_price
            )  # Using purchase price as a baseline for now

            if previous_price and previous_price > 0:
                percentage_change = (
                    (current_price - previous_price) / previous_price
                ) * 100

                alert_type = None
                if percentage_change >= threshold:
                    alert_type = "price_gain"
                elif percentage_change <= -threshold:
                    alert_type = "price_drop"

                if alert_type:
                    message = f"ALERT: {holding.symbol} price changed by {percentage_change:.2f}% to ${current_price:.2f}."

                    # Calculate relevance score
                    user_preferences = (
                        self.alert_service.user_config_service.get_user_config(user_id)
                    )
                    alert_dict = {
                        "type": alert_type,
                        "symbol": holding.symbol,
                        "change": percentage_change,
                    }
                    relevance_score = self.relevance_model.predict_relevance(
                        alert_dict, user_preferences
                    )

                    user_config = self.user_config_service.get_user_config(user_id)
                    threshold = user_config.get("price_change_threshold", 1.0)

                    # Prevent duplicate alerts for the same type and symbol within a short period
                    existing_alerts = self.alert_service.get_alerts_for_user(
                        user_id, active_only=True
                    )
                    alert_exists = any(
                        alert.alert_type == alert_type
                        and alert.symbol == holding.symbol
                        and (datetime.now() - alert.triggered_at).total_seconds()
                        < 3600  # Within last hour
                        for alert in existing_alerts
                    )

                    if not alert_exists:
                        self.alert_service.create_alert(
                            Alert(
                                user_id=user_id,
                                portfolio_id=portfolio.user_id,
                                alert_type=alert_type,
                                symbol=holding.symbol,
                                message=message,
                                triggered_at=datetime.now(),
                                relevance_score=relevance_score,
                            )
                        )
                        print(f"    {message}")
                    else:
                        print(
                            f"    Duplicate price change alert for {holding.symbol} already exists."
                        )
            else:
                print(
                    f"    Previous price for {holding.symbol} is not valid. Cannot calculate change."
                )


if __name__ == "__main__":

    # Initialize services
    alert_service = AlertService()
    relevance_model = RelevanceModel()
    monitoring_service = MonitoringService(alert_service, relevance_model)

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

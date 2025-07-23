from typing import List
from datetime import datetime, timedelta

from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.models.alert import Alert
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.tools.alpha_vantage_tool import (
    get_quote_endpoint,
    get_time_series_data,
    get_historical_data,
)


class SummaryService:
    """Service for generating email summaries of alerts and market intelligence."""

    def __init__(
        self, alert_service: AlertService, monitoring_service: MonitoringService
    ):
        self.alert_service = alert_service
        self.monitoring_service = monitoring_service

    def generate_daily_summary(self, user_id: str, portfolio: Portfolio) -> str:
        """Generates a comprehensive daily summary for a user's portfolio.

        This summary includes:
        - Recent price change alerts
        - Upcoming earnings reports
        - Recent news sentiment alerts
        """
        summary_lines = [
            f"Daily Investor Intelligence Summary for {portfolio.name} ({datetime.now().strftime('%Y-%m-%d')})\n"
        ]
        summary_lines.append("=====================================================\n")

        # 1. Price Change Alerts
        summary_lines.append("## Price Change Alerts\n")
        all_price_alerts = [
            alert
            for alert in self.alert_service.get_alerts_for_user(
                user_id, active_only=True
            )
            if alert.alert_type in ["price_drop", "price_gain"]
        ]
        price_alerts = self.alert_service.filter_alerts(all_price_alerts, user_id)
        if price_alerts:
            for alert in price_alerts:
                summary_lines.append(f"- {alert.message}\n")
                # Optionally deactivate price alerts after including them in summary
                # self.alert_service.deactivate_alert(alert.id)
        else:
            summary_lines.append("No significant price changes detected.\n")
        summary_lines.append("\n")

        # 2. Earnings Reports
        summary_lines.append("## Upcoming Earnings Reports\n")
        earnings_summary_text = self.monitoring_service.generate_earnings_summary(
            user_id, portfolio
        )
        summary_lines.append(earnings_summary_text)
        summary_lines.append("\n")

        # 3. News Sentiment Alerts
        summary_lines.append("## News Sentiment Alerts\n")
        all_news_alerts = [
            alert
            for alert in self.alert_service.get_alerts_for_user(
                user_id, active_only=True
            )
            if alert.alert_type == "news_sentiment"
        ]
        news_alerts = self.alert_service.filter_alerts(all_news_alerts, user_id)
        if news_alerts:
            for alert in news_alerts:
                summary_lines.append(f"- {alert.message}\n")
                # Optionally deactivate news alerts after including them in summary
                # self.alert_service.deactivate_alert(alert.id)
        else:
            summary_lines.append("No significant news sentiment detected.\n")
        summary_lines.append("\n")

        summary_lines.append("=====================================================\n")
        summary_lines.append(
            "This is an automated summary from your Investor Intelligence Agent. \n"
        )
        summary_lines.append(
            "Disclaimer: This information is for educational purposes only and not financial advice.\n"
        )

        return "".join(summary_lines)

    def generate_weekly_summary(self, user_id: str, portfolio: Portfolio) -> str:
        """Generates a comprehensive weekly summary for a user's portfolio.

        This summary includes:
        - Portfolio performance over the last week
        - Market trend analysis (basic)
        - Consolidated alerts from the week
        """
        summary_lines = [
            f"Weekly Investor Intelligence Summary for {portfolio.name} ({datetime.now().strftime('%Y-%m-%d')})\n"
        ]
        summary_lines.append("=====================================================\n")

        # 1. Portfolio Performance Overview
        summary_lines.append("## Portfolio Performance Overview (Last 7 Days)\n")
        total_current_value = 0.0
        total_initial_value = 0.0

        for holding in portfolio.holdings:
            current_price_data = get_quote_endpoint(holding.symbol)
            if current_price_data:
                current_price = float(current_price_data["05. price"])
                holding_value = current_price * holding.quantity
                print(
                    f"{holding.symbol}: {holding.quantity} × ${current_price:.2f} = ${holding_value:.2f}"
                )
                total_current_value += holding_value

            # Get historical price from 7 days ago
            historical_data = get_historical_data(
                holding.symbol, interval="1d", outputsize="full"
            )
            if historical_data:
                # Find the closest date to 7 days ago
                seven_days_ago = (datetime.now() - timedelta(days=7)).strftime(
                    "%Y-%m-%d"
                )
                historical_price_7_days_ago = None
                for date_str, data in historical_data.items():
                    if date_str <= seven_days_ago:
                        historical_price_7_days_ago = float(data["4. close"])
                        break

                if historical_price_7_days_ago:
                    total_initial_value += (
                        historical_price_7_days_ago * holding.quantity
                    )

        if total_initial_value > 0:
            weekly_change_percent = (
                (total_current_value - total_initial_value) / total_initial_value
            ) * 100
            summary_lines.append(f"Total Portfolio Value: ${total_current_value:.2f}\n")
            summary_lines.append(f"Weekly Change: {weekly_change_percent:.2f}%\n")
        else:
            summary_lines.append(
                "Cannot calculate weekly change (insufficient historical data or initial value).\n"
            )
        summary_lines.append("\n")

        # 2. Consolidated Alerts from the Week
        summary_lines.append("## Alerts from the Past Week\n")
        one_week_ago = datetime.now() - timedelta(days=7)
        all_weekly_alerts = [
            alert
            for alert in self.alert_service.get_alerts_for_user(
                user_id, active_only=False
            )
            if alert.created_at >= one_week_ago
        ]
        weekly_alerts = self.alert_service.filter_alerts(all_weekly_alerts, user_id)

        if weekly_alerts:
            for alert in weekly_alerts:
                summary_lines.append(
                    f"- [{alert.created_at.strftime('%Y-%m-%d %H:%M')}] {alert.alert_type.upper()} for {alert.symbol}: {alert.message}\n"
                )
        else:
            summary_lines.append("No new alerts generated in the past week.\n")
        summary_lines.append("\n")

        # 3. Market Trend Analysis (Basic)
        summary_lines.append("## Basic Market Trend Analysis\n")
        # This is a placeholder. A real implementation would involve analyzing
        # broader market indices (e.g., S&P 500) or economic indicators.
        summary_lines.append(
            "Market trends will be analyzed in more detail in future updates.\n"
        )
        summary_lines.append("\n")

        summary_lines.append("=====================================================\n")
        summary_lines.append(
            "This is an automated weekly summary from your Investor Intelligence Agent. \n"
        )
        summary_lines.append(
            "Disclaimer: This information is for educational purposes only and not financial advice.\n"
        )

        return "".join(summary_lines)


if __name__ == "__main__":
    from investor_intelligence.services.portfolio_service import PortfolioService
    from investor_intelligence.services.alert_service import AlertService
    from investor_intelligence.services.monitoring_service import MonitoringService
    from investor_intelligence.models.portfolio import Portfolio, StockHolding
    from datetime import date

    # Initialize services
    alert_service = AlertService()
    monitoring_service = MonitoringService(alert_service)
    summary_service = SummaryService(alert_service, monitoring_service)

    # Create a test portfolio (ensure symbols have some historical data)
    test_holdings = [
        StockHolding(
            symbol="AAPL",
            quantity=10,
            purchase_price=150.0,
            purchase_date=date(2025, 7, 1),
        ),
        StockHolding(
            symbol="MSFT",
            quantity=5,
            purchase_price=300.0,
            purchase_date=date(2025, 7, 5),
        ),
        StockHolding(
            symbol="GOOG",
            quantity=8,
            purchase_price=140.0,
            purchase_date=date(2025, 7, 10),
        ),
    ]

    test_portfolio = Portfolio(
        user_id="test_user_weekly", name="Weekly Test Portfolio", holdings=test_holdings
    )

    user_id = "test_user_weekly"

    print("\n--- Testing weekly summary generation ---")
    weekly_summary_content = summary_service.generate_weekly_summary(
        user_id, test_portfolio
    )
    print(weekly_summary_content)

    # You can also manually check the alerts created in the database for the past week
    print("\nChecking alerts from the past week for test_user_weekly...")
    one_week_ago = datetime.now() - timedelta(days=7)
    recent_alerts = [
        alert
        for alert in alert_service.get_alerts_for_user(user_id, active_only=False)
        if alert.created_at >= one_week_ago
    ]
    if recent_alerts:
        for alert in recent_alerts:
            print(f"  - {alert.alert_type} for {alert.symbol}: {alert.message}")
    else:
        print("  No recent alerts found for test_user_weekly.")

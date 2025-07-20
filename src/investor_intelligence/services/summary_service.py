from typing import List
from datetime import datetime, timedelta

from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.models.alert import Alert
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.services.monitoring_service import MonitoringService


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
        price_alerts = [
            alert
            for alert in self.alert_service.get_alerts_for_user(
                user_id, active_only=True
            )
            if alert.alert_type in ["price_drop", "price_gain"]
        ]
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
        news_alerts = [
            alert
            for alert in self.alert_service.get_alerts_for_user(
                user_id, active_only=True
            )
            if alert.alert_type == "news_sentiment"
        ]
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

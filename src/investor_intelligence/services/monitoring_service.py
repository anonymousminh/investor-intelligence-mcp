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
            symbol="IBM", quantity=8, purchase_price=140.0, purchase_date=date.today()
        ),
    ]

    test_portfolio = Portfolio(
        user_id="test_user", name="Test Portfolio", holdings=test_holdings
    )

    user_id = "test_user_earnings"

    print("Testing earnings monitoring...")
    monitoring_service.monitor_earnings_reports(user_id, test_portfolio)

    print("\nTesting earnings summary generation...")
    earnings_summary = monitoring_service.generate_earnings_summary(
        user_id, test_portfolio
    )
    print(earnings_summary)

    print("\nChecking created alerts...")
    alerts = alert_service.get_alerts_for_user(user_id, active_only=True)
    for alert in alerts:
        print(f"  - {alert.alert_type} for {alert.symbol}: {alert.message}")

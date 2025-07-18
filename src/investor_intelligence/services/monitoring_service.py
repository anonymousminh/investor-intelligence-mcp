from typing import List
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.tools.alpha_vantage_tool import get_current_price
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.models.alert import Alert
from datetime import datetime


class MonitoringService:
    """Service for monitoring stock prices and generating alerts."""

    def __init__(self, alert_service: AlertService):
        self.alert_service = alert_service

    def monitor_portfolio_prices(self, user_id: str, portfolio: Portfolio):
        """Monitors the current prices of stocks in a given portfolio and generates alerts.

        Args:
            user_id (str): The ID of the user owning the portfolio.
            portfolio (Portfolio): The portfolio to monitor.
        """
        print(
            f"\nMonitoring prices for portfolio {portfolio.name} (User: {user_id})..."
        )
        for holding in portfolio.holdings:
            print(f"  - Checking {holding.symbol}...")
            current_price = get_current_price(holding.symbol)
            if current_price is None:
                print(f"    Could not retrieve current price for {holding.symbol}.")
                continue

            current_price_float = float(current_price)
            purchase_price_float = float(holding.purchase_price)

            print(
                f"    Current Price: ${current_price_float:.2f}, Purchase Price: ${purchase_price_float:.2f}"
            )

            # Example: Check for significant price drops or gains relative to purchase price
            price_change_percent = (
                (current_price_float - purchase_price_float) / purchase_price_float
            ) * 100

            # Define alert thresholds (these could be configurable)
            DROP_THRESHOLD = -5.0  # 5% drop
            GAIN_THRESHOLD = 10.0  # 10% gain

            if price_change_percent <= DROP_THRESHOLD:
                message = f"ALERT: {holding.symbol} has dropped by {abs(price_change_percent):.2f}% to ${current_price_float:.2f} (from ${purchase_price_float:.2f})."
                self.alert_service.create_alert(
                    Alert(
                        user_id=user_id,
                        portfolio_id=portfolio.user_id,  # Using user_id as portfolio_id for simplicity here
                        alert_type="price_drop",
                        symbol=holding.symbol,
                        threshold=DROP_THRESHOLD,
                        message=message,
                        triggered_at=datetime.now(),
                    )
                )
                print(f"    {message}")
            elif price_change_percent >= GAIN_THRESHOLD:
                message = f"ALERT: {holding.symbol} has gained by {price_change_percent:.2f}% to ${current_price_float:.2f} (from ${purchase_price_float:.2f})."
                self.alert_service.create_alert(
                    Alert(
                        user_id=user_id,
                        portfolio_id=portfolio.user_id,  # Using user_id as portfolio_id for simplicity here
                        alert_type="price_gain",
                        symbol=holding.symbol,
                        threshold=GAIN_THRESHOLD,
                        message=message,
                        triggered_at=datetime.now(),
                    )
                )
                print(f"    {message}")
            else:
                print(
                    f"    {holding.symbol} price change within thresholds ({price_change_percent:.2f}%)."
                )


if __name__ == "__main__":
    from investor_intelligence.services.portfolio_service import PortfolioService
    from investor_intelligence.services.alert_service import AlertService
    from investor_intelligence.models.portfolio import Portfolio, StockHolding
    from datetime import date

    # Initialize services
    alert_service = AlertService()
    monitoring_service = MonitoringService(alert_service)

    # IMPORTANT: Replace with your actual Google Sheet ID and range
    SAMPLE_SPREADSHEET_ID = "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q"
    SAMPLE_RANGE_NAME = "Sheet1!A1:D"

    portfolio_service = PortfolioService(SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)

    user_id = "test_user_monitor"
    portfolio_name = "Monitoring Portfolio"

    # Load portfolio from sheets (or create a dummy one for testing if sheet access is an issue)
    loaded_portfolio = portfolio_service.load_portfolio_from_sheets(
        user_id, portfolio_name
    )

    if loaded_portfolio:
        print(
            f"\nSuccessfully loaded portfolio for monitoring: {loaded_portfolio.name}"
        )
        monitoring_service.monitor_portfolio_prices(user_id, loaded_portfolio)

        # Verify alerts were created
        print("\nChecking for created alerts...")
        alerts = alert_service.get_alerts_for_user(user_id, active_only=False)
        if alerts:
            for alert in alerts:
                print(f"  - {alert.alert_type} for {alert.symbol}: {alert.message}")
        else:
            print("  No alerts created (prices within thresholds or API issues).")

    else:
        print(
            "Failed to load portfolio for monitoring. Please check Google Sheet ID and range."
        )

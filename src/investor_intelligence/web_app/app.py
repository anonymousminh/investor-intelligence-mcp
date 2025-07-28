from flask import Flask, render_template, request, redirect, url_for
import os

# Import services and models
from investor_intelligence.services.portfolio_service import PortfolioService
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.models.alert import Alert
from investor_intelligence.services.analytics_service import AnalyticsService
from datetime import date, datetime
from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.utils.logging import logger

app = Flask(__name__)

# Initialize services
alert_service = AlertService()
analytics_service = AnalyticsService()
monitoring_service = MonitoringService(alert_service, analytics_service)

# IMPORTANT: Replace with your actual Google Sheet ID and range for a test user
# In a real application, this would be dynamic based on the logged-in user
SAMPLE_USER_ID = "web_user_123"
SAMPLE_PORTFOLIO_NAME = "Web Dashboard Portfolio"
SAMPLE_SPREADSHEET_ID = "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q"  # Replace this
SAMPLE_RANGE_NAME = "Sheet1!A1:D"

portfolio_service = PortfolioService(SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)


@app.route("/")
def index():
    logger.info("Accessed index route")
    # Load portfolio data for the sample user
    portfolio = portfolio_service.load_portfolio_from_sheets(
        SAMPLE_USER_ID, SAMPLE_PORTFOLIO_NAME
    )

    # Get active alerts for the sample user
    alerts = alert_service.get_alerts_for_user(SAMPLE_USER_ID, active_only=True)

    portfolio_performance = None
    if portfolio:
        portfolio_performance = analytics_service.calculate_portfolio_performance(
            portfolio
        )

    return render_template(
        "index.html",
        portfolio=portfolio,
        alerts=alerts,
        performance=portfolio_performance,
    )


@app.route("/add_holding", methods=["POST"])
def add_holding():
    try:
        symbol = request.form["symbol"].upper()
        quantity = int(request.form["quantity"])
        purchase_price = float(request.form["purchase_price"])
        purchase_date_str = request.form["purchase_date"]
        logger.info(
            f"Adding holding: {symbol}, Qty: {quantity}, Price: {purchase_price}, Date: {purchase_date_str}"
        )
        # Convert date string to date object
        purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
        # Load portfolio to add holding
        portfolio = portfolio_service.load_portfolio_from_sheets(
            SAMPLE_USER_ID, SAMPLE_PORTFOLIO_NAME
        )
        if portfolio:
            new_holding = StockHolding(
                symbol=symbol,
                quantity=quantity,
                purchase_price=purchase_price,
                purchase_date=purchase_date,
            )
            portfolio.add_holding(new_holding)
            portfolio_service.save_portfolio_to_sheets()  # Assuming this method exists and updates the sheet
            logger.info(f"Successfully added holding {symbol} to portfolio.")
        else:
            logger.warning("Portfolio not found when trying to add holding.")
    except Exception as e:
        logger.error(f"Error adding holding: {e}")
    return redirect(url_for("index"))


@app.route("/deactivate_alert/<int:alert_id>")
def deactivate_alert(alert_id):
    try:
        alert_service.deactivate_alert(alert_id)
        logger.info(f"Deactivated alert with ID: {alert_id}")
    except Exception as e:
        logger.error(f"Error deactivating alert {alert_id}: {e}")
    return redirect(url_for("index"))


@app.route("/monitor")
def monitor():
    logger.info("Accessed monitor route")
    # Load portfolio data for the sample user
    portfolio = portfolio_service.load_portfolio_from_sheets(
        SAMPLE_USER_ID, SAMPLE_PORTFOLIO_NAME
    )
    if not portfolio:
        logger.warning("No portfolio found for monitoring.")
        return "No portfolio found for monitoring."
    try:
        # Run monitoring services
        monitoring_service.monitor_earnings_reports(SAMPLE_USER_ID, portfolio)
        monitoring_service.monitor_news_sentiment(SAMPLE_USER_ID, portfolio)
        monitoring_service.monitor_price_changes(SAMPLE_USER_ID, portfolio)
        logger.info("Monitoring services executed successfully.")
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
    # Get updated alerts
    alerts = alert_service.get_alerts_for_user(SAMPLE_USER_ID, active_only=True)
    return render_template(
        "index.html",
        portfolio=portfolio,
        alerts=alerts,
        performance=analytics_service.calculate_portfolio_performance(portfolio),
        message="Monitoring complete. Alerts and behavior reflect your current configuration.",
    )


if __name__ == "__main__":
    # Ensure the 'data' directory exists for SQLite DB
    os.makedirs(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"),
        exist_ok=True,
    )
    logger.info("Starting Flask web app...")
    app.run(debug=True, host="0.0.0.0")

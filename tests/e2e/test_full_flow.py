import pytest
import os
import time
from datetime import datetime, timedelta

# Import services and tools (adjust paths as necessary)
from investor_intelligence.services.portfolio_service import PortfolioService
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.services.summary_service import SummaryService
from investor_intelligence.services.nlp_service import NLPService
from investor_intelligence.services.query_processor_service import QueryProcessorService
from investor_intelligence.services.user_config_service import UserConfigService
from investor_intelligence.tools.gmail_tool import send_message, get_unread_emails
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.models.alert import Alert
from investor_intelligence.ml.relevance_model import RelevanceModel

# --- Setup Fixtures (for pytest) ---


@pytest.fixture(scope="module")
def setup_test_environment():
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")

    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Clean up any existing test databases or files
    if os.path.exists(os.path.join(data_dir, "investor_intelligence.db")):
        os.remove(os.path.join(data_dir, "investor_intelligence.db"))
    if os.path.exists(os.path.join(data_dir, "user_configs.db")):
        os.remove(os.path.join(data_dir, "user_configs.db"))

    # Initialize services with clean state
    alert_service = AlertService()
    user_config_service = UserConfigService()
    relevance_model = RelevanceModel()
    monitoring_service = MonitoringService(alert_service, relevance_model)
    summary_service = SummaryService(alert_service, monitoring_service)
    nlp_service = NLPService()
    query_processor_service = QueryProcessorService(
        nlp_service, PortfolioService("", ""), monitoring_service
    )  # Dummy PortfolioService for query_processor

    # Set up a test user and portfolio
    test_user_id = "e2e_test_user"
    test_user_email = "e2e_test@example.com"
    test_portfolio_name = "E2E Test Portfolio"
    test_spreadsheet_id = (
        "YOUR_TEST_GOOGLE_SHEET_ID"  # Replace with a real test sheet ID
    )
    test_range_name = "Sheet1!A1:D"

    # Save user config (e.g., alert preferences)
    user_config_service.save_user_config(test_user_id, {"min_price_change_alert": 0.5})

    # Create a test portfolio (ensure symbols are valid and have data)
    test_holdings = [
        StockHolding(
            symbol="AAPL",
            quantity=10,
            purchase_price=150.0,
            purchase_date=datetime.now().date(),
        ),
        StockHolding(
            symbol="MSFT",
            quantity=5,
            purchase_price=300.0,
            purchase_date=datetime.now().date(),
        ),
    ]
    test_portfolio = Portfolio(
        user_id=test_user_id, name=test_portfolio_name, holdings=test_holdings
    )

    # Yield services and test data
    yield {
        "alert_service": alert_service,
        "monitoring_service": monitoring_service,
        "summary_service": summary_service,
        "nlp_service": nlp_service,
        "query_processor_service": query_processor_service,
        "user_config_service": user_config_service,
        "test_user_id": test_user_id,
        "test_user_email": test_user_email,
        "test_portfolio": test_portfolio,
        "test_spreadsheet_id": test_spreadsheet_id,
        "test_range_name": test_range_name,
    }

    # Teardown (clean up after tests)
    if os.path.exists(os.path.join(data_dir, "investor_intelligence.db")):
        os.remove(os.path.join(data_dir, "investor_intelligence.db"))
    if os.path.exists(os.path.join(data_dir, "user_configs.db")):
        os.remove(os.path.join(data_dir, "user_configs.db"))


# --- Test Functions ---


def test_price_monitoring_and_alerting(setup_test_environment):
    env = setup_test_environment
    monitoring_service = env["monitoring_service"]
    alert_service = env["alert_service"]
    test_user_id = env["test_user_id"]
    test_portfolio = env["test_portfolio"]

    # Simulate price change (this requires mocking external API calls in a real E2E test)
    # For now, we assume get_current_price will return a value that triggers an alert
    monitoring_service.monitor_price_changes(
        test_user_id, test_portfolio, threshold=0.1
    )

    # Verify alert was created
    alerts = alert_service.get_alerts_for_user(test_user_id, active_only=True)
    assert any(
        alert.alert_type == "price_gain" or alert.alert_type == "price_drop"
        for alert in alerts
    )
    print("E2E Test: Price monitoring and alerting successful.")


def test_email_query_processing(setup_test_environment):
    env = setup_test_environment
    query_processor_service = env["query_processor_service"]
    test_user_id = env["test_user_id"]
    test_user_email = env["test_user_email"]

    # Simulate an incoming email query (requires mocking gmail_tool.get_unread_emails and send_email)
    # For this E2E test, we'll directly call process_email_query and assert the response content
    query_text = "What is the current price of AAPL?"
    response = query_processor_service.process_email_query(
        test_user_id, test_user_email, query_text
    )
    assert "AAPL" in response and "price" in response
    print("E2E Test: Email query processing successful.")


def test_daily_summary_generation(setup_test_environment):
    env = setup_test_environment
    summary_service = env["summary_service"]
    test_user_id = env["test_user_id"]
    test_portfolio = env["test_portfolio"]

    # Generate daily summary
    daily_summary = summary_service.generate_daily_summary(test_user_id, test_portfolio)
    assert "Daily Investor Intelligence Summary" in daily_summary
    assert "AAPL" in daily_summary  # Check if portfolio holdings are mentioned
    print("E2E Test: Daily summary generation successful.")


# Add more E2E tests for other functionalities (weekly summary, web app, etc.)

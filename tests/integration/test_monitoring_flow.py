import pytest
from unittest.mock import patch, MagicMock

from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.services.alert_service import AlertService
from investor_intelligence.models.portfolio import Portfolio, StockHolding
from datetime import datetime, date
from investor_intelligence.ml.relevance_model import RelevanceModel


@pytest.fixture
def mock_alpha_vantage_tool():
    with patch(
        "investor_intelligence.tools.alpha_vantage_tool.get_current_price"
    ) as mock_get_price, patch(
        "investor_intelligence.tools.alpha_vantage_tool.get_earnings_calendar"
    ) as mock_get_earnings:
        mock_get_price.return_value = 160.0  # Mock a price that triggers an alert
        mock_get_earnings.return_value = []  # Mock no earnings for simplicity
        yield


@pytest.fixture
def mock_news_tool():
    with patch(
        "investor_intelligence.tools.news_tool.get_news_articles"
    ) as mock_get_news:
        mock_get_news.return_value = []  # Mock no news for simplicity
        yield


def test_monitoring_service_triggers_alert(mock_alpha_vantage_tool, mock_news_tool):
    alert_service = AlertService()
    relevance_model = RelevanceModel()
    monitoring_service = MonitoringService(alert_service, relevance_model)

    test_portfolio = Portfolio(
        user_id="test_user_int",
        name="Integration Test Portfolio",
        holdings=[
            StockHolding(
                symbol="AAPL",
                quantity=10,
                purchase_price=150.0,
                purchase_date=date.today(),
            ),
        ],
    )

    # Ensure alert service is clean
    alert_service.create_table()  # Recreate table for clean state

    monitoring_service.monitor_price_changes(
        "test_user_int", test_portfolio, threshold=0.1
    )

    alerts = alert_service.get_alerts_for_user("test_user_int", active_only=True)
    assert len(alerts) == 1
    assert alerts[0].alert_type == "price_gain"
    assert alerts[0].symbol == "AAPL"
    print("Integration Test: Monitoring service successfully triggered price alert.")

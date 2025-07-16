import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from investor_intelligence.services.portfolio_service import PortfolioService
from investor_intelligence.models.portfolio import Portfolio, StockHolding


# Mock the read_spreadsheet_data function from sheets_tool
@patch("investor_intelligence.services.portfolio_service.read_spreadsheet_data")
def test_load_portfolio_from_sheets_success(mock_read_spreadsheet_data):
    mock_read_spreadsheet_data.return_value = [
        ["Stock Symbol", "Quantity", "Purchase Price", "Purchase Date"],
        ["AAPL", "10", "150.00", "2023-01-15"],
        ["MSFT", "5", "250.00", "2023-02-20"],
    ]

    service = PortfolioService("test_sheet_id", "Sheet1!A1:D")
    portfolio = service.load_portfolio_from_sheets("user123", "My Portfolio")

    assert portfolio is not None
    assert portfolio.user_id == "user123"
    assert portfolio.name == "My Portfolio"
    assert len(portfolio.holdings) == 2
    assert portfolio.holdings[0].symbol == "AAPL"
    assert portfolio.holdings[1].quantity == 5


@patch("investor_intelligence.services.portfolio_service.read_spreadsheet_data")
def test_load_portfolio_from_sheets_empty(mock_read_spreadsheet_data):
    mock_read_spreadsheet_data.return_value = []

    service = PortfolioService("test_sheet_id", "Sheet1!A1:D")
    portfolio = service.load_portfolio_from_sheets("user123", "My Portfolio")

    assert portfolio is None


@patch("investor_intelligence.services.portfolio_service.read_spreadsheet_data")
def test_load_portfolio_from_sheets_invalid_data(mock_read_spreadsheet_data):
    mock_read_spreadsheet_data.return_value = [
        ["Stock Symbol", "Quantity", "Purchase Price", "Purchase Date"],
        ["AAPL", "invalid_qty", "150.00", "2023-01-15"],
    ]

    service = PortfolioService("test_sheet_id", "Sheet1!A1:D")
    portfolio = service.load_portfolio_from_sheets("user123", "My Portfolio")

    assert (
        portfolio is not None
    )  # It should still create a portfolio, but with no valid holdings
    assert len(portfolio.holdings) == 0


def test_add_holding_to_portfolio():
    portfolio = Portfolio(user_id="user1", name="Test")
    service = PortfolioService("", "")  # Dummy values, not used for this test
    service._portfolio = portfolio  # Directly set the internal portfolio for testing

    holding = StockHolding("GOOG", 10, 100.0, date(2023, 1, 1))
    service.add_holding_to_portfolio(holding)
    assert len(portfolio.holdings) == 1
    assert portfolio.holdings[0].symbol == "GOOG"


def test_remove_holding_from_portfolio():
    portfolio = Portfolio(
        user_id="user1",
        name="Test",
        holdings=[
            StockHolding("GOOG", 10, 100.0, date(2023, 1, 1)),
            StockHolding("AAPL", 5, 150.0, date(2023, 2, 1)),
        ],
    )
    service = PortfolioService("", "")
    service._portfolio = portfolio

    removed = service.remove_holding_from_portfolio("GOOG")
    assert removed is True
    assert len(portfolio.holdings) == 1
    assert portfolio.holdings[0].symbol == "AAPL"

    removed_non_existent = service.remove_holding_from_portfolio("XYZ")
    assert removed_non_existent is False
    assert len(portfolio.holdings) == 1

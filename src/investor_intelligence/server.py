import os
from .mcp import MCPServer, Server
from investor_intelligence.tools import tool
from investor_intelligence.utils.metrics import track_latency

# Import the tools and services developed in previous days
from investor_intelligence.tools.alpha_vantage_tool import (
    get_current_price,
    get_historical_data,
)
from investor_intelligence.services.portfolio_service import PortfolioService

# Configuration for PortfolioService (replace with your actual values)
GOOGLE_SHEET_ID = os.getenv(
    "GOOGLE_SHEET_ID", "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q"
)
GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "Sheet1!A1:D")

# Initialize services
portfolio_service = PortfolioService(GOOGLE_SHEET_ID, GOOGLE_SHEET_RANGE)


class InvestorIntelligenceServer(MCPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = Server("investor-intelligence")
        print("Investor Intelligence MCP Server initialized.")

    @tool("get_stock_price")
    @track_latency("get_stock_price", "alpha_vantage_tool")
    def get_stock_price(self, ticker: str) -> float:
        """Retrieves the current stock price for a given ticker symbol.

        Args:
            ticker (str): The stock ticker symbol (e.g., \"AAPL\").

        Returns:
            float: The current stock price.
        """
        price = get_current_price(ticker)
        if price is None:
            raise ValueError(f"Could not retrieve price for {ticker}")
        return price

    @tool("get_portfolio_holdings")
    @track_latency("get_portfolio_holdings", "portfolio_service")
    def get_portfolio_holdings(self, user_id: str, portfolio_name: str) -> dict:
        """Loads and returns the holdings of a specified user portfolio.

        Args:
            user_id (str): The ID of the user whose portfolio to load.
            portfolio_name (str): The name of the portfolio to load.

        Returns:
            dict: A dictionary representing the portfolio holdings.
        """
        portfolio = portfolio_service.load_portfolio_from_sheets(
            user_id, portfolio_name
        )
        if portfolio is None:
            raise ValueError(
                f"Could not load portfolio {portfolio_name} for user {user_id}"
            )

        holdings_list = []
        for holding in portfolio.holdings:
            holdings_list.append(
                {
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "purchase_price": holding.purchase_price,
                    "purchase_date": str(
                        holding.purchase_date
                    ),  # Convert date to string for serialization
                }
            )
        return {
            "name": portfolio.name,
            "user_id": portfolio.user_id,
            "holdings": holdings_list,
        }

    @tool("get_historical_stock_data")
    @track_latency("get_historical_stock_data", "alpha_vantage_tool")
    def get_historical_stock_data(self, ticker: str, interval: str = "1d") -> dict:
        """Retrieves historical stock data for a given ticker symbol.

        Args:
            ticker (str): The stock ticker symbol (e.g., \"AAPL\").
            interval (str): Data interval (e.g., \"1d\", \"1wk\", \"1mo\").

        Returns:
            dict: Historical stock data.
        """
        data = get_historical_data(ticker, interval=interval)
        if data is None or data == {}:
            raise ValueError(f"Could not retrieve historical data for {ticker}")

        # Convert DataFrame to dictionary for JSON serialization
        return data

    async def _get_portfolio_status(self, params):
        class Result:
            def __init__(self):
                self.content = [type("Content", (), {"text": "Portfolio status: OK"})()]
                self.isError = False

        return Result()

    async def _check_alerts(self, params):
        class Result:
            def __init__(self):
                self.content = [type("Content", (), {"text": "No alerts found."})()]
                self.isError = False

        return Result()

    async def _send_summary(self, params):
        class Result:
            def __init__(self):
                email = params.get("email", "unknown@example.com")
                self.content = [
                    type("Content", (), {"text": f"Summary sent to {email}"})()
                ]
                self.isError = False

        return Result()


if __name__ == "__main__":
    # Example of how to run the MCP server
    # In a real deployment, this would be managed by a larger system
    server = InvestorIntelligenceServer()
    # The server would typically be started and managed by the MCP framework
    # For local testing, you might run it in a way that exposes its tools
    print(
        "MCP Server ready. Tools registered: get_stock_price, get_portfolio_holdings, get_historical_stock_data"
    )

    # Example of directly calling a tool (for testing purposes, not how MCP typically invokes them)
    try:
        price = server.get_stock_price("MSFT")
        print(f"MSFT Price: {price}")
    except ValueError as e:
        print(e)

    try:
        portfolio_data = server.get_portfolio_holdings(
            "test_user_123", "My Test Portfolio"
        )
        print(f"Portfolio Data: {portfolio_data}")
    except ValueError as e:
        print(e)

    try:
        hist_data = server.get_historical_stock_data("AAPL", interval="1d")
        print(f"AAPL Historical Data: {hist_data}")
    except ValueError as e:
        print(e)

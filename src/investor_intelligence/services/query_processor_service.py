from investor_intelligence.services.nlp_service import NLPService
from investor_intelligence.services.portfolio_service import PortfolioService
from investor_intelligence.services.monitoring_service import MonitoringService
from investor_intelligence.tools.alpha_vantage_tool import (
    get_quote_endpoint,
    get_earnings_calendar,
)
from investor_intelligence.tools.news_tool import get_news_articles
from investor_intelligence.models.portfolio import Portfolio


class QueryProcessorService:
    """Service for processing user queries and generating contextual responses."""

    def __init__(
        self,
        nlp_service: NLPService,
        portfolio_service: PortfolioService,
        monitoring_service: MonitoringService,
    ):
        self.nlp_service = nlp_service
        self.portfolio_service = portfolio_service
        self.monitoring_service = monitoring_service

    def process_email_query(
        self, user_id: str, user_email: str, query_text: str
    ) -> str:
        """Processes an email query and generates a response.

        Args:
            user_id (str): The ID of the user sending the query.
            user_email (str): The email of the user sending the query.
            query_text (str): The text content of the user's email query.

        Returns:
            str: The generated response to the user's query.
        """
        symbols = self.nlp_service.extract_stock_symbols(query_text)
        query_type = self.nlp_service.identify_query_type(query_text)

        response_lines = []

        if query_type == "price_query":
            if symbols:
                response_lines.append(
                    "Here are the current prices for your requested symbols:\n"
                )
                for symbol in symbols:
                    quote = get_quote_endpoint(symbol)
                    if quote:
                        response_lines.append(
                            f"- {symbol}: Current Price: ${float(quote['05. price']):.2f}, Volume: {quote['06. volume']}\n"
                        )
                    else:
                        response_lines.append(
                            f"- Could not retrieve price for {symbol}.\n"
                        )
            else:
                response_lines.append(
                    'Please specify a stock symbol for price queries (e.g., "What is AAPL price?").\n'
                )

        elif query_type == "earnings_query":
            if symbols:
                response_lines.append(
                    "Here is the earnings calendar information for your requested symbols:\n"
                )
                for symbol in symbols:
                    earnings_data = get_earnings_calendar(
                        horizon="3month", symbol=symbol
                    )
                    if earnings_data:
                        found_earnings = False
                        for event in earnings_data:
                            if event.get("symbol", "").upper() == symbol.upper():
                                response_lines.append(
                                    f"- {symbol}: Report Date: {event.get('reportDate')}, Fiscal Date Ending: {event.get('fiscalDateEnding')}\n"
                                )
                                found_earnings = True
                                break
                        if not found_earnings:
                            response_lines.append(
                                f"- No upcoming earnings found for {symbol} in the next 3 months.\n"
                            )
                    else:
                        response_lines.append(
                            f"- Could not retrieve earnings data for {symbol}.\n"
                        )
            else:
                response_lines.append(
                    'Please specify a stock symbol for earnings queries (e.g., "When is IBM earnings?").\n'
                )

        elif query_type == "news_query":
            if symbols:
                response_lines.append(
                    "Here are the latest news headlines for your requested symbols:\n"
                )
                for symbol in symbols:
                    articles = get_news_articles(symbol, page_size=3)
                    if articles:
                        for article in articles:
                            response_lines.append(
                                f"- {symbol}: {article.get('title')} (Source: {article.get('source', {}).get('name')})\n"
                            )
                            response_lines.append(f"  URL: {article.get('url')}\n")
                    else:
                        response_lines.append(f"- No recent news found for {symbol}.\n")
            else:
                response_lines.append(
                    'Please specify a stock symbol for news queries (e.g., "Latest news on TSLA?").\n'
                )

        elif query_type == "portfolio_query":
            # Assuming a way to map user_id to their portfolio
            # For this example, we'll use a dummy portfolio or load from a predefined sheet
            # In a real system, you'd fetch the user's actual portfolio
            # For demonstration, let's assume a portfolio can be loaded by user_id

            # IMPORTANT: You need to pass the correct spreadsheet_id and range_name
            # for the user's portfolio. This example uses placeholders.
            # You might need a user management system to store this mapping.
            dummy_portfolio = Portfolio(
                user_id=user_id,
                name="User Portfolio",
                holdings=[],  # This would be loaded from sheets
            )
            # Attempt to load the actual portfolio for the user
            # This part needs to be adapted based on how you manage user portfolios
            # For now, let's assume a simple case where we load a known portfolio

            # Example: If you have a single default portfolio for a user
            # Replace with actual logic to retrieve user's portfolio config
            portfolio_config = {
                "spreadsheet_id": "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q",
                "range_name": "Sheet1!A1:D",
            }
            if (
                portfolio_config["spreadsheet_id"]
                != "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q"
            ):
                loaded_portfolio = self.portfolio_service.load_portfolio_from_sheets(
                    user_id, dummy_portfolio.name
                )
                if loaded_portfolio and loaded_portfolio.holdings:
                    response_lines.append(f"Your current portfolio holdings:\n")
                    for holding in loaded_portfolio.holdings:
                        response_lines.append(
                            f"- {holding.symbol}: Quantity {holding.quantity}, Purchase Price ${holding.purchase_price:.2f}\n"
                        )
                else:
                    response_lines.append(
                        "No holdings found in your portfolio. Please ensure your Google Sheet ID is correctly configured and contains data.\n"
                    )
            else:
                response_lines.append(
                    "Portfolio configuration not set up. Please configure your Google Sheet ID for portfolio queries.\n"
                )

        else:  # query_type == "unknown"
            response_lines.append(
                "I'm sorry, I didn't understand your query. Please ask about stock prices, earnings, news, or your portfolio.\n"
            )

        return "".join(response_lines)


if __name__ == "__main__":
    # Example Usage:
    # Initialize services (assuming they are properly set up)
    nlp_service = NLPService()

    # Dummy portfolio service for testing query processor
    class MockPortfolioService:
        def load_portfolio_from_sheets(self, user_id, portfolio_name):
            if user_id == "test_user_query":
                return Portfolio(
                    user_id="test_user_query",
                    name="Test Query Portfolio",
                    holdings=[
                        StockHolding(
                            symbol="AAPL",
                            quantity=10,
                            purchase_price=150.0,
                            purchase_date=date.today(),
                        ),
                        StockHolding(
                            symbol="MSFT",
                            quantity=5,
                            purchase_price=300.0,
                            purchase_date=date.today(),
                        ),
                    ],
                )
            return None

    class MockMonitoringService:
        def __init__(self, alert_service):
            pass  # Not used in this test

    mock_portfolio_service = MockPortfolioService()
    mock_monitoring_service = MockMonitoringService(
        None
    )  # Pass None for alert_service as it's not used here

    query_processor = QueryProcessorService(
        nlp_service, mock_portfolio_service, mock_monitoring_service
    )

    user_id = "test_user_query"
    user_email = "test@example.com"

    print("\n--- Testing Price Query ---")
    response = query_processor.process_email_query(
        user_id, user_email, "What is the price of AAPL and MSFT?"
    )
    print(response)

    print("\n--- Testing Earnings Query ---")
    response = query_processor.process_email_query(
        user_id, user_email, "When are the earnings for IBM?"
    )
    print(response)

    print("\n--- Testing News Query ---")
    response = query_processor.process_email_query(
        user_id, user_email, "Latest news on GOOG?"
    )
    print(response)

    print("\n--- Testing Portfolio Query ---")
    response = query_processor.process_email_query(
        user_id, user_email, "Show me my portfolio."
    )
    print(response)

    print("\n--- Testing Unknown Query ---")
    response = query_processor.process_email_query(
        user_id, user_email, "Tell me a joke."
    )
    print(response)

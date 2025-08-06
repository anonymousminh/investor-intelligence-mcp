from typing import List, Optional
from datetime import date, datetime

from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.tools.sheets_tool import (
    read_spreadsheet_data,
    get_sheets_service,
)
from investor_intelligence.utils.metrics import track_latency


class PortfolioService:
    """Manages user portfolios, including loading from Google Sheets."""

    def __init__(self, spreadsheet_id: str, range_name: str):
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self._portfolio: Optional[Portfolio] = None

    @track_latency("load_portfolio_from_sheets", "portfolio_service")
    def load_portfolio_from_sheets(
        self, user_id: str, portfolio_name: str
    ) -> Optional[Portfolio]:
        """Loads portfolio data from Google Sheets.

        Assumes the Google Sheet has columns: Stock Symbol, Quantity, Purchase Price, Purchase Date
        """
        print(
            f"Attempting to load portfolio for user {user_id} from spreadsheet {self.spreadsheet_id}..."
        )
        try:
            sheet_data = read_spreadsheet_data(self.spreadsheet_id, self.range_name)
            if not sheet_data:
                print("No data found in the specified Google Sheet range.")
                return None

            # Assuming the first row is headers, skip it
            headers = sheet_data[0]
            data_rows = sheet_data[1:]

            holdings: List[StockHolding] = []
            for row in data_rows:
                try:
                    # Basic validation and type conversion
                    symbol = str(row[0]).strip()
                    quantity = int(row[1])
                    purchase_price = float(row[2])
                    # Parse date in YYYY-MM-DD format
                    purchase_date = datetime.strptime(
                        str(row[3]).strip(), "%Y-%m-%d"
                    ).date()

                    holding = StockHolding(
                        symbol=symbol,
                        quantity=quantity,
                        purchase_price=purchase_price,
                        purchase_date=purchase_date,
                    )
                    holdings.append(holding)
                except (ValueError, IndexError) as e:
                    print(f"Skipping invalid row: {row}. Error: {e}")
                    continue

            self._portfolio = Portfolio(
                user_id=user_id, name=portfolio_name, holdings=holdings
            )
            print(
                f"Successfully loaded portfolio for user {user_id} with {len(holdings)} holdings."
            )
            return self._portfolio

        except Exception as e:
            print(f"Error loading portfolio from Google Sheets: {e}")
            self._portfolio = None
            return None

    def get_portfolio(self) -> Optional[Portfolio]:
        """Returns the currently loaded portfolio."""
        return self._portfolio

    def add_holding_to_portfolio(self, holding: StockHolding):
        """Adds a new holding to the current portfolio.
        Requires a portfolio to be loaded first.
        """
        if self._portfolio:
            self._portfolio.add_holding(holding)
            print(f"Added holding {holding.symbol} to portfolio.")
        else:
            print("No portfolio loaded. Cannot add holding.")

    def remove_holding_from_portfolio(self, symbol: str) -> bool:
        """Removes holdings for a given symbol from the current portfolio.
        Requires a portfolio to be loaded first.
        """
        if self._portfolio:
            if self._portfolio.remove_holding(symbol):
                print(f"Removed holdings for {symbol} from portfolio.")
                return True
            else:
                print(f"No holdings found for {symbol} to remove.")
                return False
        else:
            print("No portfolio loaded. Cannot remove holding.")
            return False

    def save_portfolio_to_sheets(self):
        """
        Saves the current portfolio holdings back to the Google Sheet.
        """
        if not self._portfolio:
            print("No portfolio loaded. Cannot save.")
            return False

        service = get_sheets_service()
        sheet = service.spreadsheets()

        # Prepare data: header + holdings
        data = [["Stock Symbol", "Quantity", "Purchase Price", "Purchase Date"]]
        for holding in self._portfolio.holdings:
            data.append(
                [
                    holding.symbol,
                    holding.quantity,
                    holding.purchase_price,
                    holding.purchase_date.strftime("%Y-%m-%d"),
                ]
            )

        body = {"values": data}

        result = (
            sheet.values()
            .update(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )

        print(f"{result.get('updatedCells')} cells updated in Google Sheet.")
        return True


if __name__ == "__main__":
    # IMPORTANT: Replace with your actual Google Sheet ID and range
    # This should be the same sheet you used for testing Day 2
    SAMPLE_SPREADSHEET_ID = "16Bi8WR-mn5ggPZsGmu3Yr3XAg_S7LaZqDhdy2D6x35Q"
    SAMPLE_RANGE_NAME = "Sheet1!A1:D"

    # Initialize the service
    portfolio_service = PortfolioService(SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)

    # Load a portfolio
    user_id = "test_user_123"
    portfolio_name = "My Test Portfolio"
    loaded_portfolio = portfolio_service.load_portfolio_from_sheets(
        user_id, portfolio_name
    )

    if loaded_portfolio:
        print(
            f"\nLoaded Portfolio: {loaded_portfolio.name} for User: {loaded_portfolio.user_id}"
        )
        print("Holdings:")
        for holding in loaded_portfolio.holdings:
            print(
                f"  - {holding.symbol}: {holding.quantity} shares at ${holding.purchase_price} on {holding.purchase_date}"
            )

        # Test adding a new holding
        new_holding = StockHolding("GOOG", 5, 120.50, date(2024, 1, 15))
        portfolio_service.add_holding_to_portfolio(new_holding)
        print(
            f"\nPortfolio after adding GOOG: {portfolio_service.get_portfolio().holdings}"
        )

        # Test removing a holding
        portfolio_service.remove_holding_from_portfolio("AAPL")
        print(
            f"\nPortfolio after removing AAPL: {portfolio_service.get_portfolio().holdings}"
        )

        # Test getting a specific holding
        msft_holding = portfolio_service.get_portfolio().get_holding("MSFT")
        if msft_holding:
            print(f"\nFound MSFT holding: {msft_holding.quantity} shares")

        # Test total quantity for a symbol
        total_aapl = portfolio_service.get_portfolio().total_quantity("AAPL")
        print(f"\nTotal AAPL quantity: {total_aapl}")

    else:
        print("Failed to load portfolio.")

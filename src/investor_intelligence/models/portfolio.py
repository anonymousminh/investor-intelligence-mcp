from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class StockHolding:
    """Represents a single stock holding within a portfolio."""

    symbol: str
    quantity: int
    purchase_price: float
    purchase_date: date

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("Stock symbol must be a non-empty string.")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        if (
            not isinstance(self.purchase_price, (int, float))
            or self.purchase_price <= 0
        ):
            raise ValueError("Purchase price must be a positive number.")
        if not isinstance(self.purchase_date, date):
            raise ValueError("Purchase date must be a valid date object.")


@dataclass
class Portfolio:
    """Represents a user's stock portfolio."""

    user_id: str
    name: str
    holdings: List[StockHolding] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.user_id, str) or not self.user_id:
            raise ValueError("User ID must be a non-empty string.")
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Portfolio name must be a non-empty string.")
        if not isinstance(self.holdings, list):
            raise ValueError("Holdings must be a list.")
        for holding in self.holdings:
            if not isinstance(holding, StockHolding):
                raise TypeError("All holdings must be StockHolding instances.")

    def add_holding(self, holding: StockHolding):
        """Adds a stock holding to the portfolio."""
        if not isinstance(holding, StockHolding):
            raise TypeError("Holding must be a StockHolding instance.")
        self.holdings.append(holding)

    def remove_holding(self, symbol: str):
        """Removes all holdings for a given stock symbol from the portfolio."""
        initial_len = len(self.holdings)
        self.holdings = [h for h in self.holdings if h.symbol.upper() != symbol.upper()]
        return initial_len > len(self.holdings)

    def get_holding(self, symbol: str) -> Optional[StockHolding]:
        """Returns the first holding for a given stock symbol, if found."""
        for holding in self.holdings:
            if holding.symbol.upper() == symbol.upper():
                return holding
        return None

    def total_quantity(self, symbol: str) -> int:
        """Calculates the total quantity held for a given stock symbol."""
        return sum(
            h.quantity for h in self.holdings if h.symbol.upper() == symbol.upper()
        )

from typing import List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from investor_intelligence.models.portfolio import Portfolio, StockHolding
from investor_intelligence.tools.alpha_vantage_tool import (
    get_time_series_data,
    get_quote_endpoint,
)

import yfinance as yf
from investor_intelligence.services.user_config_service import UserConfigService
from investor_intelligence.services.alert_service import AlertService


class AnalyticsService:
    """Service for performing portfolio analytics."""

    def __init__(self):
        self.alert_service = AlertService()

    def calculate_portfolio_performance(self, portfolio: Portfolio) -> dict:
        """Calculates key performance metrics for the given portfolio.

        Args:
            portfolio (Portfolio): The portfolio to analyze.

        Returns:
            dict: A dictionary containing performance metrics.
        """
        total_current_value = 0.0
        total_purchase_value = 0.0

        # To calculate daily returns, we need a common date range for all holdings
        # For simplicity, let's just calculate total return for now.
        # A more robust solution would involve fetching historical data for all stocks
        # and aligning their dates.

        for holding in portfolio.holdings:
            current_price_data = get_quote_endpoint(holding.symbol)
            if current_price_data:
                current_price = float(current_price_data["05. price"])
                total_current_value += current_price * holding.quantity
            total_purchase_value += holding.purchase_price * holding.quantity

        total_return = total_current_value - total_purchase_value
        percentage_return = (
            (total_return / total_purchase_value) * 100
            if total_purchase_value > 0
            else 0.0
        )

        return {
            "total_current_value": total_current_value,
            "total_purchase_value": total_purchase_value,
            "total_return": total_return,
            "percentage_return": percentage_return,
        }

    def calculate_daily_returns(self, portfolio: Portfolio) -> pd.DataFrame:
        """Calculates daily returns for each holding in the portfolio.

        Returns:
            pd.DataFrame: DataFrame with daily returns for each stock.
        """
        all_daily_prices = {}
        for holding in portfolio.holdings:
            daily_data = get_time_series_data(holding.symbol)
            if daily_data:
                # Convert to DataFrame and get '4. close' prices
                df = pd.DataFrame.from_dict(daily_data, orient="index")
                df.index = pd.to_datetime(df.index)
                all_daily_prices[holding.symbol] = df["4. close"].astype(float)

        if not all_daily_prices:
            return pd.DataFrame()

        # Combine all prices into a single DataFrame
        prices_df = pd.DataFrame(all_daily_prices)
        prices_df = prices_df.sort_index()

        # Calculate daily returns
        daily_returns = prices_df.pct_change().dropna()
        return daily_returns

    def calculate_portfolio_daily_returns(self, portfolio: Portfolio) -> pd.Series:
        """Calculates the daily returns of the entire portfolio.

        This assumes equal weighting for simplicity. For weighted returns,
        you would need to factor in the quantity and initial value of each holding.
        """
        daily_returns_per_stock = self.calculate_daily_returns(portfolio)
        if daily_returns_per_stock.empty:
            return pd.Series()

        # Simple average of daily returns for each stock for portfolio return
        # For a more accurate portfolio return, you'd need to weight by value.
        portfolio_daily_returns = daily_returns_per_stock.mean(axis=1)
        return portfolio_daily_returns

    def calculate_annualized_return(self, portfolio_daily_returns: pd.Series) -> float:
        """Calculates the annualized return from daily portfolio returns.

        Args:
            portfolio_daily_returns (pd.Series): Daily returns of the portfolio.

        Returns:
            float: Annualized return percentage.
        """
        if portfolio_daily_returns.empty:
            return 0.0

        # Assuming 252 trading days in a year
        annualized_return = ((1 + portfolio_daily_returns.mean()) ** 252 - 1) * 100
        return annualized_return

    def calculate_volatility(self, portfolio_daily_returns: pd.Series) -> float:
        """Calculates the annualized volatility (standard deviation) of portfolio returns.

        Args:
            portfolio_daily_returns (pd.Series): Daily returns of the portfolio.

        Returns:
            float: Annualized volatility percentage.
        """
        if portfolio_daily_returns.empty:
            return 0.0

        # Assuming 252 trading days in a year
        annualized_volatility = portfolio_daily_returns.std() * np.sqrt(252) * 100
        return annualized_volatility

    def calculate_beta(self, stock_symbol: str, market_symbol: str = "SPY") -> float:
        """Calculates the Beta of a stock relative to a market index.

        Args:
            stock_symbol (str): The stock ticker symbol.
            market_symbol (str): The market index symbol (default: SPY for S&P 500 ETF).

        Returns:
            float: The Beta value, or None if data is insufficient.
        """
        stock_daily_data = get_time_series_data(stock_symbol, outputsize="full")
        market_daily_data = get_time_series_data(market_symbol, outputsize="full")

        if not stock_daily_data or not market_daily_data:
            return None

        stock_df = pd.DataFrame.from_dict(stock_daily_data, orient="index")
        market_df = pd.DataFrame.from_dict(market_daily_data, orient="index")

        stock_df.index = pd.to_datetime(stock_df.index)
        market_df.index = pd.to_datetime(market_df.index)

        stock_returns = stock_df["4. close"].astype(float).pct_change().dropna()
        market_returns = market_df["4. close"].astype(float).pct_change().dropna()

        # Align the dataframes by date
        combined_returns = pd.DataFrame(
            {"stock": stock_returns, "market": market_returns}
        ).dropna()

        if len(combined_returns) < 2:
            return None  # Not enough data to calculate covariance

        covariance = combined_returns["stock"].cov(combined_returns["market"])
        market_variance = combined_returns["market"].var()

        if market_variance == 0:
            return None  # Avoid division by zero

        beta = covariance / market_variance
        return beta

    def analyze_diversification(self, portfolio: Portfolio) -> dict:
        """Analyzes the diversification of the portfolio.

        Args:
            portfolio (Portfolio): The portfolio to analyze.

        Returns:
            dict: A dictionary containing diversification insights.
        """
        sectors = {}
        # This is a simplified example. In a real application, you'd need
        # a mapping from stock symbol to sector/industry.
        # For demonstration, let's assume some sectors.
        # You might need to integrate with a financial data provider that offers sector data.
        sector_mapping = {
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOG": "Technology",
            "JPM": "Financials",
            "GS": "Financials",
            "XOM": "Energy",
            "CVX": "Energy",
            "PFE": "Healthcare",
            "JNJ": "Healthcare",
        }

        for holding in portfolio.holdings:
            sector = sector_mapping.get(holding.symbol.upper(), "Other")
            sectors[sector] = sectors.get(sector, 0) + (
                holding.quantity * holding.purchase_price
            )  # Using purchase value for simplicity

        total_portfolio_value = sum(sectors.values())
        sector_distribution = (
            {
                sector: (value / total_portfolio_value) * 100
                for sector, value in sectors.items()
            }
            if total_portfolio_value > 0
            else {}
        )

        num_holdings = len(portfolio.holdings)
        # Simple diversification score: higher score for more holdings and even distribution
        diversification_score = num_holdings * (
            1
            - (
                np.std(list(sector_distribution.values())) / 100
                if sector_distribution
                else 0
            )
        )

        return {
            "sector_distribution": sector_distribution,
            "num_holdings": num_holdings,
            "diversification_score": diversification_score,
        }

    def get_optimization_suggestions(
        self, portfolio: Portfolio, user_id: str = None, portfolio_id: str = None
    ) -> List[str]:
        """Provides basic portfolio optimization suggestions based on diversification and user risk profile.

        Args:
            portfolio (Portfolio): The portfolio to analyze.
            user_id (str, optional): The user ID to fetch risk profile from config.
            portfolio_id (str, optional): The portfolio ID for portfolio-specific config.

        Returns:
            List[str]: A list of optimization suggestions.
        """
        suggestions = []
        diversification_analysis = self.analyze_diversification(portfolio)
        sector_distribution = diversification_analysis["sector_distribution"]

        # Fetch user risk profile if user_id is provided
        risk_profile = "moderate"
        if user_id is not None:
            user_config_service = UserConfigService()
            config = user_config_service.get_user_config(user_id, portfolio_id)
            risk_profile = config.get("risk_profile", "moderate")

        if not sector_distribution:
            suggestions.append(
                "Add more holdings to your portfolio to begin diversification analysis."
            )
            return suggestions

        # Identify over-concentrated sectors
        for sector, percentage in sector_distribution.items():
            if percentage > 50:  # Arbitrary threshold for over-concentration
                if risk_profile == "conservative":
                    suggestions.append(
                        f"As a conservative investor, consider reducing exposure to the {sector} sector, which accounts for {percentage:.2f}% of your portfolio. Diversification can help reduce risk."
                    )
                elif risk_profile == "aggressive":
                    suggestions.append(
                        f"As an aggressive investor, high concentration in {sector} ({percentage:.2f}%) may align with your risk tolerance, but be aware of potential volatility."
                    )
                else:
                    suggestions.append(
                        f"Consider reducing exposure to the {sector} sector, which accounts for {percentage:.2f}% of your portfolio."
                    )

        # Suggest further diversification if score is low
        if (
            diversification_analysis["diversification_score"] < 5
        ):  # Arbitrary low score threshold
            if risk_profile == "conservative":
                suggestions.append(
                    "As a conservative investor, your portfolio could benefit from further diversification across stable sectors or asset classes."
                )
                suggestions.append(
                    "Explore adding holdings in sectors like Healthcare, Utilities, or Consumer Staples for lower volatility."
                )
            elif risk_profile == "aggressive":
                suggestions.append(
                    "As an aggressive investor, you may seek higher returns with concentrated positions, but diversification can still help manage downside risk."
                )
                suggestions.append(
                    "Consider balancing high-growth sectors with some defensive holdings to mitigate risk."
                )
            else:
                suggestions.append(
                    "Your portfolio could benefit from further diversification across different sectors or asset classes."
                )
                suggestions.append(
                    "Explore adding holdings in sectors like Healthcare, Energy, or Financials if you are currently concentrated in Technology."
                )

        if not suggestions:
            if risk_profile == "conservative":
                suggestions.append(
                    "Your portfolio appears reasonably diversified for a conservative risk profile. Continue to monitor and rebalance as needed."
                )
            elif risk_profile == "aggressive":
                suggestions.append(
                    "Your portfolio appears reasonably diversified for an aggressive risk profile. Continue to monitor and rebalance as needed."
                )
            else:
                suggestions.append(
                    "Your portfolio appears reasonably diversified based on current analysis. Continue to monitor and rebalance as needed."
                )

        return suggestions

    def get_alert_effectiveness_metrics(self, user_id: Portfolio) -> dict:
        """Calculates metrics for alert effectiveness.

        Args:
            user_id (str, optional): Filter metrics for a specific user. Defaults to None (all users).

        Returns:
            dict: A dictionary containing alert effectiveness metrics.
        """
        all_alerts = (
            self.alert_service.get_alerts_for_user(user_id, active_only=False)
            if user_id
            else self.alert_service.get_all_alerts(active_only=False)
        )  # Need a get_all_alerts method in AlertService

        # Average Relevance Score
        avg_relevance_score = (
            sum(alert.relevance_score for alert in all_alerts) / total_alerts
        )

        # Feedback Distribution
        feedback_counts = {"relevant": 0, "irrelevant": 0, "null": 0}
        for alert in all_alerts:
            feedback_counts[alert.feedback if alert.feedback else "null"] += 1

        feedback_distribution = {
            k: (v / total_alerts) * 100 for k, v in feedback_counts.items()
        }

        return {
            "total_alerts": total_alerts,
            "avg_relevance_score": avg_relevance_score,
            "feedback_distribution": feedback_distribution,
        }

    def get_all_alerts(self, active_only: bool = True) -> List[Alert]:
        conn = self.alert_service._get_db_connection()
        cursor = conn.cursor()
        query = "SELECT id, user_id, portfolio_id, alert_type, symbol, message, triggered_at, is_active, relevance_score, feedback FROM alerts"
        if active_only:
            query += " WHERE is_active = 1"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        alerts = []
        for row in rows:
            alerts.append(
                Alert(
                    id=row[0],
                    user_id=row[1],
                    portfolio_id=row[2],
                    alert_type=row[3],
                    symbol=row[4],
                    message=row[5],
                    triggered_at=datetime.fromisoformat(row[6]),
                    is_active=bool(row[7]),
                    relevance_score=row[8] if row[8] is not None else 0.0,
                    feedback=row[9],
                )
            )
        return alerts


if __name__ == "__main__":
    # Example Usage:
    from investor_intelligence.models.portfolio import Portfolio, StockHolding
    from datetime import date

    analytics_service = AnalyticsService()

    # Create a test portfolio with some holdings
    test_portfolio = Portfolio(
        user_id="test_user_analytics",
        name="Analytics Test Portfolio",
        holdings=[
            StockHolding(
                symbol="AAPL",
                quantity=10,
                purchase_price=150.0,
                purchase_date=date(2024, 1, 1),
            ),
            StockHolding(
                symbol="MSFT",
                quantity=5,
                purchase_price=300.0,
                purchase_date=date(2024, 1, 15),
            ),
            StockHolding(
                symbol="GOOG",
                quantity=8,
                purchase_price=140.0,
                purchase_date=date(2024, 2, 1),
            ),
        ],
    )

    print("\n--- Calculating Portfolio Performance ---")
    performance = analytics_service.calculate_portfolio_performance(test_portfolio)
    print(f"Total Current Value: ${performance['total_current_value']:.2f}")
    print(f"Total Purchase Value: ${performance['total_purchase_value']:.2f}")
    print(f"Total Return: ${performance['total_return']:.2f}")
    print(f"Percentage Return: {performance['percentage_return']:.2f}%")

    print("\n--- Calculating Daily Returns and Annualized Metrics ---")
    portfolio_daily_returns = analytics_service.calculate_portfolio_daily_returns(
        test_portfolio
    )
    if not portfolio_daily_returns.empty:
        print(
            "Portfolio Daily Returns (first 5 rows):\n", portfolio_daily_returns.head()
        )
        annualized_return = analytics_service.calculate_annualized_return(
            portfolio_daily_returns
        )
        annualized_volatility = analytics_service.calculate_volatility(
            portfolio_daily_returns
        )
        print(f"Annualized Return: {annualized_return:.2f}%")
        print(f"Annualized Volatility: {annualized_volatility:.2f}%")
    else:
        print("Could not calculate daily returns (insufficient data).")

    print("\n--- Testing Risk Assessment (Beta) ---")
    # Note: Beta calculation requires sufficient historical data for both stock and market
    # and can be slow due to API calls. Use sparingly for testing.
    # beta_aapl = analytics_service.calculate_beta("AAPL")
    # if beta_aapl is not None:
    #     print(f"AAPL Beta: {beta_aapl:.2f}")
    # else:
    #     print("Could not calculate Beta for AAPL.")

    print("\n--- Testing Diversification Analysis ---")
    diversification_analysis = analytics_service.analyze_diversification(test_portfolio)
    print("Sector Distribution:", diversification_analysis["sector_distribution"])
    print("Number of Holdings:", diversification_analysis["num_holdings"])
    print("Diversification Score:", diversification_analysis["diversification_score"])

    print("\n--- Testing Optimization Suggestions ---")
    optimization_suggestions = analytics_service.get_optimization_suggestions(
        test_portfolio, user_id="test_user_analytics"
    )
    for suggestion in optimization_suggestions:
        print(f"- {suggestion}")

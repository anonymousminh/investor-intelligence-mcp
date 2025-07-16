import os
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import time

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")


def get_stock_info(symbol):
    """
    Retrieve the latest stock information for a given symbol using Alpha Vantage's quote endpoint.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: A dictionary containing the latest stock information fields from Alpha Vantage.
    """
    # Alpha Vantage does not provide company sector/name in free tier, only time series data
    # You can get price and historical data
    data, meta_data = ts.get_quote_endpoint(symbol)
    return data


def get_current_price(symbol):
    """
    Get the latest closing price for a given stock symbol.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        str or None: The latest closing price as a string, or None if not found.
    """
    data = get_stock_info(symbol)
    return data.get("05. price")


def get_historical_data(symbol, interval="1d", outputsize="compact"):
    """
    Retrieve historical price data for a given stock symbol and interval.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').
        interval (str): Data interval ('1d', '1wk', '1mo', or intraday intervals like '5min').
        outputsize (str): 'compact' (default, latest 100 points) or 'full' (full-length data).

    Returns:
        dict: Historical price data indexed by date/time.
    """
    # interval: '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'
    if interval == "1d":
        data, meta_data = ts.get_daily(symbol=symbol, outputsize=outputsize)
    elif interval == "1wk":
        data, meta_data = ts.get_weekly(symbol=symbol)
    elif interval == "1mo":
        data, meta_data = ts.get_monthly(symbol=symbol)
    else:
        data, meta_data = ts.get_intraday(
            symbol=symbol, interval=interval, outputsize=outputsize
        )
    return data


def get_time_series_data(symbol):
    """
    Retrieve daily time series data (compact) for a given stock symbol.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: Daily time series data indexed by date.
    """
    ts_local = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
    data, _ = ts_local.get_daily(symbol=symbol, outputsize="compact")
    return data


def get_intraday_data(symbol, interval="5min"):
    """
    Retrieve intraday time series data for a given stock symbol and interval.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').
        interval (str): Intraday interval (e.g., '1min', '5min', '15min', '30min', '60min').

    Returns:
        dict: Intraday time series data indexed by datetime.
    """
    ts_local = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
    data, _ = ts_local.get_intraday(
        symbol=symbol, interval=interval, outputsize="compact"
    )
    return data


def get_quote_endpoint(symbol):
    """
    Retrieve the latest quote data for a given stock symbol using Alpha Vantage's quote endpoint.

    Args:
        symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: The latest quote data for the symbol.
    """
    ts_local = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
    data, _ = ts_local.get_quote_endpoint(symbol=symbol)
    return data


if __name__ == "__main__":
    symbol = "MSFT"
    info = get_stock_info(symbol)
    print(f"\n{symbol} Info: {info}")

    price = get_current_price(symbol)
    print(f"{symbol} Current Price: {price}")

    hist = get_historical_data(symbol, interval="1d")
    print(f"\n{symbol} Daily Historical Data (compact):")
    for date, values in list(hist.items())[:5]:  # Show first 5 days
        print(date, values)

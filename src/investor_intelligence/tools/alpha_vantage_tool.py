import os
import csv
from io import StringIO
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import time
from alpha_vantage.fundamentaldata import FundamentalData
import requests

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


# def get_earnings_calendar(symbol=None, horizon="3month"):
#     """
#     Fetches earnings calendar data from Alpha Vantage API.

#     Args:
#         symbol (str, optional): Stock ticker symbol. If None, fetches all.
#         horizon (str): '3month', '6month', or '12month'.

#     Returns:
#         dict: Earnings calendar data, or None if error.
#     """
#     url = "https://www.alphavantage.co/query"
#     params = {
#         "function": "EARNINGS_CALENDAR",
#         "apikey": ALPHA_VANTAGE_API_KEY,
#         "horizon": horizon,
#     }
#     if symbol:
#         params["symbol"] = symbol

#     response = requests.get(url, params=params)
#     try:
#         response.raise_for_status()
#         try:
#             data = response.json()
#         except Exception as e:
#             print(f"Error decoding JSON: {e}\nRaw response: {response.text}")
#             return None
#         # Check for Alpha Vantage error messages
#         if any(k in data for k in ("Error Message", "Information", "Note")):
#             print(f"Alpha Vantage API message: {data}")
#             return None
#         return data
#     except Exception as e:
#         print(f"Error fetching earnings calendar: {e}\nRaw response: {response.text}")
#         return None


def get_earnings_calendar(horizon="3month", symbol=None):
    """Fetches earnings calendar data directly from Alpha Vantage API.

    Note: The Alpha Vantage Earnings Calendar API returns CSV format data.

    Args:
        horizon (str): The reporting horizon ('3month', '6month', '12month').
        symbol (str, optional): The stock ticker symbol. If None, returns full list.

    Returns:
        list: A list of dictionaries, where each dictionary represents an earnings event.
              Each dictionary contains keys like 'symbol', 'reportDate', 'fiscalDateEnding', etc.
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "EARNINGS_CALENDAR",
        "horizon": horizon,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    if symbol:
        params["symbol"] = symbol

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # The earnings calendar API returns CSV data, not JSON
        csv_data = response.text

        # Check if we got an error message instead of CSV data
        if csv_data.startswith('{"Error Message"') or csv_data.startswith('{"Note"'):
            print(f"API Error: {csv_data}")
            return None

        # Parse CSV data
        csv_reader = csv.DictReader(StringIO(csv_data))
        earnings_list = []
        for row in csv_reader:
            earnings_list.append(row)

        return earnings_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching earnings calendar: {e}")
        return None
    except Exception as e:
        print(f"Error parsing earnings calendar data: {e}")
        return None


if __name__ == "__main__":
    # IMPORTANT: Replace "YOUR_ALPHA_VANTAGE_API_KEY" with your actual API key
    # or set it as an environment variable named ALPHA_VANTAGE_API_KEY

    # Example Usage:
    symbol = "IBM"

    print(f"\n--- Fetching daily data for {symbol} ---")
    daily_data = get_time_series_data(symbol)
    if daily_data:
        print("Latest daily data:")
        # For JSON output, daily_data is a dictionary where keys are dates
        # and values are dictionaries of open, high, low, close, volume.
        # We'll print the first item for brevity.
        first_date = list(daily_data.keys())[0]
        print(f"Date: {first_date}, Close: {daily_data[first_date]['4. close']}")

    print(f"\n--- Fetching intraday (5min) data for {symbol} ---")
    intraday_data = get_intraday_data(symbol, interval="5min")
    if intraday_data:
        print("Latest intraday data:")
        # Similar to daily data, intraday_data is a dictionary of time-stamped data.
        first_timestamp = list(intraday_data.keys())[0]
        print(
            f"Timestamp: {first_timestamp}, Close: {intraday_data[first_timestamp]['4. close']}"
        )

    print(f"\n--- Fetching latest quote for {symbol} ---")
    quote_data = get_quote_endpoint(symbol)
    if quote_data:
        print("Latest quote data:")
        print(
            f"Open: {quote_data['02. open']}, High: {quote_data['03. high']}, Low: {quote_data['04. low']}, Price: {quote_data['05. price']}, Volume: {quote_data['06. volume']}"
        )

    print(f"\n--- Fetching earnings calendar (quarterly) ---")
    earnings_calendar = get_earnings_calendar(horizon="3month")
    if earnings_calendar:
        print("First 5 earnings events:")
        # Earnings calendar is a list of dictionaries
        for i, event in enumerate(earnings_calendar[:5]):
            print(
                f"  Symbol: {event.get('symbol')}, Report Date: {event.get('reportDate')}, Fiscal Date Ending: {event.get('fiscalDateEnding')}"
            )
    else:
        print("Could not retrieve earnings calendar data.")

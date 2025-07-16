import os
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
import time

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")


def get_stock_info(symbol):
    # Alpha Vantage does not provide company sector/name in free tier, only time series data
    # You can get price and historical data
    data, meta_data = ts.get_quote_endpoint(symbol)
    return data


def get_current_price(symbol):
    data = get_stock_info(symbol)
    return data.get("05. price")


def get_historical_data(symbol, interval="1d", outputsize="compact"):
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
    ts_local = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
    data, _ = ts_local.get_daily(symbol=symbol, outputsize="compact")
    return data


def get_intraday_data(symbol, interval="5min"):
    ts_local = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
    data, _ = ts_local.get_intraday(
        symbol=symbol, interval=interval, outputsize="compact"
    )
    return data


def get_quote_endpoint(symbol):
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

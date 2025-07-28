import pytest
from unittest.mock import patch, MagicMock
from investor_intelligence.tools.alpha_vantage_tool import (
    get_time_series_data,
    get_intraday_data,
    get_quote_endpoint,
)
from alpha_vantage.timeseries import TimeSeries


# Mock the TimeSeries class from alpha_vantage.timeseries
@patch("investor_intelligence.tools.alpha_vantage_tool.TimeSeries")
def test_get_time_series_data(mock_timeseries):
    get_time_series_data.cache_clear()
    mock_ts_instance = MagicMock()
    mock_timeseries.return_value = mock_ts_instance

    # Configure the mock to return sample data
    mock_ts_instance.get_daily.return_value = (
        {"2023-01-01": {"4. close": "150.00"}},
        {},
    )

    symbol = "TEST"
    data = get_time_series_data(symbol)

    # Check that TimeSeries was called with the correct arguments
    mock_timeseries.assert_called_once()
    call_args = mock_timeseries.call_args
    assert call_args is not None
    assert "key" in call_args.kwargs
    assert call_args.kwargs["output_format"] == "json"

    mock_ts_instance.get_daily.assert_called_once_with(
        symbol=symbol, outputsize="compact"
    )
    assert data == {"2023-01-01": {"4. close": "150.00"}}


@patch("investor_intelligence.tools.alpha_vantage_tool.TimeSeries")
def test_get_intraday_data(mock_timeseries):
    mock_ts_instance = MagicMock()
    mock_timeseries.return_value = mock_ts_instance

    mock_ts_instance.get_intraday.return_value = (
        {"2023-01-01 10:00:00": {"4. close": "150.50"}},
        {},
    )

    symbol = "TEST"
    interval = "5min"
    data = get_intraday_data(symbol, interval=interval)

    # Check that TimeSeries was called with the correct arguments
    mock_timeseries.assert_called_once()
    call_args = mock_timeseries.call_args
    assert call_args is not None
    assert "key" in call_args.kwargs
    assert call_args.kwargs["output_format"] == "json"

    mock_ts_instance.get_intraday.assert_called_once_with(
        symbol=symbol, interval=interval, outputsize="compact"
    )
    assert data == {"2023-01-01 10:00:00": {"4. close": "150.50"}}


@patch("investor_intelligence.tools.alpha_vantage_tool._make_api_call")
def test_get_quote_endpoint(mock_api_call):
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {"Global Quote": {"05. price": "151.00"}}
    mock_api_call.return_value = mock_response

    symbol = "TEST"
    data = get_quote_endpoint(symbol)

    # Check that _make_api_call was called with the correct URL
    mock_api_call.assert_called_once()
    call_args = mock_api_call.call_args
    assert call_args is not None
    assert "function=GLOBAL_QUOTE" in call_args[0][0]  # URL should contain GLOBAL_QUOTE
    assert f"symbol={symbol}" in call_args[0][0]  # URL should contain the symbol

    assert data == {"05. price": "151.00"}

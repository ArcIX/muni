import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path
from muni.providers import YFinanceProvider

@pytest.mark.unit
def test_yfinance_provider_init():
    # SETUP

    # ACTION
    yfinance_provider = YFinanceProvider()

    # ASSERT
    assert isinstance(yfinance_provider.cache_dir, Path)

@patch("muni.providers.yfinance.yf.Ticker")
@pytest.mark.unit
def test_get_data_returns_dataframe(mock_ticker, tmp_path, create_mock_yf_data):
    # SETUP
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-01-31"
    mock_strategy = MagicMock()

    cache_path = tmp_path / "data" / ".cache"
    cache_path.mkdir(parents=True)

    mock_df = create_mock_yf_data(days=31, start=start_date)
    mock_strategy.get_data.return_value = mock_df

    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df

    # ACTION
    yfinance_provider = YFinanceProvider()
    yfinance_provider.cache_dir = cache_path
    results_df = yfinance_provider.get_data(ticker, start_date, end_date, mock_strategy)

    # ASSERT
    mock_ticker.assert_called_once_with(ticker)

    mock_ticker_instance.history.assert_called_once_with(
        start=start_date, end=end_date, auto_adjust=False
    )

    copy_mock_df = mock_df.copy()
    copy_mock_df.reset_index(inplace=True)

    cols = {
        "Date": "trade_date", "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Adj Close": "adj_close", "Volume": "volume"
    }

    for yf_col, target_col in cols.items():
        pd.testing.assert_series_equal(copy_mock_df[yf_col], results_df[target_col], check_names=False)

@patch("muni.providers.yfinance.yf.Ticker") 
@pytest.mark.unit
def test_get_data_caches_results(mock_ticker, tmp_path, create_mock_yf_data):
    # SETUP
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-01-31"
    mock_strategy = MagicMock()

    cache_path = tmp_path / "data" / ".cache"
    cache_path.mkdir(parents=True)

    mock_df = create_mock_yf_data(days=31, start=start_date)
    mock_strategy.get_data.return_value = mock_df

    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df

    # ACTION
    yfinance_provider = YFinanceProvider()
    yfinance_provider.cache_dir = cache_path
    yfinance_provider.get_data(ticker, start_date, end_date, mock_strategy)

    # ASSERT
    save_path = cache_path / (
        f"{ticker}_{start_date}_{end_date}_"
        f"{mock_strategy.__class__.__name__}.parquet"
    )
    assert save_path.exists()

@pytest.mark.unit
def test_align_schema_reconciliation(create_mock_yf_data):
    # SETUP
    ticker = "AAPL"
    start_date = "2020-01-01"

    mock_df = create_mock_yf_data(days=31, start=start_date)

    # ACTION
    yfinance_provider = YFinanceProvider()
    results_df = yfinance_provider._align_schema(mock_df, ticker)

    # ASSERT
    copy_mock_df = mock_df.copy()
    copy_mock_df.reset_index(inplace=True)

    cols = {
        "Date": "trade_date", "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Adj Close": "adj_close", "Volume": "volume"
    }

    for yf_col, target_col in cols.items():
        pd.testing.assert_series_equal(copy_mock_df[yf_col], results_df[target_col], check_names=False)
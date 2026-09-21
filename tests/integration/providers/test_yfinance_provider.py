import pytest
import pandas as pd
from pathlib import Path
import yfinance as yf
from muni.providers import YFinanceProvider
from muni.strategies import SMACrossover, RSIMeanReversion

@pytest.mark.integration
def test_yf_provider_returns_aligned_schema(tmp_path):
    '''
    Test that the yfinance provider returns a dataframe
    with the following column names and data types:
    - trade_date, datetime
    - ticker, object
    - open, float
    - high, float
    - low, float
    - close, float
    - adj_close, float
    - volume, int
    '''
    yf_provider = YFinanceProvider()
    ticker = "AAPL"
    start_date = "2022-01-01"
    end_date = "2022-01-31"
    sma_strat = SMACrossover(fast_window=5, slow_window=20)

    cache_path = tmp_path / "data" / ".cache"
    cache_path.mkdir(parents=True)
    yf_provider.cache_dir = cache_path

    results_df = yf_provider.get_data(ticker, start_date, end_date, sma_strat)

    assert isinstance(results_df, pd.DataFrame)
    assert results_df.columns.to_list() == ["trade_date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    assert results_df["trade_date"].dtype == "datetime64[ns]"
    assert results_df["ticker"].dtype == "object"
    assert results_df["open"].dtype == "float64"
    assert results_df["high"].dtype == "float64"
    assert results_df["low"].dtype == "float64"
    assert results_df["close"].dtype == "float64"
    assert results_df["adj_close"].dtype == "float64"
    assert results_df["volume"].dtype == "int64"
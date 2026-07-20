import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from muni.data_loader import fetch_data
from muni.strategies import BaseStrategy, SMACrossover
from muni.providers import BaseProvider, YFinanceProvider, BigQueryProvider
from muni.engine import BacktestEngine
from main import run_pipeline

@pytest.mark.integration
@patch("main.BigQueryProvider.get_data")
def test_run_pipeline_returns_dataframe(mock_fetch, create_mock_stock_data):
    # SETUP
    ticker = "AAPL"
    start_date = "2022-01-01"
    end_date = "2022-01-31"
    stocks_df = create_mock_stock_data(days=31, start=start_date)
    stocks_df["bq_signal"] = pd.Series(
        np.random.choice(
            [0, 1],
            size=31,
            p=[0.3, 0.7]
        )
    )
    mock_fetch.return_value = stocks_df

    mock_client = MagicMock()
    dataset_name = "test_dataset"

    # ACTION
    sma_strat = SMACrossover(fast_window=5, slow_window=20)
    bq_provider = BigQueryProvider(mock_client, dataset_name)
    results_df = run_pipeline(ticker, start_date, end_date, sma_strat, bq_provider, 10000)

    # ASSERT
    mock_fetch.assert_called_once_with(ticker, start_date, end_date, sma_strat)
    assert isinstance(results_df, pd.DataFrame)

@pytest.mark.integration
@patch("main.BigQueryProvider.get_data")
def test_run_pipeline_handles_empty_data(mock_fetch):
    ticker = "AAPL"
    start_date = "2022-01-01"
    end_date = "2022-01-31"
    stocks_df = pd.DataFrame()
    mock_fetch.return_value = stocks_df

    mock_client = MagicMock()
    dataset_name = "test_dataset"

    # ACTION
    sma_strat = SMACrossover(fast_window=5, slow_window=20)
    bq_provider = BigQueryProvider(mock_client, dataset_name)
    
    with pytest.raises(ValueError, match="No data returned"):
        results_df = run_pipeline(ticker, start_date, end_date, sma_strat, bq_provider, 10000)

@pytest.mark.integration
@patch("main.YFinanceProvider.get_data")
def test_run_pipeline_sma_yf_returns_dataframe(mock_fetch, create_mock_stock_data):
    # SETUP
    ticker = "AAPL"
    start_date = "2022-01-01"
    end_date = "2022-01-31"
    stocks_df = create_mock_stock_data(days=31, start=start_date)
    mock_fetch.return_value = stocks_df

    # ACTION
    sma_strat = SMACrossover(fast_window=5, slow_window=20)
    yf_provider = YFinanceProvider()
    results_df = run_pipeline(ticker, start_date, end_date, sma_strat, yf_provider, 10000)

    # ASSERT
    mock_fetch.assert_called_once_with(ticker, start_date, end_date, sma_strat)
    assert isinstance(results_df, pd.DataFrame)
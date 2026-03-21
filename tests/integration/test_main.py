import pytest
import pandas as pd
from unittest.mock import patch
from muni.data_loader import fetch_data
from muni.strategies import BaseStrategy, SMACrossover
from muni.engine import BacktestEngine
from main import run_pipeline

@pytest.mark.integration
@patch("main.fetch_data")
def test_run_pipeline_returns_dataframe(mock_fetch, create_mock_stock_data):
    # SETUP
    stocks_df = create_mock_stock_data(days=100)
    mock_fetch.return_value = stocks_df

    # ACTION
    sma_strat = SMACrossover(fast_window=5, slow_window=20)
    results_df = run_pipeline("AAPL", sma_strat, 10000)

    # ASSERT
    mock_fetch.assert_called_once_with("AAPL")
    assert isinstance(results_df, pd.DataFrame)
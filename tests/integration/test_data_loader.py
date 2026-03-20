import pytest
import os
import pandas as pd
from muni.data_loader import fetch_data
from unittest.mock import patch

@pytest.mark.integration
@patch("muni.data_loader.yf.download")
def test_fetch_data_creates_parquet(mock_yf_download, tmp_path, create_mock_stock_data):
    ticker = "AAPL"
    save_path = tmp_path / f"{ticker}.parquet"

    # MOCK: Define what yfinance *would* return
    mock_new_data = create_mock_stock_data(days=30, start="2024-01-01")
    mock_yf_download.return_value = mock_new_data

    # EXECUTE: Run the function
    df = fetch_data(ticker, data_dir=str(tmp_path))

    # ASSERT: Verify the logic worked
    assert isinstance(df, pd.DataFrame)
    assert os.path.exists(save_path)
    assert not df.empty

@pytest.mark.integration
@patch("muni.data_loader.yf.download")
def test_fetch_data_incremental_update(mock_yf_download, tmp_path, create_mock_stock_data):
    """
    Test that if a parquet file exists, the loader only fetches 
    dates AFTER the last recorded date and combines them correctly.
    """
    ticker = "AAPL"
    data_dir = str(tmp_path)
    file_path = tmp_path / f"{ticker}.parquet"
    
    # SETUP: Create a fake "existing" Parquet file
    existing_data = create_mock_stock_data(days=3, start="2024-01-01")
    existing_data.to_parquet(file_path)

    # MOCK: Define what yfinance *would* return for the new dates
    mock_new_data = create_mock_stock_data(days=2, start="2024-01-04")
    
    # Tell our mocked yfinance to return this fake new dataframe
    mock_yf_download.return_value = mock_new_data

    # EXECUTE: Run the function
    # We freeze 'today' in our test logic so it doesn't fail if we run this months from now.
    # To keep the test simple without mocking datetime, we just call the function.
    with patch("muni.data_loader.datetime") as mock_datetime:
        # Force 'now' to be Jan 6, so it triggers the fetch for Jan 4 and Jan 5
        mock_datetime.now.return_value = pd.to_datetime("2024-01-06")
        
        result_df = fetch_data(ticker, data_dir=data_dir)
    
    # ASSERT: Verify the logic worked
    
    # Did it ask yfinance for the correct start date? 
    # (Existing ended on Jan 3, so it should ask for Jan 4)
    mock_yf_download.assert_called_once_with(ticker, start="2024-01-04")
    
    # Is the returned dataframe correctly combined? (3 old + 2 new = 5 rows)
    assert len(result_df) == 5
    assert result_df.index[0] == pd.Timestamp("2024-01-01")
    assert result_df.index[-1] == pd.Timestamp("2024-01-05")
    
    # Was the parquet file actually overwritten with the combined data?
    saved_df = pd.read_parquet(file_path)
    assert len(saved_df) == 5
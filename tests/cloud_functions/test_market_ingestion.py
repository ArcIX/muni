import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import io
from datetime import datetime, timedelta
from google.api_core.exceptions import Forbidden
from cloud_functions.market_ingestion.main import ingest_market_data

def test_ingest_valid_ticker(create_mock_stock_data):
    """
    Test that a valid ticker request triggers a fetch and a storage upload.
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    mock_request = MagicMock()
    mock_request.get_json.return_value = {"ticker": "AAPL"}
    mock_request.args = {}
    
    # Create a dummy DataFrame to simulate yfinance data
    mock_df = create_mock_stock_data(days=2)
    
    # Mocking the external dependencies
    with (
        patch('yfinance.Ticker') as mock_ticker,
        patch('google.cloud.storage.Client') as mock_storage
    ):
        
        # Setup the fake yfinance behavior
        mock_ticker_instance = mock_ticker.return_value
        mock_ticker_instance.history.return_value = mock_df
        
        # Setup the fake storage behavior
        mock_bucket = mock_storage.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        
        # ACT
        response, status_code = ingest_market_data(mock_request)
        
        # ASSERT
        # Did the function return a success code?
        assert status_code == 200
        assert "Success" in response
        
        # Did it actually attempt to talk to Google Cloud Storage?
        mock_storage.return_value.bucket.assert_called_with("muni-bronze-us-east1")
        
        # Did it call the upload method?
        mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_ingest_invalid_ticker(mock_ticker, mock_get_client):
    """
    Test that an invalid ticker request triggers a 404.
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    mock_request = MagicMock()
    mock_request.get_json.return_value = {"ticker": "UNKNOWN"}
    mock_request.args = {}
    
    # yfinance will return an empty DataFrame
    mock_df = pd.DataFrame()
        
    # Setup the fake yfinance behavior
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df
    
    # Setup the fake storage behavior
    mock_storage = MagicMock()
    mock_get_client.return_value = mock_storage
    mock_bucket = mock_storage.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    
    # ACT
    response, status_code = ingest_market_data(mock_request)
    
    # ASSERT
    # Did the function return 404?
    assert status_code == 404
    assert "UNKNOWN" in response
    assert "No data found" in response

    # In this scenario,the upload method should not have been called
    mock_blob.upload_from_string.assert_not_called()

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_ingest_missing_ticker(mock_ticker, mock_get_client, create_mock_stock_data):
    """
    Test that an ticker defaults to AAPL if no ticker is provided.
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    mock_request = MagicMock()
    mock_request.get_json.return_value = {}
    mock_request.args = {}
    
    # yfinance will return an empty DataFrame
    mock_df = create_mock_stock_data(days=2)
        
    # Setup the fake yfinance behavior
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df
    
    # Setup the fake storage behavior
    mock_storage = MagicMock()
    mock_get_client.return_value = mock_storage
    mock_bucket = mock_storage.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    
    # ACT
    response, status_code = ingest_market_data(mock_request)
    
    # ASSERT
    # Did the function return 404?
    assert status_code == 200
    assert "Success" in response

    # Did it actually default to AAPL?
    mock_ticker.assert_called_once_with("AAPL")

    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")
        
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_raises_server_error(mock_ticker, mock_get_client, create_mock_stock_data):
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    mock_request = MagicMock()
    mock_request.get_json.return_value = {"ticker": "AAPL"}
    mock_request.args = {}

    # Fake yfinance behavior
    mock_df = create_mock_stock_data(days=2)
        
    # Setup the fake yfinance behavior
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df
    
    # Setup the fake storage behavior
    mock_storage = MagicMock()
    mock_get_client.return_value = mock_storage
    mock_storage.bucket.side_effect = Forbidden("Access Denied")

    # ACT
    response, status_code = ingest_market_data(mock_request)
    
    # ASSERT
    # Did the function return 500?
    # Note: Storage client will return 403,
    # but the function should return 500 as
    # it represents an internal server error
    assert status_code == 500
    # Ensure the exception details were captured in the return string
    assert "403" in response
    assert "Access Denied" in response

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_history_with_date_range(
    mock_ticker, mock_get_client, create_mock_stock_data
):
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    start_date = "2020-01-01"
    end_date = "2020-01-31"

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": "AAPL",
        "start_date": start_date,
        "end_date": end_date,
    }
    mock_request.args = {}
    
    # Create a dummy DataFrame to simulate yfinance data
    mock_df = create_mock_stock_data(days=31, start=start_date)
    
    # Setup the fake yfinance behavior
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df
    
    # Setup the fake storage behavior
    mock_storage = MagicMock()
    mock_get_client.return_value = mock_storage
    mock_bucket = mock_storage.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    
    # ACT
    response, status_code = ingest_market_data(mock_request)
    
    # ASSERT
    # Did the function return a success code?
    assert status_code == 200
    assert "Success" in response

    # Did it download based on start and end dates?
    mock_ticker_instance.history.assert_called_once_with(
        start=start_date, end=end_date
    )
    
    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")
    
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_end_date_without_start_date(
    mock_ticker, mock_get_client, create_mock_stock_data
):
    """
    Test that providing an end date without a start date defaults the 
    start date to 30 days prior.
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    end_date = "2020-01-31"

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": "AAPL",
        "end_date": end_date
    }
    mock_request.args = {}
    
    # Create a dummy DataFrame to simulate yfinance data
    # Start date should default to 30 days prior
    start_date = (
        datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)
    ).strftime("%Y-%m-%d")
    mock_df = create_mock_stock_data(days=31, start=start_date)
    
    # Setup the fake yfinance behavior
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df
    
    # Setup the fake storage behavior
    mock_storage = MagicMock()
    mock_get_client.return_value = mock_storage
    mock_bucket = mock_storage.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    
    # ACT
    response, status_code = ingest_market_data(mock_request)
    
    print(response)

    # ASSERT
    # Did the function return a success code?
    assert status_code == 200
    assert "Success" in response

    # Did it download based on start and end dates?
    mock_ticker_instance.history.assert_called_once_with(
        start=start_date, end=end_date
    )
    
    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")
    
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_blob_file_path(
    mock_ticker, mock_get_client, create_mock_stock_data
):
    """
    Test that blob file path is constructed correctly
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-01-31"

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    year = start_date_obj.year
    month = start_date_obj.month

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date
    }
    mock_request.args = {}
    
    # Create a dummy DataFrame to simulate yfinance data
    mock_df = create_mock_stock_data(days=31, start=start_date)
    
    # Setup the fake yfinance behavior
    mock_ticker_instance = mock_ticker.return_value
    mock_ticker_instance.history.return_value = mock_df
    
    # Setup the fake storage behavior
    mock_storage = MagicMock()
    mock_get_client.return_value = mock_storage
    mock_bucket = mock_storage.bucket.return_value
    mock_get_blob = mock_bucket.blob
    mock_blob = mock_get_blob.return_value
    
    file_path = (
        f"raw_market_data"
        f"/ticker={ticker}"
        f"/year={year}"
        f"/month={month}"
        f"/history.parquet"
    )

    # ACT
    response, status_code = ingest_market_data(mock_request)

    # ASSERT
    
    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")

    mock_get_blob.assert_called_with(file_path)
    
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()
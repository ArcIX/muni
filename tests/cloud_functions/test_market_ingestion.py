import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import io
from cloud_functions.market_ingestion.main import ingest_market_data

def test_ingest_valid_ticker(create_mock_stock_data):
    """
    Test that a valid ticker request triggers a fetch and a storage upload.
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    mock_request = MagicMock()
    mock_request.get_json.return_value = {"ticker": "AAPL"}
    
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
from dotenv import load_dotenv
load_dotenv(".env")

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import io
from datetime import datetime, timedelta
import calendar
from google.api_core.exceptions import Forbidden
import pyarrow.parquet as pq
from dateutil.relativedelta import relativedelta
from cloud_functions.market_ingestion.main import (
    ingest_market_data, get_ingestion_range, get_full_month_ingestion_range
)

@patch("cloud_functions.market_ingestion.main.datetime")
def test_mtd_end_date_is_tomorrow(mock_dt):
    # SETUP
    mock_dt.today.return_value = datetime(2026, 4, 3)

    # ACTION
    start, end = get_ingestion_range()
    
    # ASSERT
    # Assert that end is strictly greater than start
    assert end > start, "End date must be after start date for yfinance exclusivity"
    
    # If today is April 3rd, start should be April 1st and end should be April 3rd
    assert start.day == 1
    assert end.day == 4

@patch("cloud_functions.market_ingestion.main.datetime")
def test_ingestion_range_end_date_is_2nd(mock_dt):
    # SETUP
    mock_dt.today.return_value = datetime(2026, 4, 1)

    # ACTION
    start, end = get_ingestion_range()
    
    # ASSERT
    # Assert that end is strictly greater than start
    assert end > start, "End date must be after start date for yfinance exclusivity"
    
    # If today is April 1st, start should be April 1st and end should be April 2nd
    assert start == datetime(2026, 4, 1)
    assert end == datetime(2026, 4, 2)

@patch("cloud_functions.market_ingestion.main.datetime")
def test_ingestion_range_end_date_is_1st_of_next_month(mock_dt):
    # SETUP
    mock_dt.today.return_value = datetime(2026, 3, 31)

    # ACTION
    start, end = get_ingestion_range()
    
    # ASSERT
    # Assert that end is strictly greater than start
    assert end > start, "End date must be after start date for yfinance exclusivity"
    
    # If today is March 31st, start should be March 1st and end should be April 1st
    assert start == datetime(2026, 3, 1)
    assert end == datetime(2026, 4, 1)

@patch("cloud_functions.market_ingestion.main.datetime")
def test_ingestion_range_end_date_is_1st_of_next_year(mock_dt):
    # SETUP
    mock_dt.today.return_value = datetime(2025, 12, 31)

    # ACTION
    start, end = get_ingestion_range()
    
    # ASSERT
    # Assert that end is strictly greater than start
    assert end > start, "End date must be after start date for yfinance exclusivity"
    
    # If today is December 31st, start should be December 1st and end should be Jan 1st
    # of next year
    assert start == datetime(2025, 12, 1)
    assert end == datetime(2026, 1, 1)

def test_full_month_ingestion_range_end_date_is_1st_of_next_month():
    # SETUP
    base_date_obj = datetime(2026, 4, 30)

    # ACTION
    start, end = get_full_month_ingestion_range(base_date_obj)
    
    # ASSERT
    # Assert that end is strictly greater than start
    assert end > start, "End date must be after start date for yfinance exclusivity"
    
    # If today is April 3rd, start should be April 1st and end should be April 3rd
    assert start == datetime(2026, 4, 1)
    assert end ==  datetime(2026,  5, 1)

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
        start=start_date, end=end_date,  auto_adjust=False
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
    start date to the first of the month and overwrites the end date
    to the first of the next month
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    end_date = "2020-01-28"

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": "AAPL",
        "end_date": end_date
    }
    mock_request.args = {}

    base_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    # Start date should default to first of the month
    # based on the end date
    start_date = (
        base_date_obj.replace(day=1)
    ).strftime("%Y-%m-%d")

    # End date should become the first day of the next month
    end_date = (
        base_date_obj.replace(day=1) + relativedelta(months=1)
    ).strftime("%Y-%m-%d")

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
    
    print(response)

    # ASSERT
    # Did the function return a success code?
    assert status_code == 200
    assert "Success" in response

    # Did it download based on start and end dates?
    mock_ticker_instance.history.assert_called_once_with(
        start=start_date, end=end_date, auto_adjust=False
    )
    
    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")
    
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_start_date_without_end_date(
    mock_ticker, mock_get_client, create_mock_stock_data
):
    """
    Test that providing a start date without an end date defaults the 
    end date to the first of the next month and overwrites the start 
    date to the first of the month
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    start_date = "2020-01-05"

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": "AAPL",
        "start_date": start_date
    }
    mock_request.args = {}
    
    base_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

    # Start date should become the first of the month
    start_date = (
        base_date_obj.replace(day=1)
    ).strftime("%Y-%m-%d")

    # End date should default to the first day of the next month
    end_date = (
        base_date_obj.replace(day=1) + relativedelta(months=1)
    ).strftime("%Y-%m-%d")

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
    
    print(response)

    # ASSERT
    # Did the function return a success code?
    assert status_code == 200
    assert "Success" in response

    # Did it download based on start and end dates?
    mock_ticker_instance.history.assert_called_once_with(
        start=start_date, end=end_date, auto_adjust=False
    )
    
    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")
    
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.datetime")
@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_no_start_date_and_end_date(
    mock_ticker, mock_get_client, mock_dt, create_mock_stock_data
):
    """
    Test that providing no start and end date defaults the 
    start date to the first of the month and end date to
    tomorrow (month to date)
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": "AAPL"
    }
    mock_request.args = {}
    
    today_date_obj = datetime(2020, 1, 5).date()
    mock_dt.today.return_value = today_date_obj

    # Start date should default to first of the month
    start_date = (
        today_date_obj.replace(day=1)
    ).strftime("%Y-%m-%d")

    # End date should become tomorrow
    end_date = (today_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    # Create a dummy DataFrame to simulate yfinance data
    mock_df = create_mock_stock_data(days=4, start=start_date)
    
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
        start=start_date, end=end_date, auto_adjust=False
    )
    
    # Did it actually attempt to talk to Google Cloud Storage?
    mock_storage.bucket.assert_called_with("muni-bronze-us-east1")
    
    # Did it call the upload method?
    mock_blob.upload_from_string.assert_called_once()

@patch("cloud_functions.market_ingestion.main.datetime")
@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_no_start_date_and_end_date_first_of_month(
    mock_ticker, mock_get_client, mock_dt, create_mock_stock_data
):
    """
    Test that providing no start and end date when its the first day of
    the month defaults the start date to today and end date to tomorrow
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions

    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "ticker": "AAPL"
    }
    mock_request.args = {}
    
    today_date_obj = datetime(2020, 1, 1)
    mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
    mock_dt.today.return_value = today_date_obj

    # End date should become tomorrow
    end_date = (today_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    # Start date should default to today
    start_date = today_date_obj.strftime("%Y-%m-%d")

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
    
    print(response)

    # ASSERT
    # Did the function return a success code?
    assert status_code == 200
    assert "Success" in response

    # Did it download based on start and end dates?
    mock_ticker_instance.history.assert_called_once_with(
        start=start_date, end=end_date, auto_adjust=False
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
    (month must be zero padded)
    """
    # SETUP
    # Mock the incoming HTTP request from Google Cloud Functions
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-01-31"

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    year_str = start_date_obj.strftime("%Y")
    month_str = start_date_obj.strftime("%m")

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
        f"/year={year_str}"
        f"/month={month_str}"
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

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_history_contains_adjusted_close(
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

    # Grab the data that was sent to the upload mock
    args, kwargs = mock_blob.upload_from_string.call_args
    uploaded_bytes = args[0]
    # Read it back into a DataFrame to inspect the "contract"
    results_df = pd.read_parquet(io.BytesIO(uploaded_bytes))
    
    # ASSERT
    assert "Adj Close" in results_df.columns, "Adj Close column is missing!"

@patch("cloud_functions.market_ingestion.main.get_storage_client")
@patch("yfinance.Ticker")
def test_history_date_is_date_type(
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

    # Grab the data that was sent to the upload mock
    args, kwargs = mock_blob.upload_from_string.call_args
    uploaded_bytes = args[0]
    # Read it back into a parquet table to avoid finicky data type issues
    # for Date column
    results_tbl = pq.read_table(io.BytesIO(uploaded_bytes))
    date_field = results_tbl.schema.field("Date")
    
    # ASSERT
    assert str(date_field.type) == "date32[day]", f"Expected date32[day], got {date_field.type}"
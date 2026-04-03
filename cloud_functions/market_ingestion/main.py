import yfinance as yf
import pandas as pd
from google.cloud import storage
import functions_framework
import io
from datetime import datetime, timedelta
import os
import calendar
from dateutil.relativedelta import relativedelta

BRONZE_BUCKET_NAME = os.environ.get("BRONZE_BUCKET_NAME")
if not BRONZE_BUCKET_NAME:
    raise RuntimeError("The BRONZE_BUCKET_NAME environment variable is not set.")

# This lives in the global memory space of the "warm" instance
_STORAGE_CLIENT = None

# Lazy Singleton for the storage client
def get_storage_client():
    global _STORAGE_CLIENT
    
    if _STORAGE_CLIENT is None:
        _STORAGE_CLIENT = storage.Client()

    return _STORAGE_CLIENT

def get_ingestion_range():
    """
    Calculates the 1st of the current month and tomorrow's date
    to account for the end date exclusivity of yfinance
    mtd = month to date
    """
    today = datetime.today()
    # The 1st of this month
    first_of_month = today.replace(day=1)
    # Tomorrow
    tomorrow = today + timedelta(days=1)
    
    return first_of_month, tomorrow

def get_full_month_ingestion_range(base_date_obj: datetime):
    """
    Calculates the start of the month and the next month from the base date.
    """
    # The 1st of the month
    first_of_month = base_date_obj.replace(day=1)
    # The 1st of the next month
    first_of_next_month = first_of_month + relativedelta(months=1)

    return first_of_month, first_of_next_month
@functions_framework.http
def ingest_market_data(request):
    """HTTP Cloud Function to fetch yfinance data and save to GCS."""
    
    # Parse the ticker from the trigger request (Default to AAPL)
    request_json = request.get_json(silent=True)
    request_args = request.args

    ticker_symbol = "AAPL"
    if request_json and 'ticker' in request_json:
        ticker_symbol = request_json['ticker']
    elif request_args and 'ticker' in request_args:
        ticker_symbol = request_args['ticker']

    # Parse the start_date and end_date from the trigger request
    start_date = (request_json or {}).get('start_date') or (request_args or {}).get('start_date')
    end_date = (request_json or {}).get('end_date') or (request_args or {}).get('end_date')

    # If both start_date and end_date are provided, use them
    if start_date and end_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    # Default values:
    # If either only start_date or only end_date is provided, use:
    #   start_date = first of the month of start_date/end_date
    #   end_date = end of the month of start_date/end_date
    elif (start_date and not end_date) or (end_date and not start_date):
        base_date = start_date or end_date
        start_date_obj, end_date_obj = get_full_month_ingestion_range(
            datetime.strptime(base_date, "%Y-%m-%d")
        )
        start_date = start_date_obj.strftime("%Y-%m-%d")
        end_date = end_date_obj.strftime("%Y-%m-%d")
    # If neither start_date nor end_date are provided, use month to date
    else:
        start_date_obj, end_date_obj = get_ingestion_range()

    # Update the date strings based on what we calculated
    # from above if statements
    start_date = start_date_obj.strftime("%Y-%m-%d")
    end_date = end_date_obj.strftime("%Y-%m-%d")

    if start_date_obj > end_date_obj:
        return f"Invalid date range: {start_date} to {end_date}", 400

    print(f"Starting ingestion for {ticker_symbol}...")
    print(f"From {start_date} to {end_date}...")

    try:
        # Fetch historical data
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
        
        if df.empty:
            return f"No data found for {ticker_symbol}", 404
            
        # Clean up the index so 'Date' is a normal column
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # Convert DataFrame to a Parquet file in memory (no local disk needed)
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
        
        # Upload to Google Cloud Storage
        bucket = get_storage_client().bucket(BRONZE_BUCKET_NAME)
        
        # We partition by ticker, year, and month (zero padded) to keep the 
        # data lake organized and easy to query
        year = start_date_obj.strftime("%Y")
        month = start_date_obj.strftime("%m")

        file_path = (
            f"raw_market_data"
            f"/ticker={ticker_symbol}"
            f"/year={year}"
            f"/month={month}"
            f"/history.parquet"
        )
        blob = bucket.blob(file_path)
        
        blob.upload_from_string(
            parquet_buffer.getvalue(), 
            content_type='application/octet-stream'
        )
        
        return f"Success! {len(df)} rows for {ticker_symbol} saved to {file_path}", 200

    except Exception as e:
        print(f"Error ingesting {ticker_symbol}: {str(e)}")
        return f"Failed to ingest {ticker_symbol}: {str(e)}", 500
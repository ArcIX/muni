import yfinance as yf
import pandas as pd
from google.cloud import storage
import functions_framework
import io
from datetime import datetime, timedelta

BRONZE_BUCKET_NAME = "muni-bronze-us-east1"

# This lives in the global memory space of the "warm" instance
_STORAGE_CLIENT = None

# Lazy Singleton for the storage client
def get_storage_client():
    global _STORAGE_CLIENT
    
    if _STORAGE_CLIENT is None:
        _STORAGE_CLIENT = storage.Client()

    return _STORAGE_CLIENT

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
    # (Default to today and 30 days ago)
    end_date = (request_json or {}).get('end_date') or (request_args or {}).get('end_date')
    if end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date_obj = datetime.today()
        end_date = end_date_obj.strftime("%Y-%m-%d")
    
    start_date = (request_json or {}).get('start_date') or (request_args or {}).get('start_date')
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date_obj = end_date_obj - timedelta(days=30)
        start_date = start_date_obj.strftime("%Y-%m-%d")

    if start_date_obj > end_date_obj:
        return f"Invalid date range: {start_date} to {end_date}", 400

    print(f"Starting ingestion for {ticker_symbol}...")
    print(f"From {start_date} to {end_date}...")

    try:
        # Fetch historical data
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            return f"No data found for {ticker_symbol}", 404
            
        # Clean up the index so 'Date' is a normal column
        df.reset_index(inplace=True)
        
        # Convert DataFrame to a Parquet file in memory (no local disk needed)
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
        
        # Upload to Google Cloud Storage
        bucket = get_storage_client().bucket(BRONZE_BUCKET_NAME)
        
        # We partition by ticker, year, and month to keep the data lake organized
        year = start_date_obj.year
        month = start_date_obj.month

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
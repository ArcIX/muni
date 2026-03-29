import yfinance as yf
import pandas as pd
from google.cloud import storage
import functions_framework
import io

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

    print(f"Starting ingestion for {ticker_symbol}...")

    try:
        # Fetch max historical data
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="max")
        
        if df.empty:
            return f"No data found for {ticker_symbol}", 404
            
        # Clean up the index so 'Date' is a normal column
        df.reset_index(inplace=True)
        
        # Convert DataFrame to a Parquet file in memory (no local disk needed)
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
        
        # Upload to Google Cloud Storage
        bucket = get_storage_client().bucket(BRONZE_BUCKET_NAME)
        
        # We partition by ticker to keep the data lake organized
        file_path = f"raw_market_data/ticker={ticker_symbol}/history.parquet"
        blob = bucket.blob(file_path)
        
        blob.upload_from_string(
            parquet_buffer.getvalue(), 
            content_type='application/octet-stream'
        )
        
        return f"Success! {len(df)} rows for {ticker_symbol} saved to {file_path}", 200

    except Exception as e:
        print(f"Error ingesting {ticker_symbol}: {str(e)}")
        return f"Failed to ingest {ticker_symbol}: {str(e)}", 500
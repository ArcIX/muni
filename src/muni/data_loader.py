import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

def fetch_data(ticker: str, data_dir: str = "data") -> pd.DataFrame:
    # Make the directories if they don't exist
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, f"{ticker}.parquet")
    
    # If no local file exists, download 1 month's worth of data
    # We're avoiding a full historical download for now
    if not os.path.exists(file_path):
        print(f"--- Downloading 1 month history for {ticker} ---")
        df = yf.download(ticker, period="1mo")
        if df.empty:
            raise ValueError(f"No data found for {ticker}")
        
        # Save to parquet
        df.to_parquet(file_path)
        return df
        
    # If file exists, load it and find the last recorded date
    df_existing = pd.read_parquet(file_path)
    
    # Ensure the index is datetime, then get the maximum date
    df_existing.index = pd.to_datetime(df_existing.index)
    last_date = df_existing.index.max()
    
    # Calculate the next day to start fetching from
    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check if we actually need to download anything
    if start_date >= today:
        print(f"--- Data for {ticker} is up to date. ---")
        return df_existing
        
    # Fetch only the missing dates
    print(f"--- Fetching missing data for {ticker} from {start_date} ---")
    df_new = yf.download(ticker, start=start_date)
    
    # Combine, clean, and overwrite
    if not df_new.empty:
        # Combine the old and new DataFrames
        df_combined = pd.concat([df_existing, df_new])
        
        # Drop duplicates just in case yfinance returned overlapping days
        df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
        
        # Sort by date to keep everything strictly chronological
        df_combined.sort_index(inplace=True)
        
        # Overwrite the Parquet file with the complete dataset
        df_combined.to_parquet(file_path)
        return df_combined
        
    # If yfinance returned empty data (e.g., weekends/holidays), just return existing
    return df_existing
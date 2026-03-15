import yfinance as yf
import pandas as pd
import os

def fetch_data(ticker: str, data_dir: str = "data") -> pd.DataFrame:
    # Make the directories if they don't exist
    os.makedirs(data_dir, exist_ok=True)

    # Fetch the data
    df = yf.download(ticker, period="1mo")

    # Save to parquet
    file_path = os.path.join(
        data_dir,
        f"{ticker}.parquet"
    )
    df.to_parquet(file_path)

    return df
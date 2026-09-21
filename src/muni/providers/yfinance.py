import pandas as pd
import os
import time
import yfinance as yf
from muni.strategies import BaseStrategy
from muni.providers import BaseProvider

class YFinanceProvider(BaseProvider):
    def __init__(self, cache_dir: str = "data/.cache", max_age_seconds: float = 86400) -> None:
        super().__init__(cache_dir, max_age_seconds)

    def get_data(self, ticker: str, start_date: str, end_date: str, strategy: BaseStrategy) -> pd.DataFrame:
        cache_filename = f"{ticker}_{start_date}_{end_date}_{strategy.__class__.__name__}.parquet"
        cache_path = self.cache_dir / cache_filename

        # Check if we can use the local version
        if cache_path.exists():
            file_age = time.time() - os.path.getmtime(cache_path)
            if file_age < self.max_age_seconds:
                print(f"--- Cache Hit: {ticker} (Age: {int(file_age/3600)}h) ---")
                return pd.read_parquet(cache_path)

        print(f"--- Cache Miss: Fetching {ticker} from YFinance ---")
        # Fetch the data from YFinance
        yf_ticker = yf.Ticker(ticker)
        results_df = yf_ticker.history(start=start_date, end=end_date, auto_adjust=False)
        
        # Align schema
        results_df = self._align_schema(results_df, ticker)
        
        # Save to parquet
        results_df.to_parquet(cache_path)

        return results_df

    def _align_schema(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        aligned_df = df.copy()

        # Remove columns we don't need
        aligned_df = aligned_df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]

        # Add trade_date column
        aligned_df.reset_index(inplace=True)
        aligned_df["trade_date"] = pd.to_datetime(aligned_df["Date"]).dt.tz_localize(None).dt.normalize()

        # Add ticker column
        aligned_df["ticker"] = ticker

        # Rename columns
        aligned_df = aligned_df.rename(
            columns={
                "Open": "open", "High": "high", "Low": "low", "Close": "close",
                "Adj Close": "adj_close", "Volume": "volume"
            }
        )

        # Reorder columns
        aligned_df = aligned_df[["trade_date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]]

        return aligned_df
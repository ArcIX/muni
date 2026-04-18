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
        ticker = yf.Ticker(ticker)
        results_df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

        results_df.to_parquet(cache_path)

        return results_df
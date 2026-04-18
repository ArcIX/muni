import pandas as pd
from pathlib import Path
import os
import time
from google.cloud import bigquery
from muni.strategies import BaseStrategy
from muni.providers import BaseProvider

class BigQueryProvider(BaseProvider):
    def __init__(
        self, client: bigquery.Client, dataset_name: str, cache_dir: str = "data/.cache",
        max_age_seconds: float = 86400
    ) -> None:
        self.client = client
        self.dataset_name = dataset_name

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.max_age_seconds = max_age_seconds

    def get_data(
        self, ticker: str, start_date: str, end_date: str, strategy: BaseStrategy
    ) -> pd.DataFrame:
        cache_filename = f"{ticker}_{start_date}_{end_date}_{strategy.__class__.__name__}.parquet"
        cache_path = self.cache_dir / cache_filename

        # Check if we can use the local version
        if cache_path.exists():
            file_age = time.time() - os.path.getmtime(cache_path)
            if file_age < self.max_age_seconds:
                print(f"--- Cache Hit: {ticker} (Age: {int(file_age/3600)}h) ---")
                return pd.read_parquet(cache_path)

        print(f"--- Cache Miss: Fetching {ticker} from BigQuery ---")
        query_str = strategy.get_sql_query_string(ticker, start_date, end_date)
        results_df = self.client.query(query_str).to_dataframe()

        results_df.to_parquet(cache_path)

        return results_df
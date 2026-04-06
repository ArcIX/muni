import pandas as pd
from google.cloud import bigquery
from muni.strategies import BaseStrategy
from muni.providers import BaseProvider

class BigQueryProvider(BaseProvider):
    def __init__(self, client: bigquery.Client, dataset_name: str) -> None:
        self.client = client
        self.dataset_name = dataset_name

    def get_data(
        self, ticker: str, start_date: str, end_date: str, strategy: BaseStrategy
    ) -> pd.DataFrame:
        query_str = strategy.get_sql_query_string(ticker, start_date, end_date)
        results_df = self.client.query(query_str).to_dataframe()
        return results_df
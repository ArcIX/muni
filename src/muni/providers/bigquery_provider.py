import pandas as pd
from google.cloud import bigquery
from muni.providers import BaseProvider

class BigQueryProvider(BaseProvider):
    def __init__(self, client: bigquery.Client, dataset_name: str) -> None:
        self.client = client
        self.dataset_name = dataset_name

    def get_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame()
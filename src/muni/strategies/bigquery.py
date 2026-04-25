from abc import ABC, abstractmethod
import pandas as pd
import os
from muni.strategies import BaseStrategy

class BigQueryStrategy(BaseStrategy, ABC):
    def __init__(self):
        super().__init__()

    def _get_dataset_name(self) -> str:
        return os.environ.get("BIGQUERY_DATASET_NAME")

    def _get_table_name(self) -> str:
        return os.environ.get("SILVER_TABLE_NAME")

    @abstractmethod
    def get_sql_query_string(ticker, start_date, end_date) -> str:
        """This method must be overridden by subclasses."""
        pass
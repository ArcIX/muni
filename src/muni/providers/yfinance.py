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
        pass
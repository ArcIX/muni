from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from muni.strategies import BaseStrategy

class BaseProvider(ABC):
    def __init__(self, cache_dir: str = "data/.cache", max_age_seconds: float = 86400) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.max_age_seconds = max_age_seconds
    
    @abstractmethod
    def get_data(
        self, ticker: str, start_date: str, end_date: str, strategy: BaseStrategy
    ) -> pd.DataFrame:
        pass
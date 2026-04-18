from abc import ABC, abstractmethod
import pandas as pd
from muni.strategies import BaseStrategy

class BaseProvider(ABC):
    @abstractmethod
    def get_data(
        self, ticker: str, start_date: str, end_date: str, strategy: BaseStrategy
    ) -> pd.DataFrame:
        pass
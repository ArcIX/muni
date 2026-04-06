from abc import ABC, abstractmethod
import pandas as pd

class BaseProvider(ABC):
    @abstractmethod
    def get_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        pass
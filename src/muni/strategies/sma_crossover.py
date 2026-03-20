import pandas as pd
from muni.strategies import BaseStrategy

class SMACrossover(BaseStrategy):
    def __init__(self, fast_window: int = 50, slow_window: int = 200):
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        pass
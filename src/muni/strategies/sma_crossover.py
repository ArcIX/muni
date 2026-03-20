import pandas as pd
from muni.strategies import BaseStrategy

class SMACrossover(BaseStrategy):
    def __init__(self, fast_window: int = 50, slow_window: int = 200):
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data_df = df.copy()
        data_df["fast_ma"] = data_df["Close"].rolling(window=self.fast_window).mean()
        data_df["slow_ma"] = data_df["Close"].rolling(window=self.slow_window).mean()
        
        # Raw signal: 1 if fast > slow
        raw_signal = (data_df["fast_ma"] > data_df["slow_ma"]).astype(int)
        
        # Shift to avoid Lookahead Bias
        data_df["signal"] = raw_signal.shift(1).fillna(0)
        return data_df
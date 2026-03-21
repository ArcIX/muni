import pandas as pd
from .base import BaseStrategy

class RSIMeanReversion(BaseStrategy):
    def  __init__(
            self, window: int = 14,
            oversold_threshold: float = 30.0,
            overbought_threshold: float = 70.0
        ):
        self.window = window
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

    def generate_signals(self, df: pd.DataFrame):
        pass
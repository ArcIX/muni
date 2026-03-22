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
        data_df = df.copy()

        data_df["delta"] = data_df["Close"].diff()

        # Gains are the positive deltas.
        # Turn negative deltas to 0.
        data_df["gain"] = data_df["delta"].clip(lower=0)

        # Calculate the average gain
        data_df["avg_gain"] = (
            data_df["gain"]
            .rolling(window=self.window)
            .mean()
        )

        # Losses are the negative deltas.
        # Turn positive deltas to 0 and get the absolute value.
        data_df["loss"] = data_df["delta"].clip(upper=0).abs()

        # Calculate the average loss
        data_df["avg_loss"] = (
            data_df["loss"]
            .rolling(window=self.window)
            .mean()
        )

        # Calculate the RS
        data_df["rs"] = data_df["avg_gain"] / data_df["avg_loss"]

        # Calculate the RSI (Relative Strength Index)
        data_df["rsi"] = 100 - (100 / (1 + data_df["rs"]))

        # Signals
        signal_srs = pd.Series(index=data_df.index,  dtype=float)
        signal_srs[data_df["rsi"] < self.oversold_threshold] =  1
        signal_srs[data_df["rsi"] > self.overbought_threshold] =  0
        data_df["signal"] = signal_srs.ffill().shift(1).fillna(0)

        return data_df
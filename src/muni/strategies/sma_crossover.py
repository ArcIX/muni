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
    
    def get_sql_query_string(self, ticker: str, start_date: str, end_date: str) -> str:
        return f"""
            WITH indicators AS (
                SELECT
                    trade_date,
                    ticker,
                    adj_close,
                    -- Calculate short and long term averages
                    AVG(adj_close) OVER(fast_window) AS fast_sma,
                    AVG(adj_close) OVER(slow_window) AS slow_sma
                FROM `test_dataset.test_table`
                WHERE 
                    ticker = '{ticker}' AND 
                    trade_date BETWEEN '{start_date}' AND '{end_date}'
                WINDOW 
                    fast_window AS (
                        PARTITION BY ticker
                        ORDER BY trade_date
                        ROWS BETWEEN {self.fast_window - 1} PRECEDING AND CURRENT ROW
                    ),
                    slow_window AS (
                        PARTITION BY ticker
                        ORDER BY trade_date
                        ROWS BETWEEN {self.slow_window - 1} PRECEDING AND CURRENT ROW
                    )
            ),
            raw_signals AS (
                SELECT
                    *,
                    -- Signal Generation Logic
                    -- Calculate the "State" (1 if fast > slow)
                    CASE
                    WHEN fast_sma > slow_sma THEN 1
                    ELSE 0
                    END AS raw_signal
                FROM indicators
            )
            SELECT
            *,
            -- Shift the signal by 1 day to match Python's .shift(1)
            -- This ensures 'today's' signal is actually 'yesterday's' math
            LAG(raw_signal) OVER(PARTITION BY ticker ORDER BY trade_date) AS bq_signal
            FROM raw_signals;
        """
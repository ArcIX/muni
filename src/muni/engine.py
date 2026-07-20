import pandas as pd

class BacktestEngine():
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital

    def run(self, stock_with_signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates returns based on the signal column.
        Expects a DataFrame with 'Close' and 'signal' columns.
        """
        results_df = stock_with_signals_df.copy()

        # StrategyReturns = Signal x Market Returns
        # Calculate the market returns using percentage change on Close
        results_df["market_returns"] = results_df["Close"].pct_change()
        
        # Calculate the strategy returns
        results_df["strategy_returns"] = results_df["signal"] * results_df["market_returns"]

        # Calculate the cumulative growth
        results_df["cumulative_return"] = (1 + results_df['strategy_returns'].fillna(0)).cumprod()

        # Finally, calculate the final equity curve
        results_df["equity"] = results_df["cumulative_return"] * self.initial_capital

        return results_df
    
    def get_performance_summary(self, results_df: pd.DataFrame) -> dict:
        """
        Returns a dictionary of key performance indicators
        """
        # Total Return
        total_return = (results_df['cumulative_return'].iloc[-1] - 1) * 100

        # Max Drawdown
        peak = results_df['equity'].cummax()
        drawdown = (results_df['equity'] - peak) / peak
        max_drawdown = drawdown.min() * 100

        # Final Equity
        final_equity = results_df['equity'].iloc[-1]

        performance_dict = {
            "Total Return (%)": round(total_return, 2),
            "Max Drawdown (%)": round(max_drawdown, 2),
            "Final Value ($)": round(final_equity, 2)
        }
        return performance_dict

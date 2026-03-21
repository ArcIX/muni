import pandas as pd
from muni.data_loader import fetch_data
from muni.strategies import BaseStrategy, SMACrossover
from muni.engine import BacktestEngine

def run_pipeline(ticker: str, strategy: BaseStrategy, capital: float):
    print(f"\n{'='*30}")
    print(f"STARTING BACKTEST: {ticker}")
    print(f"{'='*30}")

    # Load Data
    stocks_df = fetch_data(ticker)

    # Generate Signals
    stocks_with_signals_df = strategy.generate_signals(stocks_df)

    # Engine
    engine = BacktestEngine(initial_capital=capital)
    results_df = engine.run(stocks_with_signals_df)

    print(
        results_df[[
            "Close",
            "signal",
            "market_returns",
            "strategy_returns",
            "cumulative_return",
            "equity"
        ]]
        .head(30)
    )
    
    print(f"\n{'='*30}")
    print(f"END OF BACKTEST: {ticker}")
    print(f"{'='*30}")

    return results_df

if __name__ == "__main__":
    # Example: Backtesting Apple with SMA Crossover
    sma_strat = SMACrossover(fast_window=4, slow_window=8)
    run_pipeline("AAPL", sma_strat, 10000.0)
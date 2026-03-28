import pandas as pd
from muni.data_loader import fetch_data
from muni.strategies import BaseStrategy, SMACrossover, RSIMeanReversion
from muni.engine import BacktestEngine

def run_pipeline(ticker: str, strategy: BaseStrategy, capital: float):
    print(f"\n{'='*30}")
    print(f"STARTING BACKTEST: {ticker}")
    print(f"{'='*30}")

    # Load Data
    stocks_df = fetch_data(ticker)
    if stocks_df.empty:
        raise ValueError("No data returned")

    # Generate Signals
    stocks_with_signals_df = strategy.generate_signals(stocks_df)

    # Engine
    engine = BacktestEngine(initial_capital=capital)
    results_df = engine.run(stocks_with_signals_df)

    # Get Performance Metrics
    stats = engine.get_performance_summary(results_df)

    print(f"\nRESULTS FOR {ticker} (Strategy: {strategy.__class__.__name__}):")
    for key, value in stats.items():
        print(f" - {key}: {value}")

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

    # Example: Backtesting Apple with RSI Mean Reversion
    rsi_strat = RSIMeanReversion(window=3)
    run_pipeline("AAPL", rsi_strat, 10000.0)
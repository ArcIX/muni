import pandas as pd
import os
from google.cloud import bigquery
from muni.data_loader import fetch_data
from muni.strategies import BaseStrategy, SMACrossover, RSIMeanReversion
from muni.providers import BaseProvider, YFinanceProvider, BigQueryProvider
from muni.engine import BacktestEngine

def run_pipeline(
    ticker: str, start_date: str, end_date: str,
    strategy: BaseStrategy, provider: BaseProvider,
    capital: float
):
    print(f"\n{'='*30}")
    print(f"STARTING BACKTEST: {ticker}")
    print(f"{'='*30}")

    # Load Data
    stocks_df = provider.get_data(ticker, start_date, end_date, strategy)
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
    # Using YFinance
    # Example: Backtesting Apple with SMA Crossover
    ticker = "AAPL"
    start_date = "2026-01-01"
    end_date = "2026-01-31"
    sma_strat = SMACrossover(fast_window=4, slow_window=8)
    yf_provider = YFinanceProvider()
    capital = 10000
    run_pipeline(ticker, start_date, end_date, sma_strat, yf_provider, capital)

    # Example: Backtesting Apple with RSI Mean Reversion
    ticker = "AAPL"
    start_date = "2026-01-01"
    end_date = "2026-01-31"
    rsi_strat = RSIMeanReversion(window=3)
    yf_provider = YFinanceProvider()
    capital = 10000
    run_pipeline(ticker, start_date, end_date, sma_strat, yf_provider, capital)

    # Using BigQuery
    # Example: Backtesting Apple with SMA Crossover
    # ticker = "AAPL"
    # start_date = "2026-01-01"
    # end_date = "2026-01-31"
    # sma_strat = SMACrossover(fast_window=4, slow_window=8)
    # bq_client = bigquery.Client()
    # bq_dataset_name = os.environ.get("BIGQUERY_DATASET_NAME")
    # bq_provider = BigQueryProvider(bq_client, bq_dataset_name)
    # capital = 10000
    # run_pipeline(ticker, start_date, end_date, sma_strat, bq_provider, capital)
# Modular Vectorized Backtester

A high-performance, vectorized backtesting framework built in Python for validating quantitative trading strategies against historical equity data. This system is designed with a "Plug-and-Play" architecture, allowing for rapid development and testing of technical analysis indicators while strictly enforcing zero-lookahead bias.

## Project Architecture

The project follows a modular design pattern to separate data acquisition, mathematical strategy logic, and performance calculation:

* **`main.py`**: The entry point that orchestrates the data loading, strategy execution, and engine reporting.
* **`muni/`**:
    * `engine.py`: The `BacktestEngine` that computes PnL, Total Return, and Max Drawdown using high-speed Pandas operations.
    * `data_loader.py`: Handles historical data fetching via `yfinance` with local Parquet caching.
    * **`strategies/`**: 
        * `base.py`: The abstract base class defining the strategy contract.
        * `sma_crossover.py`: A trend-following strategy using Dual Moving Averages.
        * `rsi_mean_reversion.py`: A mean-reversion strategy using the Relative Strength Index with $T+1$ execution logic.

## Quick Start

### 1. Installation
Clone the repository and install the required dependencies:
```bash
pip install pandas numpy yfinance pyarrow
```

### 2. Running a Backtest
You can run the full pipeline for any ticker supported by Yahoo Finance:
```python
from backtester.strategies import RSIMeanReversion
from main import run_pipeline

# Run RSI Mean Reversion on Apple (AAPL)
results = run_pipeline(
    ticker="AAPL",
    strategy_class=RSIMeanReversion,
    strategy_params={"window": 14, "oversold_threshold": 30.0}
)

print(f"Final Portfolio Value: ${results['final_value']:.2f}")
```

## Testing Suite

This project emphasizes **Test-Driven Development (TDD)**. We use `pytest` to validate mathematical edge cases, particularly focusing on the "Burn-in" period of indicators.

Key test scenarios include:
* **The Mountain Peak**: Validates RSI state transitions (Overbought $\rightarrow$ Neutral $\rightarrow$ Oversold) during high volatility.
* **The Continuous Bleed**: Ensures the `BacktestEngine` correctly calculates negative returns and peak-to-trough Max Drawdown.
* **The NaN Guard**: Verifies that signals are not "invented" during the initial lookback window.

Run the tests using:
```bash
pytest tests/
```

## Key Features

* **Zero-Lookahead Bias**: All signals are shifted by one period ($T+1$) to ensure trades are executed on available information.
* **Vectorized Performance**: PnL is calculated via geometric returns across the entire DataFrame, avoiding slow Python `for` loops.
* **Local Caching**: Historical data is saved as `.parquet` files to reduce API calls and speed up iterative testing.
* **Persistence Logic**: Strategies use `.ffill()` to maintain positions until an explicit exit signal is triggered.
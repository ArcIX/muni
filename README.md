# Muni: A Modular Vectorized Backtester

A high-performance, vectorized backtesting framework built in Python for validating quantitative trading strategies against historical equity data. This system is designed with a "Plug-and-Play" architecture, allowing for rapid development and testing of technical analysis indicators while strictly enforcing zero-lookahead bias.

## Project Architecture

The project follows a modular design pattern to separate data acquisition, mathematical strategy logic, and performance calculation:

* **`main.py`**: The entry point that orchestrates the data loading, strategy execution, and engine reporting.
* **`muni/`**:
    * `engine.py`: The `BacktestEngine` that computes PnL, Total Return, and Max Drawdown using high-speed Pandas operations.
    * **`providers/`**: 
        * `base.py`: The abstract base class defining the data fetching method. 
        * `bigquery.py`: Handles data fetching via `BigQuery`. You must setup your own cloud architecture that ingests data into
                         `Bigquery` datasets to make use of this.
        * `yfinance.py`: Handles data fetching via `yfinance`.
    * **`strategies/`**: 
        * `base.py`: The abstract base class defining the strategy contract.
        * `bigquery.py`: The abstract class defining the strategies whose signal generation logic is supported via `BigQuery`.
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
from muni.strategies import RSIMeanReversion
from muni.providers import YFinanceProvider
from main import run_pipeline

# Instantiate the RSI Mean Reversion strategy
rsi_strat = RSIMeanReversion(window=14)

# Instantiate the YFinanceProvider to fetch the data
# directly from yfinance
yf_provider = YFinanceProvider()

# Run RSI Mean Reversion on Apple (AAPL)
results_df = run_pipeline(
    ticker="AAPL",
    start_date="2026-01-01",
    end_date="2026-01-31",
    strategy=rsi_strat,
    provider=yf_provider,
    capital=10000.0
)

print(f"Final Portfolio Value: ${results_df['equity'].iloc[-1]:.2f}")
```

## Testing Suite

This project emphasizes **Test-Driven Development (TDD)**. We use `pytest` to validate mathematical edge cases, particularly focusing on the "Burn-in" period of indicators.

Key test scenarios include:
* **The Mountain Peak**: Validates RSI state transitions (Overbought $\rightarrow$ Neutral $\rightarrow$ Oversold) during high volatility.
* **The Continuous Bleed**: Ensures the `BacktestEngine` correctly calculates negative returns and peak-to-trough Max Drawdown.
* **The NaN Guard**: Verifies that signals are not "invented" during the initial lookback window.
* **Mocked Providers**: Validates that strategies seamlessly interface with data structures offline using mock providers and dynamic `conftest.py` fixtures.

Run the tests using:
```bash
pytest tests/
```

## Key Features

* **Zero-Lookahead Bias**: All signals are shifted by one period ($T+1$) to ensure trades are executed on available information.
* **Vectorized Performance**: PnL is calculated via geometric returns across the entire DataFrame, avoiding slow Python `for` loops.
* **Local Caching**: Historical data is saved as `.parquet` files to reduce API calls and speed up iterative testing.
* **Persistence Logic**: Strategies use `.ffill()` to maintain positions until an explicit exit signal is triggered.
* **BigQuery Integration**: `BigQuery` can be utilized as an alternative data source provided that it setup accordingly.

## Design Decisions

* **Why Parquet?**: Fast column-oriented reading and small disk memory footprint for historical daily bars.
* **Why Vectorized vs. Event-Driven?**: Prioritizes execution speed and mathematical correctness across daily series over
tick-by-tick order-book simulation
* **Abstract Base Classes (ABCs):**: Decoupling data fetching from calculation so strategy logic remains 100% independent of
whether data comes from Yahoo Finance, BigQuery, or a local CSV.

## Data Pipeline Architecture (GCS & BigQuery)

`Muni` supports an enterprise data pipeline pattern built on the **Medallion Architecture** (Bronze $\rightarrow$ Silver) to
ingest and process market data efficiently in Google Cloud Platform.

```
yfinance ──> GCS Bucket (.parquet) ──> Bronze Layer (External Table) ──> Silver Layer (Partitioned BigQuery Table)
```

### Layer Breakdown

* **Bronze Layer (Raw Ingestion):** An external BigQuery table pointed directly at your Google Cloud Storage (GCS) `.parquet`
bucket. It serves as a live, zero-cost lens into your raw landing data without requiring manual loading jobs.
* **Silver Layer (Processed & Deduplicated):** A native, Hive-partitioned BigQuery table. Uses an incremental `MERGE` (upsert)
pattern to clean raw records, eliminate duplicates, and provide high-performance query execution for vectorized strategy
backtests.

### Setting Up Your Own Automated GCP Pipeline

If you want to use the `BigQueryProvider` for large-scale data backtesting, follow these steps to deploy the data pipeline:

#### 1. Configure Cloud Storage (GCS)
Create a GCS bucket structured with Hive partitioning for optimal query pruning:
`gs://your-bucket-name/raw_market_data/ticker=AAPL/`

#### 2. Create the Bronze External Table
In BigQuery, create an external table pointing to your GCS bucket pattern. This ensures new `.parquet` uploads are immediately queryable without ingestion pipelines:
```sql
CREATE EXTERNAL TABLE `market_data.bronze_quotes`
WITH PARTITION COLUMNS (
  ticker STRING,
  year INT64,
  month INT64
)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://your-bucket-name/raw_market_data/*'],
  hive_partition_uri_prefix = 'gs://your-bucket-name/raw_market_data/'
);
```

#### 3. Create the Silver Table
Create a native BigQuery table partitioned by date.
```sql
CREATE TABLE `your-project-name.market_data.silver_quotes`
(
  trade_date DATE OPTIONS(description="The primary time axis (YYYY-MM-DD)"),
  ticker STRING OPTIONS(description="The stock symbol (e.g., AAPL)"),
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  adj_close FLOAT64 OPTIONS(description="Critical for math; accounts for splits/dividends"),
  volume INT64
)
PARTITION BY trade_date
CLUSTER BY ticker;
```

#### 4. Orchestrate with Cloud Run
Refer to the `cloud_functions\market_ingetions` directory of this project. Deploy this serverless Cloud Function (triggered via HTTP or Cloud Scheduler) with `ingest_market_data` as the entry point.

The pipeline workflow looks like this:
1. Fetch the latest market data from `yfinance`
2. Dump structured `.parquet` files directly to the GCS Bronze bucket. This will also update `market_data.bronze_quotes`, the 
external table created previously.
3. Execute the MERGE query (found in `upsert_ticker_history`) to refresh the Silver table for your backtesting strategies

**Note on Architecture**: The pipeline is designed such that strategy code queries the Silver Layer for blazing-fast execution, while the Bronze Layer keeps raw storage costs virtually at zero
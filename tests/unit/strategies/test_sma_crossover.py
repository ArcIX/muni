from dotenv import load_dotenv
load_dotenv(".env")

import pytest
import pandas as pd
import textwrap
import os
from muni.strategies import SMACrossover

@pytest.mark.unit
def test_sma_crossover_init():
    sma_strat = SMACrossover(fast_window=10, slow_window=30)

    assert sma_strat.fast_window == 10
    assert sma_strat.slow_window == 30

@pytest.mark.unit
def test_sma_crossover_signal_generation(create_mock_stock_data):
    # SETUP
    stock_df = create_mock_stock_data(days=50)
    sma_strat = SMACrossover(fast_window=5, slow_window=10)
    
    # ACTION
    results_df = sma_strat.generate_signals(stock_df)
    
    # ASSERT
    assert "signal" in results_df.columns
    assert results_df["signal"].iloc[0] == 0  # Should be 0 due to shift/NaNs

@pytest.mark.unit
def test_sma_crossover_insufficient_data(create_mock_stock_data):
    """
    If the data is shorter than the slow_window, 
    the strategy should return all 0s, not crash.
    """
    # SETUP: Only 10 days of data
    stock_df = create_mock_stock_data(days=10)
    
    # ACTION: Request a 20-day SMA
    sma_strat = SMACrossover(fast_window=5, slow_window=20)
    results_df = sma_strat.generate_signals(stock_df)
    
    # ASSERT: No signals should be generated
    assert results_df['signal'].sum() == 0
    assert len(results_df) == 10

@pytest.mark.unit
def test_sma_crossover_fast_below_slow():
    """
    Verify that the signal flips from 1 to 0 when 
    the fast MA crosses BELOW the slow MA.
    """
    # SETUP: Create a "mountain" price pattern
    # Price goes up (Golden Cross), then crashes (Death Cross)
    prices = [10, 11, 12, 13, 14, 15, 10, 8, 6, 4]
    stock_df = pd.DataFrame({"adj_close": prices}, index=pd.date_range("2024-01-01", periods=10))
    
    # ACTION: Using very small windows to force the cross quickly
    sma_strat = SMACrossover(fast_window=2, slow_window=4)
    results_df = sma_strat.generate_signals(stock_df)
    
    # ASSERT: Check for the presence of both 1s and then 0s later
    assert 1 in results_df["signal"].values
    
    # Check that the final state is 0 (we exited)
    assert results_df["signal"].iloc[-1] == 0

@pytest.mark.unit
def test_sma_crossover_fast_above_slow():
    """
    Verify that the signal flips from 0 to 1 when 
    the fast MA crosses above the slow MA.
    """
    # SETUP: Create a "valley" price pattern
    # Price goes down, then goes up
    prices = [14, 11, 7, 6, 4, 6, 10, 12, 15, 20]
    stock_df = pd.DataFrame({"adj_close": prices}, index=pd.date_range("2024-01-01", periods=10))
    
    # ACTION: Using very small windows to force the cross quickly
    sma_strat = SMACrossover(fast_window=2, slow_window=4)
    results_df = sma_strat.generate_signals(stock_df)
    
    # ASSERT: Check for the presence of both 0s and then 1s later
    assert 0 in results_df["signal"].values
    
    # Check that the final state is 1 (we entered)
    assert results_df["signal"].iloc[-1] == 1

@pytest.mark.unit
def test_sma_signal_entry_timing():
    """
    Verify the 'Golden Cross' timing:
    Day X: Fast crosses Slow.
    Day X: Signal must be 0 (cannot trade on same-day info).
    Day X+1: Signal must be 1.
    """
    # SETUP: Fast MA (2-day) will cross Slow MA (4-day) on Day 5
    # Price sequence that forces a crossover
    prices = [10, 10, 10, 10, 20, 25, 30] 
    stock_df = pd.DataFrame({"adj_close": prices}, index=pd.date_range("2024-01-01", periods=7))
    
    # ACTION
    sma_strat = SMACrossover(fast_window=2, slow_window=4)
    results_df = sma_strat.generate_signals(stock_df)
    
    # ASSERT: Find the crossover point
    # Day 5 (index 4) is when the 2-day average jumps ahead of the 4-day
    # Because of our .shift(1), the signal should still be 0 on Day 5
    assert results_df["signal"].iloc[4] == 0, "Signal triggered too early (Lookahead Bias!)"
    
    # Day 6 (index 5) is the first day we are actually 'In the Market'
    assert results_df["signal"].iloc[5] == 1, "Signal failed to trigger on the day after crossover"

@pytest.mark.unit
def test_get_sql_query_string():
    # SETUP
    dataset_name = os.environ.get("BIGQUERY_DATASET_NAME")
    table_name = os.environ.get("SILVER_TABLE_NAME")

    ticker = "AAPL"
    start_date = "2022-01-01"
    end_date = "2023-01-01"

    fast_window = 5
    slow_window = 10

    # ACTION
    sma_strat = SMACrossover(fast_window=fast_window, slow_window=slow_window)
    query_string = sma_strat.get_sql_query_string(ticker, start_date, end_date)

    # ASSERT
    sma_signals_query_string = f"""
        WITH indicators AS (
            SELECT
                trade_date,
                ticker,
                adj_close,
                -- Calculate short and long term averages
                AVG(adj_close) OVER(fast_window) AS fast_sma,
                AVG(adj_close) OVER(slow_window) AS slow_sma
            FROM `{dataset_name}.{table_name}`
            WHERE 
                ticker = '{ticker}' AND 
                trade_date BETWEEN '{start_date}' AND '{end_date}'
            WINDOW 
                fast_window AS (
                    PARTITION BY ticker
                    ORDER BY trade_date
                    ROWS BETWEEN {fast_window - 1} PRECEDING AND CURRENT ROW
                ),
                slow_window AS (
                    PARTITION BY ticker
                    ORDER BY trade_date
                    ROWS BETWEEN {slow_window - 1} PRECEDING AND CURRENT ROW
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
    assert textwrap.dedent(query_string) == textwrap.dedent(sma_signals_query_string)

@pytest.mark.unit
def test_sma_crossover_bigquery_signal_generation():
    # SETUP
    data_df = pd.DataFrame({"bq_signal": [0, 1, 1, 1, 0, 0, 0]}, index=pd.date_range("2024-01-01", periods=7))

    fast_window = 5
    slow_window = 10

    # ACTION
    sma_strat = SMACrossover(fast_window=fast_window, slow_window=slow_window)
    results_df = sma_strat.generate_signals(data_df)

    # ASSERT
    assert (results_df["signal"] == data_df["bq_signal"]).all()
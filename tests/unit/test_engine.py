import pytest
import pandas as pd
from muni.engine import BacktestEngine

@pytest.mark.unit
def test_engine_ten_percent_gain():
    """Test that $10,000 grows correctly with a 10% gain and signal=1."""
    # SETUP: 2 days of data. Price goes from 100 to 110 (10% gain)
    stock_df = pd.DataFrame({
        "Close": [100.0, 110.0]
    }, index=pd.date_range("2024-01-01", periods=2))
    
    # Fake strategy results where we are "Long" on the second day
    stock_with_signals_df = stock_df.copy()
    stock_with_signals_df["signal"] = [0, 1]
    
    # ACTION: Run the engine
    engine = BacktestEngine(initial_capital=10000.0)
    results = engine.run(stock_with_signals_df)
    
    # ASSERT: Final value should be 11,000
    assert results["equity"].iloc[-1] == 11000.0
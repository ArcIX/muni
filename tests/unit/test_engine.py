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

@pytest.mark.unit
def test_engine_ten_percent_loss():
    """Test that $10,000 experiences a 10% loss when price dips"""
    # SETUP: 2 days of data. Price goes from 100 to 90 (10% loss)
    stock_df = pd.DataFrame({
        "Close": [100.0, 90.0]
    }, index=pd.date_range("2024-01-01", periods=2))
    
    # Fake strategy results where we are "Long" on the second day.
    # Note that no strategy should ever result with these signals
    # given the scenario. This test case is just to prove that the
    # calculation works properly
    stock_with_signals_df = stock_df.copy()
    stock_with_signals_df["signal"] = [0, 1]
    
    # ACTION: Run the engine
    engine = BacktestEngine(initial_capital=10000.0)
    results = engine.run(stock_with_signals_df)
    
    # ASSERT: Final value should be 9,000
    assert results["equity"].iloc[-1] == 9000.0

@pytest.mark.unit
def test_get_performance_summary_returns_dict():
    # SETUP: 2 days of data. Price goes from 100 to 110 (10% gain)
    stock_df = pd.DataFrame({
        "Close": [100.0, 110.0]
    }, index=pd.date_range("2024-01-01", periods=2))
    
    # Fake strategy results where we are "Long" on the second day
    stock_with_signals_df = stock_df.copy()
    stock_with_signals_df["signal"] = [0, 1]

    # ACTION: Run the engine
    engine = BacktestEngine(initial_capital=10000.0)
    results_df = engine.run(stock_with_signals_df)
    performance = engine.get_performance_summary(results_df)

    # ASSERT
    assert isinstance(performance, dict)

@pytest.mark.unit
def test_performance_summary_values_price_goes_up():
    # SETUP: 2 days of data. Price goes from 100 to 110
    stock_df = pd.DataFrame({
        "Close": [100.0, 110.0]
    }, index=pd.date_range("2024-01-01", periods=2))
    
    # Fake strategy results where we are "Long" on the second day
    stock_with_signals_df = stock_df.copy()
    stock_with_signals_df["signal"] = [0, 1]

    # ACTION: Run the engine
    engine = BacktestEngine(initial_capital=10000.0)
    results_df = engine.run(stock_with_signals_df)
    performance_dict = engine.get_performance_summary(results_df)

    # ASSERT
    assert performance_dict["Total Return (%)"] == 10.0
    assert performance_dict["Max Drawdown (%)"] == 0.0
    assert performance_dict["Final Value ($)"] == 11000

@pytest.mark.unit
def test_performance_summary_values_price_goes_down():
    # SETUP: 3 days of data. Price goes from 100 to 60
    stock_df = pd.DataFrame({
        "Close": [100.0, 80.0, 60]
    }, index=pd.date_range("2024-01-01", periods=3))
    
    # Fake strategy results where we are "Long" all 3 days
    stock_with_signals_df = stock_df.copy()
    stock_with_signals_df["signal"] = [1, 1, 1]

    # ACTION: Run the engine
    engine = BacktestEngine(initial_capital=10000.0)
    results_df = engine.run(stock_with_signals_df)
    performance_dict = engine.get_performance_summary(results_df)

    # ASSERT
    assert performance_dict["Total Return (%)"] == -40.0
    assert performance_dict["Max Drawdown (%)"] == -40.0
    assert performance_dict["Final Value ($)"] == 6000
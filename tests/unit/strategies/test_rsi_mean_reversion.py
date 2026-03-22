import pytest
import pandas as pd
from muni.strategies import RSIMeanReversion

@pytest.mark.unit
def test_rsi_mean_reversion_init():
    rsi_mr_strat = RSIMeanReversion(
        window=14,
        oversold_threshold=30,
        overbought_threshold=70
    )

    assert rsi_mr_strat.window == 14
    assert rsi_mr_strat.oversold_threshold == 30
    assert rsi_mr_strat.overbought_threshold == 70

@pytest.mark.unit
def test_rsi_mean_reversion_signal_generation(create_mock_stock_data):
    # SETUP
    stock_df = create_mock_stock_data(days=50)
    rsi_mr_strat = RSIMeanReversion(
        window=3,
        oversold_threshold=30,
        overbought_threshold=70
    )

    # ACTION
    results_df = rsi_mr_strat.generate_signals(stock_df)

    # ASSERT
    assert "signal" in results_df.columns
    assert results_df["signal"].iloc[0] == 0

def test_rsi_mean_reversion_valley_prices():
    # SETUP: Scenario where the prices dip then rise back up
    prices = [100, 90, 80, 70, 100, 150, 140]
    stock_df = pd.DataFrame({"Close": prices}, index=pd.date_range("2024-01-01", periods=7))

    rsi_mr_strat = RSIMeanReversion(
        window=3,
        oversold_threshold=30,
        overbought_threshold=70
    )

    # ACTION
    results_df = rsi_mr_strat.generate_signals(stock_df)

    # ASSERT: Under the above conditions, we should enter on
    # the 5th day (index 4) and exit on the 7th day (index 6)
    assert results_df["signal"].iloc[4] == 1
    assert results_df["signal"].iloc[6] == 0

@pytest.mark.unit
def test_rsi_signal_persistence_and_timing():
    """
    Test the persistence and timing of our long signals.
    Uses same scenario as in test_rsi_mean_reversion_valley_prices().
    """
    # SETUP
    prices = [100, 90, 80, 70, 100, 150, 140]
    stock_df = pd.DataFrame({'Close': prices}, index=pd.date_range("2024-01-01", periods=7))
    
    rsi_mr_strat = RSIMeanReversion(
        window=3,
        oversold_threshold=30.0,
        overbought_threshold=70.0
    )
    results_df = rsi_mr_strat.generate_signals(stock_df)

    # ASSERT
    # Define our "expectation map" (index: expected signal)
    expected_signals = {
        3: 0.0,  # Day 4: RSI hits 0, but we can't trade yet (No lookahead!)
        4: 1.0,  # Day 5: ENTRY (First day we are actually Long)
        5: 1.0,  # Day 6: HOLD (RSI is ~88, but signal persists until Day 7)
        6: 0.0   # Day 7: EXIT (Actioned after Day 6 overbought signal)
    }

    for idx, expected in expected_signals.items():
        actual = results_df['signal'].iloc[idx]
        assert actual == expected, f"Signal mismatch at index {idx}. Expected {expected}, got {actual}"

def test_rsi_signal_persistence_and_timing_mountain_prices():
    # SETUP: Scenario where the prices rise then dip
    prices = [100, 110, 120, 130, 110, 90, 70, 80]
    stock_df = pd.DataFrame({"Close": prices}, index=pd.date_range("2024-01-01", periods=8))

    rsi_mr_strat = RSIMeanReversion(
        window=3,
        oversold_threshold=30,
        overbought_threshold=70
    )

    # ACTION
    results_df = rsi_mr_strat.generate_signals(stock_df)

    # ASSERT
    # Define our "expectation map" (index: expected signal)
    expected_signals = {
        3: 0.0,  # Day 4: RSI hits 100 (overbought)
        4: 0.0,  # Day 5: NEUTRAL
        5: 0.0,  # Day 6: NEUTRAL (RSI is 20 (oversold), but we can't trade yet (No lookahead!))
        6: 1.0,  # Day 7: ENTRY (Actioned after Day 6 oversold signal)
        7: 1.0   # Day 8: HOLD
    }

    for idx, expected in expected_signals.items():
        actual = results_df['signal'].iloc[idx]
        assert actual == expected, f"Signal mismatch at index {idx}. Expected {expected}, got {actual}"
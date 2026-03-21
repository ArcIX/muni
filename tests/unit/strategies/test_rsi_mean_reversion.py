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
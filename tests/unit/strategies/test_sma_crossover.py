import pytest
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
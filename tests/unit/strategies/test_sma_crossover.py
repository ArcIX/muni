import pytest
from muni.strategies import SMACrossover

@pytest.mark.unit
def test_sma_crossover_init():
    sma_strat = SMACrossover(fast_window=10, slow_window=30)

    assert sma_strat.fast_window == 10
    assert sma_strat.slow_window == 30
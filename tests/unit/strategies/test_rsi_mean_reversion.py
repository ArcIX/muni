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
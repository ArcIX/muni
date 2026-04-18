import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path
from muni.providers import YFinanceProvider

@pytest.mark.unit
def test_yfinance_provider_init():
    # SETUP

    # ACTION
    yfinance_provider = YFinanceProvider()

    # ASSERT
    assert isinstance(yfinance_provider.cache_dir, Path)
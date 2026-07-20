import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def create_mock_stock_data():
    """
    A factory fixture that returns a function to create fake OHLCV data.
    Usage: df = create_mock_stock_data(days=10, start="2024-01-01")
    """
    def _generate(days=30, start="2024-01-01", base_price=150.0):
        dates = pd.date_range(start=start, periods=days, freq='D')
        
        # Create a synthetic upward trend with some noise
        noise = np.random.normal(0, 1, days)
        close_prices = base_price + np.cumsum(noise + 0.5)
        
        data = {
            "Open": close_prices - 0.5,
            "High": close_prices + 1.0,
            "Low": close_prices - 1.5,
            "Close": close_prices,
            "Adj Close": close_prices * 1.1,
            "Volume": np.random.randint(1000, 5000, size=days).astype(float)
        }
        
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    return _generate
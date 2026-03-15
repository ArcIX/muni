import pytest
import os
import pandas as pd
from muni.data_loader import fetch_data

@pytest.mark.integration
def test_fetch_data_creates_parquet(tmp_path):
    ticker = "AAPL"
    save_path = tmp_path / f"{ticker}.parquet"

    df = fetch_data(ticker, data_dir=str(tmp_path))

    assert isinstance(df, pd.DataFrame)
    assert os.path.exists(save_path)
    assert not df.empty
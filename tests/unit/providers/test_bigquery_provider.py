import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from google.cloud import bigquery
from muni.providers import BigQueryProvider

@patch("google.cloud.bigquery.Client")
@pytest.mark.unit
def test_bigquery_provider_init(mock_client):
    # SETUP
    mock_client.return_value = MagicMock()

    # ACTION
    bigquery_provider = BigQueryProvider(mock_client, "test_dataset")

    # ASSERT
    assert bigquery_provider.client is mock_client
    assert isinstance(bigquery_provider.dataset_name, str)

@pytest.mark.unit
def test_get_data_returns_dataframe(create_mock_stock_data):
    # SETUP
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2020-01-31"
    dataset_name = "test_dataset"

    mock_client = MagicMock()
    mock_query_job = MagicMock()
    mock_df = create_mock_stock_data(days=31, start=start_date)
    mock_client.query.return_value = mock_query_job
    mock_query_job.to_dataframe.return_value = mock_df

    mock_strategy = MagicMock()
    # Mock the strategy's unimplemented get_sql_query_string method
    # to return a valid SQL query
    mock_query_str = f"""
        SELECT
            *
        FROM `{dataset_name}.test_table`
        WHERE
            ticker = '{ticker}'
            AND date BETWEEN '{start_date}' AND '{end_date}'
    """
    mock_strategy.get_sql_query_string.return_value = mock_query_str

    # ACTION
    bigquery_provider = BigQueryProvider(mock_client, dataset_name)
    results_df = bigquery_provider.get_data(
        "AAPL", "2020-01-01", "2020-01-31", mock_strategy
    )

    # ASSERT
    # Verify the strategy was asked for the SQL
    mock_strategy.get_sql_query_string.assert_called_once_with("AAPL", "2020-01-01", "2020-01-31")
    
    # Verify BigQuery was called with that exact SQL
    mock_client.query.assert_called_once_with(mock_query_str)
    
    # Verify the final output is our mock dataframe
    pd.testing.assert_frame_equal(results_df, mock_df)
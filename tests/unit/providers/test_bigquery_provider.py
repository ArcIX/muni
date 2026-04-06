import pytest
from unittest.mock import MagicMock, patch
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
from unittest.mock import MagicMock, patch

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.cache", new_callable=MagicMock)
def test_hello_returns_hit_count(mock_cache, client):
    mock_cache.incr.return_value = 1
    response = client.get("/")
    assert response.status_code == 200
    assert b"1 times" in response.data


@patch("app.cache", new_callable=MagicMock)
def test_hello_increments_counter(mock_cache, client):
    mock_cache.incr.return_value = 42
    response = client.get("/")
    assert response.status_code == 200
    assert b"42 times" in response.data
    mock_cache.incr.assert_called_with("hits")

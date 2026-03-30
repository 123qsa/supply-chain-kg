"""Tests for PostgresClient"""
import sys
import os
import importlib.util

# Load postgres_client module directly
spec = importlib.util.spec_from_file_location(
    "postgres_client",
    os.path.join(os.path.dirname(__file__), "..", "clients", "postgres_client.py")
)
postgres_client = importlib.util.module_from_spec(spec)

# Mock config before loading
sys.modules['config'] = type(sys)('config')
sys.modules['config'].get_settings = lambda: type('Settings', (), {
    'postgres_host': 'localhost',
    'postgres_port': 5432,
    'postgres_db': 'testdb',
    'postgres_user': 'testuser',
    'postgres_password': 'testpass'
})()

spec.loader.exec_module(postgres_client)
PostgresClient = postgres_client.PostgresClient

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.asyncio
async def test_postgres_client_context_manager():
    """Test PostgresClient supports async context manager"""
    async with PostgresClient() as client:
        assert isinstance(client, PostgresClient)


@pytest.mark.asyncio
async def test_postgres_client_context_manager_closes():
    """Test PostgresClient context manager properly closes"""
    with patch.object(PostgresClient, 'close', new_callable=AsyncMock) as mock_close:
        async with PostgresClient() as client:
            pass

        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_client_execute():
    """Test execute runs query without returning results"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch.object(PostgresClient, '_pool', mock_pool):
        result = await PostgresClient.execute("INSERT INTO test VALUES ($1)", "value")

        mock_conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_client_fetch():
    """Test fetch returns multiple rows"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"symbol": "NVDA", "price": 100.0},
        {"symbol": "AMD", "price": 50.0}
    ]

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch.object(PostgresClient, '_pool', mock_pool):
        result = await PostgresClient.fetch("SELECT * FROM prices WHERE symbol = $1", "NVDA")

        assert len(result) == 2
        assert result[0]["symbol"] == "NVDA"


@pytest.mark.asyncio
async def test_postgres_client_fetchrow():
    """Test fetchrow returns single row"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"symbol": "NVDA", "price": 100.0}

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch.object(PostgresClient, '_pool', mock_pool):
        result = await PostgresClient.fetchrow("SELECT * FROM prices WHERE symbol = $1", "NVDA")

        assert result is not None
        assert result["symbol"] == "NVDA"


@pytest.mark.asyncio
async def test_postgres_client_save_prices():
    """Test save_prices bulk inserts price data"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    prices = [
        {"date": "2024-01-01", "open": 100.0, "high": 105.0, "low": 99.0, "close": 102.0, "volume": 1000000},
        {"date": "2024-01-02", "open": 102.0, "high": 108.0, "low": 101.0, "close": 107.0, "volume": 1500000}
    ]

    with patch.object(PostgresClient, '_pool', mock_pool):
        result = await PostgresClient.save_prices("NVDA", "us", prices)

        assert result == 2
        assert mock_conn.execute.call_count == 2


@pytest.mark.asyncio
async def test_postgres_client_log_discovery():
    """Test log_discovery records discovery event"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch.object(PostgresClient, '_pool', mock_pool):
        await PostgresClient.log_discovery("NVDA", "AMD", "COMPETES_WITH", "openbb", 1)

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "discovery_log" in call_args[0]


@pytest.mark.asyncio
async def test_postgres_client_log_impact():
    """Test log_impact records impact analysis"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch.object(PostgresClient, '_pool', mock_pool):
        await PostgresClient.log_impact(
            event="AI chip shortage",
            source="NVDA",
            affected="AMD",
            direction="利好",
            magnitude="高",
            reasoning="Supply constraint benefits competitors",
            confidence=0.85
        )

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "impact_log" in call_args[0]

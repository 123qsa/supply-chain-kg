"""Tests for Neo4jClient"""
import sys
import os
import importlib.util

# Load neo4j_client module directly from parent directory
spec = importlib.util.spec_from_file_location(
    "neo4j_client",
    os.path.join(os.path.dirname(__file__), "..", "clients", "neo4j_client.py")
)
neo4j_client = importlib.util.module_from_spec(spec)

# Mock config before loading
sys.modules['config'] = type(sys)('config')
sys.modules['config'].get_settings = lambda: type('Settings', (), {
    'neo4j_uri': 'bolt://localhost:7687',
    'neo4j_user': 'neo4j',
    'neo4j_password': 'password'
})()

spec.loader.exec_module(neo4j_client)
Neo4jClient = neo4j_client.Neo4jClient

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.asyncio
async def test_neo4j_client_context_manager():
    """Test Neo4jClient supports async context manager"""
    # Should be able to use async with
    async with Neo4jClient() as client:
        assert isinstance(client, Neo4jClient)


@pytest.mark.asyncio
async def test_neo4j_client_context_manager_closes():
    """Test Neo4jClient context manager properly closes"""
    with patch.object(Neo4jClient, 'close', new_callable=AsyncMock) as mock_close:
        async with Neo4jClient() as client:
            pass

        # After exiting context, close should be called
        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_neo4j_client_run_query():
    """Test run_query executes Cypher and returns results"""
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data.return_value = [{"ticker": "NVDA", "name": "NVIDIA"}]

    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch.object(Neo4jClient, '_instance', mock_driver):
        result = await Neo4jClient.run_query(
            "MATCH (c:Company) RETURN c.ticker, c.name LIMIT 1"
        )

        assert len(result) == 1
        assert result[0]["ticker"] == "NVDA"


@pytest.mark.asyncio
async def test_neo4j_client_create_company():
    """Test create_company creates or merges company node"""
    with patch.object(Neo4jClient, 'run_query', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [{"c": {"ticker": "NVDA", "name": "NVIDIA"}}]

        result = await Neo4jClient.create_company("NVDA", "NVIDIA", "us", depth=0)

        assert result is not None
        assert result["c"]["ticker"] == "NVDA"
        mock_run.assert_called_once()

        # Verify the query contains MERGE
        call_args = mock_run.call_args
        assert "MERGE" in call_args[0][0]


@pytest.mark.asyncio
async def test_neo4j_client_update_status():
    """Test update_status modifies company discovery status"""
    with patch.object(Neo4jClient, 'run_query', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [{"c": {"ticker": "NVDA"}}]

        result = await Neo4jClient.update_status("NVDA", "explored")

        assert result is True
        mock_run.assert_called_once()

        # Verify query contains status update and was called with ticker
        call_args = mock_run.call_args
        assert "discoveryStatus" in call_args[0][0]
        assert "NVDA" in str(call_args)


@pytest.mark.asyncio
async def test_neo4j_client_create_relation():
    """Test create_relation creates relationship between companies"""
    with patch.object(Neo4jClient, 'run_query', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [{"r": {}}]

        result = await Neo4jClient.create_relation(
            "NVDA", "AMD", "COMPETES_WITH", "openbb", confidence=0.95
        )

        assert result is True
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_neo4j_client_get_pending_nodes():
    """Test get_pending_nodes returns companies waiting to be explored"""
    with patch.object(Neo4jClient, 'run_query', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = [
            {"ticker": "AMD", "market": "us", "name": "AMD", "depth": 1},
            {"ticker": "INTC", "market": "us", "name": "Intel", "depth": 1}
        ]

        result = await Neo4jClient.get_pending_nodes(limit=10)

        assert len(result) == 2
        assert result[0]["ticker"] == "AMD"
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_neo4j_client_verify_connectivity():
    """Test verify_connectivity checks database connection"""
    mock_driver = MagicMock()
    mock_driver.verify_connectivity = AsyncMock()

    with patch.object(Neo4jClient, '_instance', mock_driver):
        result = await Neo4jClient.verify_connectivity()
        assert result is True
        mock_driver.verify_connectivity.assert_called_once()


@pytest.mark.asyncio
async def test_neo4j_client_verify_connectivity_failure():
    """Test verify_connectivity returns False on failure"""
    mock_driver = MagicMock()
    mock_driver.verify_connectivity = AsyncMock(side_effect=Exception("Connection failed"))

    with patch.object(Neo4jClient, '_instance', mock_driver):
        result = await Neo4jClient.verify_connectivity()
        assert result is False

"""Tests for discovery tools"""
import pytest
from unittest.mock import MagicMock, patch
from tools.discover import discover_peers, discover_etf_holdings, discover_institutional


@pytest.mark.asyncio
async def test_discover_peers_returns_list():
    """Test discover_peers returns a list of competitor companies"""
    with patch('tools.discover.openbb') as mock_openbb:
        mock_openbb.discover_peers.return_value = [
            {"symbol": "AMD", "name": "AMD Corporation"},
            {"symbol": "INTC", "name": "Intel Corporation"}
        ]

        result = await discover_peers("NVDA")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["ticker"] == "AMD"
        assert result[0]["relation"] == "COMPETES_WITH"


@pytest.mark.asyncio
async def test_discover_peers_handles_error():
    """Test discover_peers handles API errors gracefully"""
    with patch('tools.discover.openbb') as mock_openbb:
        mock_openbb.discover_peers.side_effect = Exception("API Error")

        result = await discover_peers("NVDA")

        assert result == []


@pytest.mark.asyncio
async def test_discover_etf_holdings_returns_list():
    """Test discover_etf_holdings returns ETF constituents"""
    with patch('tools.discover.openbb') as mock_openbb:
        mock_openbb.discover_etf_holdings.return_value = [
            {"symbol": "NVDA", "name": "NVIDIA"},
            {"symbol": "AMD", "name": "AMD"}
        ]

        result = await discover_etf_holdings("SOXX")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["relation"] == "IN_ETF"
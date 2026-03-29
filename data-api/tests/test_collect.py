"""Tests for collection tools"""
import pytest
from unittest.mock import patch
from tools.collect import get_price, get_profile


@pytest.mark.asyncio
async def test_get_profile_for_us_market():
    """Test get_profile for US market uses OpenBB"""
    with patch('tools.collect.openbb') as mock_openbb:
        mock_openbb.get_profile.return_value = {"name": "NVIDIA", "symbol": "NVDA"}

        result = await get_profile("NVDA", "us")

        assert result is not None
        assert result["symbol"] == "NVDA"


@pytest.mark.asyncio
async def test_get_price_normalizes_data():
    """Test get_price normalizes data to common format"""
    with patch('tools.collect.openbb') as mock_openbb:
        mock_openbb.get_price.return_value = [
            {"date": "2024-01-01", "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000000}
        ]

        result = await get_price("NVDA", "2024-01-01", "2024-01-31", "us")

        assert len(result) == 1
        assert "date" in result[0]
        assert "close" in result[0]
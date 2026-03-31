"""OpenBB data source client"""
from openbb import obb
from typing import List, Dict, Any, Optional
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class OpenBBClient:
    """OpenBB data source client"""

    def __init__(self):
        settings = get_settings()
        if settings.openbb_pat:
            obb.account.login(pat=settings.openbb_pat)

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        return False

    def discover_peers(self, symbol: str, provider: str = "yfinance") -> List[Dict[str, Any]]:
        """Discover competitor companies"""
        try:
            result = obb.equity.compare.peers(symbol=symbol, provider=provider)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get peers for {symbol}: {e}")
            return []

    def discover_etf_holdings(self, symbol: str = "SOXX", provider: str = "yfinance") -> List[Dict[str, Any]]:
        """Discover ETF holdings"""
        try:
            result = obb.etf.holdings(symbol=symbol, provider=provider)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get ETF holdings for {symbol}: {e}")
            return []

    def discover_institutional(self, symbol: str, provider: str = "yfinance") -> List[Dict[str, Any]]:
        """Discover institutional ownership"""
        try:
            result = obb.equity.ownership.institutional(symbol=symbol, provider=provider)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get institutional ownership for {symbol}: {e}")
            return []

    def get_profile(self, symbol: str, provider: str = "yfinance") -> Optional[Dict[str, Any]]:
        """Get company profile"""
        try:
            result = obb.equity.profile(symbol=symbol, provider=provider)
            return result.to_dict() if result else None
        except Exception as e:
            logger.error(f"Failed to get profile for {symbol}: {e}")
            return None

    def get_price(self, symbol: str, start_date: str, end_date: str, provider: str = "yfinance") -> List[Dict[str, Any]]:
        """Get historical price data"""
        try:
            result = obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider=provider
            )
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return []

    def get_income(self, symbol: str, period: str = "annual", limit: int = 4) -> List[Dict[str, Any]]:
        """Get income statement"""
        try:
            result = obb.equity.fundamental.income(symbol=symbol, period=period, limit=limit)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get income for {symbol}: {e}")
            return []

    def get_estimates(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get analyst estimates"""
        try:
            result = obb.equity.estimates.consensus(symbol=symbol)
            return result.to_dict() if result else None
        except Exception as e:
            logger.error(f"Failed to get estimates for {symbol}: {e}")
            return None

    def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get company news"""
        try:
            result = obb.news.company(symbol=symbol, limit=limit)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get news for {symbol}: {e}")
            return []
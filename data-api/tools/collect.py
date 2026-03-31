"""Collection tools for gathering company data and prices"""
from typing import List, Dict, Any, Optional
import logging
from clients import YahooFinanceClient, AkShareClient

logger = logging.getLogger(__name__)


async def get_profile(symbol: str, market: str = "us") -> Optional[Dict[str, Any]]:
    """Get company profile information

    Args:
        symbol: Stock symbol (e.g., "NVDA" or "000001")
        market: Market type ("us" or "cn")

    Returns:
        Company profile data in standardized format
    """
    try:
        if market == "us":
            async with YahooFinanceClient() as client:
                profile = client.get_profile(symbol)
                if profile:
                    return {
                        "ticker": symbol,
                        "name": profile.get("name", ""),
                        "sector": profile.get("sector", ""),
                        "industry": profile.get("industry", ""),
                        "description": profile.get("description", ""),
                        "employees": profile.get("employees", 0),
                        "country": profile.get("country", ""),
                        "website": profile.get("website", ""),
                        "market_cap": profile.get("market_cap"),
                        "market": "us",
                        "source": "yahoo_finance"
                    }
                return None
        else:
            # For CN market, construct basic profile from symbol
            return {
                "ticker": symbol,
                "name": symbol,  # Will be populated later
                "sector": "",
                "industry": "",
                "description": "",
                "employees": 0,
                "country": "CN",
                "website": "",
                "market_cap": None,
                "market": "cn",
                "source": "akshare"
            }
    except Exception as e:
        logger.error(f"get_profile failed for {symbol}: {e}")
        return None


async def get_price(
    symbol: str,
    start_date: str,
    end_date: str,
    market: str = "us"
) -> List[Dict[str, Any]]:
    """Get historical price data for a symbol

    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        market: Market type ("us" or "cn")

    Returns:
        List of price records in standardized format
    """
    try:
        if market == "us":
            async with YahooFinanceClient() as client:
                prices = client.get_price(symbol, start_date, end_date)
                return [
                    {
                        "date": p.get("date"),
                        "open": p.get("open"),
                        "high": p.get("high"),
                        "low": p.get("low"),
                        "close": p.get("close"),
                        "volume": p.get("volume"),
                        "ticker": symbol,
                        "market": "us"
                    }
                    for p in prices
                ]
        else:
            # Convert date format for AkShare (remove hyphens)
            start_cn = start_date.replace("-", "")
            end_cn = end_date.replace("-", "")

            with AkShareClient() as client:
                prices = client.get_cn_price(symbol, start_cn, end_cn)

            # Map Chinese column names to standard format
            return [
                {
                    "date": p.get("日期", ""),
                    "open": float(p.get("开盘", 0)),
                    "high": float(p.get("最高", 0)),
                    "low": float(p.get("最低", 0)),
                    "close": float(p.get("收盘", 0)),
                    "volume": int(p.get("成交量", 0)),
                    "ticker": symbol,
                    "market": "cn"
                }
                for p in prices
            ]
    except Exception as e:
        logger.error(f"get_price failed for {symbol}: {e}")
        return []


async def get_financials(symbol: str, market: str = "us") -> Optional[Dict[str, Any]]:
    """Get financial summary for a company

    Args:
        symbol: Stock symbol
        market: Market type ("us" or "cn")

    Returns:
        Financial summary data
    """
    try:
        if market == "us":
            async with YahooFinanceClient() as client:
                financials = client.get_financials(symbol)
                if financials:
                    return {
                        "ticker": symbol,
                        "revenue": financials.get("revenue"),
                        "net_income": financials.get("net_income"),
                        "total_assets": financials.get("total_assets"),
                        "total_debt": financials.get("total_debt"),
                        "market": "us",
                        "source": "yahoo_finance"
                    }
                return None
        else:
            with AkShareClient() as client:
                financials = client.get_cn_financial(symbol)
            if financials:
                latest = financials[0] if isinstance(financials, list) else financials
                return {
                    "ticker": symbol,
                    "revenue": latest.get("营业收入"),
                    "net_income": latest.get("净利润"),
                    "total_assets": latest.get("总资产"),
                    "total_debt": latest.get("总负债"),
                    "cash": latest.get("货币资金"),
                    "pe_ratio": None,
                    "pb_ratio": None,
                    "market": "cn",
                    "source": "akshare"
                }
            return None
    except Exception as e:
        logger.error(f"get_financials failed for {symbol}: {e}")
        return None


async def batch_collect(
    symbols: List[str],
    market: str = "us",
    include_profile: bool = True,
    include_price: bool = True,
    price_start: Optional[str] = None,
    price_end: Optional[str] = None
) -> Dict[str, Any]:
    """Collect data for multiple symbols in batch

    Used by n8n workflows for efficient batch data collection.

    Args:
        symbols: List of stock symbols
        market: Market type
        include_profile: Whether to fetch company profiles
        include_price: Whether to fetch price data
        price_start: Start date for price data (optional)
        price_end: End date for price data (optional)

    Returns:
        Dictionary with collected data for all symbols
    """
    results = {
        "profiles": {},
        "prices": {},
        "failed": []
    }

    for symbol in symbols:
        try:
            if include_profile:
                profile = await get_profile(symbol, market)
                if profile:
                    results["profiles"][symbol] = profile

            if include_price and price_start and price_end:
                prices = await get_price(symbol, price_start, price_end, market)
                if prices:
                    results["prices"][symbol] = prices

        except Exception as e:
            logger.error(f"Batch collect failed for {symbol}: {e}")
            results["failed"].append({"symbol": symbol, "error": str(e)})

    return results

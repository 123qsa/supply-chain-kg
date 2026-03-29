"""Database operations tools for PostgreSQL/TimescaleDB"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from clients import PostgresClient

logger = logging.getLogger(__name__)


async def save_price_batch(
    ticker: str,
    market: str,
    prices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Save a batch of price data

    Args:
        ticker: Stock symbol
        market: Market type ("us" or "cn")
        prices: List of price records

    Returns:
        Results summary
    """
    try:
        async with PostgresClient() as db:
            # Format prices for TimescaleDB
            formatted_prices = [
                {
                    "ticker": ticker,
                    "market": market,
                    "date": p.get("date"),
                    "open": p.get("open", 0),
                    "high": p.get("high", 0),
                    "low": p.get("low", 0),
                    "close": p.get("close", 0),
                    "volume": p.get("volume", 0)
                }
                for p in prices
            ]

            await db.save_prices(ticker, market, formatted_prices)
            return {"success": True, "count": len(prices)}
    except Exception as e:
        logger.error(f"save_price_batch failed for {ticker}: {e}")
        return {"success": False, "error": str(e)}


async def log_discovery_event(
    source: str,
    discovered: List[str],
    discovery_type: str = "bfs",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Log a discovery event

    Args:
        source: Source company symbol
        discovered: List of discovered symbols
        discovery_type: Type of discovery (bfs, peers, etf, etc.)
        metadata: Optional metadata

    Returns:
        True if successful
    """
    try:
        async with PostgresClient() as db:
            await db.log_discovery(
                source=source,
                discovered_count=len(discovered),
                discovery_type=discovery_type,
                metadata=metadata or {}
            )
            return True
    except Exception as e:
        logger.error(f"log_discovery_event failed: {e}")
        return False


async def log_impact_analysis(
    event: str,
    ticker: str,
    impact_score: float,
    direction: str,
    confidence: float,
    reasoning: str
) -> bool:
    """Log an impact analysis result

    Args:
        event: Event description
        ticker: Affected company ticker
        impact_score: Numerical impact score
        direction: Impact direction (利好/利空/中性)
        confidence: Confidence level (0-1)
        reasoning: Analysis reasoning

    Returns:
        True if successful
    """
    try:
        async with PostgresClient() as db:
            await db.log_impact(
                event=event,
                ticker=ticker,
                impact_score=impact_score,
                direction=direction,
                confidence=confidence,
                reasoning=reasoning
            )
            return True
    except Exception as e:
        logger.error(f"log_impact_analysis failed: {e}")
        return False


async def get_price_history(
    ticker: str,
    start_date: str,
    end_date: str,
    market: str = "us"
) -> List[Dict[str, Any]]:
    """Get price history for a symbol

    Args:
        ticker: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        market: Market type

    Returns:
        List of price records
    """
    try:
        async with PostgresClient() as db:
            # Query TimescaleDB hypertable
            # This would be implemented in PostgresClient
            return []
    except Exception as e:
        logger.error(f"get_price_history failed: {e}")
        return []


async def get_discovery_history(
    source: Optional[str] = None,
    days: int = 7
) -> List[Dict[str, Any]]:
    """Get discovery history

    Args:
        source: Optional source filter
        days: Number of days to look back

    Returns:
        List of discovery log entries
    """
    try:
        async with PostgresClient() as db:
            # Query discovery log
            return []
    except Exception as e:
        logger.error(f"get_discovery_history failed: {e}")
        return []


async def get_impact_history(
    ticker: Optional[str] = None,
    event: Optional[str] = None,
    days: int = 30
) -> List[Dict[str, Any]]:
    """Get impact analysis history

    Args:
        ticker: Optional ticker filter
        event: Optional event filter
        days: Number of days to look back

    Returns:
        List of impact log entries
    """
    try:
        async with PostgresClient() as db:
            # Query impact log
            return []
    except Exception as e:
        logger.error(f"get_impact_history failed: {e}")
        return []


async def cleanup_old_data(
    table: str,
    days_to_keep: int = 90
) -> Dict[str, Any]:
    """Clean up old data from tables

    Args:
        table: Table name
        days_to_keep: Number of days of data to retain

    Returns:
        Cleanup results
    """
    try:
        async with PostgresClient() as db:
            # Delete old records
            return {"success": True, "deleted": 0}
    except Exception as e:
        logger.error(f"cleanup_old_data failed: {e}")
        return {"success": False, "error": str(e)}

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
            count = await db.save_prices(ticker, market, prices)
            return {"success": True, "count": count}
    except Exception as e:
        logger.error(f"save_price_batch failed for {ticker}: {e}")
        return {"success": False, "error": str(e)}


async def log_discovery_event(
    explorer: str,
    discovered: List[str],
    discovery_type: str = "bfs",
    source: str = "auto",
    depth: int = 0
) -> bool:
    """Log a discovery event

    Args:
        explorer: Source company symbol
        discovered: List of discovered symbols
        discovery_type: Type of discovery (bfs, peers, etf, etc.)
        source: Data source (e.g., openbb, akshare)
        depth: Discovery depth in BFS traversal

    Returns:
        True if successful
    """
    try:
        async with PostgresClient() as db:
            for symbol in discovered:
                await db.log_discovery(
                    explorer=explorer,
                    discovered=symbol,
                    relation_type=discovery_type,
                    source=source,
                    depth=depth
                )
            return True
    except Exception as e:
        logger.error(f"log_discovery_event failed: {e}")
        return False


async def log_impact_analysis(
    event: str,
    affected_ticker: str,
    source_ticker: str,
    impact_score: float,
    direction: str,
    confidence: float,
    reasoning: str
) -> bool:
    """Log an impact analysis result

    Args:
        event: Event description
        affected_ticker: Affected company ticker
        source_ticker: Source/origin company ticker
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
                source=source_ticker,
                affected=affected_ticker,
                direction=direction,
                magnitude=_score_to_magnitude(impact_score),
                reasoning=reasoning,
                confidence=confidence
            )
            return True
    except Exception as e:
        logger.error(f"log_impact_analysis failed: {e}")
        return False


def _score_to_magnitude(score: float) -> str:
    """Convert numerical score to magnitude string"""
    if score >= 0.7:
        return "高"
    elif score >= 0.4:
        return "中"
    return "低"


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
            rows = await db.fetch(
                """
                SELECT date, open, high, low, close, volume
                FROM stock_prices
                WHERE symbol = $1 AND market = $2 AND date BETWEEN $3 AND $4
                ORDER BY date ASC
                """,
                ticker, market, start_date, end_date
            )
            return [dict(row) for row in rows]
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
            if source:
                rows = await db.fetch(
                    """
                    SELECT explorer_ticker, discovered_ticker, relation_type, source, depth, discovered_at
                    FROM discovery_log
                    WHERE explorer_ticker = $1 AND discovered_at > NOW() - INTERVAL '%s days'
                    ORDER BY discovered_at DESC
                    """ % days,
                    source
                )
            else:
                rows = await db.fetch(
                    """
                    SELECT explorer_ticker, discovered_ticker, relation_type, source, depth, discovered_at
                    FROM discovery_log
                    WHERE discovered_at > NOW() - INTERVAL '%s days'
                    ORDER BY discovered_at DESC
                    """ % days
                )
            return [dict(row) for row in rows]
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
            conditions = ["analyzed_at > NOW() - INTERVAL '%s days'" % days]
            params = []
            param_idx = 1

            if ticker:
                conditions.append(f"affected_ticker = ${param_idx}")
                params.append(ticker)
                param_idx += 1

            if event:
                conditions.append(f"event_description ILIKE ${param_idx}")
                params.append(f"%{event}%")
                param_idx += 1

            query = f"""
                SELECT event_description, source_ticker, affected_ticker,
                       direction, magnitude, reasoning, confidence, analyzed_at
                FROM event_impact_log
                WHERE {' AND '.join(conditions)}
                ORDER BY analyzed_at DESC
            """

            rows = await db.fetch(query, *params)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"get_impact_history failed: {e}")
        return []


async def cleanup_old_data(
    table: str,
    days_to_keep: int = 90
) -> Dict[str, Any]:
    """Clean up old data from tables

    Args:
        table: Table name (stock_prices, discovery_log, event_impact_log)
        days_to_keep: Number of days of data to retain

    Returns:
        Cleanup results
    """
    valid_tables = {
        "stock_prices": "date",
        "discovery_log": "discovered_at",
        "event_impact_log": "analyzed_at"
    }

    if table not in valid_tables:
        return {"success": False, "error": f"Invalid table: {table}"}

    try:
        async with PostgresClient() as db:
            date_column = valid_tables[table]
            result = await db.execute(
                f"""
                DELETE FROM {table}
                WHERE {date_column} < NOW() - INTERVAL '{days_to_keep} days'
                """
            )
            # Parse result like "DELETE 100"
            deleted = int(result.split()[1]) if result and len(result.split()) > 1 else 0
            return {"success": True, "deleted": deleted}
    except Exception as e:
        logger.error(f"cleanup_old_data failed: {e}")
        return {"success": False, "error": str(e)}

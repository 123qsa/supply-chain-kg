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
    source: str,
    found: List[str],
    method: str = "bfs",
    market: str = "us"
) -> bool:
    """Log a discovery event

    Args:
        source: Source company symbol
        found: List of discovered symbols
        method: Discovery method (bfs, peers, etf, etc.)
        market: Market type

    Returns:
        True if successful
    """
    try:
        async with PostgresClient() as db:
            for symbol in found:
                await db.log_discovery(
                    explorer=source,
                    discovered=symbol,
                    relation_type=method,
                    source=market,
                    depth=0
                )
            return True
    except Exception as e:
        logger.error(f"log_discovery_event failed: {e}")
        return False


async def log_impact_analysis(
    event: str,
    affected_companies: List[str],
    impact_score: float = 0.5,
    confidence: float = 0.8
) -> bool:
    """Log an impact analysis result

    Args:
        event: Event description
        affected_companies: List of affected company tickers
        impact_score: Numerical impact score (0-1)
        confidence: Confidence level (0-1)

    Returns:
        True if successful
    """
    try:
        async with PostgresClient() as db:
            for ticker in affected_companies:
                await db.log_impact(
                    event=event,
                    source="analysis",
                    affected=ticker,
                    direction="中性" if impact_score == 0.5 else ("利好" if impact_score > 0.5 else "利空"),
                    magnitude=_score_to_magnitude(abs(impact_score - 0.5) * 2),
                    reasoning=f"Automated analysis for event: {event[:50]}...",
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
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: str = "us",
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """Get price history for a symbol

    Args:
        ticker: Stock symbol
        start_date: Start date (YYYY-MM-DD), defaults to 30 days ago
        end_date: End date (YYYY-MM-DD), defaults to today
        market: Market type
        limit: Maximum rows to return

    Returns:
        List of price records
    """
    try:
        if not start_date:
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            from datetime import datetime
            end_date = datetime.now().strftime('%Y-%m-%d')

        async with PostgresClient() as db:
            rows = await db.fetch(
                """
                SELECT date, open, high, low, close, volume
                FROM stock_prices
                WHERE symbol = $1 AND market = $2 AND date BETWEEN $3 AND $4
                ORDER BY date DESC
                LIMIT $5
                """,
                ticker, market, start_date, end_date, limit
            )
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"get_price_history failed: {e}")
        return []


async def get_discovery_history(
    source: Optional[str] = None,
    method: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get discovery history

    Args:
        source: Optional source filter
        method: Optional method filter
        limit: Maximum rows to return

    Returns:
        List of discovery log entries
    """
    try:
        async with PostgresClient() as db:
            conditions = ["1=1"]
            params = []
            param_idx = 1

            if source:
                conditions.append(f"explorer_ticker = ${param_idx}")
                params.append(source)
                param_idx += 1

            if method:
                conditions.append(f"relation_type = ${param_idx}")
                params.append(method)
                param_idx += 1

            query = f"""
                SELECT explorer_ticker, discovered_ticker, relation_type, source, depth, discovered_at
                FROM discovery_log
                WHERE {' AND '.join(conditions)}
                ORDER BY discovered_at DESC
                LIMIT ${param_idx}
            """
            params.append(limit)

            rows = await db.fetch(query, *params)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"get_discovery_history failed: {e}")
        return []


async def get_impact_history(
    event_keyword: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get impact analysis history

    Args:
        event_keyword: Optional event keyword filter
        limit: Maximum rows to return

    Returns:
        List of impact log entries
    """
    try:
        async with PostgresClient() as db:
            if event_keyword:
                rows = await db.fetch(
                    """
                    SELECT event_description, source_ticker, affected_ticker,
                           direction, magnitude, reasoning, confidence, analyzed_at
                    FROM event_impact_log
                    WHERE event_description ILIKE $1
                    ORDER BY analyzed_at DESC
                    LIMIT $2
                    """,
                    f"%{event_keyword}%", limit
                )
            else:
                rows = await db.fetch(
                    """
                    SELECT event_description, source_ticker, affected_ticker,
                           direction, magnitude, reasoning, confidence, analyzed_at
                    FROM event_impact_log
                    ORDER BY analyzed_at DESC
                    LIMIT $1
                    """,
                    limit
                )
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

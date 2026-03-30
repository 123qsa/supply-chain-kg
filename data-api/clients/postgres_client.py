"""PostgreSQL database client"""
import asyncpg
from typing import Optional, List, Dict, Any
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class PostgresClient:
    """PostgreSQL database client"""

    _pool: Optional[asyncpg.Pool] = None

    def __init__(self):
        """Initialize client instance for context manager usage"""
        pass

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close connection"""
        await self.close()
        return False

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            settings = get_settings()
            cls._pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                min_size=5,
                max_size=20
            )
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Execute a query without returning results"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    @classmethod
    async def log_discovery(cls, explorer: str, discovered: str,
                           relation_type: str, source: str, depth: int) -> None:
        """Log a discovery event"""
        query = """
        INSERT INTO discovery_log (explorer_ticker, discovered_ticker, relation_type, source, depth)
        VALUES ($1, $2, $3, $4, $5)
        """
        await cls.execute(query, explorer, discovered, relation_type, source, depth)

    @classmethod
    async def log_impact(cls, event: str, source: str, affected: str,
                        direction: str, magnitude: str, reasoning: str,
                        confidence: float) -> None:
        """Log an impact analysis result"""
        query = """
        INSERT INTO event_impact_log (event_description, source_ticker, affected_ticker,
                                      direction, magnitude, reasoning, confidence)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await cls.execute(query, event, source, affected, direction, magnitude, reasoning, confidence)

    @classmethod
    async def save_prices(cls, symbol: str, market: str, prices: List[Dict[str, Any]]) -> int:
        """Save price data, return count inserted"""
        if not prices:
            return 0

        query = """
        INSERT INTO stock_prices (symbol, market, date, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (symbol, date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """

        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            count = 0
            for price in prices:
                await conn.execute(
                    query,
                    symbol,
                    market,
                    price.get("date"),
                    price.get("open"),
                    price.get("high"),
                    price.get("low"),
                    price.get("close"),
                    price.get("volume")
                )
                count += 1
            return count
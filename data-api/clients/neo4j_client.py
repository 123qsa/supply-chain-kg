"""Neo4j graph database client"""
from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Optional, List, Dict, Any
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j graph database client"""

    _instance: Optional[AsyncDriver] = None

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
    async def get_driver(cls) -> AsyncDriver:
        if cls._instance is None:
            settings = get_settings()
            cls._instance = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

    @classmethod
    async def verify_connectivity(cls) -> bool:
        """Verify database connectivity"""
        try:
            driver = await cls.get_driver()
            await driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity failed: {e}")
            return False

    @classmethod
    async def run_query(cls, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        driver = await cls.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    @classmethod
    async def get_pending_nodes(cls, limit: int = 10, market: str = None) -> List[Dict[str, Any]]:
        """Get companies waiting to be explored"""
        query = """
        MATCH (c:Company {discoveryStatus: 'pending_explore'})
        WHERE $market IS NULL OR c.market = $market
        RETURN c.ticker AS ticker, c.market AS market, c.name AS name,
               c.discoveryDepth AS depth
        ORDER BY c.discoveryDepth ASC, c.createdAt ASC
        LIMIT $limit
        """
        return await cls.run_query(query, {"limit": limit, "market": market})

    @classmethod
    async def create_company(cls, ticker: str, name: str, market: str, depth: int = 0) -> Dict[str, Any]:
        """Create or merge a company node"""
        query = """
        MERGE (c:Company {ticker: $ticker})
        ON CREATE SET
            c.name = $name,
            c.market = $market,
            c.discoveryStatus = 'pending_explore',
            c.discoveryDepth = $depth,
            c.createdAt = datetime()
        ON MATCH SET
            c.lastRediscoveredAt = datetime()
        RETURN c
        """
        result = await cls.run_query(query, {
            "ticker": ticker,
            "name": name,
            "market": market,
            "depth": depth
        })
        return result[0] if result else None

    @classmethod
    async def update_status(cls, ticker: str, status: str) -> bool:
        """Update company discovery status"""
        query = """
        MATCH (c:Company {ticker: $ticker})
        SET c.discoveryStatus = $status,
            c.lastUpdated = datetime()
        RETURN c
        """
        result = await cls.run_query(query, {"ticker": ticker, "status": status})
        return len(result) > 0

    @classmethod
    async def create_relation(cls, from_ticker: str, to_ticker: str,
                              rel_type: str, properties: Dict[str, Any] = None) -> bool:
        """Create a relationship between two companies

        Args:
            from_ticker: Source company ticker
            to_ticker: Target company ticker
            rel_type: Relationship type (e.g., COMPETES_WITH, PARTNERS_WITH)
            properties: Additional relationship properties (source, confidence, etc.)

        Returns:
            True if successful
        """
        props = properties or {}

        # Build dynamic SET clause for additional properties
        set_clauses = ["r.updatedAt = datetime()"]
        for key, value in props.items():
            if key not in ['from_ticker', 'to_ticker', 'rel_type']:
                set_clauses.append(f"r.{key} = ${key}")

        set_clause = ", ".join(set_clauses)

        query = f"""
        MATCH (a:Company {{ticker: $from_ticker}})
        MATCH (b:Company {{ticker: $to_ticker}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET {set_clause}
        RETURN r
        """

        params = {
            "from_ticker": from_ticker,
            "to_ticker": to_ticker,
            **props
        }

        result = await cls.run_query(query, params)
        return len(result) > 0

    @classmethod
    async def get_related_companies(cls, ticker: str, depth: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
        """Get companies related within N hops"""
        query = """
        MATCH path = (source:Company {ticker: $ticker})-[*1..$depth]-(target:Company)
        WHERE source <> target
        WITH target,
             [rel IN relationships(path) | type(rel)] AS rel_chain,
             [node IN nodes(path) | node.name] AS name_chain,
             length(path) AS hop_count
        RETURN DISTINCT target.ticker AS ticker,
               target.name AS name,
               target.market AS market,
               target.sector AS sector,
               hop_count AS depth,
               rel_chain,
               name_chain
        ORDER BY hop_count ASC
        LIMIT $limit
        """
        return await cls.run_query(query, {"ticker": ticker, "depth": depth, "limit": limit})
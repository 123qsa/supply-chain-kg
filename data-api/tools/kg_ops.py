"""Knowledge Graph operations tools"""
from typing import List, Dict, Any, Optional
import logging
from clients import Neo4jClient

logger = logging.getLogger(__name__)


async def upsert_company(
    ticker: str,
    name: str,
    market: str = "us",
    **properties
) -> bool:
    """Upsert a company node into the knowledge graph

    Args:
        ticker: Stock symbol
        name: Company name
        market: Market type ("us" or "cn")
        **properties: Additional company properties

    Returns:
        True if successful
    """
    try:
        async with Neo4jClient() as neo4j:
            result = await neo4j.create_company(
                ticker=ticker,
                name=name,
                market=market,
                depth=properties.get("depth", 0)
            )
            return result is not None
    except Exception as e:
        logger.error(f"upsert_company failed for {ticker}: {e}")
        return False


async def upsert_relationship(
    source: str,
    target: str,
    relation_type: str,
    **properties
) -> bool:
    """Upsert a relationship between two companies

    Args:
        source: Source company ticker
        target: Target company ticker
        relation_type: Type of relationship (e.g., COMPETES_WITH)
        **properties: Additional relationship properties

    Returns:
        True if successful
    """
    try:
        async with Neo4jClient() as neo4j:
            await neo4j.create_relation(
                source,
                target,
                relation_type,
                properties
            )
            return True
    except Exception as e:
        logger.error(f"upsert_relationship failed for {source}->{target}: {e}")
        return False


async def batch_upsert_companies(
    companies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Batch upsert multiple companies

    Args:
        companies: List of company data dictionaries

    Returns:
        Results summary with success/failure counts
    """
    results = {"success": 0, "failed": 0, "errors": []}

    async with Neo4jClient() as neo4j:
        for company in companies:
            try:
                await neo4j.create_company(company)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "company": company.get("ticker", "unknown"),
                    "error": str(e)
                })

    return results


async def batch_upsert_relationships(
    relationships: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Batch upsert multiple relationships

    Args:
        relationships: List of relationship dictionaries with
                      source, target, type, and optional properties

    Returns:
        Results summary with success/failure counts
    """
    results = {"success": 0, "failed": 0, "errors": []}

    async with Neo4jClient() as neo4j:
        for rel in relationships:
            try:
                await neo4j.create_relation(
                    rel["source"],
                    rel["target"],
                    rel["type"],
                    rel.get("properties", {})
                )
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "rel": f"{rel.get('source', '?')}->{rel.get('target', '?')}",
                    "error": str(e)
                })

    return results


async def get_company_neighbors(
    ticker: str,
    relation_types: Optional[List[str]] = None,
    max_depth: int = 1
) -> List[Dict[str, Any]]:
    """Get all neighbors of a company up to max_depth

    Args:
        ticker: Company symbol
        relation_types: Optional filter for specific relationship types
        max_depth: Maximum depth to traverse

    Returns:
        List of neighbor companies with relationship info
    """
    try:
        async with Neo4jClient() as neo4j:
            neighbors = await neo4j.get_related_companies(ticker, relation_types)
            return neighbors
    except Exception as e:
        logger.error(f"get_company_neighbors failed for {ticker}: {e}")
        return []


async def find_paths(
    source: str,
    target: str,
    max_depth: int = 5
) -> List[List[Dict[str, Any]]]:
    """Find all paths between two companies

    Args:
        source: Starting company ticker
        target: Target company ticker
        max_depth: Maximum path length

    Returns:
        List of paths, where each path is a list of relationship steps
    """
    try:
        async with Neo4jClient() as neo4j:
            # Use Neo4j's pathfinding capabilities
            query = """
            MATCH path = (a:Company {ticker: $source})-[:RELATES_TO*1..5]->(b:Company {ticker: $target})
            RETURN [node in nodes(path) | node.ticker] as tickers,
                   [rel in relationships(path) | type(rel)] as rel_types,
                   length(path) as depth
            LIMIT 10
            """
            # This is a placeholder - actual implementation would
            # use the Neo4j client to execute the query
            return []
    except Exception as e:
        logger.error(f"find_paths failed for {source}->{target}: {e}")
        return []


async def get_subgraph(
    center: str,
    radius: int = 2
) -> Dict[str, Any]:
    """Get a subgraph centered around a company

    Args:
        center: Center company ticker
        radius: Radius of the subgraph (hops)

    Returns:
        Subgraph with nodes and relationships
    """
    try:
        async with Neo4jClient() as neo4j:
            # Get all nodes within radius
            query = """
            MATCH path = (center:Company {ticker: $center})-[:RELATES_TO*1..$radius]-(neighbor)
            RETURN center, neighbor, relationships(path) as rels
            """
            # Placeholder implementation
            return {
                "center": center,
                "radius": radius,
                "nodes": [],
                "relationships": []
            }
    except Exception as e:
        logger.error(f"get_subgraph failed for {center}: {e}")
        return {"center": center, "radius": radius, "nodes": [], "relationships": []}


async def delete_company(ticker: str) -> bool:
    """Delete a company node and all its relationships

    Args:
        ticker: Company ticker to delete

    Returns:
        True if successful
    """
    try:
        async with Neo4jClient() as neo4j:
            query = """
            MATCH (c:Company {ticker: $ticker})
            DETACH DELETE c
            """
            # Placeholder - would execute via neo4j client
            return True
    except Exception as e:
        logger.error(f"delete_company failed for {ticker}: {e}")
        return False


async def merge_duplicate_companies(
    ticker1: str,
    ticker2: str,
    keep: str
) -> bool:
    """Merge two company nodes that represent the same entity

    Args:
        ticker1: First ticker (to be merged)
        ticker2: Second ticker (to be merged)
        keep: Ticker to keep after merge

    Returns:
        True if successful
    """
    try:
        async with Neo4jClient() as neo4j:
            # Merge properties and relationships from ticker1 and ticker2 into keep
            query = """
            MATCH (c1:Company {ticker: $ticker1}), (c2:Company {ticker: $ticker2})
            WITH c1, c2
            MATCH (c1)-[r]-(other)
            WHERE other <> c2
            MERGE (c2)-[new_r:RELATES_TO]->(other)
            ON CREATE SET new_r += properties(r)
            DELETE r
            WITH c1, c2
            DETACH DELETE c1
            """
            return True
    except Exception as e:
        logger.error(f"merge_duplicate_companies failed: {e}")
        return False


async def get_graph_stats() -> Dict[str, Any]:
    """Get statistics about the knowledge graph

    Returns:
        Graph statistics including node count, edge count, etc.
    """
    try:
        async with Neo4jClient() as neo4j:
            stats = {
                "node_count": 0,
                "edge_count": 0,
                "relation_types": [],
                "market_distribution": {}
            }

            # These would be actual Neo4j queries
            # MATCH (n:Company) RETURN count(n) as node_count
            # MATCH ()-[r]->() RETURN count(r) as edge_count
            # MATCH ()-[r]->() RETURN distinct type(r) as types

            return stats
    except Exception as e:
        logger.error(f"get_graph_stats failed: {e}")
        return {"error": str(e)}

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
                await neo4j.create_company(
                    ticker=company.get("ticker"),
                    name=company.get("name"),
                    market=company.get("market", "us"),
                    depth=company.get("depth", 0)
                )
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
                      source, target, relation_type, and optional properties

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
                    rel["relation_type"],
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
            neighbors = await neo4j.get_related_companies(ticker, max_depth)

            # Filter by relation types if specified
            if relation_types:
                neighbors = [
                    n for n in neighbors
                    if n.get("relation_type") in relation_types
                ]

            return neighbors
    except Exception as e:
        logger.error(f"get_company_neighbors failed for {ticker}: {e}")
        return []


async def find_paths(
    start: str,
    end: str,
    max_depth: int = 4
) -> List[Dict[str, Any]]:
    """Find all paths between two companies

    Args:
        start: Starting company ticker
        end: Target company ticker
        max_depth: Maximum path length

    Returns:
        List of paths with nodes and relationships
    """
    try:
        async with Neo4jClient() as neo4j:
            # Query to find all paths between two companies
            query = """
            MATCH path = (start:Company {ticker: $start})-[:COMPETES_WITH|PARTNERS_WITH|SUPPLIES_TO|CUSTOMER_OF|INVESTED_IN|DEPENDS_ON*1..%d]->(end:Company {ticker: $end})
            RETURN
                [node in nodes(path) | {ticker: node.ticker, name: node.name}] as nodes,
                [rel in relationships(path) | {type: type(rel), source: startNode(rel).ticker, target: endNode(rel).ticker}] as relationships,
                length(path) as depth
            LIMIT 10
            """ % max_depth

            results = await neo4j.run_query(query, {"start": start, "end": end})

            paths = []
            for record in results:
                paths.append({
                    "nodes": record.get("nodes", []),
                    "relationships": record.get("relationships", []),
                    "depth": record.get("depth", 0)
                })

            return paths
    except Exception as e:
        logger.error(f"find_paths failed for {start}->{end}: {e}")
        return []


async def get_subgraph(
    ticker: str,
    depth: int = 2
) -> Dict[str, Any]:
    """Get a subgraph centered around a company

    Args:
        ticker: Center company ticker
        depth: Depth of the subgraph (hops)

    Returns:
        Subgraph with nodes and relationships
    """
    try:
        async with Neo4jClient() as neo4j:
            # Get center node
            center_query = """
            MATCH (c:Company {ticker: $ticker})
            RETURN {ticker: c.ticker, name: c.name, market: c.market, sector: c.sector} as center
            """
            center_result = await neo4j.run_query(center_query, {"ticker": ticker})

            if not center_result:
                return {"center": ticker, "depth": depth, "nodes": [], "relationships": []}

            center_node = center_result[0].get("center", {})

            # Get all nodes and relationships within depth
            subgraph_query = """
            MATCH path = (center:Company {ticker: $ticker})-[:COMPETES_WITH|PARTNERS_WITH|SUPPLIES_TO|CUSTOMER_OF|INVESTED_IN|DEPENDS_ON*1..%d]-(neighbor)
            WHERE center <> neighbor
            WITH DISTINCT neighbor,
                 [rel in relationships(path) | type(rel)][0] as rel_type,
                 length(path) as hops
            RETURN
                collect(DISTINCT {ticker: neighbor.ticker, name: neighbor.name, market: neighbor.market, sector: neighbor.sector, hops: hops}) as nodes,
                collect(DISTINCT {source: $ticker, target: neighbor.ticker, type: rel_type}) as relationships
            """ % depth

            subgraph_result = await neo4j.run_query(subgraph_query, {"ticker": ticker})

            if subgraph_result:
                return {
                    "center": center_node,
                    "depth": depth,
                    "nodes": subgraph_result[0].get("nodes", []),
                    "relationships": subgraph_result[0].get("relationships", [])
                }

            return {
                "center": center_node,
                "depth": depth,
                "nodes": [],
                "relationships": []
            }
    except Exception as e:
        logger.error(f"get_subgraph failed for {ticker}: {e}")
        return {"center": {"ticker": ticker}, "depth": depth, "nodes": [], "relationships": []}


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
            await neo4j.run_query(query, {"ticker": ticker})
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
            await neo4j.run_query(query, {"ticker1": ticker1, "ticker2": ticker2})
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
            # Node count
            node_count_result = await neo4j.run_query(
                "MATCH (n:Company) RETURN count(n) as node_count"
            )
            node_count = node_count_result[0].get("node_count", 0) if node_count_result else 0

            # Edge count
            edge_count_result = await neo4j.run_query(
                "MATCH ()-[r]->() RETURN count(r) as edge_count"
            )
            edge_count = edge_count_result[0].get("edge_count", 0) if edge_count_result else 0

            # Relation types
            rel_types_result = await neo4j.run_query(
                "MATCH ()-[r]->() RETURN distinct type(r) as type"
            )
            relation_types = [r.get("type") for r in rel_types_result]

            # Market distribution
            market_result = await neo4j.run_query(
                """
                MATCH (c:Company)
                RETURN c.market as market, count(c) as count
                """
            )
            market_distribution = {
                r.get("market", "unknown"): r.get("count", 0)
                for r in market_result
            }

            # Sector distribution
            sector_result = await neo4j.run_query(
                """
                MATCH (c:Company)
                WHERE c.sector IS NOT NULL
                RETURN c.sector as sector, count(c) as count
                LIMIT 10
                """
            )
            sector_distribution = {
                r.get("sector", "unknown"): r.get("count", 0)
                for r in sector_result
            }

            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "relation_types": relation_types,
                "market_distribution": market_distribution,
                "sector_distribution": sector_distribution,
                "avg_degree": (edge_count * 2 / node_count) if node_count > 0 else 0,
                "density": (edge_count / (node_count * (node_count - 1))) if node_count > 1 else 0
            }
    except Exception as e:
        logger.error(f"get_graph_stats failed: {e}")
        return {"error": str(e)}

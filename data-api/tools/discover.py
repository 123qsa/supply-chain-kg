"""Discovery tools for finding relationships between companies"""
from typing import List, Dict, Any, Optional
import logging
from clients import OpenBBClient, AkShareClient, Neo4jClient

logger = logging.getLogger(__name__)

# Relationship type constants
REL_COMPETES_WITH = "COMPETES_WITH"
REL_IN_ETF = "IN_ETF"
REL_SAME_SECTOR = "SAME_SECTOR"
REL_SAME_CONCEPT = "SAME_CONCEPT"
REL_SUPPLIES_TO = "SUPPLIES_TO"
REL_CUSTOMER_OF = "CUSTOMER_OF"
REL_PARTNERS_WITH = "PARTNERS_WITH"
REL_INVESTED_IN = "INVESTED_IN"
REL_DEPENDS_ON = "DEPENDS_ON"


async def discover_peers(symbol: str, market: str = "us") -> List[Dict[str, Any]]:
    """Discover peer companies (competitors) for a given symbol

    Args:
        symbol: Stock symbol (e.g., "NVDA")
        market: Market type ("us" or "cn")

    Returns:
        List of peer companies with standardized format
    """
    try:
        if market == "us":
            async with OpenBBClient() as client:
                peers = await client.discover_peers(symbol)
                return [
                    {
                        "ticker": p.get("symbol", p.get("ticker", "")),
                        "name": p.get("name", ""),
                        "relation": REL_COMPETES_WITH,
                        "source": "openbb"
                    }
                    for p in peers
                ]
        else:
            # For CN market, use sector/industry classification
            ak_client = AkShareClient()
            # Try to find companies in same concept board
            concept_boards = ["芯片概念", "人工智能", "半导体"]  # Common boards for tech
            results = []
            for board in concept_boards:
                try:
                    companies = ak_client.discover_cn_concept(board)
                    for c in companies:
                        if c.get("代码") != symbol:
                            results.append({
                                "ticker": c.get("代码", ""),
                                "name": c.get("名称", ""),
                                "relation": REL_SAME_CONCEPT,
                                "source": "akshare",
                                "board": board
                            })
                except Exception:
                    continue
            return results[:20]  # Limit results
    except Exception as e:
        logger.error(f"discover_peers failed for {symbol}: {e}")
        return []


async def discover_etf_holdings(symbol: str) -> List[Dict[str, Any]]:
    """Discover ETF holdings for a given ETF symbol

    Args:
        symbol: ETF symbol (e.g., "SOXX")

    Returns:
        List of ETF constituents
    """
    try:
        async with OpenBBClient() as client:
            holdings = await client.discover_etf_holdings(symbol)
            return [
                {
                    "ticker": h.get("symbol", h.get("ticker", "")),
                    "name": h.get("name", ""),
                    "relation": REL_IN_ETF,
                    "source": "openbb",
                    "etf": symbol,
                    "weight": h.get("weight", None)
                }
                for h in holdings
            ]
    except Exception as e:
        logger.error(f"discover_etf_holdings failed for {symbol}: {e}")
        return []


async def discover_institutional(symbol: str, market: str = "us") -> List[Dict[str, Any]]:
    """Discover institutional holders for a given symbol

    Args:
        symbol: Stock symbol
        market: Market type ("us" or "cn")

    Returns:
        List of institutional holders
    """
    try:
        if market == "us":
            async with OpenBBClient() as client:
                holders = await client.discover_institutional(symbol)
                return [
                    {
                        "holder": h.get("investor", h.get("holder", "")),
                        "shares": h.get("shares", 0),
                        "relation": REL_INVESTED_IN,
                        "source": "openbb"
                    }
                    for h in holders
                ]
        else:
            ak_client = AkShareClient()
            holders = ak_client.discover_cn_holders(symbol)
            return [
                {
                    "holder": h.get("股东名称", ""),
                    "shares": h.get("持股数量", 0),
                    "relation": REL_INVESTED_IN,
                    "source": "akshare"
                }
                for h in holders
            ]
    except Exception as e:
        logger.error(f"discover_institutional failed for {symbol}: {e}")
        return []


async def bfs_discovery(
    start_symbol: str,
    market: str = "us",
    max_depth: int = 3
) -> List[Dict[str, Any]]:
    """Breadth-first search to discover supply chain relationships

    Starting from a seed company, discover related companies up to max_depth
    levels of relationships.

    Args:
        start_symbol: Starting company symbol
        market: Market type ("us" or "cn")
        max_depth: Maximum relationship depth to explore

    Returns:
        List of discovered companies with relationship chains
    """
    visited = {start_symbol}
    queue = [(start_symbol, 0, [])]  # (symbol, depth, path)
    results = []

    async with Neo4jClient() as neo4j:
        while queue:
            current, depth, path = queue.pop(0)

            if depth >= max_depth:
                continue

            # Discover peers (competitors)
            peers = await discover_peers(current, market)
            for peer in peers:
                ticker = peer["ticker"]
                if ticker and ticker not in visited:
                    visited.add(ticker)
                    new_path = path + [{
                        "from": current,
                        "to": ticker,
                        "relation": peer["relation"]
                    }]
                    queue.append((ticker, depth + 1, new_path))
                    results.append({
                        **peer,
                        "depth": depth + 1,
                        "path": new_path,
                        "source_symbol": start_symbol
                    })

            # Check for existing relationships in Neo4j
            try:
                related = await neo4j.get_related_companies(current)
                for rel in related:
                    target = rel.get("target")
                    if target and target not in visited:
                        visited.add(target)
                        new_path = path + [{
                            "from": current,
                            "to": target,
                            "relation": rel.get("type", "RELATED")
                        }]
                        queue.append((target, depth + 1, new_path))
                        results.append({
                            "ticker": target,
                            "name": rel.get("name", ""),
                            "relation": rel.get("type", "RELATED"),
                            "depth": depth + 1,
                            "path": new_path,
                            "source_symbol": start_symbol
                        })
            except Exception as e:
                logger.warning(f"Neo4j query failed during BFS: {e}")

    return results


async def expand_node(
    symbol: str,
    market: str = "us",
    relation_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Expand a single node to discover its relationships

    Similar to BFS but for a single depth level, used by n8n workflows
    for incremental graph expansion.

    Args:
        symbol: Company symbol to expand
        market: Market type
        relation_types: Optional filter for specific relationship types

    Returns:
        Dictionary with discovered relationships
    """
    results = {
        "symbol": symbol,
        "market": market,
        "relations": []
    }

    # Always get peers
    if not relation_types or REL_COMPETES_WITH in relation_types:
        peers = await discover_peers(symbol, market)
        results["relations"].extend(peers)

    # For US market, also check ETF holdings if it's an ETF
    if market == "us" and (not relation_types or REL_IN_ETF in relation_types):
        # Only query ETF holdings if symbol looks like an ETF
        if len(symbol) <= 4 and symbol.isalpha():
            try:
                holdings = await discover_etf_holdings(symbol)
                results["relations"].extend(holdings)
            except Exception:
                pass

    # Check Neo4j for existing relationships
    async with Neo4jClient() as neo4j:
        try:
            related = await neo4j.get_related_companies(symbol)
            for rel in related:
                if not relation_types or rel.get("type") in relation_types:
                    results["relations"].append({
                        "ticker": rel.get("target"),
                        "name": rel.get("name", ""),
                        "relation": rel.get("type", "RELATED"),
                        "source": "neo4j"
                    })
        except Exception as e:
            logger.warning(f"Neo4j expand failed: {e}")

    return results

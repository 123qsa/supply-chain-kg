"""Discovery tools for finding relationships between companies"""
from typing import List, Dict, Any, Optional
import logging
from clients import YahooFinanceClient, AkShareClient, Neo4jClient

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
            async with YahooFinanceClient() as client:
                peers = client.discover_peers(symbol)
                return [
                    {
                        "ticker": p.get("symbol", ""),
                        "name": p.get("name", ""),
                        "sector": p.get("sector", ""),
                        "industry": p.get("industry", ""),
                        "relation": p.get("relation", REL_COMPETES_WITH),
                        "source": "yahoo_finance"
                    }
                    for p in peers
                    if p.get("symbol") and p.get("symbol") != symbol
                ]
        else:
            # For CN market, use AkShare
            with AkShareClient() as client:
                # Try to find companies in same concept board
                concept_boards = ["芯片概念", "人工智能", "半导体", "5G概念", "新能源"]
                results = []
                for board in concept_boards:
                    try:
                        companies = client.discover_cn_concept(board)
                        for c in companies:
                            code = c.get("代码", "")
                            if code and code != symbol:
                                results.append({
                                    "ticker": code,
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
        async with YahooFinanceClient() as client:
            holdings = client.discover_etf_holdings(symbol)
            return [
                {
                    "ticker": h.get("symbol", ""),
                    "name": h.get("name", ""),
                    "relation": REL_IN_ETF,
                    "source": "yahoo_finance",
                    "etf": symbol,
                    "weight": h.get("weight")
                }
                for h in holdings
                if h.get("symbol")
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
            async with YahooFinanceClient() as client:
                holders = client.get_institutional_holders(symbol)
                return [
                    {
                        "holder": h.get("holder", ""),
                        "shares": h.get("shares", 0),
                        "pct_out": h.get("pct_out", 0),
                        "relation": REL_INVESTED_IN,
                        "source": "yahoo_finance"
                    }
                    for h in holders
                ]
        else:
            with AkShareClient() as client:
                holders = client.discover_cn_holders(symbol)
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
) -> Dict[str, Any]:
    """Breadth-first search to discover supply chain relationships

    Starting from a seed company, discover related companies up to max_depth
    levels of relationships.

    Args:
        start_symbol: Starting company symbol
        market: Market type ("us" or "cn")
        max_depth: Maximum relationship depth to explore

    Returns:
        Dictionary with discovered companies and relationships
    """
    visited = {start_symbol}
    queue = [(start_symbol, 0, [])]  # (symbol, depth, path)
    companies = []
    relationships = []

    async with Neo4jClient() as neo4j:
        while queue:
            current, depth, path = queue.pop(0)

            if depth >= max_depth:
                continue

            # Discover peers (competitors)
            peers = await discover_peers(current, market)
            for peer in peers:
                ticker = peer.get("ticker")
                if ticker and ticker not in visited:
                    visited.add(ticker)
                    new_path = path + [{
                        "from": current,
                        "to": ticker,
                        "relation": peer.get("relation", REL_COMPETES_WITH)
                    }]
                    queue.append((ticker, depth + 1, new_path))

                    companies.append({
                        "ticker": ticker,
                        "name": peer.get("name", ""),
                        "market": market,
                        "sector": peer.get("sector", ""),
                        "industry": peer.get("industry", ""),
                        "depth": depth + 1,
                        "source": peer.get("source", "discovery")
                    })

                    relationships.append({
                        "source": current,
                        "target": ticker,
                        "relation_type": peer.get("relation", REL_COMPETES_WITH),
                        "properties": {"discovered_at": "now()", "source": peer.get("source", "discovery")}
                    })

            # Check for existing relationships in Neo4j
            try:
                related = await neo4j.get_related_companies(current)
                for rel in related:
                    target = rel.get("ticker")
                    rel_type = rel.get("relation_type", "RELATED")
                    if target and target not in visited:
                        visited.add(target)
                        new_path = path + [{
                            "from": current,
                            "to": target,
                            "relation": rel_type
                        }]
                        queue.append((target, depth + 1, new_path))

                        companies.append({
                            "ticker": target,
                            "name": rel.get("name", ""),
                            "market": market,
                            "sector": rel.get("sector", ""),
                            "depth": depth + 1,
                            "source": "neo4j"
                        })

                        relationships.append({
                            "source": current,
                            "target": target,
                            "relation_type": rel_type,
                            "properties": {"source": "neo4j"}
                        })
            except Exception as e:
                logger.warning(f"Neo4j query failed during BFS: {e}")

    return {
        "start_symbol": start_symbol,
        "market": market,
        "max_depth": max_depth,
        "companies_discovered": len(companies),
        "companies": companies,
        "relationships": relationships
    }


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
                if not relation_types or rel.get("relation_type") in relation_types:
                    results["relations"].append({
                        "ticker": rel.get("ticker"),
                        "name": rel.get("name", ""),
                        "relation": rel.get("relation_type", "RELATED"),
                        "source": "neo4j"
                    })
        except Exception as e:
            logger.warning(f"Neo4j expand failed: {e}")

    return results

"""AI Analysis tools for event impact assessment"""
from typing import List, Dict, Any, Optional
import logging
from clients import KimiClient, Neo4jClient

logger = logging.getLogger(__name__)


async def analyze_event_impact(
    event: str,
    companies: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Analyze event impact on related companies using LLM

    Args:
        event: Event description (e.g., "NVIDIA announces new AI chip")
        companies: List of company data with relationship chains
        context: Optional additional context

    Returns:
        List of impact assessments for each company
    """
    if not companies:
        return []

    try:
        async with KimiClient() as kimi:
            # Prepare company data with relationship paths
            enriched_companies = []
            for c in companies:
                enriched = {
                    "ticker": c.get("ticker", ""),
                    "name": c.get("name", ""),
                    "depth": c.get("depth", 0),
                    "relation": c.get("relation", "RELATED"),
                    "name_chain": _build_name_chain(c.get("path", [])),
                    **c
                }
                enriched_companies.append(enriched)

            # Call Kimi for analysis
            result = await kimi.analyze_impact(event, enriched_companies)

            if result.get("error"):
                logger.error(f"Kimi analysis error: {result['error']}")
                return []

            # Process and validate results
            impacts = result.get("results", [])
            validated_impacts = []

            for impact in impacts:
                validated = {
                    "ticker": impact.get("ticker", ""),
                    "company": impact.get("company", ""),
                    "direction": _validate_direction(impact.get("direction", "中性")),
                    "magnitude": _validate_magnitude(impact.get("magnitude", "低")),
                    "reasoning": impact.get("reasoning", ""),
                    "confidence": float(impact.get("confidence", 0.5)),
                    "event": event
                }
                validated_impacts.append(validated)

            return validated_impacts

    except Exception as e:
        logger.error(f"analyze_event_impact failed: {e}")
        return []


def _build_name_chain(path: List[Dict[str, Any]]) -> List[str]:
    """Build human-readable chain from path"""
    if not path:
        return []

    chain = []
    for step in path:
        chain.append(f"{step.get('from')} --[{step.get('relation')}]--> {step.get('to')}")
    return chain


def _validate_direction(direction: str) -> str:
    """Validate and normalize impact direction"""
    valid = ["利好", "利空", "中性", "positive", "negative", "neutral"]
    direction_lower = direction.lower()

    if direction_lower in ["利好", "positive", "bullish"]:
        return "利好"
    elif direction_lower in ["利空", "negative", "bearish"]:
        return "利空"
    return "中性"


def _validate_magnitude(magnitude: str) -> str:
    """Validate and normalize impact magnitude"""
    valid_high = ["高", "high", "大", "large"]
    valid_medium = ["中", "medium", "med", "moderate"]
    valid_low = ["低", "low", "小", "small"]

    mag_lower = magnitude.lower()

    if mag_lower in valid_high:
        return "高"
    elif mag_lower in valid_medium:
        return "中"
    return "低"


async def analyze_supply_chain_impact(
    event: str,
    start_symbol: str,
    max_depth: int = 3
) -> Dict[str, Any]:
    """Analyze impact across the entire supply chain starting from a company

    This combines graph traversal with LLM analysis for comprehensive
    supply chain impact assessment.

    Args:
        event: Event description
        start_symbol: Starting company symbol
        max_depth: Maximum relationship depth to analyze

    Returns:
        Complete impact analysis with graph data
    """
    from tools.discover import bfs_discovery

    # Discover related companies
    discovered = await bfs_discovery(start_symbol, max_depth=max_depth)

    if not discovered:
        return {
            "event": event,
            "start_symbol": start_symbol,
            "companies_analyzed": 0,
            "impacts": [],
            "graph_stats": {}
        }

    # Analyze impact on discovered companies
    impacts = await analyze_event_impact(event, discovered)

    # Aggregate statistics
    direction_counts = {"利好": 0, "利空": 0, "中性": 0}
    magnitude_counts = {"高": 0, "中": 0, "低": 0}

    for impact in impacts:
        direction_counts[impact["direction"]] += 1
        magnitude_counts[impact["magnitude"]] += 1

    return {
        "event": event,
        "start_symbol": start_symbol,
        "companies_analyzed": len(impacts),
        "impacts": impacts,
        "discovered_companies": discovered,
        "graph_stats": {
            "total_discovered": len(discovered),
            "max_depth_reached": max((c.get("depth", 0) for c in discovered), default=0),
            "direction_distribution": direction_counts,
            "magnitude_distribution": magnitude_counts,
            "avg_confidence": sum(i.get("confidence", 0) for i in impacts) / len(impacts) if impacts else 0
        }
    }


async def generate_impact_summary(
    analysis_result: Dict[str, Any]
) -> str:
    """Generate human-readable summary of impact analysis

    Args:
        analysis_result: Result from analyze_supply_chain_impact

    Returns:
        Markdown-formatted summary string
    """
    event = analysis_result.get("event", "")
    stats = analysis_result.get("graph_stats", {})
    impacts = analysis_result.get("impacts", [])

    lines = [
        f"# 产业链影响分析报告\n",
        f"## 事件\n{event}\n",
        f"## 统计概览\n",
        f"- 分析公司数: {stats.get('total_discovered', 0)}",
        f"- 最大关联深度: {stats.get('max_depth_reached', 0)}",
        f"- 平均置信度: {stats.get('avg_confidence', 0):.2%}\n",
        f"### 影响方向分布\n",
        f"- 利好: {stats.get('direction_distribution', {}).get('利好', 0)}",
        f"- 利空: {stats.get('direction_distribution', {}).get('利空', 0)}",
        f"- 中性: {stats.get('direction_distribution', {}).get('中性', 0)}\n",
        f"### 影响程度分布\n",
        f"- 高: {stats.get('magnitude_distribution', {}).get('高', 0)}",
        f"- 中: {stats.get('magnitude_distribution', {}).get('中', 0)}",
        f"- 低: {stats.get('magnitude_distribution', {}).get('低', 0)}\n",
        f"## 详细影响分析\n"
    ]

    # Sort by magnitude (high first) then confidence
    sorted_impacts = sorted(
        impacts,
        key=lambda x: (
            {"高": 3, "中": 2, "低": 1}.get(x.get("magnitude", "低"), 0),
            x.get("confidence", 0)
        ),
        reverse=True
    )

    for impact in sorted_impacts[:20]:  # Top 20
        lines.append(f"### {impact.get('company', '')} ({impact.get('ticker', '')})")
        lines.append(f"- **影响方向**: {impact.get('direction', '')}")
        lines.append(f"- **影响程度**: {impact.get('magnitude', '')}")
        lines.append(f"- **置信度**: {impact.get('confidence', 0):.1%}")
        lines.append(f"- **分析理由**: {impact.get('reasoning', '')}")
        lines.append("")

    return "\n".join(lines)

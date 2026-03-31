"""MCP Server implementation for Supply Chain Knowledge Graph"""
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from tools import (
    discover_peers,
    discover_etf_holdings,
    discover_institutional,
    bfs_discovery,
    expand_node,
    get_profile,
    get_price,
    get_financials,
    batch_collect,
    analyze_event_impact,
    analyze_supply_chain_impact,
    generate_impact_summary,
    upsert_company,
    upsert_relationship,
    batch_upsert_companies,
    batch_upsert_relationships,
    get_company_neighbors,
    find_paths,
    get_subgraph,
    delete_company,
    get_graph_stats,
    save_price_batch,
    log_discovery_event,
    log_impact_analysis,
    get_price_history,
    get_discovery_history,
    get_impact_history,
)

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP tool request"""
    tool: str
    params: Dict[str, Any] = {}
    request_id: Optional[str] = None


class MCPResponse(BaseModel):
    """MCP tool response"""
    result: Any = None
    error: Optional[str] = None
    request_id: Optional[str] = None


# Tool registry
TOOLS: Dict[str, Callable] = {
    # Discovery tools
    "discover_peers": discover_peers,
    "discover_etf_holdings": discover_etf_holdings,
    "discover_institutional": discover_institutional,
    "bfs_discovery": bfs_discovery,
    "expand_node": expand_node,
    # Collection tools
    "get_profile": get_profile,
    "get_price": get_price,
    "get_financials": get_financials,
    "batch_collect": batch_collect,
    # Analysis tools
    "analyze_event_impact": analyze_event_impact,
    "analyze_supply_chain_impact": analyze_supply_chain_impact,
    "generate_impact_summary": generate_impact_summary,
    # KG operations
    "upsert_company": upsert_company,
    "upsert_relationship": upsert_relationship,
    "batch_upsert_companies": batch_upsert_companies,
    "batch_upsert_relationships": batch_upsert_relationships,
    "get_company_neighbors": get_company_neighbors,
    "find_paths": find_paths,
    "get_subgraph": get_subgraph,
    "delete_company": delete_company,
    "get_graph_stats": get_graph_stats,
    # DB operations
    "save_price_batch": save_price_batch,
    "log_discovery_event": log_discovery_event,
    "log_impact_analysis": log_impact_analysis,
    "get_price_history": get_price_history,
    "get_discovery_history": get_discovery_history,
    "get_impact_history": get_impact_history,
}


# Tool schemas for MCP protocol
TOOL_SCHEMAS = {
    "discover_peers": {
        "name": "discover_peers",
        "description": "Discover peer companies (competitors) for a given stock symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol (e.g., NVDA)"},
                "market": {"type": "string", "description": "Market type: us or cn", "default": "us"}
            },
            "required": ["symbol"]
        }
    },
    "discover_etf_holdings": {
        "name": "discover_etf_holdings",
        "description": "Discover ETF holdings/constituents for a given ETF symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "ETF symbol (e.g., SOXX)"}
            },
            "required": ["symbol"]
        }
    },
    "bfs_discovery": {
        "name": "bfs_discovery",
        "description": "Breadth-first search to discover supply chain relationships",
        "parameters": {
            "type": "object",
            "properties": {
                "start_symbol": {"type": "string", "description": "Starting company symbol"},
                "market": {"type": "string", "description": "Market type", "default": "us"},
                "max_depth": {"type": "integer", "description": "Maximum depth", "default": 3}
            },
            "required": ["start_symbol"]
        }
    },
    "expand_node": {
        "name": "expand_node",
        "description": "Expand a single node to discover its direct relationships",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Company symbol to expand"},
                "market": {"type": "string", "description": "Market type", "default": "us"},
                "relation_types": {"type": "array", "description": "Optional relation type filter"}
            },
            "required": ["symbol"]
        }
    },
    "get_profile": {
        "name": "get_profile",
        "description": "Get company profile information",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "market": {"type": "string", "description": "Market type", "default": "us"}
            },
            "required": ["symbol"]
        }
    },
    "get_price": {
        "name": "get_price",
        "description": "Get historical price data",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "market": {"type": "string", "description": "Market type", "default": "us"}
            },
            "required": ["symbol", "start_date", "end_date"]
        }
    },
    "batch_collect": {
        "name": "batch_collect",
        "description": "Collect data for multiple symbols in batch",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "description": "List of stock symbols"},
                "market": {"type": "string", "description": "Market type", "default": "us"},
                "include_profile": {"type": "boolean", "default": True},
                "include_price": {"type": "boolean", "default": True},
                "price_start": {"type": "string"},
                "price_end": {"type": "string"}
            },
            "required": ["symbols"]
        }
    },
    "analyze_event_impact": {
        "name": "analyze_event_impact",
        "description": "Analyze event impact on companies using LLM",
        "parameters": {
            "type": "object",
            "properties": {
                "event": {"type": "string", "description": "Event description"},
                "companies": {"type": "array", "description": "List of company data"},
                "context": {"type": "object", "description": "Optional context"}
            },
            "required": ["event", "companies"]
        }
    },
    "analyze_supply_chain_impact": {
        "name": "analyze_supply_chain_impact",
        "description": "Analyze impact across entire supply chain",
        "parameters": {
            "type": "object",
            "properties": {
                "event": {"type": "string", "description": "Event description"},
                "start_symbol": {"type": "string", "description": "Starting company"},
                "max_depth": {"type": "integer", "default": 3}
            },
            "required": ["event", "start_symbol"]
        }
    },
    "upsert_company": {
        "name": "upsert_company",
        "description": "Upsert a company node into knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "name": {"type": "string"},
                "market": {"type": "string", "default": "us"}
            },
            "required": ["ticker", "name"]
        }
    },
    "upsert_relationship": {
        "name": "upsert_relationship",
        "description": "Create relationship between two companies",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "target": {"type": "string"},
                "relation_type": {"type": "string"}
            },
            "required": ["source", "target", "relation_type"]
        }
    },
    "batch_upsert_companies": {
        "name": "batch_upsert_companies",
        "description": "Batch upsert multiple companies",
        "parameters": {
            "type": "object",
            "properties": {
                "companies": {"type": "array"}
            },
            "required": ["companies"]
        }
    },
    "get_company_neighbors": {
        "name": "get_company_neighbors",
        "description": "Get neighbors of a company from knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "relation_types": {"type": "array"},
                "max_depth": {"type": "integer", "default": 1}
            },
            "required": ["ticker"]
        }
    },
    "save_price_batch": {
        "name": "save_price_batch",
        "description": "Save price data batch to database",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string"},
                "prices": {"type": "array"}
            },
            "required": ["ticker", "market", "prices"]
        }
    },
    "discover_institutional": {
        "name": "discover_institutional",
        "description": "Discover institutional holders for a given stock symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol (e.g., NVDA)"},
                "market": {"type": "string", "description": "Market type: us or cn", "default": "us"}
            },
            "required": ["symbol"]
        }
    },
    "get_financials": {
        "name": "get_financials",
        "description": "Get financial data for a company",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "market": {"type": "string", "description": "Market type", "default": "us"}
            },
            "required": ["symbol"]
        }
    },
    "generate_impact_summary": {
        "name": "generate_impact_summary",
        "description": "Generate human-readable impact summary from analysis results",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis_results": {"type": "array", "description": "Analysis results from analyze_event_impact"},
                "event": {"type": "string", "description": "Event description"}
            },
            "required": ["analysis_results", "event"]
        }
    },
    "batch_upsert_relationships": {
        "name": "batch_upsert_relationships",
        "description": "Batch upsert multiple relationships",
        "parameters": {
            "type": "object",
            "properties": {
                "relationships": {"type": "array", "description": "List of relationship objects with source, target, relation_type"}
            },
            "required": ["relationships"]
        }
    },
    "find_paths": {
        "name": "find_paths",
        "description": "Find paths between two companies in the knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "Starting company ticker"},
                "end": {"type": "string", "description": "Ending company ticker"},
                "max_depth": {"type": "integer", "description": "Maximum path depth", "default": 4}
            },
            "required": ["start", "end"]
        }
    },
    "get_subgraph": {
        "name": "get_subgraph",
        "description": "Extract subgraph around a company",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Center company ticker"},
                "depth": {"type": "integer", "description": "Depth of subgraph", "default": 2}
            },
            "required": ["ticker"]
        }
    },
    "delete_company": {
        "name": "delete_company",
        "description": "Delete a company node from the knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Company ticker to delete"}
            },
            "required": ["ticker"]
        }
    },
    "get_graph_stats": {
        "name": "get_graph_stats",
        "description": "Get knowledge graph statistics",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "get_price_history": {
        "name": "get_price_history",
        "description": "Query price history from TimescaleDB",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker"},
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "limit": {"type": "integer", "description": "Max rows to return", "default": 1000}
            },
            "required": ["ticker"]
        }
    },
    "get_discovery_history": {
        "name": "get_discovery_history",
        "description": "Query discovery history log",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source symbol filter"},
                "method": {"type": "string", "description": "Discovery method filter"},
                "limit": {"type": "integer", "description": "Max rows", "default": 100}
            }
        }
    },
    "get_impact_history": {
        "name": "get_impact_history",
        "description": "Query impact analysis history",
        "parameters": {
            "type": "object",
            "properties": {
                "event_keyword": {"type": "string", "description": "Event keyword filter"},
                "limit": {"type": "integer", "description": "Max rows", "default": 100}
            }
        }
    },
}


def create_mcp_router(app: FastAPI):
    """Create MCP routes for FastAPI app"""

    @app.get("/mcp/tools")
    async def list_tools():
        """List available MCP tools"""
        return {
            "tools": list(TOOL_SCHEMAS.values())
        }

    @app.post("/mcp/call", response_model=MCPResponse)
    async def call_tool(request: MCPRequest):
        """Execute an MCP tool"""
        tool_name = request.tool
        params = request.params
        request_id = request.request_id

        if tool_name not in TOOLS:
            return MCPResponse(
                error=f"Unknown tool: {tool_name}",
                request_id=request_id
            )

        try:
            tool_func = TOOLS[tool_name]
            result = await tool_func(**params)
            return MCPResponse(result=result, request_id=request_id)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return MCPResponse(
                error=str(e),
                request_id=request_id
            )

    @app.post("/mcp/call/{tool_name}", response_model=MCPResponse)
    async def call_tool_by_path(tool_name: str, request: Request):
        """Execute tool via path parameter"""
        try:
            body = await request.json()
            params = body.get("params", {})
            request_id = body.get("request_id")
        except Exception:
            params = {}
            request_id = None

        if tool_name not in TOOLS:
            return MCPResponse(
                error=f"Unknown tool: {tool_name}",
                request_id=request_id
            )

        try:
            tool_func = TOOLS[tool_name]
            result = await tool_func(**params)
            return MCPResponse(result=result, request_id=request_id)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return MCPResponse(
                error=str(e),
                request_id=request_id
            )

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "tools_available": len(TOOLS),
            "version": "1.0.0"
        }


# Legacy SSE endpoint for MCP (optional)
async def mcp_sse_handler(request: Request):
    """SSE handler for streaming MCP responses"""
    from fastapi.responses import StreamingResponse
    import asyncio

    async def event_generator():
        while True:
            # Send heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

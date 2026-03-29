# n8n Workflows

This directory contains n8n workflow configurations for the supply chain knowledge graph system.

## Overview

The system uses n8n for workflow orchestration with 10 main workflows:

| Workflow | ID | Description | Trigger |
|----------|-----|-------------|---------|
| Seed | WF-0 | Initialize graph with seed company | Manual |
| BFS Discovery | WF-1 | Expand graph via BFS | Schedule (daily) |
| Batch Collect | WF-2 | Fetch company data | Schedule (daily after close) |
| Event Impact | WF-3 | Analyze event impact | Webhook/Manual |
| Price Alert | WF-4 | Monitor price changes | Schedule (hourly) |
| Graph Analytics | WF-5 | Calculate centrality metrics | Schedule (weekly) |
| Report | WF-6 | Generate reports | Schedule (weekly) |
| Health Check | WF-7 | System health monitoring | Schedule (hourly) |
| Data Sync | WF-8 | Sync external data | Schedule (daily) |
| Cleanup | WF-9 | Data retention cleanup | Schedule (monthly) |

## MCP Integration

All workflows communicate with the data-api via MCP (Model Context Protocol):

### MCP Server Configuration
```
URL: http://data-api:8000/mcp/call
Authentication: None (internal network)
```

### Available MCP Tools

**Discovery:**
- `discover_peers` - Find competitor companies
- `discover_etf_holdings` - Get ETF constituents
- `bfs_discovery` - BFS graph expansion
- `expand_node` - Single node expansion

**Collection:**
- `get_profile` - Company profile data
- `get_price` - Historical prices
- `batch_collect` - Batch data collection

**Analysis:**
- `analyze_event_impact` - LLM impact analysis
- `analyze_supply_chain_impact` - Full chain analysis

**Knowledge Graph:**
- `upsert_company` - Create/update company node
- `upsert_relationship` - Create relationship
- `get_company_neighbors` - Get related companies

**Database:**
- `save_price_batch` - Save prices to TimescaleDB
- `log_discovery_event` - Log discovery
- `log_impact_analysis` - Log impact results

## Workflow Examples

### WF-1: BFS Discovery
```json
{
  "nodes": [
    {
      "type": "schedule",
      "name": "Daily Trigger"
    },
    {
      "type": "mcp-tool",
      "name": "Get Pending Nodes",
      "tool": "get_pending_nodes"
    },
    {
      "type": "mcp-tool",
      "name": "Expand Node",
      "tool": "expand_node"
    },
    {
      "type": "mcp-tool",
      "name": "Upsert Companies",
      "tool": "batch_upsert_companies"
    }
  ]
}
```

### WF-3: Event Impact
```json
{
  "nodes": [
    {
      "type": "webhook",
      "name": "Event Webhook"
    },
    {
      "type": "mcp-tool",
      "name": "Analyze Impact",
      "tool": "analyze_supply_chain_impact"
    },
    {
      "type": "mcp-tool",
      "name": "Log Results",
      "tool": "log_impact_analysis"
    }
  ]
}
```

## Setup Instructions

1. Start n8n: `docker-compose up n8n`
2. Access n8n UI: http://localhost:5678
3. Import workflows from this directory
4. Configure MCP credentials (API endpoint: `http://data-api:8000`)

## Environment Variables

Required in n8n:
- `DATA_API_URL` - MCP server endpoint
- `NEO4J_URI` - Neo4j connection
- `POSTGRES_URI` - PostgreSQL connection

## Importing Workflows

```bash
# Import all workflows
n8n import:workflow --input=./workflows/

# Or import individually via UI
# Settings > Workflows > Import
```

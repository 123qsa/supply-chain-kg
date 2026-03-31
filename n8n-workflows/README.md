# n8n Workflows

This directory contains n8n workflow configurations for the supply chain knowledge graph system.

## Workflow Files

| File | Workflow | Description |
|------|----------|-------------|
| [wf-0-seed.json](wf-0-seed.json) | WF-0 | Seed initialization with NVDA |
| [wf-1-bfs-crawler.json](wf-1-bfs-crawler.json) | WF-1 | BFS discovery crawler (runs every 6 hours) |
| [wf-2-batch-collect.json](wf-2-batch-collect.json) | WF-2 | Batch data collection (daily at 21:00) |
| [wf-3-event-impact.json](wf-3-event-impact.json) | WF-3 | Event impact analysis webhook |
| [wf-4-price-alert.json](wf-4-price-alert.json) | WF-4 | Price alert monitor (hourly) |
| [wf-5-graph-analytics.json](wf-5-graph-analytics.json) | WF-5 | Graph analytics (weekly) |
| [wf-6-weekly-report.json](wf-6-weekly-report.json) | WF-6 | Weekly report generation |
| [wf-7-health-check.json](wf-7-health-check.json) | WF-7 | System health monitoring (hourly) |
| [wf-8-data-sync.json](wf-8-data-sync.json) | WF-8 | Daily data synchronization |
| [wf-9-cleanup.json](wf-9-cleanup.json) | WF-9 | Monthly data cleanup |

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

### Via n8n UI

1. Open n8n at http://localhost:5678
2. Go to **Workflows** → **Import from File**
3. Select one of the JSON files from this directory:
   - Start with `wf-0-seed.json` to initialize the graph
   - Then import `wf-1-bfs-crawler.json` for automated discovery
   - Import `wf-3-event-impact.json` for event analysis

### Via CLI (requires n8n CLI)

```bash
# Import a single workflow
n8n import:workflow --input=./n8n-workflows/wf-0-seed.json

# Import all workflows
for f in n8n-workflows/wf-*.json; do
  n8n import:workflow --input="$f"
done
```

### Automated Setup Script

```bash
# Run the setup script to import all workflows
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @n8n-workflows/wf-0-seed.json
```

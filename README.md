# Supply Chain Knowledge Graph + AI Double-Layer Architecture

A comprehensive supply chain knowledge graph system with Neo4j (memory layer) and LLM (reasoning layer), orchestrated via n8n workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    n8n Workflows (10)                        │
│  WF-0 → WF-1 → WF-2 → ... → WF-9                            │
│  Seed → BFS → Collect → Impact → Alert → Analytics → Report │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (FastAPI + 26+ Tools)               │
│  • Discovery: peers, ETF holdings, BFS                      │
│  • Collection: profiles, prices, financials                 │
│  • Analysis: LLM impact assessment                          │
│  • KG Ops: Neo4j graph operations                           │
│  • DB Ops: TimescaleDB storage                              │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  Layer 1: Memory        │     │  Layer 2: Reasoning     │
│  Neo4j Knowledge Graph  │     │  Kimi LLM (OAuth)       │
│                         │     │                         │
│  • Company nodes        │     │  • Impact analysis      │
│  • 9 relationship types │◄────┤  • Chain reasoning      │
│  • BFS traversal        │     │  • Confidence scoring   │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  TimescaleDB            │     │  External Data Sources  │
│  • Price time-series    │     │  • OpenBB (US/Global)   │
│  • Discovery logs       │     │  • AkShare (A-share)    │
│  • Impact analysis log  │     │                         │
└─────────────────────────┘     └─────────────────────────┘
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd supply-chain-kg

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
./scripts/verify-setup.sh
```

### 3. Initialize Graph

```bash
# Seed with NVIDIA as starting point
curl -X POST http://localhost:8000/mcp/call/upsert_company \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "ticker": "NVDA",
      "name": "NVIDIA Corporation",
      "market": "us",
      "sector": "Technology"
    }
  }'
```

### 4. Run Discovery

```bash
# BFS discovery from NVDA
curl -X POST http://localhost:8000/mcp/call/bfs_discovery \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "start_symbol": "NVDA",
      "market": "us",
      "max_depth": 2
    }
  }'
```

### 5. Access Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| n8n | http://localhost:5678 | Workflow orchestration |
| Data API | http://localhost:8000/docs | FastAPI documentation |
| Neo4j Browser | http://localhost:7474 | Graph visualization |

## Project Structure

```
.
├── docker-compose.yml          # All services configuration
├── .env.example                # Environment template
├── data-api/                   # FastAPI MCP Server
│   ├── main.py                 # FastAPI application
│   ├── mcp_server.py           # MCP protocol implementation
│   ├── config.py               # Configuration management
│   ├── clients/                # Data source clients
│   │   ├── neo4j_client.py     # Neo4j driver
│   │   ├── postgres_client.py  # PostgreSQL/TimescaleDB
│   │   ├── openbb_client.py    # OpenBB API (US/Global)
│   │   ├── akshare_client.py   # AkShare (A-share)
│   │   └── kimi_client.py      # LLM OAuth client
│   ├── tools/                  # MCP tool implementations
│   │   ├── discover.py         # Discovery tools
│   │   ├── collect.py          # Data collection
│   │   ├── analyze.py          # LLM analysis
│   │   ├── kg_ops.py           # Graph operations
│   │   └── db_ops.py           # Database operations
│   ├── tests/                  # Test suite
│   └── Dockerfile              # Container build
├── init-scripts/               # Database initialization
│   ├── neo4j-init.cypher       # Neo4j schema + seed
│   └── postgres-init.sql       # TimescaleDB schema
├── n8n-workflows/              # n8n workflow configs
└── scripts/                    # Utility scripts
    └── verify-setup.sh         # Setup verification
```

## MCP Tools (26+)

### Discovery Tools
| Tool | Description |
|------|-------------|
| `discover_peers` | Find competitor companies |
| `discover_etf_holdings` | Get ETF constituents |
| `discover_institutional` | Find institutional holders |
| `bfs_discovery` | BFS graph expansion |
| `expand_node` | Single node expansion |

### Collection Tools
| Tool | Description |
|------|-------------|
| `get_profile` | Company profile data |
| `get_price` | Historical price data |
| `get_financials` | Financial summary |
| `batch_collect` | Batch data collection |

### Analysis Tools
| Tool | Description |
|------|-------------|
| `analyze_event_impact` | LLM impact on companies |
| `analyze_supply_chain_impact` | Full chain analysis |
| `generate_impact_summary` | Human-readable report |

### Knowledge Graph Tools
| Tool | Description |
|------|-------------|
| `upsert_company` | Create/update company node |
| `upsert_relationship` | Create relationship |
| `batch_upsert_companies` | Batch company upsert |
| `batch_upsert_relationships` | Batch relationship upsert |
| `get_company_neighbors` | Get related companies |
| `find_paths` | Find paths between companies |
| `get_subgraph` | Extract subgraph |
| `get_graph_stats` | Graph statistics |

### Database Tools
| Tool | Description |
|------|-------------|
| `save_price_batch` | Save prices to TimescaleDB |
| `log_discovery_event` | Log discovery event |
| `log_impact_analysis` | Log impact analysis |
| `get_price_history` | Query price history |
| `get_discovery_history` | Query discovery log |
| `get_impact_history` | Query impact log |

## Relationship Types (9)

1. **SUPPLIES_TO** - Supply chain relationship
2. **CUSTOMER_OF** - Customer relationship
3. **COMPETES_WITH** - Competitor relationship
4. **PARTNERS_WITH** - Partnership
5. **INVESTED_IN** - Investment relationship
6. **SAME_SECTOR** - Same industry sector
7. **SAME_CONCEPT** - Same concept/theme
8. **IN_ETF** - ETF constituent
9. **DEPENDS_ON** - Dependency relationship

## n8n Workflows

| ID | Workflow | Trigger | Description |
|----|----------|---------|-------------|
| WF-0 | Seed | Manual | Initialize with seed company |
| WF-1 | BFS Discovery | Daily | Expand graph via BFS |
| WF-2 | Batch Collect | Daily | Fetch company data |
| WF-3 | Event Impact | Webhook | Analyze event impact |
| WF-4 | Price Alert | Hourly | Monitor price changes |
| WF-5 | Graph Analytics | Weekly | Calculate metrics |
| WF-6 | Report | Weekly | Generate reports |
| WF-7 | Health Check | Hourly | Monitor system health |
| WF-8 | Data Sync | Daily | Sync external data |
| WF-9 | Cleanup | Monthly | Data retention cleanup |

## Environment Variables

```bash
# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=supply-chain-kg

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=supply_chain
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# OpenBB (US/Global markets)
OPENBB_PAT=your_personal_access_token

# Kimi (LLM)
KIMI_CLIENT_ID=your_client_id
KIMI_CLIENT_SECRET=your_client_secret

# n8n
N8N_ENCRYPTION_KEY=your_encryption_key

# Data API
DATA_API_HOST=0.0.0.0
DATA_API_PORT=8000
```

## Example Usage

### Discover NVIDIA's Competitors

```bash
curl -X POST http://localhost:8000/mcp/call/discover_peers \
  -H "Content-Type: application/json" \
  -d '{"params": {"symbol": "NVDA", "market": "us"}}'
```

### Analyze Event Impact

```bash
curl -X POST http://localhost:8000/mcp/call/analyze_supply_chain_impact \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "event": "NVIDIA announces new AI chip architecture",
      "start_symbol": "NVDA",
      "max_depth": 2
    }
  }'
```

### Get Price Data

```bash
curl -X POST http://localhost:8000/mcp/call/get_price \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "symbol": "NVDA",
      "start_date": "2024-01-01",
      "end_date": "2024-03-01",
      "market": "us"
    }
  }'
```

## Testing

```bash
# Run tests
cd data-api
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_discover.py -v
```

## Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs -f <service_name>

# Verify setup
./scripts/verify-setup.sh
```

### Neo4j connection issues
```bash
# Reset Neo4j
docker-compose down neo4j
docker volume rm supply-chain_neo4j_data
docker-compose up -d neo4j
```

### API not responding
```bash
# Restart data-api
docker-compose restart data-api

# Check logs
docker-compose logs -f data-api
```

## License

MIT License - See LICENSE file for details.

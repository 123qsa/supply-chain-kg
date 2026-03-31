# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Supply Chain Knowledge Graph + AI Double-Layer Architecture** system.
It combines Neo4j (memory layer) with a Kimi LLM (reasoning layer), orchestrated
via n8n workflows. A FastAPI-based MCP (Model Context Protocol) server exposes
26+ tools for discovery, data collection, graph operations, and AI analysis.

## Common Commands

**Start all services:**
```bash
docker-compose up -d
```

**Verify setup:**
```bash
./scripts/verify-setup.sh
```

**View service logs:**
```bash
docker-compose logs -f data-api
docker-compose logs -f neo4j
```

**Restart the API:**
```bash
docker-compose restart data-api
```

**Run tests:**
```bash
cd data-api
python -m pytest tests/ -v
python -m pytest tests/test_discover.py -v
python -m pytest tests/test_config.py -v
```

**Lint / type-check:** There is no configured linter or formatter (no `ruff`,
`black`, `mypy`, etc. configured yet).

**Install local dependencies:**
```bash
cd data-api
pip install -r requirements.txt
```

## High-Level Architecture

### Services (docker-compose.yml)
- **n8n** (`:5678`) — Workflow orchestration
- **data-api** (`:8000`) — FastAPI MCP server
- **neo4j** (`:7474` browser, `:7687` bolt) — Graph database
- **postgres** (`:5432`) — TimescaleDB for time-series and logs
- **redis** (`:6379`) — Cache

### Layered Design
```
n8n Workflows (WF-0 .. WF-9)
         │
         ▼
   MCP Server (FastAPI)
         │
    ┌────┴────┐
    ▼         ▼
Neo4j      Kimi LLM
(Memory)   (Reasoning)
    │         │
    ▼         ▼
TimescaleDB  OpenBB / AkShare
```

### MCP Server (`data-api/`)

**Entry points:**
- `main.py` — Creates the FastAPI app, registers CORS, and calls `create_mcp_router(app)`.
- `mcp_server.py` — Defines the `TOOLS` registry (dict of name → async callable)
  and `TOOL_SCHEMAS` (parameter specs), then mounts HTTP routes.

**Exposed HTTP routes:**
- `GET  /mcp/tools` — List available tools
- `POST /mcp/call` — Execute a tool (body: `{tool, params, request_id}`)
- `POST /mcp/call/{tool_name}` — Execute a tool by path
- `GET  /health` — Health check
- `GET  /api/v1/status` — Feature-flags for connected services

**Tool categories (`data-api/tools/`):**
- `discover.py` — Peer/ETF/institutional discovery, BFS graph expansion
- `collect.py` — Price, profile, financial data fetching
- `analyze.py` — Event impact analysis via Kimi LLM, summary generation
- `kg_ops.py` — Neo4j CRUD: upsert companies, relationships, neighbors, paths
- `db_ops.py` — TimescaleDB ops: save prices, log discovery/impact

**Relationship constants** (defined in `tools/discover.py`):
`SUPPLIES_TO`, `CUSTOMER_OF`, `COMPETES_WITH`, `PARTNERS_WITH`, `INVESTED_IN`,
`SAME_SECTOR`, `SAME_CONCEPT`, `IN_ETF`, `DEPENDS_ON`

### Clients (`data-api/clients/`)

Each client wraps an external service and is exposed via `clients/__init__.py`.
- `Neo4jClient` — Singleton `AsyncDriver` via `AsyncGraphDatabase.driver(...)`
- `PostgresClient` — Singleton `asyncpg.Pool`
- `OpenBBClient` — US/Global market data (async context manager)
- `AkShareClient` — CN A-share data
- `KimiClient` — OAuth-based LLM client for impact analysis

**Important:** Several tool modules use `async with Neo4jClient() as neo4j:` and
`async with PostgresClient() as db:`, but the current client classes do **not**
implement `__aenter__` / `__aexit__`. They only expose `@classmethod` helpers
(`get_driver`, `get_pool`, `run_query`, etc.). When editing these files, be
aware that either the context-manager usage needs to be replaced with direct
calls, or the clients need `__aenter__` / `__aexit__` added.

### Configuration

`data-api/config.py` uses Pydantic `BaseSettings` with `.env` file support.
Key env vars:
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `OPENBB_PAT`
- `KIMI_CLIENT_ID`, `KIMI_CLIENT_SECRET`

### n8n Workflows

Workflows are documented in `n8n-workflows/README.md`. They call the MCP server
at `http://data-api:8000/mcp/call`.

| ID | Name | Trigger |
|--|--|--|
| WF-0 | Seed | Manual |
| WF-1 | BFS Discovery | Daily |
| WF-2 | Batch Collect | Daily |
| WF-3 | Event Impact | Webhook |
| WF-4 | Price Alert | Hourly |
| WF-5 | Graph Analytics | Weekly |
| WF-6 | Report | Weekly |
| WF-7 | Health Check | Hourly |
| WF-8 | Data Sync | Daily |
| WF-9 | Cleanup | Monthly |

### Database Initialization

- `init-scripts/neo4j-init.cypher` — Runs automatically on first Neo4j startup.
  Creates unique constraint on `Company.ticker`, indexes, and seeds NVIDIA with
  initial peers/partners.
- `init-scripts/postgres-init.sql` — Runs automatically on first TimescaleDB
  startup. Creates the `prices` hypertable, `discovery_log`, `impact_log`, and
  `company_cache`.

## Notable Code Patterns

1. **MCP tool registration is manual.** `mcp_server.py` imports every tool
   individually and lists it in `TOOLS`. `TOOL_SCHEMAS` is also manually
   maintained. Some tools exported in `tools/__init__.py` (e.g. `find_paths`,
   `get_subgraph`, `delete_company`) are **not** registered in `TOOLS` or
   `TOOL_SCHEMAS` and therefore not reachable via HTTP.

2. **Tests use `unittest.mock.patch`.** `test_discover.py` patches
   `tools.discover.openbb` to avoid real API calls. `test_config.py` asserts
   default Pydantic-settings values and the `@lru_cache` behavior of
   `get_settings()`.

3. **Error handling style:** Most tools catch broad exceptions, log an error,
   and return an empty list / empty dict / `False` rather than raising. This is
   by design so the n8n workflows can continue on partial failures.

# Init Scripts

This directory contains initialization scripts for the supply chain knowledge graph system.

## Files

### neo4j-init.cypher
Initial Neo4j graph setup:
- Creates constraints (unique ticker)
- Creates indexes (market, sector)
- Seeds initial company (NVIDIA) with known relationships
- Sets up sample competitors and partners

### postgres-init.sql
Initial PostgreSQL/TimescaleDB setup:
- Enables TimescaleDB extension
- Creates prices hypertable for time-series data
- Creates discovery_log table for tracking discoveries
- Creates impact_log table for impact analysis results
- Creates company_cache table for metadata caching

## Usage

These scripts are automatically executed when the Docker containers start for the first time.

### Manual Execution

**Neo4j:**
```bash
cypher-shell -u neo4j -p password < neo4j-init.cypher
```

**PostgreSQL:**
```bash
psql -U postgres -d supply_chain < postgres-init.sql
```

## Schema Notes

### Neo4j Graph Schema
- **Node**: `Company` (ticker, name, market, sector, industry, description)
- **Relationships**: `COMPETES_WITH`, `PARTNERS_WITH`, `SUPPLIES_TO`, `CUSTOMER_OF`, `IN_ETF`, `INVESTED_IN`, `DEPENDS_ON`, `SAME_SECTOR`, `SAME_CONCEPT`

### PostgreSQL Schema
- **prices**: Time-series data (TimescaleDB hypertable)
- **discovery_log**: BFS discovery event tracking
- **impact_log**: LLM impact analysis results
- **company_cache**: Company metadata cache

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create price data hypertable (matches db_ops.py queries)
CREATE TABLE IF NOT EXISTS stock_prices (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    UNIQUE(symbol, time)
);

-- Convert to hypertable
SELECT create_hypertable('stock_prices', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices (symbol, market);
CREATE INDEX IF NOT EXISTS idx_stock_prices_time ON stock_prices (time DESC);

-- Create discovery log table (matches PostgresClient.log_discovery)
CREATE TABLE IF NOT EXISTS discovery_log (
    id SERIAL PRIMARY KEY,
    explorer_ticker TEXT NOT NULL,
    discovered_ticker TEXT NOT NULL,
    relation_type TEXT,
    source TEXT,
    depth INTEGER DEFAULT 0,
    discovered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes on discovery log
CREATE INDEX IF NOT EXISTS idx_discovery_explorer ON discovery_log (explorer_ticker);
CREATE INDEX IF NOT EXISTS idx_discovery_discovered ON discovery_log (discovered_ticker);
CREATE INDEX IF NOT EXISTS idx_discovery_time ON discovery_log (discovered_at DESC);

-- Create event impact log table (matches PostgresClient.log_impact)
CREATE TABLE IF NOT EXISTS event_impact_log (
    id SERIAL PRIMARY KEY,
    event_description TEXT NOT NULL,
    source_ticker TEXT,
    affected_ticker TEXT NOT NULL,
    direction TEXT,
    magnitude TEXT,
    reasoning TEXT,
    confidence DOUBLE PRECISION,
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes on impact log
CREATE INDEX IF NOT EXISTS idx_impact_affected ON event_impact_log (affected_ticker);
CREATE INDEX IF NOT EXISTS idx_impact_event ON event_impact_log (event_description);
CREATE INDEX IF NOT EXISTS idx_impact_time ON event_impact_log (analyzed_at DESC);

-- Create company metadata cache table
CREATE TABLE IF NOT EXISTS company_cache (
    ticker TEXT PRIMARY KEY,
    market TEXT NOT NULL,
    name TEXT,
    sector TEXT,
    industry TEXT,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on company cache
CREATE INDEX IF NOT EXISTS idx_company_cache_market ON company_cache (market);

-- Create health checks table for WF-7
CREATE TABLE IF NOT EXISTS health_checks (
    id SERIAL PRIMARY KEY,
    status TEXT NOT NULL,
    details JSONB,
    check_time TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_checks_time ON health_checks (check_time DESC);

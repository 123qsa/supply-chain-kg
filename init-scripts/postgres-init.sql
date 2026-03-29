-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create price data hypertable
CREATE TABLE IF NOT EXISTS prices (
    time TIMESTAMPTZ NOT NULL,
    ticker TEXT NOT NULL,
    market TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT
);

-- Convert to hypertable
SELECT create_hypertable('prices', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices (ticker, market);
CREATE INDEX IF NOT EXISTS idx_prices_time ON prices (time DESC);

-- Create discovery log table
CREATE TABLE IF NOT EXISTS discovery_log (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    discovered_count INTEGER,
    discovery_type TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on discovery log
CREATE INDEX IF NOT EXISTS idx_discovery_source ON discovery_log (source);
CREATE INDEX IF NOT EXISTS idx_discovery_time ON discovery_log (created_at DESC);

-- Create impact analysis log table
CREATE TABLE IF NOT EXISTS impact_log (
    id SERIAL PRIMARY KEY,
    event TEXT NOT NULL,
    ticker TEXT NOT NULL,
    impact_score DOUBLE PRECISION,
    direction TEXT,
    confidence DOUBLE PRECISION,
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on impact log
CREATE INDEX IF NOT EXISTS idx_impact_ticker ON impact_log (ticker);
CREATE INDEX IF NOT EXISTS idx_impact_event ON impact_log (event);
CREATE INDEX IF NOT EXISTS idx_impact_time ON impact_log (created_at DESC);

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
CREATE INDEX IF NOT EXISTS idx_company_market ON company_cache (market);

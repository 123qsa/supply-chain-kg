#!/bin/bash
# Setup verification script for Supply Chain Knowledge Graph

set -e

echo "================================"
echo "Supply Chain KG Setup Verification"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding"
        return 1
    fi
}

echo "Checking services..."
echo ""

# Check Neo4j
check_service "Neo4j (HTTP)" "http://localhost:7474" || true
check_service "Neo4j (Bolt)" "bolt://localhost:7687" || true
echo ""

# Check PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL is running"
else
    echo -e "${RED}✗${NC} PostgreSQL is not responding"
fi
echo ""

# Check Redis
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is running"
else
    echo -e "${RED}✗${NC} Redis is not responding"
fi
echo ""

# Check Data API
check_service "Data API" "http://localhost:8000/health" || true
echo ""

# Check n8n
check_service "n8n" "http://localhost:5678/healthz" || true
echo ""

echo "================================"
echo "Checking environment variables..."
echo "================================"
echo ""

# Check required env vars
if [ -f .env ]; then
    source .env
fi

check_env() {
    local var=$1
    if [ -n "${!var}" ]; then
        echo -e "${GREEN}✓${NC} $var is set"
    else
        echo -e "${YELLOW}⚠${NC} $var is not set"
    fi
}

check_env "NEO4J_URI"
check_env "POSTGRES_HOST"
check_env "OPENBB_PAT"
check_env "KIMI_CLIENT_ID"
check_env "N8N_ENCRYPTION_KEY"

echo ""
echo "================================"
echo "Checking Python dependencies..."
echo "================================"
echo ""

# Check Python packages
check_pkg() {
    local pkg=$1
    if python3 -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $pkg installed"
    else
        echo -e "${RED}✗${NC} $pkg not found"
    fi
}

check_pkg "fastapi" || true
check_pkg "neo4j" || true
check_pkg "asyncpg" || true
check_pkg "httpx" || true

echo ""
echo "================================"
echo "Verification complete"
echo "================================"

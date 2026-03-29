# 供应链知识图谱 + AI 双层架构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的产业链知识图谱系统，支持从 NVDA 种子自动扩散发现产业链公司，采集行情财务数据，并通过 AI 双层架构分析事件影响。

**Architecture:** FastAPI MCP Server 作为数据服务层，提供统一接口供 n8n 工作流调用；Neo4j 存储知识图谱关系，PostgreSQL 存储时序数据，Redis 作为缓存；n8n 编排 10 个工作流实现自动化。

**Tech Stack:** Python 3.11, FastAPI, Neo4j 5.x, PostgreSQL 15 + TimescaleDB, Redis 7, n8n, OpenBB, AkShare, Kimi API

---

## 文件结构规划

```
Supply-Chain_Analysis/
├── docker-compose.yml              # 基础设施编排
├── .env                            # 环境变量
├── .env.example                    # 环境变量示例
├── data-api/                       # FastAPI MCP Server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI 应用入口
│   ├── mcp_server.py               # MCP 协议实现
│   ├── config.py                   # 配置管理
│   ├── clients/                    # 数据源客户端
│   │   ├── __init__.py
│   │   ├── openbb_client.py        # OpenBB 封装
│   │   ├── akshare_client.py       # AkShare 封装
│   │   ├── kimi_client.py          # Kimi OAuth 封装
│   │   ├── neo4j_client.py         # Neo4j 连接
│   │   └── postgres_client.py      # PostgreSQL 连接
│   ├── tools/                      # MCP 工具定义
│   │   ├── __init__.py
│   │   ├── discover.py             # 发现接口
│   │   ├── collect.py              # 采集接口
│   │   ├── analyze.py              # AI 分析接口
│   │   ├── kg_ops.py               # 图谱操作
│   │   └── db_ops.py               # 数据库操作
│   └── tests/                      # 单元测试
│       ├── __init__.py
│       ├── test_clients.py
│       └── test_tools.py
├── init-scripts/                   # 初始化脚本
│   ├── neo4j-init.cypher           # Neo4j 初始种子 + 索引
│   └── postgres-init.sql           # PostgreSQL 表结构
├── n8n-workflows/                  # n8n 工作流导出
│   └── README.md
└── docs/
    └── superpowers/
        ├── specs/                  # 设计文档
        └── plans/                  # 本文件
```

---

## Phase 1: 项目基础设置

### Task 1: 创建环境变量模板

**Files:**
- Create: `.env.example`

- [ ] **Step 1: 创建环境变量模板文件**

```bash
cat > .env.example << 'EOF'
# Neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# PostgreSQL
POSTGRES_PASSWORD=your_postgres_password_here

# n8n
N8N_PASSWORD=your_n8n_password_here

# OpenBB
OPENBB_PAT=your_openbb_pat_here

# Kimi OAuth
KIMI_CLIENT_ID=your_kimi_client_id_here
KIMI_CLIENT_SECRET=your_kimi_client_secret_here
EOF
```

- [ ] **Step 2: 复制为实际环境变量文件（本地开发用）**

```bash
cp .env.example .env
```

- [ ] **Step 3: Commit**

```bash
git add .env.example .gitignore
git commit -m "chore: add environment variable template"
```

---

### Task 2: 创建 .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: 创建 .gitignore 文件**

```bash
cat > .gitignore << 'EOF'
# Environment
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Data directories
neo4j/data/
postgres/data/
redis/data/
n8n_data/

# n8n
.n8n/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
EOF
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add gitignore"
```

---

### Task 3: 创建 Docker Compose 配置

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: "3.8"

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-kg
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - EXECUTIONS_TIMEOUT=600
      - GENERIC_TIMEZONE=Asia/Shanghai
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=industry_kg
      - POSTGRES_USER=nvidia
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - MCP_SERVER_URL=http://data-api:8000/mcp
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n-workflows:/backup/workflows
    depends_on:
      - neo4j
      - postgres
      - data-api

  data-api:
    build: ./data-api
    container_name: kg-data-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - OPENBB_PAT=${OPENBB_PAT}
      - KIMI_CLIENT_ID=${KIMI_CLIENT_ID}
      - KIMI_CLIENT_SECRET=${KIMI_CLIENT_SECRET}
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=industry_kg
      - POSTGRES_USER=nvidia
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
    volumes:
      - ./data-api:/app
    depends_on:
      - neo4j
      - postgres
      - redis

  neo4j:
    image: neo4j:5-community
    container_name: neo4j-kg
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_server_memory_heap_max__size=2G
      - NEO4J_server_memory_pagecache_size=1G
    volumes:
      - ./neo4j/data:/data
      - ./init-scripts/neo4j-init.cypher:/docker-entrypoint-initdb.d/init.cypher

  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: pg-kg
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=industry_kg
      - POSTGRES_USER=nvidia
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
      - ./init-scripts/postgres-init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    container_name: redis-kg
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - ./redis/data:/data

volumes:
  n8n_data:
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add docker-compose configuration"
```

---

## Phase 2: FastAPI MCP Server 核心

### Task 4: 创建 data-api 目录结构

**Files:**
- Create: `data-api/requirements.txt`

- [ ] **Step 1: 创建 requirements.txt**

```bash
mkdir -p data-api/clients data-api/tools data-api/tests

cat > data-api/requirements.txt << 'EOF'
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0

# MCP Protocol
mcp==1.0.0

# Data Sources
openbb==4.0.0
akshare==1.12.0

# Database
neo4j==5.15.0
asyncpg==0.29.0
psycopg2-binary==2.9.9
redis==5.0.1

# HTTP Client
httpx==0.26.0
aiohttp==3.9.0

# Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Utilities
python-dotenv==1.0.0
python-dateutil==2.8.2

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
httpx==0.26.0
EOF
```

- [ ] **Step 2: Commit**

```bash
git add data-api/requirements.txt
git commit -m "chore: add data-api requirements"
```

---

### Task 5: 创建配置模块

**Files:**
- Create: `data-api/config.py`
- Test: `data-api/tests/test_config.py`

- [ ] **Step 1: 编写配置类**

```python
# data-api/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration"""

    # OpenBB
    openbb_pat: str = ""

    # Kimi OAuth
    kimi_client_id: str = ""
    kimi_client_secret: str = ""

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "industry_kg"
    postgres_user: str = "nvidia"
    postgres_password: str = "password"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: 编写测试**

```python
# data-api/tests/test_config.py
import os
import pytest
from config import Settings, get_settings


def test_settings_default_values():
    """Test that settings have expected defaults"""
    settings = Settings()
    assert settings.neo4j_uri == "bolt://localhost:7687"
    assert settings.neo4j_user == "neo4j"
    assert settings.postgres_port == 5432


def test_postgres_dsn():
    """Test PostgreSQL DSN construction"""
    settings = Settings(
        postgres_host="testhost",
        postgres_port=5432,
        postgres_db="testdb",
        postgres_user="testuser",
        postgres_password="testpass"
    )
    assert settings.postgres_dsn == "postgresql://testuser:testpass@testhost:5432/testdb"


def test_get_settings_cached():
    """Test that get_settings is cached"""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
```

- [ ] **Step 3: 安装依赖并运行测试**

```bash
cd data-api
pip install -r requirements.txt -q
python -m pytest tests/test_config.py -v
```

Expected output:
```
tests/test_config.py::test_settings_default_values PASSED
tests/test_config.py::test_postgres_dsn PASSED
tests/test_config.py::test_get_settings_cached PASSED
```

- [ ] **Step 4: Commit**

```bash
git add data-api/config.py data-api/tests/test_config.py
git commit -m "feat: add configuration module with tests"
```

---

### Task 6: 创建 Neo4j 客户端

**Files:**
- Create: `data-api/clients/neo4j_client.py`
- Test: `data-api/tests/test_neo4j_client.py`

- [ ] **Step 1: 编写 Neo4j 客户端**

```python
# data-api/clients/neo4j_client.py
from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Optional, List, Dict, Any
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j graph database client"""

    _instance: Optional[AsyncDriver] = None

    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        if cls._instance is None:
            settings = get_settings()
            cls._instance = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

    @classmethod
    async def verify_connectivity(cls) -> bool:
        """Verify database connectivity"""
        try:
            driver = await cls.get_driver()
            await driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity failed: {e}")
            return False

    @classmethod
    async def run_query(cls, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        driver = await cls.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    # Company operations
    @classmethod
    async def get_pending_nodes(cls, limit: int = 10, market: str = None) -> List[Dict[str, Any]]:
        """Get companies waiting to be explored"""
        query = """
        MATCH (c:Company {discoveryStatus: 'pending_explore'})
        WHERE $market IS NULL OR c.market = $market
        RETURN c.ticker AS ticker, c.market AS market, c.name AS name,
               c.discoveryDepth AS depth
        ORDER BY c.discoveryDepth ASC, c.createdAt ASC
        LIMIT $limit
        """
        return await cls.run_query(query, {"limit": limit, "market": market})

    @classmethod
    async def create_company(cls, ticker: str, name: str, market: str, depth: int = 0) -> Dict[str, Any]:
        """Create or merge a company node"""
        query = """
        MERGE (c:Company {ticker: $ticker})
        ON CREATE SET
            c.name = $name,
            c.market = $market,
            c.discoveryStatus = 'pending_explore',
            c.discoveryDepth = $depth,
            c.createdAt = datetime()
        ON MATCH SET
            c.lastRediscoveredAt = datetime()
        RETURN c
        """
        result = await cls.run_query(query, {
            "ticker": ticker,
            "name": name,
            "market": market,
            "depth": depth
        })
        return result[0] if result else None

    @classmethod
    async def update_status(cls, ticker: str, status: str) -> bool:
        """Update company discovery status"""
        query = """
        MATCH (c:Company {ticker: $ticker})
        SET c.discoveryStatus = $status,
            c.lastUpdated = datetime()
        RETURN c
        """
        result = await cls.run_query(query, {"ticker": ticker, "status": status})
        return len(result) > 0

    @classmethod
    async def create_relation(cls, from_ticker: str, to_ticker: str,
                              rel_type: str, source: str, confidence: float = 1.0) -> bool:
        """Create a relationship between two companies"""
        query = f"""
        MATCH (a:Company {{ticker: $from_ticker}})
        MATCH (b:Company {{ticker: $to_ticker}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r.source = $source,
            r.confidence = $confidence,
            r.updatedAt = datetime()
        RETURN r
        """
        result = await cls.run_query(query, {
            "from_ticker": from_ticker,
            "to_ticker": to_ticker,
            "source": source,
            "confidence": confidence
        })
        return len(result) > 0

    @classmethod
    async def get_related_companies(cls, ticker: str, depth: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
        """Get companies related within N hops"""
        query = """
        MATCH path = (source:Company {ticker: $ticker})-[*1..$depth]-(target:Company)
        WHERE source <> target
        WITH target,
             [rel IN relationships(path) | type(rel)] AS rel_chain,
             [node IN nodes(path) | node.name] AS name_chain,
             length(path) AS hop_count
        RETURN DISTINCT target.ticker AS ticker,
               target.name AS name,
               target.market AS market,
               target.sector AS sector,
               hop_count AS depth,
               rel_chain,
               name_chain
        ORDER BY hop_count ASC
        LIMIT $limit
        """
        return await cls.run_query(query, {"ticker": ticker, "depth": depth, "limit": limit})
```

- [ ] **Step 2: 编写测试（使用 Mock）**

```python
# data-api/tests/test_neo4j_client.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from clients.neo4j_client import Neo4jClient


@pytest.fixture
def mock_driver():
    """Create a mock Neo4j driver"""
    driver = AsyncMock()
    session = AsyncMock()
    result = AsyncMock()

    driver.session.return_value.__aenter__ = AsyncMock(return_value=session)
    driver.session.return_value.__aexit__ = AsyncMock(return_value=False)
    session.run.return_value = result

    return driver, session, result


@pytest.mark.asyncio
async def test_get_pending_nodes(mock_driver):
    """Test retrieving pending nodes"""
    driver, session, result = mock_driver
    result.data = AsyncMock(return_value=[
        {"ticker": "NVDA", "market": "us", "name": "NVIDIA", "depth": 0}
    ])

    with patch.object(Neo4jClient, '_instance', driver):
        nodes = await Neo4jClient.get_pending_nodes(limit=10)

    assert len(nodes) == 1
    assert nodes[0]["ticker"] == "NVDA"


@pytest.mark.asyncio
async def test_create_company(mock_driver):
    """Test creating a company node"""
    driver, session, result = mock_driver
    result.data = AsyncMock(return_value=[{"c": {"ticker": "NVDA"}}])

    with patch.object(Neo4jClient, '_instance', driver):
        company = await Neo4jClient.create_company("NVDA", "NVIDIA", "us", 0)

    assert company is not None
    assert company["c"]["ticker"] == "NVDA"
```

- [ ] **Step 3: 运行测试**

```bash
cd data-api
python -m pytest tests/test_neo4j_client.py -v
```

- [ ] **Step 4: Commit**

```bash
git add data-api/clients/neo4j_client.py data-api/tests/test_neo4j_client.py
git commit -m "feat: add Neo4j client with CRUD operations"
```

---

### Task 7: 创建 PostgreSQL 客户端

**Files:**
- Create: `data-api/clients/postgres_client.py`

- [ ] **Step 1: 编写 PostgreSQL 客户端**

```python
# data-api/clients/postgres_client.py
import asyncpg
from typing import Optional, List, Dict, Any
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class PostgresClient:
    """PostgreSQL database client"""

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            settings = get_settings()
            cls._pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                min_size=5,
                max_size=20
            )
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Execute a query without returning results"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    # Discovery log operations
    @classmethod
    async def log_discovery(cls, explorer: str, discovered: str,
                           relation_type: str, source: str, depth: int) -> None:
        """Log a discovery event"""
        query = """
        INSERT INTO discovery_log (explorer_ticker, discovered_ticker, relation_type, source, depth)
        VALUES ($1, $2, $3, $4, $5)
        """
        await cls.execute(query, explorer, discovered, relation_type, source, depth)

    @classmethod
    async def log_impact(cls, event: str, source: str, affected: str,
                        direction: str, magnitude: str, reasoning: str,
                        confidence: float) -> None:
        """Log an impact analysis result"""
        query = """
        INSERT INTO event_impact_log (event_description, source_ticker, affected_ticker,
                                      direction, magnitude, reasoning, confidence)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await cls.execute(query, event, source, affected, direction, magnitude, reasoning, confidence)

    # Price operations
    @classmethod
    async def save_prices(cls, symbol: str, prices: List[Dict[str, Any]]) -> int:
        """Save price data, return count inserted"""
        if not prices:
            return 0

        query = """
        INSERT INTO stock_prices (symbol, date, open, high, low, close, volume, amount)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (symbol, date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            amount = EXCLUDED.amount
        """

        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            count = 0
            for price in prices:
                await conn.execute(
                    query,
                    symbol,
                    price.get("date"),
                    price.get("open"),
                    price.get("high"),
                    price.get("low"),
                    price.get("close"),
                    price.get("volume"),
                    price.get("amount")
                )
                count += 1
            return count
```

- [ ] **Step 2: Commit**

```bash
git add data-api/clients/postgres_client.py
git commit -m "feat: add PostgreSQL client with connection pooling"
```

---

### Task 8: 创建 OpenBB 客户端

**Files:**
- Create: `data-api/clients/openbb_client.py`

- [ ] **Step 1: 编写 OpenBB 客户端**

```python
# data-api/clients/openbb_client.py
from openbb import obb
from typing import List, Dict, Any, Optional
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class OpenBBClient:
    """OpenBB data source client"""

    def __init__(self):
        settings = get_settings()
        if settings.openbb_pat:
            obb.account.login(pat=settings.openbb_pat)

    def discover_peers(self, symbol: str) -> List[Dict[str, Any]]:
        """Discover competitor companies"""
        try:
            result = obb.equity.compare.peers(symbol=symbol)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get peers for {symbol}: {e}")
            return []

    def discover_etf_holdings(self, symbol: str = "SOXX") -> List[Dict[str, Any]]:
        """Discover ETF holdings"""
        try:
            result = obb.etf.holdings(symbol=symbol)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get ETF holdings for {symbol}: {e}")
            return []

    def discover_institutional(self, symbol: str) -> List[Dict[str, Any]]:
        """Discover institutional ownership"""
        try:
            result = obb.equity.ownership.institutional(symbol=symbol)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get institutional ownership for {symbol}: {e}")
            return []

    def get_profile(self, symbol: str, provider: str = "yfinance") -> Optional[Dict[str, Any]]:
        """Get company profile"""
        try:
            result = obb.equity.profile(symbol=symbol, provider=provider)
            return result.to_dict() if result else None
        except Exception as e:
            logger.error(f"Failed to get profile for {symbol}: {e}")
            return None

    def get_price(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical price data"""
        try:
            result = obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return []

    def get_income(self, symbol: str, period: str = "annual", limit: int = 4) -> List[Dict[str, Any]]:
        """Get income statement"""
        try:
            result = obb.equity.fundamental.income(symbol=symbol, period=period, limit=limit)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get income for {symbol}: {e}")
            return []

    def get_estimates(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get analyst estimates"""
        try:
            result = obb.equity.estimates.consensus(symbol=symbol)
            return result.to_dict() if result else None
        except Exception as e:
            logger.error(f"Failed to get estimates for {symbol}: {e}")
            return None

    def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get company news"""
        try:
            result = obb.news.company(symbol=symbol, limit=limit)
            return result.to_dict() if result else []
        except Exception as e:
            logger.error(f"Failed to get news for {symbol}: {e}")
            return []
```

- [ ] **Step 2: Commit**

```bash
git add data-api/clients/openbb_client.py
git commit -m "feat: add OpenBB client for US/global market data"
```

---

### Task 9: 创建 AkShare 客户端

**Files:**
- Create: `data-api/clients/akshare_client.py`

- [ ] **Step 1: 编写 AkShare 客户端**

```python
# data-api/clients/akshare_client.py
import akshare as ak
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AkShareClient:
    """AkShare data source client for A-share markets"""

    def discover_cn_concept(self, board_name: str) -> List[Dict[str, Any]]:
        """Discover companies in a concept board"""
        try:
            df = ak.stock_board_concept_cons_em(symbol=board_name)
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get concept board {board_name}: {e}")
            return []

    def discover_cn_industry(self, board_name: str) -> List[Dict[str, Any]]:
        """Discover companies in an industry board"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=board_name)
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get industry board {board_name}: {e}")
            return []

    def discover_cn_holders(self, symbol: str) -> List[Dict[str, Any]]:
        """Discover top 10 shareholders"""
        try:
            df = ak.stock_main_stock_holder(stock=symbol)
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get holders for {symbol}: {e}")
            return []

    def get_cn_price(self, symbol: str, start_date: str = "20240101",
                     end_date: str = "20261231") -> List[Dict[str, Any]]:
        """Get A-share historical price data"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get CN price for {symbol}: {e}")
            return []

    def get_cn_financial(self, symbol: str) -> List[Dict[str, Any]]:
        """Get A-share financial summary"""
        try:
            df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按年度")
            return df.to_dict(orient="records") if df is not None else []
        except Exception as e:
            logger.error(f"Failed to get CN financial for {symbol}: {e}")
            return []
```

- [ ] **Step 2: Commit**

```bash
git add data-api/clients/akshare_client.py
git commit -m "feat: add AkShare client for A-share market data"
```

---

### Task 10: 创建 Kimi 客户端

**Files:**
- Create: `data-api/clients/kimi_client.py`

- [ ] **Step 1: 编写 Kimi OAuth 客户端**

```python
# data-api/clients/kimi_client.py
import httpx
from typing import Optional, Dict, Any, List
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class KimiClient:
    """Kimi API client for LLM inference"""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.kimi_client_id
        self.client_secret = settings.kimi_client_secret
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """Get OAuth access token"""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def analyze_impact(self, event: str, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze event impact on companies"""
        try:
            token = await self._get_access_token()

            # Build prompt
            company_list = "\n".join([
                f"{i+1}. {c['name']}({c['ticker']}) — 路径: {' → '.join(c.get('name_chain', []))} "
                f"[{c.get('depth', 0)}跳]"
                for i, c in enumerate(companies)
            ])

            prompt = f"""你是一位资深产业链分析专家。请基于以下产业链关系数据，分析事件对每家关联公司的影响。

## 事件
{event}

## 关联公司及产业链路径
{company_list}

## 分析要求
对每家公司判断：
1. 影响方向：利好 / 利空 / 中性
2. 影响程度：高(>5%) / 中(2-5%) / 低(<2%)
3. 传导逻辑：基于产业链路径，用一句话解释影响如何从事件源传导到该公司
4. 置信度：0-1

## 重要原则
- 同一关系在不同事件下可能有完全相反的影响
- 跳数越多，影响通常越弱，但关键依赖(DEPENDS_ON)可以跨跳保持高影响
- 竞争关系(COMPETES_WITH)通常产生反向影响
- 供应关系(SUPPLIES_TO)的影响方向取决于事件性质

输出严格 JSON 格式：
[{{"ticker": "XXX", "company": "名称", "direction": "利好/利空/中性", "magnitude": "高/中/低", "reasoning": "...", "confidence": 0.8}}]"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()

                # Extract JSON from response
                content = data["choices"][0]["message"]["content"]
                import json
                # Try to find JSON array in response
                start = content.find("[")
                end = content.rfind("]")
                if start >= 0 and end > start:
                    results = json.loads(content[start:end+1])
                    return {"results": results}
                return {"results": [], "raw": content}

        except Exception as e:
            logger.error(f"Kimi analysis failed: {e}")
            return {"results": [], "error": str(e)}
```

- [ ] **Step 2: Commit**

```bash
git add data-api/clients/kimi_client.py
git commit -m "feat: add Kimi OAuth client for LLM inference"
```

---

### Task 11: 创建 clients __init__.py

**Files:**
- Create: `data-api/clients/__init__.py`

- [ ] **Step 1: 导出所有客户端**

```python
# data-api/clients/__init__.py
from .neo4j_client import Neo4jClient
from .postgres_client import PostgresClient
from .openbb_client import OpenBBClient
from .akshare_client import AkShareClient
from .kimi_client import KimiClient

__all__ = [
    "Neo4jClient",
    "PostgresClient",
    "OpenBBClient",
    "AkShareClient",
    "KimiClient",
]
```

- [ ] **Step 2: Commit**

```bash
git add data-api/clients/__init__.py
git commit -m "chore: export all clients from package"
```

---

## Phase 3: MCP 工具实现

### Task 12: 创建发现工具 (discover.py)

**Files:**
- Create: `data-api/tools/discover.py`

- [ ] **Step 1: 编写发现工具**

```python
# data-api/tools/discover.py
from typing import List, Dict, Any
from clients import OpenBBClient, AkShareClient
import logging

logger = logging.getLogger(__name__)

openbb = OpenBBClient()
akshare = AkShareClient()


async def discover_peers(symbol: str) -> List[Dict[str, Any]]:
    """Discover competitor companies"""
    peers = openbb.discover_peers(symbol)
    results = []
    for peer in peers:
        results.append({
            "ticker": peer.get("symbol"),
            "name": peer.get("name"),
            "market": "us",
            "relation": "COMPETES_WITH",
            "source": "peers"
        })
    return results


async def discover_etf_holdings(symbol: str = "SOXX") -> List[Dict[str, Any]]:
    """Discover ETF holdings"""
    holdings = openbb.discover_etf_holdings(symbol)
    results = []
    for holding in holdings:
        results.append({
            "ticker": holding.get("symbol"),
            "name": holding.get("name"),
            "market": "us",
            "relation": "IN_ETF",
            "source": f"etf_{symbol}",
            "etf_symbol": symbol
        })
    return results


async def discover_institutional(symbol: str) -> List[Dict[str, Any]]:
    """Discover institutional investors"""
    holders = openbb.discover_institutional(symbol)
    results = []
    for holder in holders:
        investor = holder.get("investor", "")
        results.append({
            "investor": investor,
            "relation": "INVESTED_IN",
            "source": "institutional",
            "shares": holder.get("shares"),
            "value": holder.get("value")
        })
    return results


async def discover_cn_concept(board_name: str) -> List[Dict[str, Any]]:
    """Discover A-share concept board constituents"""
    stocks = akshare.discover_cn_concept(board_name)
    results = []
    for stock in stocks:
        results.append({
            "ticker": stock.get("代码"),
            "name": stock.get("名称"),
            "market": "cn",
            "relation": "SAME_CONCEPT",
            "source": f"concept_{board_name}",
            "concept": board_name
        })
    return results


async def discover_cn_industry(board_name: str) -> List[Dict[str, Any]]:
    """Discover A-share industry board constituents"""
    stocks = akshare.discover_cn_industry(board_name)
    results = []
    for stock in stocks:
        results.append({
            "ticker": stock.get("代码"),
            "name": stock.get("名称"),
            "market": "cn",
            "relation": "SAME_SECTOR",
            "source": f"industry_{board_name}",
            "sector": board_name
        })
    return results


async def discover_cn_holders(symbol: str) -> List[Dict[str, Any]]:
    """Discover top 10 shareholders for A-share"""
    holders = akshare.discover_cn_holders(symbol)
    results = []
    for holder in holders:
        results.append({
            "holder": holder.get("股东名称"),
            "relation": "INVESTED_IN",
            "source": "cn_holders",
            "shares": holder.get("持股数量")
        })
    return results


async def discover_news(symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get company news"""
    return openbb.get_news(symbol, limit)
```

- [ ] **Step 2: Commit**

```bash
git add data-api/tools/discover.py
git commit -m "feat: add discovery tools for peers, ETF, institutional, CN boards"
```

---

### Task 13: 创建采集工具 (collect.py)

**Files:**
- Create: `data-api/tools/collect.py`

- [ ] **Step 1: 编写采集工具**

```python
# data-api/tools/collect.py
from typing import Optional, List, Dict, Any
from clients import OpenBBClient, AkShareClient
import logging

logger = logging.getLogger(__name__)

openbb = OpenBBClient()
akshare = AkShareClient()


async def get_profile(symbol: str, market: str = "us") -> Optional[Dict[str, Any]]:
    """Get company profile"""
    if market == "us":
        return openbb.get_profile(symbol)
    # For CN market, extract from price data
    prices = akshare.get_cn_price(symbol, limit=1)
    if prices:
        return {"symbol": symbol, "market": market, "name": prices[0].get("名称", "")}
    return None


async def get_price(symbol: str, start_date: str, end_date: str, market: str = "us") -> List[Dict[str, Any]]:
    """Get historical price data"""
    if market == "us":
        data = openbb.get_price(symbol, start_date, end_date)
        # Normalize to common format
        return [{
            "date": d.get("date"),
            "open": d.get("open"),
            "high": d.get("high"),
            "low": d.get("low"),
            "close": d.get("close"),
            "volume": d.get("volume"),
            "amount": d.get("amount")
        } for d in data]
    else:
        # AkShare format: 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
        data = akshare.get_cn_price(symbol, start_date.replace("-", ""), end_date.replace("-", ""))
        return [{
            "date": d.get("日期"),
            "open": d.get("开盘"),
            "high": d.get("最高"),
            "low": d.get("最低"),
            "close": d.get("收盘"),
            "volume": d.get("成交量"),
            "amount": d.get("成交额")
        } for d in data]


async def get_income(symbol: str, period: str = "annual", limit: int = 4) -> List[Dict[str, Any]]:
    """Get income statement"""
    return openbb.get_income(symbol, period, limit)


async def get_estimates(symbol: str) -> Optional[Dict[str, Any]]:
    """Get analyst estimates"""
    return openbb.get_estimates(symbol)


async def get_cn_price(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get A-share price data"""
    data = akshare.get_cn_price(symbol, start_date.replace("-", ""), end_date.replace("-", ""))
    return [{
        "date": d.get("日期"),
        "open": d.get("开盘"),
        "high": d.get("最高"),
        "low": d.get("最低"),
        "close": d.get("收盘"),
        "volume": d.get("成交量"),
        "amount": d.get("成交额")
    } for d in data]


async def get_cn_financial(symbol: str) -> List[Dict[str, Any]]:
    """Get A-share financial summary"""
    return akshare.get_cn_financial(symbol)
```

- [ ] **Step 2: Commit**

```bash
git add data-api/tools/collect.py
git commit -m "feat: add collection tools for price, financials, estimates"
```

---

### Task 14: 创建分析工具 (analyze.py)

**Files:**
- Create: `data-api/tools/analyze.py`

- [ ] **Step 1: 编写 AI 分析工具**

```python
# data-api/tools/analyze.py
from typing import List, Dict, Any
from clients import KimiClient
import logging

logger = logging.getLogger(__name__)

kimi = KimiClient()


async def analyze_impact(event: str, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze event impact on related companies using LLM"""
    return await kimi.analyze_impact(event, companies)
```

- [ ] **Step 2: Commit**

```bash
git add data-api/tools/analyze.py
git commit -m "feat: add AI impact analysis tool"
```

---

### Task 15: 创建图谱操作工具 (kg_ops.py)

**Files:**
- Create: `data-api/tools/kg_ops.py`

- [ ] **Step 1: 编写图谱操作工具**

```python
# data-api/tools/kg_ops.py
from typing import List, Dict, Any, Optional
from clients import Neo4jClient
import logging

logger = logging.getLogger(__name__)


async def kg_get_pending_nodes(limit: int = 10, market: str = None) -> List[Dict[str, Any]]:
    """Get companies waiting to be explored"""
    return await Neo4jClient.get_pending_nodes(limit, market)


async def kg_create_company(ticker: str, name: str, market: str, depth: int = 0) -> Dict[str, Any]:
    """Create or merge a company node"""
    return await Neo4jClient.create_company(ticker, name, market, depth)


async def kg_create_relation(from_ticker: str, to_ticker: str,
                             rel_type: str, source: str, confidence: float = 1.0) -> bool:
    """Create a relationship between companies"""
    return await Neo4jClient.create_relation(from_ticker, to_ticker, rel_type, source, confidence)


async def kg_update_status(ticker: str, status: str) -> bool:
    """Update company discovery status"""
    return await Neo4jClient.update_status(ticker, status)


async def kg_get_related(ticker: str, depth: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
    """Get related companies within N hops"""
    return await Neo4jClient.get_related_companies(ticker, depth, limit)


async def kg_save_impact(ticker: str, event: str, direction: str,
                        magnitude: str, reasoning: str) -> bool:
    """Save AI analysis result to company node"""
    query = """
    MATCH (c:Company {ticker: $ticker})
    SET c.lastEventImpact = $direction,
        c.lastEventMagnitude = $magnitude,
        c.lastEventReasoning = $reasoning,
        c.lastEventAnalyzedAt = datetime()
    RETURN c
    """
    result = await Neo4jClient.run_query(query, {
        "ticker": ticker,
        "direction": direction,
        "magnitude": magnitude,
        "reasoning": reasoning
    })
    return len(result) > 0
```

- [ ] **Step 2: Commit**

```bash
git add data-api/tools/kg_ops.py
git commit -m "feat: add knowledge graph operations tools"
```

---

### Task 16: 创建数据库操作工具 (db_ops.py)

**Files:**
- Create: `data-api/tools/db_ops.py`

- [ ] **Step 1: 编写数据库操作工具**

```python
# data-api/tools/db_ops.py
from typing import List, Dict, Any
from clients import PostgresClient
import logging

logger = logging.getLogger(__name__)


async def db_save_prices(symbol: str, prices: List[Dict[str, Any]]) -> int:
    """Save price data to PostgreSQL"""
    return await PostgresClient.save_prices(symbol, prices)


async def db_save_financials(symbol: str, financials: List[Dict[str, Any]]) -> int:
    """Save financial data to PostgreSQL"""
    # Implementation similar to save_prices
    if not financials:
        return 0

    query = """
    INSERT INTO financials (symbol, period, revenue, net_income,
                           gross_margin, operating_margin, eps, market_cap)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (symbol, period) DO UPDATE SET
        revenue = EXCLUDED.revenue,
        net_income = EXCLUDED.net_income,
        gross_margin = EXCLUDED.gross_margin,
        operating_margin = EXCLUDED.operating_margin,
        eps = EXCLUDED.eps,
        market_cap = EXCLUDED.market_cap
    """

    count = 0
    for fin in financials:
        await PostgresClient.execute(
            query,
            symbol,
            fin.get("period"),
            fin.get("revenue"),
            fin.get("net_income"),
            fin.get("gross_margin"),
            fin.get("operating_margin"),
            fin.get("eps"),
            fin.get("market_cap")
        )
        count += 1
    return count


async def db_log_discovery(explorer: str, discovered: str, relation_type: str,
                          source: str, depth: int) -> None:
    """Log discovery event"""
    await PostgresClient.log_discovery(explorer, discovered, relation_type, source, depth)


async def db_log_impact(event: str, source: str, affected: str,
                       direction: str, magnitude: str, reasoning: str,
                       confidence: float) -> None:
    """Log impact analysis result"""
    await PostgresClient.log_impact(event, source, affected, direction, magnitude, reasoning, confidence)
```

- [ ] **Step 2: Commit**

```bash
git add data-api/tools/db_ops.py
git commit -m "feat: add database operations tools"
```

---

### Task 17: 创建 tools __init__.py

**Files:**
- Create: `data-api/tools/__init__.py`

- [ ] **Step 1: 导出所有工具**

```python
# data-api/tools/__init__.py
from .discover import (
    discover_peers,
    discover_etf_holdings,
    discover_institutional,
    discover_cn_concept,
    discover_cn_industry,
    discover_cn_holders,
    discover_news,
)
from .collect import (
    get_profile,
    get_price,
    get_income,
    get_estimates,
    get_cn_price,
    get_cn_financial,
)
from .analyze import analyze_impact
from .kg_ops import (
    kg_get_pending_nodes,
    kg_create_company,
    kg_create_relation,
    kg_update_status,
    kg_get_related,
    kg_save_impact,
)
from .db_ops import (
    db_save_prices,
    db_save_financials,
    db_log_discovery,
    db_log_impact,
)

__all__ = [
    # Discovery
    "discover_peers",
    "discover_etf_holdings",
    "discover_institutional",
    "discover_cn_concept",
    "discover_cn_industry",
    "discover_cn_holders",
    "discover_news",
    # Collection
    "get_profile",
    "get_price",
    "get_income",
    "get_estimates",
    "get_cn_price",
    "get_cn_financial",
    # Analysis
    "analyze_impact",
    # KG Operations
    "kg_get_pending_nodes",
    "kg_create_company",
    "kg_create_relation",
    "kg_update_status",
    "kg_get_related",
    "kg_save_impact",
    # DB Operations
    "db_save_prices",
    "db_save_financials",
    "db_log_discovery",
    "db_log_impact",
]
```

- [ ] **Step 2: Commit**

```bash
git add data-api/tools/__init__.py
git commit -m "chore: export all tools from package"
```

---

## Phase 4: FastAPI 主应用与 MCP Server

### Task 18: 创建 MCP Server 协议实现

**Files:**
- Create: `data-api/mcp_server.py`

- [ ] **Step 1: 编写 MCP Server 实现**

```python
# data-api/mcp_server.py
from typing import Any, Dict, List, Callable, Awaitable
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., Awaitable[Any]]


class MCPServer:
    """Simple MCP Server implementation"""

    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}

    def register_tool(self, name: str, description: str,
                     parameters: Dict[str, Any],
                     handler: Callable[..., Awaitable[Any]]) -> None:
        """Register a tool"""
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        logger.info(f"Registered tool: {name}")

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "list_tools":
            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                    for tool in self.tools.values()
                ]
            }

        elif method == "call_tool":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                return {"error": f"Tool not found: {tool_name}"}

            tool = self.tools[tool_name]
            try:
                result = await tool.handler(**arguments)
                return {"result": result}
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                return {"error": str(e)}

        else:
            return {"error": f"Unknown method: {method}"}


# Global server instance
mcp_server = MCPServer()


def register_all_tools():
    """Register all available tools"""
    from tools import (
        # Discovery
        discover_peers, discover_etf_holdings, discover_institutional,
        discover_cn_concept, discover_cn_industry, discover_cn_holders, discover_news,
        # Collection
        get_profile, get_price, get_income, get_estimates,
        get_cn_price, get_cn_financial,
        # Analysis
        analyze_impact,
        # KG
        kg_get_pending_nodes, kg_create_company, kg_create_relation,
        kg_update_status, kg_get_related, kg_save_impact,
        # DB
        db_save_prices, db_save_financials, db_log_discovery, db_log_impact,
    )

    # Discovery tools
    mcp_server.register_tool(
        "discover_peers",
        "Discover competitor companies",
        {"symbol": {"type": "string", "description": "Stock symbol"}},
        discover_peers
    )
    mcp_server.register_tool(
        "discover_etf_holdings",
        "Discover ETF holdings",
        {"symbol": {"type": "string", "description": "ETF symbol", "default": "SOXX"}},
        discover_etf_holdings
    )
    mcp_server.register_tool(
        "discover_institutional",
        "Discover institutional ownership",
        {"symbol": {"type": "string", "description": "Stock symbol"}},
        discover_institutional
    )
    mcp_server.register_tool(
        "discover_cn_concept",
        "Discover A-share concept board constituents",
        {"board_name": {"type": "string", "description": "Concept board name"}},
        discover_cn_concept
    )
    mcp_server.register_tool(
        "discover_cn_industry",
        "Discover A-share industry board constituents",
        {"board_name": {"type": "string", "description": "Industry board name"}},
        discover_cn_industry
    )
    mcp_server.register_tool(
        "discover_cn_holders",
        "Discover top 10 shareholders",
        {"symbol": {"type": "string", "description": "Stock symbol"}},
        discover_cn_holders
    )
    mcp_server.register_tool(
        "discover_news",
        "Get company news",
        {
            "symbol": {"type": "string", "description": "Stock symbol"},
            "limit": {"type": "integer", "description": "Number of news items", "default": 20}
        },
        discover_news
    )

    # Collection tools
    mcp_server.register_tool(
        "get_profile",
        "Get company profile",
        {
            "symbol": {"type": "string", "description": "Stock symbol"},
            "market": {"type": "string", "description": "Market code", "default": "us"}
        },
        get_profile
    )
    mcp_server.register_tool(
        "get_price",
        "Get historical price data",
        {
            "symbol": {"type": "string", "description": "Stock symbol"},
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "market": {"type": "string", "description": "Market code", "default": "us"}
        },
        get_price
    )
    mcp_server.register_tool(
        "get_cn_price",
        "Get A-share price data",
        {
            "symbol": {"type": "string", "description": "Stock symbol"},
            "start_date": {"type": "string", "description": "Start date (YYYYMMDD)"},
            "end_date": {"type": "string", "description": "End date (YYYYMMDD)"}
        },
        get_cn_price
    )

    # Analysis tools
    mcp_server.register_tool(
        "analyze_impact",
        "Analyze event impact on companies",
        {
            "event": {"type": "string", "description": "Event description"},
            "companies": {"type": "array", "description": "List of related companies"}
        },
        analyze_impact
    )

    # KG tools
    mcp_server.register_tool(
        "kg_get_pending_nodes",
        "Get companies waiting to be explored",
        {
            "limit": {"type": "integer", "description": "Max nodes to return", "default": 10},
            "market": {"type": "string", "description": "Filter by market", "default": None}
        },
        kg_get_pending_nodes
    )
    mcp_server.register_tool(
        "kg_create_company",
        "Create or merge a company node",
        {
            "ticker": {"type": "string", "description": "Stock ticker"},
            "name": {"type": "string", "description": "Company name"},
            "market": {"type": "string", "description": "Market code"},
            "depth": {"type": "integer", "description": "BFS depth", "default": 0}
        },
        kg_create_company
    )
    mcp_server.register_tool(
        "kg_create_relation",
        "Create relationship between companies",
        {
            "from_ticker": {"type": "string", "description": "Source company ticker"},
            "to_ticker": {"type": "string", "description": "Target company ticker"},
            "rel_type": {"type": "string", "description": "Relationship type"},
            "source": {"type": "string", "description": "Data source"},
            "confidence": {"type": "number", "description": "Confidence score", "default": 1.0}
        },
        kg_create_relation
    )
    mcp_server.register_tool(
        "kg_update_status",
        "Update company discovery status",
        {
            "ticker": {"type": "string", "description": "Company ticker"},
            "status": {"type": "string", "description": "New status"}
        },
        kg_update_status
    )
    mcp_server.register_tool(
        "kg_get_related",
        "Get companies related within N hops",
        {
            "ticker": {"type": "string", "description": "Company ticker"},
            "depth": {"type": "integer", "description": "Max hops", "default": 3},
            "limit": {"type": "integer", "description": "Max results", "default": 50}
        },
        kg_get_related
    )
    mcp_server.register_tool(
        "kg_save_impact",
        "Save AI analysis result",
        {
            "ticker": {"type": "string", "description": "Company ticker"},
            "event": {"type": "string", "description": "Event description"},
            "direction": {"type": "string", "description": "Impact direction"},
            "magnitude": {"type": "string", "description": "Impact magnitude"},
            "reasoning": {"type": "string", "description": "Reasoning"}
        },
        kg_save_impact
    )

    logger.info(f"Registered {len(mcp_server.tools)} tools")
```

- [ ] **Step 2: Commit**

```bash
git add data-api/mcp_server.py
git commit -m "feat: implement MCP server with 20+ tools"
```

---

### Task 19: 创建 FastAPI 主应用

**Files:**
- Create: `data-api/main.py`

- [ ] **Step 1: 编写 FastAPI 主应用**

```python
# data-api/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from mcp_server import mcp_server, register_all_tools
from clients import Neo4jClient, PostgresClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up...")
    register_all_tools()

    # Verify connections
    neo4j_ok = await Neo4jClient.verify_connectivity()
    logger.info(f"Neo4j connection: {'OK' if neo4j_ok else 'FAILED'}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await Neo4jClient.close()
    await PostgresClient.close()


app = FastAPI(
    title="Industry Chain KG Data API",
    description="MCP Server for supply chain knowledge graph operations",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Industry Chain KG Data API",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    neo4j_ok = await Neo4jClient.verify_connectivity()
    return {
        "status": "healthy" if neo4j_ok else "degraded",
        "neo4j": "connected" if neo4j_ok else "disconnected"
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP protocol endpoint"""
    try:
        body = await request.json()
        result = await mcp_server.handle_request(body)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools"""
    response = await mcp_server.handle_request({"method": "list_tools"})
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 2: Commit**

```bash
git add data-api/main.py
git commit -m "feat: add FastAPI main application with MCP endpoint"
```

---

### Task 20: 创建 Dockerfile

**Files:**
- Create: `data-api/Dockerfile`

- [ ] **Step 1: 编写 Dockerfile**

```dockerfile
# data-api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 2: Commit**

```bash
git add data-api/Dockerfile
git commit -m "chore: add Dockerfile for data-api service"
```

---

## Phase 5: 初始化脚本

### Task 21: 创建 Neo4j 初始化脚本

**Files:**
- Create: `init-scripts/neo4j-init.cypher`

- [ ] **Step 1: 编写 Neo4j 初始化脚本**

```cypher
// Create NVDA seed node
CREATE (c:Company {
    ticker: 'NVDA',
    name: 'NVIDIA Corporation',
    market: 'us',
    sector: 'Semiconductors',
    discoveryStatus: 'pending_explore',
    discoveryDepth: 0,
    createdAt: datetime()
});

// Create constraints and indexes
CREATE CONSTRAINT company_ticker_unique IF NOT EXISTS
FOR (c:Company) REQUIRE c.ticker IS UNIQUE;

CREATE INDEX company_status IF NOT EXISTS
FOR (c:Company) ON (c.discoveryStatus);

CREATE INDEX company_depth IF NOT EXISTS
FOR (c:Company) ON (c.discoveryDepth);

CREATE INDEX company_market IF NOT EXISTS
FOR (c:Company) ON (c.market);
```

- [ ] **Step 2: Commit**

```bash
git add init-scripts/neo4j-init.cypher
git commit -m "chore: add Neo4j initialization script with NVDA seed"
```

---

### Task 22: 创建 PostgreSQL 初始化脚本

**Files:**
- Create: `init-scripts/postgres-init.sql`

- [ ] **Step 1: 编写 PostgreSQL 初始化脚本**

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Stock prices table (hypertable)
CREATE TABLE IF NOT EXISTS stock_prices (
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    volume BIGINT,
    amount NUMERIC(18,2),
    PRIMARY KEY (symbol, date)
);

-- Convert to hypertable
SELECT create_hypertable('stock_prices', 'date', if_not_exists => TRUE);

-- Create index on symbol
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices (symbol);

-- Financials table
CREATE TABLE IF NOT EXISTS financials (
    symbol VARCHAR(20) NOT NULL,
    period VARCHAR(10) NOT NULL,
    revenue NUMERIC(18,2),
    net_income NUMERIC(18,2),
    gross_margin NUMERIC(8,4),
    operating_margin NUMERIC(8,4),
    eps NUMERIC(10,4),
    market_cap NUMERIC(20,2),
    PRIMARY KEY (symbol, period)
);

-- Discovery log table
CREATE TABLE IF NOT EXISTS discovery_log (
    id SERIAL PRIMARY KEY,
    explorer_ticker VARCHAR(20) NOT NULL,
    discovered_ticker VARCHAR(20) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    depth INTEGER NOT NULL,
    discovered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Event impact log table
CREATE TABLE IF NOT EXISTS event_impact_log (
    id SERIAL PRIMARY KEY,
    event_description TEXT NOT NULL,
    source_ticker VARCHAR(20) NOT NULL,
    affected_ticker VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('利好', '利空', '中性')),
    magnitude VARCHAR(10) NOT NULL CHECK (magnitude IN ('高', '中', '低')),
    reasoning TEXT,
    confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_discovery_log_explorer ON discovery_log (explorer_ticker);
CREATE INDEX IF NOT EXISTS idx_discovery_log_depth ON discovery_log (depth);
CREATE INDEX IF NOT EXISTS idx_event_impact_source ON event_impact_log (source_ticker);
CREATE INDEX IF NOT EXISTS idx_event_impact_analyzed ON event_impact_log (analyzed_at DESC);
```

- [ ] **Step 2: Commit**

```bash
git add init-scripts/postgres-init.sql
git commit -m "chore: add PostgreSQL initialization script with tables and indexes"
```

---

### Task 23: 创建 init-scripts 目录 README

**Files:**
- Create: `init-scripts/README.md`

- [ ] **Step 1: 编写 README**

```markdown
# Initialization Scripts

This directory contains database initialization scripts that run automatically when containers start.

## Neo4j (`neo4j-init.cypher`)

- Creates NVDA seed node
- Creates constraints and indexes for Company nodes
- Runs when Neo4j container starts for the first time

## PostgreSQL (`postgres-init.sql`)

- Enables TimescaleDB extension
- Creates stock_prices hypertable
- Creates financials, discovery_log, and event_impact_log tables
- Creates indexes for common queries
- Runs when PostgreSQL container initializes
```

- [ ] **Step 2: Commit**

```bash
git add init-scripts/README.md
git commit -m "docs: add init-scripts README"
```

---

## Phase 6: n8n 工作流占位

### Task 24: 创建 n8n-workflows 目录

**Files:**
- Create: `n8n-workflows/README.md`

- [ ] **Step 1: 编写 n8n 工作流说明**

```markdown
# n8n Workflows

This directory contains exported n8n workflow JSON files.

## Workflows

| Workflow | File | Trigger | Description |
|----------|------|---------|-------------|
| WF-0 | `wf-0-bfs-crawler.json` | Cron (6h) | BFS industry chain crawler |
| WF-1 | `wf-1-daily-price.json` | Cron (21:00) | Daily price collection |
| WF-2 | `wf-2-quarterly-financial.json` | Cron (monthly) | Quarterly financial data |
| WF-3 | `wf-3-company-profile.json` | Cron (monthly) | Company profile updates |
| WF-4 | `wf-4-news-collection.json` | Cron (2x daily) | News collection |
| WF-5 | `wf-5-analyst-estimates.json` | Cron (weekly) | Analyst estimates |
| WF-6 | `wf-6-supply-inference.json` | Cron (monthly) | Supply chain inference |
| WF-7 | `wf-7-competition-update.json` | Cron (monthly) | Competition relation updates |
| WF-8 | `wf-8-risk-precalc.json` | Event-driven | Risk propagation pre-calculation |
| WF-9 | `wf-9-event-analysis.json` | Webhook/Manual | Event impact analysis (core) |

## Importing Workflows

1. Open n8n at http://localhost:5678
2. Go to Workflows → Import from File
3. Select the JSON file to import

## MCP Connection

Configure MCP node with:
- URL: `http://data-api:8000/mcp`
- Authentication: None (internal network)
```

- [ ] **Step 2: Commit**

```bash
git add n8n-workflows/README.md
git commit -m "docs: add n8n-workflows directory with README"
```

---

## Phase 7: 测试与验证

### Task 25: 创建测试套件 init

**Files:**
- Create: `data-api/tests/__init__.py`

- [ ] **Step 1: 创建 tests __init__.py**

```python
# data-api/tests/__init__.py
# Test package
```

- [ ] **Step 2: 运行所有测试**

```bash
cd data-api
python -m pytest tests/ -v --tb=short
```

Expected output:
```
tests/test_config.py::test_settings_default_values PASSED
tests/test_config.py::test_postgres_dsn PASSED
tests/test_config.py::test_get_settings_cached PASSED
tests/test_neo4j_client.py::test_get_pending_nodes PASSED
tests/test_neo4j_client.py::test_create_company PASSED
```

- [ ] **Step 3: Commit**

```bash
git add data-api/tests/__init__.py
git commit -m "test: add test suite structure"
```

---

### Task 26: 创建启动验证脚本

**Files:**
- Create: `scripts/verify-setup.sh`

- [ ] **Step 1: 编写验证脚本**

```bash
#!/bin/bash
# scripts/verify-setup.sh
# Verification script for supply chain KG setup

echo "=== Supply Chain KG Setup Verification ==="

# Check Docker
echo -n "Docker: "
if docker --version > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ Not installed"
    exit 1
fi

# Check Docker Compose
echo -n "Docker Compose: "
if docker compose version > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ Not installed"
    exit 1
fi

# Check environment file
echo -n ".env file: "
if [ -f ".env" ]; then
    echo "✓ OK"
else
    echo "✗ Missing (cp .env.example .env)"
    exit 1
fi

# Check required directories
echo -n "Directories: "
for dir in neo4j/data postgres/data redis/data; do
    mkdir -p "$dir"
done
echo "✓ OK"

echo ""
echo "=== Ready to start ==="
echo "Run: docker compose up -d"
echo ""
echo "=== Services will be available at ==="
echo "n8n:       http://localhost:5678"
echo "Neo4j:     http://localhost:7474"
echo "Data API:  http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
```

- [ ] **Step 2: 使脚本可执行并 Commit**

```bash
chmod +x scripts/verify-setup.sh
git add scripts/verify-setup.sh
git commit -m "chore: add setup verification script"
```

---

### Task 27: 创建主 README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 编写主 README**

```markdown
# Supply Chain Knowledge Graph + AI

产业链知识图谱 + AI 双层架构系统

## Quick Start

```bash
# 1. Verify setup
./scripts/verify-setup.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start services
docker compose up -d

# 4. Verify health
curl http://localhost:8000/health
```

## Architecture

- **Layer 1**: Neo4j Knowledge Graph (structured memory)
- **Layer 2**: LLM Inference (context-aware reasoning)
- **Orchestration**: n8n workflows
- **Data API**: FastAPI MCP Server

## Services

| Service | URL | Description |
|---------|-----|-------------|
| n8n | http://localhost:5678 | Workflow automation |
| Neo4j Browser | http://localhost:7474 | Graph visualization |
| Data API | http://localhost:8000 | MCP Server |
| API Docs | http://localhost:8000/docs | OpenAPI documentation |

## Workflows

See [n8n-workflows/README.md](n8n-workflows/README.md)

## Documentation

- [Design Spec](docs/superpowers/specs/2026-03-29-supply-chain-kg-design.md)
- [Implementation Plan](docs/superpowers/plans/2026-03-29-supply-chain-kg-plan.md)

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add main project README"
```

---

## Spec 覆盖检查

| 设计文档章节 | 实现任务 | 状态 |
|--------------|----------|------|
| 三、数据模型 (Neo4j) | Task 6, 21 | ✅ |
| 三、数据模型 (PostgreSQL) | Task 7, 22 | ✅ |
| 四、MCP Server API | Task 12-17, 18-19 | ✅ |
| 五、工作流设计 | Task 24 (占位) | ⚠️ (n8n 工作流需手动导入) |
| 六、项目结构 | 全部 | ✅ |
| 七、部署配置 | Task 3, 20, 25-27 | ✅ |

**注意**: n8n 工作流 (WF-0~9) 需要在 n8n UI 中配置后导出到 `n8n-workflows/` 目录。

---

## 执行选项

**计划已完成并保存到 `docs/superpowers/plans/2026-03-29-supply-chain-kg-plan.md`**

两个执行选项：

**1. Subagent-Driven (推荐)** - 每个任务派生子代理，任务间评审，快速迭代

**2. Inline Execution** - 在当前会话中顺序执行任务，使用 executing-plans 技能批量执行

**请选择执行方式？** (推荐选项 1)

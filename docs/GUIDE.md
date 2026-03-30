# 供应链知识图谱 + AI 双层架构系统

## 完整文档

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [快速开始](#3-快速开始)
4. [详细安装指南](#4-详细安装指南)
5. [配置说明](#5-配置说明)
6. [API 使用指南](#6-api-使用指南)
7. [MCP 工具参考](#7-mcp-工具参考)
8. [n8n 工作流](#8-n8n-工作流)
9. [数据模型](#9-数据模型)
10. [开发指南](#10-开发指南)
11. [故障排除](#11-故障排除)
12. [附录](#12-附录)

---

## 1. 项目概述

### 1.1 项目背景

本项目构建一个**产业链知识图谱 + AI 双层架构系统**，旨在：

- 从种子公司（如 NVIDIA）自动发现产业链上下游关系
- 采集公司行情、财务、新闻等多维数据
- 利用 LLM 分析事件对产业链的传导影响
- 通过 n8n 工作流实现全自动化运营

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| 🔗 双层架构 | Neo4j（记忆层）+ LLM（推理层） |
| 🌐 多市场支持 | 美股/全球（OpenBB）+ A股（AkShare） |
| 🤖 AI 分析 | Kimi LLM 事件影响评估 |
| ⚡ 自动化 | 10 个 n8n 工作流编排 |
| 🔌 MCP 协议 | 标准化工具接口 |
| 📊 时序存储 | TimescaleDB 价格数据 |

### 1.3 技术栈

```
Python 3.11
├── FastAPI - Web 框架
├── Neo4j 5.x - 图数据库
├── PostgreSQL 15 + TimescaleDB - 时序数据库
├── Redis 7 - 缓存
├── n8n - 工作流编排
├── OpenBB - 美股/全球数据
├── AkShare - A股数据
└── Kimi (Moonshot) - LLM 推理
```

---

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        n8n Workflows (10)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  WF-0   │ │  WF-1   │ │  WF-2   │ │  WF-3   │ │  WF-4   │   │
│  │  Seed   │ │   BFS   │ │ Collect │ │  Impact │ │  Alert  │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       └─────────────┴──────────┴──────────┴───────────┘         │
│                           │                                      │
│                    ┌──────┴──────┐                              │
│                    │  MCP Server  │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Layer 1      │   │  Layer 2      │   │  Data Sources │
│  Memory       │   │  Reasoning    │   │               │
│               │   │               │   │               │
│  ┌─────────┐  │   │  ┌─────────┐  │   │  ┌─────────┐  │
│  │  Neo4j  │  │◄──┤  │  Kimi   │  │   │  │ OpenBB  │  │
│  │  Graph  │  │   │  │  LLM    │  │   │  │ yfinance│  │
│  └─────────┘  │   │  └─────────┘  │   │  └─────────┘  │
│               │   │               │   │               │
└───────────────┘   └───────────────┘   │  ┌─────────┐  │
                                        │  │ AkShare │  │
                                        │  │  A股    │  │
                                        │  └─────────┘  │
                                        └───────────────┘
```

### 2.2 数据流向

```
外部数据源 → Data API → 知识图谱/时序数据库 → AI 分析 → 可视化/报告
    │            │              │                  │           │
    ▼            ▼              ▼                  ▼           ▼
OpenBB      MCP Tools    Neo4j/Postgres      Kimi LLM    n8n/Web
AkShare     (26+ tools)  (存储层)            (推理层)    (展示层)
```

---

## 3. 快速开始

### 3.1 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 4GB+ 可用内存

### 3.2 三步启动

```bash
# 1. 克隆仓库
git clone https://github.com/123qsa/supply-chain-kg.git
cd supply-chain-kg

# 2. 验证环境
./scripts/verify-setup.sh

# 3. 启动服务
docker-compose up -d
```

### 3.3 验证启动

```bash
# 检查所有服务状态
docker-compose ps

# 测试 API
curl http://localhost:8000/health

# 预期输出
{
  "status": "healthy",
  "neo4j": "connected"
}
```

### 3.4 访问界面

| 服务 | URL | 默认凭证 |
|------|-----|---------|
| n8n | http://localhost:5678 | - |
| Neo4j Browser | http://localhost:7474 | neo4j/password |
| Data API Docs | http://localhost:8000/docs | - |

---

## 4. 详细安装指南

### 4.1 环境准备

#### macOS

```bash
# 安装 Homebrew (如未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Docker Desktop
brew install --cask docker

# 启动 Docker
open -a Docker
```

#### Ubuntu/Debian

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin

# 将用户加入 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

### 4.2 项目配置

```bash
# 克隆项目
git clone https://github.com/123qsa/supply-chain-kg.git
cd supply-chain-kg

# 创建数据目录
mkdir -p neo4j/data postgres/data redis/data

# 配置环境变量
cp .env.example .env
```

### 4.3 编辑 .env 文件

```bash
# 必需配置
NEO4J_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_secure_password

# 可选 - OpenBB PAT（如没有则使用免费 yfinance）
OPENBB_PAT=

# 可选 - Kimi OAuth（如需 AI 分析功能）
KIMI_CLIENT_ID=
KIMI_CLIENT_SECRET=
```

### 4.4 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 仅启动特定服务
docker-compose up -d neo4j postgres
docker-compose up -d data-api
```

### 4.5 初始化验证

```bash
# 检查 Neo4j 种子数据
curl -u neo4j:your_password \
  http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"MATCH (c:Company) RETURN c.ticker"}]}'

# 测试 MCP 工具
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "list_tools"
  }'
```

---

## 5. 配置说明

### 5.1 环境变量详解

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `NEO4J_URI` | 否 | `bolt://neo4j:7687` | Neo4j 连接地址 |
| `NEO4J_USER` | 否 | `neo4j` | Neo4j 用户名 |
| `NEO4J_PASSWORD` | 是 | - | Neo4j 密码 |
| `POSTGRES_HOST` | 否 | `postgres` | PostgreSQL 主机 |
| `POSTGRES_PORT` | 否 | `5432` | PostgreSQL 端口 |
| `POSTGRES_DB` | 否 | `industry_kg` | 数据库名 |
| `POSTGRES_USER` | 否 | `nvidia` | PostgreSQL 用户 |
| `POSTGRES_PASSWORD` | 是 | - | PostgreSQL 密码 |
| `OPENBB_PAT` | 否 | - | OpenBB Personal Access Token |
| `KIMI_CLIENT_ID` | 否 | - | Kimi OAuth Client ID |
| `KIMI_CLIENT_SECRET` | 否 | - | Kimi OAuth Client Secret |
| `REDIS_HOST` | 否 | `redis` | Redis 主机 |
| `REDIS_PORT` | 否 | `6379` | Redis 端口 |

### 5.2 服务配置

#### Neo4j 内存调优

编辑 `docker-compose.yml`：

```yaml
neo4j:
  environment:
    - NEO4J_server_memory_heap_max__size=4G  # 根据内存调整
    - NEO4J_server_memory_pagecache_size=2G
```

#### PostgreSQL 连接池

编辑 `data-api/config.py`：

```python
PostgresClient._pool = await asyncpg.create_pool(
    ...
    min_size=5,    # 最小连接数
    max_size=20    # 最大连接数
)
```

---

## 6. API 使用指南

### 6.1 基础端点

#### 健康检查

```bash
GET /health

Response:
{
  "status": "healthy",
  "neo4j": "connected"
}
```

#### 列出 MCP 工具

```bash
GET /mcp/tools

Response:
{
  "tools": [
    {
      "name": "discover_peers",
      "description": "Discover competitor companies",
      "parameters": {...}
    },
    ...
  ]
}
```

### 6.2 MCP 调用

#### 调用工具

```bash
POST /mcp
Content-Type: application/json

{
  "method": "call_tool",
  "params": {
    "name": "discover_peers",
    "arguments": {
      "symbol": "NVDA"
    }
  }
}
```

#### 示例：发现竞争对手

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "call_tool",
    "params": {
      "name": "discover_peers",
      "arguments": {
        "symbol": "NVDA"
      }
    }
  }'

Response:
{
  "result": [
    {"ticker": "AMD", "name": "AMD Corp", "relation": "COMPETES_WITH"},
    {"ticker": "INTC", "name": "Intel", "relation": "COMPETES_WITH"}
  ]
}
```

### 6.3 使用 Python SDK

```python
import httpx

async def call_mcp_tool(tool_name: str, arguments: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "method": "call_tool",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        return response.json()

# 获取 NVDA 的竞争对手
result = await call_mcp_tool("discover_peers", {"symbol": "NVDA"})

# 获取历史价格
result = await call_mcp_tool("get_price", {
    "symbol": "NVDA",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
})
```

---

## 7. MCP 工具参考

### 7.1 发现工具 (Discovery)

#### discover_peers
发现竞争对手公司

```json
{
  "name": "discover_peers",
  "parameters": {
    "symbol": {"type": "string", "description": "股票代码"}
  },
  "returns": [
    {"ticker": "AMD", "name": "AMD", "relation": "COMPETES_WITH"}
  ]
}
```

#### discover_etf_holdings
发现 ETF 持仓

```json
{
  "name": "discover_etf_holdings",
  "parameters": {
    "symbol": {"type": "string", "default": "SOXX", "description": "ETF代码"}
  }
}
```

#### discover_cn_concept
发现 A股概念板块成分股

```json
{
  "name": "discover_cn_concept",
  "parameters": {
    "board_name": {"type": "string", "description": "板块名称，如'芯片概念'"}
  }
}
```

### 7.2 采集工具 (Collection)

#### get_price
获取历史价格数据

```json
{
  "name": "get_price",
  "parameters": {
    "symbol": {"type": "string"},
    "start_date": {"type": "string", "format": "YYYY-MM-DD"},
    "end_date": {"type": "string", "format": "YYYY-MM-DD"},
    "market": {"type": "string", "default": "us", "enum": ["us", "cn"]}
  }
}
```

#### get_cn_price
获取 A股历史价格

```json
{
  "name": "get_cn_price",
  "parameters": {
    "symbol": {"type": "string", "description": "如 000001"},
    "start_date": {"type": "string", "format": "YYYYMMDD"},
    "end_date": {"type": "string", "format": "YYYYMMDD"}
  }
}
```

### 7.3 分析工具 (Analysis)

#### analyze_impact
AI 事件影响分析

```json
{
  "name": "analyze_impact",
  "parameters": {
    "event": {"type": "string", "description": "事件描述"},
    "companies": {
      "type": "array",
      "items": {
        "ticker": "string",
        "name": "string",
        "name_chain": ["string"],
        "depth": "integer"
      }
    }
  },
  "returns": {
    "results": [
      {
        "ticker": "AMD",
        "direction": "利空",
        "magnitude": "中",
        "reasoning": "...",
        "confidence": 0.85
      }
    ]
  }
}
```

### 7.4 图谱工具 (KG Operations)

#### kg_create_company
创建公司节点

```json
{
  "name": "kg_create_company",
  "parameters": {
    "ticker": {"type": "string"},
    "name": {"type": "string"},
    "market": {"type": "string", "enum": ["us", "cn"]},
    "depth": {"type": "integer", "default": 0}
  }
}
```

#### kg_create_relation
创建公司关系

```json
{
  "name": "kg_create_relation",
  "parameters": {
    "from_ticker": {"type": "string"},
    "to_ticker": {"type": "string"},
    "rel_type": {
      "type": "string",
      "enum": [
        "SUPPLIES_TO", "CUSTOMER_OF", "COMPETES_WITH",
        "PARTNERS_WITH", "INVESTED_IN", "SAME_SECTOR",
        "SAME_CONCEPT", "IN_ETF", "DEPENDS_ON"
      ]
    },
    "source": {"type": "string"},
    "confidence": {"type": "number", "default": 1.0}
  }
}
```

---

## 8. n8n 工作流

### 8.1 工作流清单

| ID | 名称 | 触发 | 功能 |
|----|------|------|------|
| WF-0 | Seed | 手动 | 初始化种子公司 |
| WF-1 | BFS Crawler | 每6小时 | BFS扩散发现公司 |
| WF-2 | Daily Price | 每天21:00 | 采集日行情 |
| WF-3 | Quarterly Financial | 每月 | 采集财报 |
| WF-4 | News Collection | 每天2次 | 采集新闻 |
| WF-5 | Analyst Estimates | 每周 | 采集分析师预测 |
| WF-6 | Supply Inference | 每月 | 供应链关系推理 |
| WF-7 | Competition Update | 每月 | 竞争关系更新 |
| WF-8 | Risk Pre-calc | 事件驱动 | 风险传播预计算 |
| WF-9 | Event Analysis | Webhook | 事件影响分析 |

### 8.2 配置 n8n MCP 节点

1. 打开 n8n: http://localhost:5678
2. 创建新工作流
3. 添加 **HTTP Request** 节点
4. 配置：
   - Method: POST
   - URL: `http://data-api:8000/mcp`
   - Body: `{"method": "call_tool", "params": {...}}`

### 8.3 示例：WF-1 BFS Crawler

```json
{
  "nodes": [
    {
      "type": "n8n-nodes-base.cron",
      "name": "Schedule",
      "parameters": {
        "rule": "0 */6 * * *"
      }
    },
    {
      "type": "n8n-nodes-base.httpRequest",
      "name": "Get Pending Nodes",
      "parameters": {
        "method": "POST",
        "url": "http://data-api:8000/mcp",
        "body": {
          "method": "call_tool",
          "params": {
            "name": "kg_get_pending_nodes",
            "arguments": {"limit": 10}
          }
        }
      }
    },
    {
      "type": "n8n-nodes-base.splitInBatches",
      "name": "Process Each Node"
    },
    {
      "type": "n8n-nodes-base.httpRequest",
      "name": "Discover Peers",
      "parameters": {
        "method": "POST",
        "url": "http://data-api:8000/mcp",
        "body": {
          "method": "call_tool",
          "params": {
            "name": "discover_peers",
            "arguments": {"symbol": "={{ $json.ticker }}"}
          }
        }
      }
    }
  ]
}
```

---

## 9. 数据模型

### 9.1 Neo4j 图模型

#### 节点标签：Company

```cypher
(:Company {
  ticker: "NVDA",           // 股票代码
  name: "NVIDIA Corp",      // 公司名称
  market: "us",             // 市场：us/cn
  sector: "Technology",     // 行业
  industry: "Semiconductors", // 细分行业
  discoveryStatus: "explored", // 发现状态
  discoveryDepth: 0,        // BFS深度
  createdAt: datetime(),    // 创建时间
  updatedAt: datetime()     // 更新时间
})
```

#### 关系类型

```cypher
// 供应关系
(a:Company)-[:SUPPLIES_TO {source: "manual", confidence: 0.9}]->(b:Company)

// 竞争关系
(a:Company)-[:COMPETES_WITH {source: "peers", discoveredAt: datetime()}]->(b:Company)

// ETF持仓
(a:Company)-[:IN_ETF {etf: "SOXX", weight: 0.05}]->(b:Company)

// 投资关系
(a:Investor)-[:INVESTED_IN {shares: 1000000, value: 50000000}]->(b:Company)
```

### 9.2 PostgreSQL 表结构

#### stock_prices (TimescaleDB hypertable)

```sql
CREATE TABLE stock_prices (
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
```

#### discovery_log

```sql
CREATE TABLE discovery_log (
    id SERIAL PRIMARY KEY,
    explorer_ticker VARCHAR(20) NOT NULL,
    discovered_ticker VARCHAR(20) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    depth INTEGER NOT NULL,
    discovered_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### event_impact_log

```sql
CREATE TABLE event_impact_log (
    id SERIAL PRIMARY KEY,
    event_description TEXT NOT NULL,
    source_ticker VARCHAR(20) NOT NULL,
    affected_ticker VARCHAR(20) NOT NULL,
    direction VARCHAR(10) CHECK (direction IN ('利好', '利空', '中性')),
    magnitude VARCHAR(10) CHECK (magnitude IN ('高', '中', '低')),
    reasoning TEXT,
    confidence NUMERIC(3,2),
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 10. 开发指南

### 10.1 本地开发环境

```bash
# 创建虚拟环境
cd data-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 启动开发服务器
uvicorn main:app --reload --port 8000
```

### 10.2 添加新工具

1. 在 `tools/` 目录创建新文件
2. 实现异步函数
3. 在 `tools/__init__.py` 导出
4. 在 `mcp_server.py` 注册

示例：

```python
# tools/my_tool.py
async def my_new_tool(param: str) -> dict:
    """工具描述"""
    return {"result": f"Processed {param}"}

# tools/__init__.py
from .my_tool import my_new_tool
__all__ = [..., "my_new_tool"]

# mcp_server.py
mcp_server.register_tool(
    "my_new_tool",
    "工具描述",
    {"param": {"type": "string"}},
    my_new_tool
)
```

### 10.3 测试规范

```python
# tests/test_my_tool.py
import pytest
from tools.my_tool import my_new_tool

@pytest.mark.asyncio
async def test_my_new_tool():
    result = await my_new_tool("test")
    assert result["result"] == "Processed test"
```

---

## 11. 故障排除

### 11.1 常见问题

#### Neo4j 连接失败

```
Error: Failed to establish connection to Neo4j
```

解决：
```bash
# 检查 Neo4j 状态
docker-compose ps neo4j

# 查看日志
docker-compose logs neo4j

# 重置数据（会清空）
docker-compose down neo4j
rm -rf neo4j/data
docker-compose up -d neo4j
```

#### API 返回空数据

可能原因：
1. yfinance 限流 → 等待后重试
2. 股票代码错误 → 检查 symbol
3. 网络问题 → 检查 Docker 网络

#### n8n 工作流执行失败

```bash
# 检查 n8n 日志
docker-compose logs n8n

# 验证 MCP 端点
curl http://localhost:8000/mcp/tools
```

### 11.2 性能优化

#### Neo4j 查询慢

```cypher
// 添加索引
CREATE INDEX company_ticker FOR (c:Company) ON (c.ticker);
CREATE INDEX company_status FOR (c:Company) ON (c.discoveryStatus);
```

#### PostgreSQL 慢查询

```sql
-- 分析慢查询
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- 添加索引
CREATE INDEX idx_prices_symbol_date ON stock_prices(symbol, date DESC);
```

---

## 12. 附录

### 12.1 目录结构

```
supply-chain-kg/
├── data-api/                 # FastAPI MCP Server
│   ├── clients/             # 数据源客户端
│   ├── tools/               # MCP 工具
│   ├── tests/               # 测试套件
│   ├── main.py              # FastAPI 入口
│   ├── mcp_server.py        # MCP 实现
│   ├── config.py            # 配置管理
│   ├── Dockerfile           # 容器构建
│   └── requirements.txt     # Python 依赖
├── init-scripts/            # 数据库初始化
│   ├── neo4j-init.cypher
│   └── postgres-init.sql
├── n8n-workflows/           # n8n 工作流配置
├── scripts/                 # 工具脚本
│   └── verify-setup.sh
├── docs/                    # 文档
├── docker-compose.yml       # 服务编排
├── .env.example             # 环境变量模板
└── README.md                # 项目说明
```

### 12.2 参考链接

- [OpenBB Documentation](https://docs.openbb.co)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [TimescaleDB Documentation](https://docs.timescale.com)
- [n8n Documentation](https://docs.n8n.io)
- [MCP Protocol](https://modelcontextprotocol.io)

### 12.3 许可证

MIT License - 详见 LICENSE 文件

---

**文档版本**: 1.0.0
**最后更新**: 2024-03-29
**维护者**: supply-chain-kg team

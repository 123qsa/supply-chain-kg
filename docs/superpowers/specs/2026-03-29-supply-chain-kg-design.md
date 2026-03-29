---
name: 供应链知识图谱 + AI 双层架构系统设计
description: 基于 Neo4j + n8n + FastAPI MCP 的全产业链知识图谱工作流实现方案
type: project
---

# 供应链知识图谱 + AI 双层架构系统设计

> 原文参考：《图谱 + AI 双层架构：全产业链知识图谱工作流设计》
>
> 核心哲学：**知识图谱 = AI 的「结构化记忆」**

---

## 一、设计目标

构建一个完整的产业链分析系统，实现：

1. **自动发现**产业链上下游公司关系（BFS 种子扩散）
2. **持续采集**行情、财务、新闻等数据（动态素材层）
3. **智能分析**事件对产业链的影响（图谱 + AI 双层推理）

### 成功标准

- [ ] 从 NVDA 种子扩散，覆盖至少 500+ 家产业链公司
- [ ] 支持 9 种关系类型的自动发现和存储
- [ ] 每日自动更新行情数据（收盘后）
- [ ] 事件分析响应时间 < 30 秒（从触发到结果）
- [ ] AI 推理准确率 > 80%（影响方向判断）

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户/事件源                                │
│              (手动触发 / Webhook / 定时 Cron)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      n8n 工作流引擎                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │  WF-0   │ │ WF-1~5  │ │ WF-6~8  │ │  WF-9   │               │
│  │ BFS爬虫 │ │数据采集 │ │关系增强 │ │AI分析  │               │
│  │(记忆构建)│ │(素材采集)│ │(记忆增强)│ │(双层核心)│              │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘               │
│       └────────────┴────────────┴────────────┘                  │
│                         │                                       │
│              ┌──────────┴──────────┐                           │
│              │    MCP Client       │                           │
│              │  (调用数据服务)      │                           │
│              └──────────┬──────────┘                           │
└─────────────────────────┼───────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │      MCP Protocol      │
              └───────────┬───────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI MCP Server                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ OpenBB 接口 │  │ AkShare 接口 │  │  LLM 接口   │             │
│  │  (美股/全球)│  │ (A股/港股)  │  │ (Kimi OAuth)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌─────────┐ ┌──────────┐ ┌─────────┐
        │  Neo4j  │ │PostgreSQL│ │  Redis  │
        │(知识图谱)│ │(时序数据)│ │ (缓存)  │
        │  记忆层  │ │  素材层   │ │  队列   │
        └─────────┘ └──────────┘ └─────────┘
```

### 双层分工

| 层 | 组件 | 职责 | 特点 |
|----|------|------|------|
| **Layer 1** | Neo4j 知识图谱 | 存储「谁和谁有什么关系」 | 确定性、快速、完整 |
| **Layer 2** | LLM 推理 | 判断「这意味着什么」 | 灵活、上下文感知、可解释 |
| **粘合层** | n8n + MCP | 编排流程、调用服务 | 可视化、低代码、可扩展 |

---

## 三、数据模型

### 3.1 Neo4j 图谱模型（Layer 1：记忆）

#### 节点：Company

```cypher
(:Company {
    // 基础标识
    ticker: "NVDA",               // 股票代码，唯一标识
    name: "NVIDIA Corporation",   // 公司名称
    market: "us",                 // 市场：us/cn/hk/tw
    sector: "Semiconductors",     // 行业

    // 发现状态
    discoveryStatus: "explored",  // pending_explore/exploring/explored/seed
    discoveryDepth: 0,            // BFS 深度（种子为0）
    createdAt: datetime(),        // 发现时间
    lastUpdated: datetime(),      // 最后更新时间

    // 运行时数据（WF-1~5 采集）
    lastPrice: 875.50,
    lastPriceUpdated: datetime(),

    // AI 分析结果（WF-9 写入）
    lastEventImpact: "利好",
    lastEventMagnitude: "高",
    lastEventReasoning: "...",
    lastEventAnalyzedAt: datetime()
})
```

#### 节点：ETF

```cypher
(:ETF {
    ticker: "SOXX",               // ETF 代码
    name: "iShares Semiconductor ETF", // 名称
    market: "us",                 // 市场
    createdAt: datetime()         // 创建时间
})
```

#### 关系边类型

| 关系类型 | 方向 | 含义 | 数据来源 |
|----------|------|------|----------|
| `SUPPLIES_TO` | A→B | A 向 B 供应产品/服务 | news_ner, etf_holdings |
| `CUSTOMER_OF` | A→B | A 是 B 的客户 | etf_holdings |
| `COMPETES_WITH` | A↔B | A 与 B 竞争 | peers |
| `PARTNERS_WITH` | A↔B | A 与 B 合作 | news |
| `INVESTED_IN` | A→B | A 投资/持股 B | institutional, holders |
| `SAME_SECTOR` | A↔B | 同一行业 | industry_board |
| `SAME_CONCEPT` | A↔B | 同一概念板块（A股） | concept_board |
| `IN_ETF` | A→ETF | A 是某 ETF 成分股 | etf_holdings |
| `DEPENDS_ON` | A→B | A 依赖 B 的技术/产品 | news_ner |

#### 关系边属性

```cypher
(a:Company)-[:SUPPLIES_TO {
    source: "news_ner",           // 数据来源
    confidence: 0.85,             // 置信度
    context: "新闻标题",           // 上下文（可选）
    updatedAt: datetime()         // 更新时间
}]->(b:Company)
```

### 3.2 PostgreSQL 时序模型（素材层）

#### stock_prices（行情数据）

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
SELECT create_hypertable('stock_prices', 'date');
```

#### financials（财务数据）

```sql
CREATE TABLE financials (
    symbol VARCHAR(20) NOT NULL,
    period VARCHAR(10) NOT NULL,      -- 2024Q1 / 2024annual
    revenue NUMERIC(18,2),
    net_income NUMERIC(18,2),
    gross_margin NUMERIC(8,4),
    operating_margin NUMERIC(8,4),
    eps NUMERIC(10,4),
    market_cap NUMERIC(20,2),
    PRIMARY KEY (symbol, period)
);
```

#### discovery_log（发现日志）

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

#### event_impact_log（事件影响分析日志）

```sql
CREATE TABLE event_impact_log (
    id SERIAL PRIMARY KEY,
    event_description TEXT NOT NULL,
    source_ticker VARCHAR(20) NOT NULL,
    affected_ticker VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,    -- 利好/利空/中性
    magnitude VARCHAR(10) NOT NULL,    -- 高/中/低
    reasoning TEXT,
    confidence NUMERIC(3,2),
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 四、MCP Server API 设计

FastAPI 服务作为 MCP Server，暴露以下工具供 n8n 调用。

### 4.1 发现接口（构建 AI 记忆）

| MCP 工具 | 功能 | 参数 | 返回 |
|----------|------|------|------|
| `discover_peers` | 发现竞争对手 | `symbol: str` | 同业公司列表 → `COMPETES_WITH` |
| `discover_etf_holdings` | ETF 成分股发现 | `symbol: str` | 成分股列表 → `IN_ETF` + 新公司 |
| `discover_institutional` | 机构持仓 | `symbol: str` | 机构持仓 → `INVESTED_IN` |
| `discover_cn_concept` | A股概念板块 | `board_name: str` | 成分股 → `SAME_CONCEPT` |
| `discover_cn_industry` | A股行业板块 | `board_name: str` | 成分股 → `SAME_SECTOR` |
| `discover_cn_holders` | 十大股东 | `symbol: str` | 股东 → `INVESTED_IN` |
| `discover_news` | 新闻获取 | `symbol: str`, `limit: int` | 新闻列表（供 NER 抽取） |

### 4.2 采集接口（AI 分析素材）

| MCP 工具 | 功能 | 参数 |
|----------|------|------|
| `get_profile` | 公司概况 | `symbol: str`, `market: str` |
| `get_price` | 历史行情 | `symbol: str`, `start_date: str`, `end_date: str` |
| `get_income` | 利润表 | `symbol: str`, `period: str`, `limit: int` |
| `get_estimates` | 分析师预期 | `symbol: str` |
| `get_cn_price` | A股行情 | `symbol: str`, `start_date: str`, `end_date: str` |
| `get_cn_financial` | A股财务摘要 | `symbol: str` |

### 4.3 AI 推理接口

| MCP 工具 | 功能 | 参数 | 返回 |
|----------|------|------|------|
| `analyze_impact` | 事件影响分析 | `event: str`, `companies: list`, `relations: list` | JSON 分析结果 |

**返回格式**：
```json
{
  "results": [
    {
      "ticker": "TSM",
      "company": "台积电",
      "direction": "利好",
      "magnitude": "低",
      "reasoning": "NVDA 涨价反映需求旺盛，但代工价格已锁定",
      "confidence": 0.75
    }
  ]
}
```

### 4.4 图谱操作接口

| MCP 工具 | 功能 | 参数 |
|----------|------|------|
| `kg_get_pending_nodes` | 获取待探索节点 | `limit: int`, `market: str?` |
| `kg_create_company` | 创建公司节点 | `ticker`, `name`, `market`, `depth` |
| `kg_create_relation` | 创建关系边 | `from`, `to`, `type`, `source`, `confidence` |
| `kg_update_status` | 更新探索状态 | `ticker`, `status` |
| `kg_get_related` | 获取关联公司 | `ticker`, `depth: int`, `limit: int` |
| `kg_save_impact` | 保存 AI 分析结果 | `ticker`, `event`, `direction`, `magnitude`, `reasoning` |

### 4.5 数据库操作接口

| MCP 工具 | 功能 | 参数 |
|----------|------|------|
| `db_save_prices` | 保存行情数据 | `symbol`, `prices: list` |
| `db_save_financials` | 保存财务数据 | `symbol`, `financials: list` |
| `db_log_discovery` | 记录发现日志 | `explorer`, `discovered`, `relation`, `source`, `depth` |
| `db_log_impact` | 记录分析日志 | `event`, `source`, `affected`, `direction`, `magnitude`, `reasoning` |

---

## 五、工作流设计

### WF-0：BFS 产业链爬虫（记忆构建核心）

**触发**：每 6 小时（Cron）
**输入**：Neo4j 中的 `pending_explore` 节点
**处理**：每批取 10 个节点，调用发现接口，写入新节点和关系
**输出**：图谱持续生长，深度逐层扩展
**初始种子**：NVDA（depth=0, status=seed）

#### n8n 流程

```
Cron触发
  → 查询pending节点(LIMIT 10)
  → 遍历每个节点
  → 市场路由(US/CN)
  → 调用MCP发现接口
  → 数据去重
  → 写入Neo4j
  → 更新状态为explored
  → 循环直到无pending
```

#### 关键 Cypher 查询

**获取待探索节点**：
```cypher
MATCH (c:Company {discoveryStatus: 'pending_explore'})
RETURN c.ticker AS ticker, c.market AS market, c.name AS name
ORDER BY c.discoveryDepth ASC, c.createdAt ASC
LIMIT 10
```

**创建/更新公司节点**：
```cypher
MERGE (c:Company {ticker: $ticker})
ON CREATE SET
    c.name = $name,
    c.market = $market,
    c.discoveryStatus = 'pending_explore',
    c.discoveryDepth = $depth,
    c.createdAt = datetime()
ON MATCH SET
    c.lastRediscoveredAt = datetime()
```

**创建关系边**：
```cypher
MATCH (a:Company {ticker: $fromTicker})
MATCH (b:Company {ticker: $toTicker})
MERGE (a)-[r:COMPETES_WITH]->(b)
SET r.source = $source,
    r.updatedAt = datetime()
```

---

### WF-1~5：动态数据采集（素材层）

| 工作流 | 触发时间 | 功能 | 数据源 |
|--------|----------|------|--------|
| **WF-1** 每日行情 | 每交易日 21:00 | 采集所有 explored 公司的价格数据 | OpenBB/AkShare |
| **WF-2** 季度财务 | 每月 1 号 02:00 | 采集财务报表 | OpenBB/AkShare |
| **WF-3** 公司概况 | 每月 15 号 02:00 | 更新公司基本信息 | OpenBB/AkShare |
| **WF-4** 新闻事件 | 每日 09:00 / 21:00 | 采集新闻 + NER 抽取关系 | OpenBB News + LLM |
| **WF-5** 分析师预期 | 每周一 09:00 | 更新一致预期数据 | OpenBB |

#### 公共逻辑

```
Cron触发
  → 查询所有explored公司列表
  → 分批处理(每批20个防超时)
  → MCP采集接口
  → 写入PostgreSQL
  → 同步更新Neo4j节点字段
```

---

### WF-6~8：关系增强（记忆增强）

| 工作流 | 触发时间 | 功能 |
|--------|----------|------|
| **WF-6** 供应关系推断 | 每月 15 号 03:00 | 新闻共现 + ETF 交叉 → 推断潜在供应链 |
| **WF-7** 竞争关系更新 | 每月 1 号 04:00 | 同行业公司营收对比 → 验证竞争关系 |
| **WF-8** 风险传导预计算 | 事件驱动 | 沿 SUPPLIES_TO 路径预计算传导链 |

---

### WF-9：事件影响分析（双层架构核心）

**触发方式**：
- Webhook: `POST /webhook/event-impact`
- 手动触发（n8n 界面）

**输入**：
```json
{
  "ticker": "NVDA",
  "event": "H200 GPU 租赁价格上涨 30%"
}
```

#### n8n 流程

```
Webhook接收
  → 解析事件
  → MCP kg_get_related(扩散3跳)
  → Code组装Prompt
  → AI Agent(LLM)
  → 解析JSON
  → MCP kg_save_impact
  → 高影响预警判断
  → 结束
```

#### AI Agent Prompt 模板

```
你是一位资深产业链分析专家。请基于以下产业链关系数据，分析事件对每家关联公司的影响。

## 事件
{event_description}

## 关联公司及产业链路径
{company_list_with_paths}

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
[{"ticker": "XXX", "company": "名称", "direction": "利好/利空/中性", "magnitude": "高/中/低", "reasoning": "...", "confidence": 0.8}]
```

#### 高影响预警

当 `magnitude = "高"` 时：
1. 发送通知（Slack/邮件/企业微信）
2. 记录到 `event_impact_log` 表
3. 可选：触发后续分析工作流

---

## 六、项目结构

```
Supply-Chain_Analysis/
├── docker-compose.yml              # 基础设施编排
├── .env                            # 环境变量（API密钥等）
├── data-api/                       # FastAPI MCP Server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI 应用入口
│   ├── mcp_server.py               # MCP 协议实现
│   ├── tools/                      # MCP 工具定义
│   │   ├── __init__.py
│   │   ├── discover.py             # 发现接口
│   │   ├── collect.py              # 采集接口
│   │   ├── analyze.py              # AI 分析接口
│   │   ├── kg_ops.py               # 图谱操作
│   │   └── db_ops.py               # 数据库操作
│   ├── clients/
│   │   ├── openbb_client.py        # OpenBB 封装
│   │   ├── akshare_client.py       # AkShare 封装
│   │   ├── kimi_client.py          # Kimi OAuth 封装
│   │   └── neo4j_client.py         # Neo4j 连接
│   └── config.py                   # 配置管理
├── n8n-workflows/                  # n8n 工作流导出
│   ├── wf-0-bfs-crawler.json
│   ├── wf-1-daily-price.json
│   ├── wf-2-quarterly-financial.json
│   ├── wf-3-company-profile.json
│   ├── wf-4-news-collection.json
│   ├── wf-5-analyst-estimates.json
│   ├── wf-6-supply-inference.json
│   ├── wf-7-competition-update.json
│   ├── wf-8-risk-precalc.json
│   └── wf-9-event-analysis.json
├── init-scripts/                   # 初始化脚本
│   ├── neo4j-init.cypher           # 初始种子 + 索引
│   └── postgres-init.sql           # 表结构
└── docs/                           # 文档
    └── superpowers/
        └── specs/
            └── 2026-03-29-supply-chain-kg-design.md  # 本文件
```

---

## 七、部署配置

### 7.1 Docker Compose

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

### 7.2 环境变量（.env）

```bash
# Neo4j
NEO4J_PASSWORD=your_neo4j_password

# PostgreSQL
POSTGRES_PASSWORD=your_postgres_password

# n8n
N8N_PASSWORD=your_n8n_password

# OpenBB
OPENBB_PAT=your_openbb_pat

# Kimi OAuth
KIMI_CLIENT_ID=your_kimi_client_id
KIMI_CLIENT_SECRET=your_kimi_client_secret
```

### 7.3 初始化脚本

#### neo4j-init.cypher

```cypher
// 创建 NVDA 种子节点
CREATE (c:Company {
    ticker: 'NVDA',
    name: 'NVIDIA Corporation',
    market: 'us',
    sector: 'Semiconductors',
    discoveryStatus: 'pending_explore',
    discoveryDepth: 0,
    createdAt: datetime()
});

// 创建索引
CREATE INDEX company_ticker IF NOT EXISTS FOR (c:Company) ON (c.ticker);
CREATE INDEX company_status IF NOT EXISTS FOR (c:Company) ON (c.discoveryStatus);
CREATE INDEX company_depth IF NOT EXISTS FOR (c:Company) ON (c.discoveryDepth);
CREATE INDEX company_market IF NOT EXISTS FOR (c:Company) ON (c.market);
```

#### postgres-init.sql

见「数据模型」部分的 DDL。

---

## 八、监控查询

### 图谱规模监控

```cypher
// 节点数量（按状态）
MATCH (c:Company)
RETURN c.discoveryStatus AS status, count(*) AS count

// 关系类型分布
MATCH ()-[r]-()
RETURN type(r) AS relationType, count(*) AS count
ORDER BY count DESC

// BFS 深度分布
MATCH (c:Company)
RETURN c.discoveryDepth AS depth, count(*) AS companies
ORDER BY depth

// 与种子无直接关联的公司（验证全拓扑）
MATCH (c:Company)
WHERE NOT (c)-[]-(:Company {ticker: 'NVDA'})
RETURN count(c) AS companiesNotDirectlyLinkedToNVDA
```

### 数据采集监控

```sql
-- 最新行情数据覆盖
SELECT symbol, MAX(date) AS last_date, COUNT(*) AS total_days
FROM stock_prices
GROUP BY symbol
ORDER BY last_date DESC
LIMIT 20;

-- 发现日志统计
SELECT depth, COUNT(*) AS discoveries
FROM discovery_log
GROUP BY depth
ORDER BY depth;

-- 最近事件分析结果
SELECT * FROM event_impact_log
ORDER BY analyzed_at DESC
LIMIT 20;
```

---

## 九、扩展路线

- [ ] **Phase 1**（当前）：BFS 种子扩散 + 全拓扑记忆 + 动态采集 + AI 事件分析
- [ ] **Phase 2**：SEC EDGAR 10-K/10-Q 全文 LLM 抽取供应链关系
- [ ] **Phase 3**：n8n MCP Server + DeerFlow Agent 按需扩散
- [ ] **Phase 4**：pgvector 语义搜索 — AI 可以用自然语言查询图谱
- [ ] **Phase 5**：Neo4j Bloom + Streamlit 实时图谱可视化
- [ ] **Phase 6**：多事件关联分析 — AI 同时考虑多个并发事件的叠加影响

---

## 十、验证清单

### 部署验证

- [ ] `docker compose up -d` 所有服务启动成功
- [ ] Neo4j Browser 访问 http://localhost:7474 正常
- [ ] n8n 访问 http://localhost:5678 正常
- [ ] FastAPI docs 访问 http://localhost:8000/docs 正常
- [ ] MCP Server 健康检查通过

### 功能验证

- [ ] WF-0：运行后 Neo4j 中新增公司节点
- [ ] WF-1：收盘后 PostgreSQL 中有行情数据
- [ ] WF-9：Webhook 触发后返回 AI 分析结果
- [ ] 双层推理：同一关系在不同事件下产生不同判断

### 性能验证

- [ ] WF-0 单批次执行时间 < 5 分钟
- [ ] WF-9 事件分析响应时间 < 30 秒
- [ ] Neo4j 3跳查询响应时间 < 100ms

---

## 附录：术语表

| 术语 | 解释 |
|------|------|
| BFS | 广度优先搜索，用于从种子节点逐层发现关联公司 |
| MCP | Model Context Protocol，模型上下文协议，用于标准化工具调用 |
| Layer 1 | 知识图谱层，负责存储和查询结构化关系 |
| Layer 2 | AI 推理层，负责基于上下文判断影响 |
| WF | Workflow，工作流，n8n 中的自动化流程单元 |
| 跳数 | 两个节点之间的最短路径边数 |
| 种子 | BFS 起点，如 NVDA |

---

**设计完成日期**：2026-03-29
**版本**：v1.0
**作者**：Claude Code

# 产业链知识图谱 + AI 双层架构系统

## 详细实施计划 (Detailed Implementation Plan)

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 版本 | 1.0.0 |
| 创建日期 | 2024-03-29 |
| 预计工期 | 4-6 周 |
| 负责人 | TBD |
| 状态 | 计划中 |

---

## 1. 项目概述

### 1.1 目标

构建一个完整的产业链知识图谱系统，实现：
- 从 NVIDIA 种子自动发现产业链上下游公司
- 采集多维度数据（行情、财务、新闻）
- 利用 LLM 分析事件影响传导
- 通过 n8n 工作流实现全自动化

### 1.2 成功标准

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 知识图谱节点数 | > 1000 | Neo4j 查询 |
| 关系边数 | > 5000 | Neo4j 查询 |
| API 响应时间 | < 500ms | 监控日志 |
| 数据新鲜度 | 每日更新 | 时间戳检查 |
| 覆盖率 | 美股 TOP100 + A股半导体 | 人工抽查 |

### 1.3 关键里程碑

```
Week 1: 基础设施 + 核心客户端
Week 2: MCP 工具 + API Server
Week 3: n8n 工作流 + 集成测试
Week 4: 性能优化 + 文档完善
Week 5-6: 用户测试 + 迭代优化
```

---

## 2. 任务分解 (WBS)

### Phase 1: 项目基础设施 (Week 1, Days 1-2)

#### Task 1.1: 环境配置
**负责人**: DevOps
**工期**: 4h
**依赖**: 无

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 1.1.1 | 创建 .env.example | 包含所有必需变量 |
| 1.1.2 | 创建 .gitignore | 排除敏感文件和缓存 |
| 1.1.3 | 创建目录结构 | data-api/, init-scripts/, scripts/ |

**输出物**:
- `.env.example`
- `.gitignore`
- 目录结构

---

#### Task 1.2: Docker Compose 编排
**负责人**: DevOps
**工期**: 8h
**依赖**: Task 1.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 1.2.1 | 配置 Neo4j 服务 | 端口 7474/7687，数据持久化 |
| 1.2.2 | 配置 PostgreSQL + TimescaleDB | 端口 5432，启用扩展 |
| 1.2.3 | 配置 Redis | 端口 6379 |
| 1.2.4 | 配置 n8n | 端口 5678，基础认证 |
| 1.2.5 | 配置 data-api | 端口 8000，热重载 |
| 1.2.6 | 服务依赖关系 | 正确的 depends_on |

**输出物**:
- `docker-compose.yml`

**检查点**:
```bash
docker-compose config  # 验证配置
docker-compose up -d   # 启动测试
```

---

#### Task 1.3: 初始化脚本
**负责人**: Backend
**工期**: 6h
**依赖**: Task 1.2

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 1.3.1 | Neo4j 约束和索引 | ticker 唯一，status/depth 索引 |
| 1.3.2 | NVDA 种子节点 | 包含完整属性 |
| 1.3.3 | PostgreSQL schema | 3 张表 + TimescaleDB hypertable |
| 1.3.4 | 测试初始化 | 容器启动自动执行 |

**输出物**:
- `init-scripts/neo4j-init.cypher`
- `init-scripts/postgres-init.sql`

---

### Phase 2: Data API 核心 (Week 1-2, Days 3-7)

#### Task 2.1: 配置管理
**负责人**: Backend
**工期**: 3h
**依赖**: Task 1.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.1.1 | Pydantic Settings | 所有环境变量类型安全 |
| 2.1.2 | DSN 构造 | PostgreSQL 连接字符串 |
| 2.1.3 | 配置缓存 | @lru_cache 优化 |
| 2.1.4 | 单元测试 | 3 个测试用例通过 |

**输出物**:
- `data-api/config.py`
- `data-api/tests/test_config.py`

---

#### Task 2.2: Neo4j 客户端
**负责人**: Backend
**工期**: 8h
**依赖**: Task 2.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.2.1 | 异步驱动连接 | 单例模式，连接池 |
| 2.2.2 | 基础 CRUD | create_company, update_status |
| 2.2.3 | 关系操作 | create_relation |
| 2.2.4 | 图查询 | get_pending_nodes, get_related |
| 2.2.5 | 连接验证 | verify_connectivity |
| 2.2.6 | 单元测试 | Mock 驱动测试 |

**输出物**:
- `data-api/clients/neo4j_client.py`
- `data-api/tests/test_neo4j_client.py`

**测试覆盖**:
- [ ] 创建节点
- [ ] 更新状态
- [ ] 创建关系
- [ ] 查询待探索节点
- [ ] 查询关联公司

---

#### Task 2.3: PostgreSQL 客户端
**负责人**: Backend
**工期**: 6h
**依赖**: Task 2.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.3.1 | asyncpg 连接池 | min=5, max=20 |
| 2.3.2 | 价格数据保存 | save_prices 批量插入 |
| 2.3.3 | 发现日志 | log_discovery |
| 2.3.4 | 影响日志 | log_impact |
| 2.3.5 | 查询接口 | fetch, fetchrow |

**输出物**:
- `data-api/clients/postgres_client.py`

---

#### Task 2.4: OpenBB 客户端
**负责人**: Data Engineer
**工期**: 6h
**依赖**: Task 2.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.4.1 | PAT 认证 | 可选登录 |
| 2.4.2 | 发现接口 | discover_peers, etf_holdings |
| 2.4.3 | 数据接口 | get_price, get_profile |
| 2.4.4 | 财务接口 | get_income, get_estimates |
| 2.4.5 | yfinance fallback | 免费数据源支持 |
| 2.4.6 | 错误处理 | 优雅降级 |

**输出物**:
- `data-api/clients/openbb_client.py`

**测试用例**:
```python
# 测试发现竞争对手
peers = client.discover_peers("NVDA")
assert len(peers) > 0

# 测试获取价格
prices = client.get_price("AAPL", "2024-01-01", "2024-01-31")
assert len(prices) == 21  # 交易日
```

---

#### Task 2.5: AkShare 客户端
**负责人**: Data Engineer
**工期**: 6h
**依赖**: Task 2.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.5.1 | 概念板块 | discover_cn_concept |
| 2.5.2 | 行业板块 | discover_cn_industry |
| 2.5.3 | 股东信息 | discover_cn_holders |
| 2.5.4 | A股价格 | get_cn_price |
| 2.5.5 | 财务摘要 | get_cn_financial |

**输出物**:
- `data-api/clients/akshare_client.py`

---

#### Task 2.6: Kimi 客户端
**负责人**: AI Engineer
**工期**: 8h
**依赖**: Task 2.1

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.6.1 | OAuth 认证 | client_credentials 流程 |
| 2.6.2 | Token 缓存 | 避免重复获取 |
| 2.6.3 | Prompt 工程 | 产业链影响分析模板 |
| 2.6.4 | 结果解析 | JSON 提取和验证 |
| 2.6.5 | 错误处理 | 超时、限流处理 |
| 2.6.6 | 测试 | Mock API 测试 |

**Prompt 模板**:
```
你是一位资深产业链分析专家...
事件: {event}
关联公司: {companies}
输出 JSON: [...]
```

**输出物**:
- `data-api/clients/kimi_client.py`

---

#### Task 2.7: 客户端整合
**负责人**: Backend
**工期**: 2h
**依赖**: Task 2.2-2.6

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 2.7.1 | __init__.py | 统一导出 |
| 2.7.2 | 导入测试 | 无循环依赖 |

**输出物**:
- `data-api/clients/__init__.py`

---

### Phase 3: MCP 工具层 (Week 2, Days 8-10)

#### Task 3.1: 发现工具 (discover)
**负责人**: Backend
**工期**: 6h
**依赖**: Task 2.7

| 工具 | 功能 | 测试 |
|------|------|------|
| discover_peers | 竞争对手发现 | ✅ |
| discover_etf_holdings | ETF持仓 | ✅ |
| discover_institutional | 机构持股 | ✅ |
| bfs_discovery | BFS扩散 | ✅ |
| expand_node | 单节点扩展 | ✅ |

**输出物**:
- `data-api/tools/discover.py`
- `data-api/tests/test_discover.py`

---

#### Task 3.2: 采集工具 (collect)
**负责人**: Backend
**工期**: 6h
**依赖**: Task 2.7

| 工具 | 功能 | 数据源 |
|------|------|--------|
| get_profile | 公司资料 | OpenBB/yfinance |
| get_price | 历史价格 | OpenBB/yfinance |
| get_financials | 财务数据 | OpenBB |
| batch_collect | 批量采集 | 组合 |

**输出物**:
- `data-api/tools/collect.py`
- `data-api/tests/test_collect.py`

---

#### Task 3.3: 分析工具 (analyze)
**负责人**: AI Engineer
**工期**: 6h
**依赖**: Task 2.6, Task 3.1

| 工具 | 功能 | 输出 |
|------|------|------|
| analyze_event_impact | 事件影响分析 | 方向/程度/置信度 |
| analyze_supply_chain_impact | 全链分析 | 完整报告 |
| generate_impact_summary | 生成摘要 | Markdown |

**输出物**:
- `data-api/tools/analyze.py`

---

#### Task 3.4: 图谱操作工具 (kg_ops)
**负责人**: Backend
**工期**: 6h
**依赖**: Task 2.2

| 工具 | 功能 |
|------|------|
| upsert_company | 创建/更新公司 |
| upsert_relationship | 创建关系 |
| batch_upsert_companies | 批量公司 |
| batch_upsert_relationships | 批量关系 |
| get_company_neighbors | 获取邻居 |
| find_paths | 路径查找 |
| get_subgraph | 子图提取 |
| get_graph_stats | 统计信息 |

**输出物**:
- `data-api/tools/kg_ops.py`

---

#### Task 3.5: 数据库操作工具 (db_ops)
**负责人**: Backend
**工期**: 4h
**依赖**: Task 2.3

| 工具 | 功能 |
|------|------|
| save_price_batch | 批量保存价格 |
| log_discovery_event | 记录发现 |
| log_impact_analysis | 记录分析 |
| get_price_history | 查询历史 |
| get_discovery_history | 查询发现日志 |
| get_impact_history | 查询影响日志 |

**输出物**:
- `data-api/tools/db_ops.py`

---

#### Task 3.6: 工具整合
**负责人**: Backend
**工期**: 2h
**依赖**: Task 3.1-3.5

**输出物**:
- `data-api/tools/__init__.py`

---

### Phase 4: MCP Server + API (Week 2, Days 11-12)

#### Task 4.1: MCP Server 实现
**负责人**: Backend
**工期**: 8h
**依赖**: Task 3.6

| 子任务 | 描述 | 验收标准 |
|--------|------|----------|
| 4.1.1 | MCPTool 定义 | name/description/parameters/handler |
| 4.1.2 | MCPServer 类 | register_tool, handle_request |
| 4.1.3 | 工具注册 | 26+ 工具全部注册 |
| 4.1.4 | 错误处理 | 友好错误返回 |
| 4.1.5 | 日志记录 | 调用日志 |

**输出物**:
- `data-api/mcp_server.py`

---

#### Task 4.2: FastAPI 主应用
**负责人**: Backend
**工期**: 6h
**依赖**: Task 4.1

| 子任务 | 描述 | 端点 |
|--------|------|------|
| 4.2.1 | 应用生命周期 | startup/shutdown |
| 4.2.2 | 健康检查 | GET /health |
| 4.2.3 | MCP 端点 | POST /mcp |
| 4.2.4 | 工具列表 | GET /mcp/tools |
| 4.2.5 | CORS 中间件 | 跨域支持 |
| 4.2.6 | 异常处理 | 全局异常捕获 |

**输出物**:
- `data-api/main.py`

---

#### Task 4.3: Dockerfile
**负责人**: DevOps
**工期**: 3h
**依赖**: Task 4.2

| 子任务 | 描述 |
|--------|------|
| 4.3.1 | Python 3.11 基础镜像 |
| 4.3.2 | 依赖安装 |
| 4.3.3 | 代码复制 |
| 4.3.4 | 启动命令 |

**输出物**:
- `data-api/Dockerfile`

---

#### Task 4.4: 集成测试
**负责人**: QA
**工期**: 4h
**依赖**: Task 4.3

| 测试项 | 描述 |
|--------|------|
| 容器构建 | docker build 成功 |
| 服务启动 | docker-compose up 成功 |
| API 测试 | 所有端点返回 200 |
| MCP 测试 | 工具调用正常 |

**输出物**:
- 测试报告

---

### Phase 5: n8n 工作流 (Week 3, Days 13-16)

#### Task 5.1: 工作流设计
**负责人**: Automation Engineer
**工期**: 8h
**依赖**: Task 4.4

| 工作流 | 触发 | 功能 | 优先级 |
|--------|------|------|--------|
| WF-0 | 手动 | 种子初始化 | P0 |
| WF-1 | 每6小时 | BFS扩散 | P0 |
| WF-2 | 每天21:00 | 价格采集 | P0 |
| WF-3 | 每月 | 财报采集 | P1 |
| WF-4 | 每天2次 | 新闻采集 | P1 |
| WF-5 | 每周 | 分析师预测 | P2 |
| WF-6 | 每月 | 供应链推理 | P2 |
| WF-7 | 每月 | 竞争更新 | P2 |
| WF-8 | 事件驱动 | 风险预计算 | P1 |
| WF-9 | Webhook | 事件分析 | P0 |

**输出物**:
- `n8n-workflows/README.md`
- 工作流设计文档

---

#### Task 5.2: 核心工作流实现 (WF-0, WF-1, WF-9)
**负责人**: Automation Engineer
**工期**: 16h
**依赖**: Task 5.1

**WF-0: Seed Initialization**
- 创建种子公司节点
- 设置初始状态

**WF-1: BFS Crawler**
- 获取待探索节点
- 调用 discover_peers
- 创建新节点和关系
- 更新状态

**WF-9: Event Impact Analysis**
- 接收事件输入
- BFS 发现关联公司
- 调用 analyze_impact
- 保存结果
- 生成报告

**输出物**:
- `n8n-workflows/wf-0-seed.json`
- `n8n-workflows/wf-1-bfs-crawler.json`
- `n8n-workflows/wf-9-event-analysis.json`

---

#### Task 5.3: 数据采集工作流 (WF-2, WF-3, WF-4)
**负责人**: Automation Engineer
**工期**: 12h
**依赖**: Task 5.1

**输出物**:
- `n8n-workflows/wf-2-daily-price.json`
- `n8n-workflows/wf-3-quarterly-financial.json`
- `n8n-workflows/wf-4-news-collection.json`

---

#### Task 5.4: 辅助工作流 (WF-5, WF-6, WF-7, WF-8)
**负责人**: Automation Engineer
**工期**: 12h
**依赖**: Task 5.1

**输出物**:
- `n8n-workflows/wf-5-analyst-estimates.json`
- `n8n-workflows/wf-6-supply-inference.json`
- `n8n-workflows/wf-7-competition-update.json`
- `n8n-workflows/wf-8-risk-precalc.json`

---

### Phase 6: 测试与优化 (Week 3-4, Days 17-21)

#### Task 6.1: 单元测试完善
**负责人**: QA
**工期**: 12h
**依赖**: Phase 2-4

| 模块 | 覆盖率目标 | 状态 |
|------|-----------|------|
| config | 100% | |
| neo4j_client | 80% | |
| openbb_client | 60% | |
| tools | 80% | |
| mcp_server | 70% | |

**输出物**:
- 测试报告
- 覆盖率报告

---

#### Task 6.2: 集成测试
**负责人**: QA
**工期**: 8h
**依赖**: Task 6.1

| 场景 | 描述 |
|------|------|
| 端到端发现 | NVDA → 发现竞争对手 → 入库 |
| 价格采集 | 获取历史价格 → 保存 TimescaleDB |
| 影响分析 | 模拟事件 → AI分析 → 保存结果 |
| 工作流 | WF-1 完整执行 |

**输出物**:
- 集成测试报告

---

#### Task 6.3: 性能优化
**负责人**: Backend
**工期**: 12h
**依赖**: Task 6.2

| 优化项 | 目标 | 方法 |
|--------|------|------|
| API 响应 | < 500ms | 缓存、连接池 |
| BFS 查询 | < 2s | 索引优化 |
| 批量插入 | > 1000条/秒 | 批量API |
| 内存使用 | < 2GB | 流式处理 |

**输出物**:
- 性能测试报告
- 优化记录

---

#### Task 6.4: 压力测试
**负责人**: DevOps
**工期**: 6h
**依赖**: Task 6.3

| 指标 | 目标 |
|------|------|
| 并发请求 | 100 |
| 吞吐量 | 1000 req/min |
| 可用性 | 99.9% |

**工具**: k6, locust

---

### Phase 7: 文档与部署 (Week 4-5, Days 22-28)

#### Task 7.1: API 文档
**负责人**: Technical Writer
**工期**: 8h
**依赖**: Phase 4

| 文档 | 内容 |
|------|------|
| OpenAPI Spec | /docs 自动生成 |
| MCP 工具手册 | 每个工具的详细说明 |
| 示例代码 | curl, Python, JavaScript |

**输出物**:
- `docs/API.md`

---

#### Task 7.2: 用户指南
**负责人**: Technical Writer
**工期**: 12h
**依赖**: Task 7.1

| 章节 | 内容 |
|------|------|
| 快速开始 | 3步启动 |
| 安装指南 | 详细安装步骤 |
| 配置说明 | 环境变量详解 |
| 使用示例 | 常见用例 |
| 故障排除 | FAQ |

**输出物**:
- `docs/GUIDE.md` (已创建)

---

#### Task 7.3: 部署文档
**负责人**: DevOps
**工期**: 6h
**依赖**: Task 7.2

| 环境 | 说明 |
|------|------|
| 本地开发 | docker-compose |
| 测试环境 | CI/CD |
| 生产环境 | Kubernetes |

**输出物**:
- `docs/DEPLOYMENT.md`
- K8s manifests (可选)

---

#### Task 7.4: 最终验收
**负责人**: PM
**工期**: 4h
**依赖**: Task 7.3

**验收清单**:
- [ ] 所有功能正常运行
- [ ] 测试通过率 > 90%
- [ ] 文档完整
- [ ] 代码审查通过
- [ ] 性能达标

---

## 3. 依赖关系图

```
Phase 1: 基础设施
├── Task 1.1: 环境配置
├── Task 1.2: Docker Compose
└── Task 1.3: 初始化脚本
    │
    ▼
Phase 2: Data API 核心
├── Task 2.1: 配置管理
├── Task 2.2: Neo4j 客户端
├── Task 2.3: PostgreSQL 客户端
├── Task 2.4: OpenBB 客户端
├── Task 2.5: AkShare 客户端
├── Task 2.6: Kimi 客户端
└── Task 2.7: 客户端整合
    │
    ▼
Phase 3: MCP 工具层
├── Task 3.1: 发现工具
├── Task 3.2: 采集工具
├── Task 3.3: 分析工具
├── Task 3.4: 图谱工具
├── Task 3.5: 数据库工具
└── Task 3.6: 工具整合
    │
    ▼
Phase 4: MCP Server + API
├── Task 4.1: MCP Server
├── Task 4.2: FastAPI
├── Task 4.3: Dockerfile
└── Task 4.4: 集成测试
    │
    ▼
Phase 5: n8n 工作流
├── Task 5.1: 工作流设计
├── Task 5.2: 核心工作流
├── Task 5.3: 采集工作流
└── Task 5.4: 辅助工作流
    │
    ▼
Phase 6: 测试与优化
├── Task 6.1: 单元测试
├── Task 6.2: 集成测试
├── Task 6.3: 性能优化
└── Task 6.4: 压力测试
    │
    ▼
Phase 7: 文档与部署
├── Task 7.1: API 文档
├── Task 7.2: 用户指南
├── Task 7.3: 部署文档
└── Task 7.4: 最终验收
```

---

## 4. 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| OpenBB API 不稳定 | 中 | 高 | 实现 yfinance fallback |
| Kimi API 限流 | 中 | 中 | 添加重试和队列 |
| Neo4j 性能瓶颈 | 低 | 高 | 提前设计索引 |
| n8n 学习曲线 | 中 | 低 | 预留学习时间 |
| 数据质量问题 | 中 | 中 | 数据验证和清洗 |

---

## 5. 资源需求

### 5.1 人力资源

| 角色 | 人数 | 时间投入 |
|------|------|----------|
| Backend Engineer | 1 | 全程 |
| Data Engineer | 1 | Week 1-2 |
| AI Engineer | 1 | Week 1-3 |
| DevOps | 1 | Week 1, 4 |
| QA | 1 | Week 3-4 |
| Technical Writer | 1 | Week 4 |

### 5.2 基础设施

| 资源 | 规格 | 成本/月 |
|------|------|---------|
| 开发服务器 | 4C8G | $50 |
| 测试服务器 | 2C4G | $25 |
| GitHub Pro | - | $4 |

---

## 6. 检查点与评审

### 6.1 每周评审

| 周次 | 评审内容 | 参与人 |
|------|----------|--------|
| Week 1 | 基础设施完成 | 全团队 |
| Week 2 | MCP Server 可用 | 全团队 |
| Week 3 | 工作流运行 | 全团队 |
| Week 4 | 测试通过 | PM + QA |
| Week 5 | 文档完成 | PM |
| Week 6 | 项目交付 | 全团队 |

### 6.2 每日站会

- 昨天完成了什么
- 今天计划做什么
- 有什么阻碍

---

## 7. 交付物清单

### 7.1 代码

- [ ] 完整代码库
- [ ] 单元测试
- [ ] 集成测试
- [ ] Dockerfile
- [ ] docker-compose.yml

### 7.2 文档

- [ ] README.md
- [ ] docs/GUIDE.md
- [ ] docs/API.md
- [ ] docs/DEPLOYMENT.md
- [ ] n8n-workflows/README.md

### 7.3 工作流

- [ ] WF-0 ~ WF-9 JSON 文件

### 7.4 配置

- [ ] .env.example
- [ ] 初始化脚本

---

## 8. 附录

### 8.1 术语表

| 术语 | 说明 |
|------|------|
| MCP | Model Context Protocol |
| BFS | Breadth-First Search |
| KG | Knowledge Graph |
| PAT | Personal Access Token |
| Hypertable | TimescaleDB 时序表 |

### 8.2 参考链接

- [OpenBB Docs](https://docs.openbb.co)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [n8n Documentation](https://docs.n8n.io)

### 8.3 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024-03-29 | 初始版本 |

---

**文档结束**

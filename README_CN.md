# FinchBot (雀翎) — 轻量灵活，自主扩展的 AI Agent 框架

<p align="center">
  <img src="docs/image/image.png" alt="FinchBot Logo" width="600">
</p>

<p align="center">
  <em>基于 LangChain v1.2 与 LangGraph v1.0 构建<br>
  具备持久记忆、动态提示词、自主能力扩展</em>
</p>

<p align="center">🌐 <strong>Language</strong>: <a href="README.md">English</a> | <a href="README_CN.md">中文</a></p>

<p align="center">
  <a href="https://blog.csdn.net/Yunyi_Chi">
    <img src="https://img.shields.io/badge/CSDN-玄同765-orange?style=flat-square&logo=csdn" alt="CSDN Blog">
  </a>
  <a href="https://github.com/xt765/FinchBot">
    <img src="https://img.shields.io/badge/GitHub-FinchBot-black?style=flat-square&logo=github" alt="GitHub">
  </a>
  <a href="https://gitee.com/xt765/FinchBot">
    <img src="https://img.shields.io/badge/Gitee-FinchBot-red?style=flat-square&logo=gitee" alt="Gitee">
  </a>
  <img src="https://img.shields.io/badge/Gitee-官方推荐-red?style=flat-square&logo=gitee&logoColor=white" alt="Gitee Recommended">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Ruff-Formatter-orange?style=flat-square&logo=ruff" alt="Ruff">
  <img src="https://img.shields.io/badge/Basedpyright-TypeCheck-purple?style=flat-square&logo=python" alt="Basedpyright">
  <img src="https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square&logo=open-source-initiative" alt="License">
</p>

**FinchBot (雀翎)** 是一个赋予智能体真正自主性的 AI Agent 框架，基于 **LangChain v1.2** 和 **LangGraph v1.0** 构建。全异步架构设计，让智能体具备自主决策、自主扩展、自主进化的能力：

1. **能力自扩展** — Agent 遇到能力边界时，可使用内置工具配置 MCP、创建技能
2. **任务自调度** — Agent 可自主设定后台任务、定时执行，不阻塞对话
3. **记忆自管理** — Agent 可自主记忆、检索、遗忘，Agentic RAG + 加权 RRF 混合检索，智能召回
4. **行为自进化** — Agent 和用户都可自主修改提示词，持续迭代优化行为

---

## 能力边界问题

| 用户请求 | 传统 AI 回应 | FinchBot 回应 |
|:---|:---|:---|
| "分析这个数据库" | "我没有数据库工具" | 自主配置 SQLite MCP，然后分析 |
| "学会做某事" | "等开发者添加功能" | 通过 skill-creator 自主创建技能 |
| "帮我监控 24 小时" | "我只能在你问的时候响应" | 创建定时任务，自主监控 |
| "处理这个大文件" | 阻塞对话，用户等待 | 后台执行，用户继续 |
| "记住我的偏好" | "下次对话就忘了" | 持久记忆，Agentic RAG + 加权 RRF 混合检索 |
| "调整你的行为" | "提示词是固定的" | 动态修改提示词，热加载 |

---

## 系统架构

**核心理念**：FinchBot 智能体不只是响应 — 它们自主执行、自主规划、自主扩展。

### 自主性金字塔

```mermaid
flowchart TB
    subgraph L4["扩展层 - 自主扩展能力"]
        direction LR
        E1["MCP 自动配置"]
        E2["技能创建"]
        E3["动态加载"]
    end

    subgraph L3["规划层 - 自主创建计划"]
        direction LR
        P1["定时任务"]
        P2["心跳监控"]
        P3["自动触发"]
    end

    subgraph L2["执行层 - 自主执行任务"]
        direction LR
        X1["后台任务"]
        X2["异步处理"]
        X3["非阻塞"]
    end

    subgraph L1["响应层 - 响应用户请求"]
        direction LR
        R1["对话系统"]
        R2["工具调用"]
        R3["上下文记忆"]
    end

    L4 --> L3 --> L2 --> L1

    style L1 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
    style L2 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    style L3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c
    style L4 fill:#fff9c4,stroke:#f9a825,stroke-width:2px,color:#f57f17
```

| 层级 | 能力 | 实现方式 | 用户价值 |
|:---:|:---|:---|:---|
| **响应层** | 响应用户请求 | 对话系统 + 工具调用 | 基础交互 |
| **执行层** | 自主执行任务 | 后台任务系统 | 对话不阻塞 |
| **规划层** | 自主创建计划 | 定时任务 + 心跳服务 | 自动化执行 |
| **扩展层** | 自主扩展能力 | MCP 配置 + 技能创建 | 无限扩展 |

### 整体架构

```mermaid
graph TB
    classDef uiLayer fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c;
    classDef coreLayer fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef infraLayer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    subgraph UI [用户交互层]
        CLI[CLI 界面]:::uiLayer
        Channels[多平台通道<br/>Discord/钉钉/飞书/微信/邮件]:::uiLayer
    end

    subgraph Core [Agent 核心层]
        Agent[LangGraph Agent<br/>决策引擎]:::coreLayer
        Context[ContextBuilder<br/>上下文构建]:::coreLayer
        Tools[ToolRegistry<br/>15 内置工具 + MCP]:::coreLayer
        Memory[MemoryManager<br/>双层记忆]:::coreLayer
    end

    subgraph Infra [基础设施层]
        Storage[双层存储<br/>SQLite + VectorStore]:::infraLayer
        LLM[LLM 提供商<br/>OpenAI/Anthropic/DeepSeek]:::infraLayer
    end

    CLI --> Agent
    Channels --> Agent

    Agent --> Context
    Agent <--> Tools
    Agent <--> Memory

    Memory --> Storage
    Agent --> LLM
```

### 数据流

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant C as 通道
    participant B as MessageBus
    participant F as AgentFactory
    participant A as Agent
    participant M as MemoryManager
    participant T as 工具
    participant L as LLM

    U->>C: 发送消息
    C->>B: InboundMessage
    B->>F: 获取/创建 Agent
    F->>A: 返回编译后的 Agent
    
    Note over A: 构建上下文
    A->>M: 召回相关记忆
    M-->>A: 返回上下文
    
    A->>L: 发送请求
    L-->>A: 流式响应
    
    alt 需要工具调用
        A->>T: 执行工具
        T-->>A: 返回结果
        A->>L: 继续处理
        L-->>A: 最终响应
    end
    
    A->>M: 存储新记忆
    A->>B: OutboundMessage
    B->>C: 路由到通道
    C->>U: 显示响应
```

### 安全机制

**智能体自主 ≠ 智能体乱来。** FinchBot 实现了多重安全机制：

| 安全机制 | 状态 | 作用 |
|:---|:---:|:---|
| **路径限制** | ✅ 已实现 | 文件操作限定在 workspace 目录内 |
| **Shell 命令黑名单** | ✅ 已实现 | 阻止 `rm -rf`、`format`、`shutdown` 等危险命令 |
| **工具注册机制** | ✅ 已实现 | 只有注册的工具可被调用 |

**理念**：给智能体解决问题的自由，但在明确的边界内。

---

## 核心组件

### 1. 能力自扩展：内置工具 + MCP 配置 + 技能创建

FinchBot 提供三层能力扩展机制，让智能体遇到能力边界时可以自主扩展。

#### 内置工具

|        类别        | 工具              | 功能                        |
| :----------------: | :---------------- | :-------------------------- |
| **文件操作** | `read_file`     | 读取本地文件                |
|                    | `write_file`    | 写入本地文件                |
|                    | `edit_file`     | 编辑文件内容                |
|                    | `list_dir`      | 列出目录内容                |
| **网络能力** | `web_search`    | 联网搜索 (Tavily/Brave/DDG) |
|                    | `web_extract`   | 网页内容提取                |
| **记忆管理** | `remember`      | 主动存储记忆                |
|                    | `recall`        | 检索记忆                    |
|                    | `forget`        | 删除/归档记忆               |
| **系统控制** | `exec`          | 安全执行 Shell 命令         |
|                    | `session_title` | 管理会话标题                |
| **配置管理** | `configure_mcp` | 动态配置 MCP 服务器（支持启用/禁用/添加/更新/删除/列出） |
|                    | `refresh_capabilities` | 刷新能力描述文件   |
|                    | `get_capabilities` | 获取当前能力描述        |
|                    | `get_mcp_config_path` | 获取 MCP 配置路径    |

#### 网页搜索：三引擎降级设计

```mermaid
flowchart TD
    classDef check fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef engine fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef fallback fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;

    Start[网页搜索请求]:::check
    
    Check1{TAVILY_API_KEY<br/>已设置?}:::check
    Tavily[Tavily<br/>质量最佳<br/>AI 优化]:::engine
    
    Check2{BRAVE_API_KEY<br/>已设置?}:::check
    Brave[Brave Search<br/>隐私友好<br/>免费额度大]:::engine
        
    DDG[DuckDuckGo<br/>零配置<br/>始终可用]:::fallback

    Start --> Check1
    Check1 -->|是| Tavily
    Check1 -->|否| Check2
    Check2 -->|是| Brave
    Check2 -->|否| DDG
```

| 优先级 |          引擎          | API Key | 特点                             |
| :----: | :--------------------: | :-----: | :------------------------------- |
|   1   |    **Tavily**    |  需要  | 质量最佳，专为 AI 优化，深度搜索 |
|   2   | **Brave Search** |  需要  | 免费额度大，隐私友好             |
|   3   |  **DuckDuckGo**  |  无需  | 始终可用，零配置                 |

**工作原理**：

1. 如果设置了 `TAVILY_API_KEY` → 使用 Tavily（质量最佳）
2. 否则如果设置了 `BRAVE_API_KEY` → 使用 Brave Search
3. 否则 → 使用 DuckDuckGo（无需 API Key，始终可用）

这个设计确保**即使没有任何 API Key 配置，网页搜索也能开箱即用**！

#### MCP 配置

智能体可通过 `configure_mcp` 工具自主管理 MCP 服务器：

| 操作 | 说明 |
| :--- | :--- |
| `add` | 添加新 MCP 服务器 |
| `update` | 更新现有服务器配置 |
| `remove` | 删除 MCP 服务器 |
| `enable` | 启用已禁用的 MCP 服务器 |
| `disable` | 暂时禁用 MCP 服务器 |
| `list` | 列出所有已配置的服务器 |

**动态提示词更新**：

当 MCP 配置变更时，Agent 可通过 `refresh_capabilities` 刷新能力描述，确保系统提示词始终反映当前能力。

```mermaid
flowchart LR
    classDef config fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef system fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef prompt fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;

    MCP[MCP 配置<br/>configure_mcp]:::config --> Refresh[refresh_capabilities]:::system --> Builder[CapabilitiesBuilder<br/>重新生成]:::system --> Write[CAPABILITIES.md]:::prompt --> Load[下次对话<br/>自动加载]:::prompt
```

#### 技能创建

FinchBot 内置 **skill-creator** 技能，智能体可自主创建新技能：

```
用户: 帮我创建一个翻译技能，可以把中文翻译成英文

Agent: 好的，我来为你创建翻译技能...
       [调用 skill-creator 技能]
       ✅ 已创建 skills/translator/SKILL.md
       现在你可以直接使用翻译功能了！
```

无需手动创建文件、无需编写代码，**一句话就能扩展 Agent 能力**！

#### 技能文件结构

```
skills/
├── skill-creator/        # 技能创建器（内置）- 开箱即用的核心
│   └── SKILL.md
├── summarize/            # 智能总结（内置）
│   └── SKILL.md
├── weather/              # 天气查询（内置）
│   └── SKILL.md
└── my-custom-skill/      # Agent 自动创建或用户自定义
    └── SKILL.md
```

#### 核心设计亮点

|           特性           | 说明                              |
| :----------------------: | :-------------------------------- |
| **Agent 自动创建** | 告诉 Agent 需求，自动生成技能文件 |
|   **双层技能源**   | 工作区技能优先，内置技能兜底      |
|    **依赖检查**    | 自动检查 CLI 工具和环境变量       |
|  **缓存失效检测**  | 基于文件修改时间，智能缓存        |
|   **渐进式加载**   | 常驻技能优先，按需加载其他        |

### 2. 任务自调度：后台任务 + 定时任务

#### 后台任务系统

FinchBot 实现了**四工具模式**用于异步任务执行：

| 工具 | 功能 | 智能体自主性 |
| :--- | :--- | :--- |
| `start_background_task` | 启动后台任务 | 智能体自主判断是否需要后台执行 |
| `check_task_status` | 检查任务状态 | 智能体自主决定何时检查 |
| `get_task_result` | 获取任务结果 | 智能体自主决定何时获取结果 |
| `cancel_task` | 取消任务 | 智能体自主决定是否取消 |

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as 智能体
    participant BG as 后台任务系统
    participant S as 子智能体

    U->>A: 执行长任务
    A->>BG: start_background_task
    BG->>S: 创建独立智能体
    BG-->>A: 返回 job_id
    A-->>U: 任务已启动 (ID: xxx)
    
    Note over U,A: 用户继续对话...
    
    U->>A: 其他问题
    A-->>U: 正常回复
    
    U->>A: 任务进度？
    A->>BG: check_task_status
    BG-->>A: running
    A-->>U: 仍在执行...
    
    S-->>BG: 任务完成
    U->>A: 获取结果
    A->>BG: get_task_result
    BG-->>A: 返回结果
    A-->>U: 展示任务结果
```

#### 定时任务系统

支持 **Cron 表达式**的定时任务：

| 表达式 | 说明 |
| :--- | :--- |
| `0 9 * * *` | 每天上午 9:00 |
| `0 */2 * * *` | 每 2 小时 |
| `30 18 * * 1-5` | 工作日下午 6:30 |
| `0 0 1 * *` | 每月 1 日午夜 |

**交互式 CLI 管理**：

| 按键 | 操作 |
| :---: | :--- |
| ↑ / ↓ | 浏览任务列表 |
| Enter | 查看任务详情 |
| n | 创建新任务 |
| d | 删除选中任务 |
| e | 启用/禁用任务 |
| r | 立即执行 |
| q | 退出管理 |

#### 会话标题：智能命名，开箱即用

`session_title` 工具体现了 FinchBot 的开箱即用理念：

|       操作方式       | 说明                                   | 示例                   |
| :------------------: | :------------------------------------- | :--------------------- |
|  **自动生成**  | 对话 2-3 轮后，AI 自动根据内容生成标题 | "Python 异步编程讨论"  |
| **Agent 修改** | 告诉 Agent "把会话标题改成 XXX"        | Agent 调用工具自动修改 |
| **手动重命名** | 在会话管理器中按 `r` 键重命名        | 用户手动输入新标题     |

这个设计让用户**无需关心技术细节**，无论是自动还是手动，都能轻松管理会话。

### 3. 记忆自管理：Agentic RAG + 加权 RRF 混合检索

FinchBot 实现了先进的**双层记忆架构**，彻底解决了 LLM 上下文窗口限制和长期记忆遗忘问题。

#### 为什么是 Agentic RAG？

|      对比维度      | 传统 RAG     | Agentic RAG (FinchBot)      |
| :----------------: | :----------- | :-------------------------- |
| **检索触发** | 固定流程     | Agent 自主决策              |
| **检索策略** | 单一向量检索 | 混合检索 + 权重动态调整     |
| **记忆管理** | 被动存储     | 主动 remember/recall/forget |
| **分类能力** | 无           | 自动分类 + 重要性评分       |
| **更新机制** | 全量重建     | 增量同步                    |

#### 双层存储架构

```mermaid
flowchart TB
    classDef businessLayer fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef serviceLayer fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef storageLayer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    MM[MemoryManager<br/>remember/recall/forget]:::businessLayer

    RS[RetrievalService<br/>混合检索 + RRF]:::serviceLayer
    CS[ClassificationService<br/>自动分类]:::serviceLayer
    IS[ImportanceScorer<br/>重要性评分]:::serviceLayer
    ES[EmbeddingService<br/>FastEmbed 本地]:::serviceLayer

    SQLite[(SQLiteStore<br/>真相源<br/>精确查询)]:::storageLayer
    Vector[(VectorStore<br/>ChromaDB<br/>语义检索)]:::storageLayer
    DS[DataSyncManager<br/>增量同步]:::storageLayer

    MM --> RS & CS & IS
    RS --> SQLite & Vector
    CS --> SQLite
    IS --> SQLite
    ES --> Vector
    
    SQLite <--> DS <--> Vector
```

#### 混合检索策略

FinchBot 采用**加权 RRF (Weighted Reciprocal Rank Fusion)** 策略：

```python
class QueryType(StrEnum):
    """查询类型，决定检索权重"""
    KEYWORD_ONLY = "keyword_only"      # 纯关键词 (1.0/0.0)
    SEMANTIC_ONLY = "semantic_only"    # 纯语义 (0.0/1.0)
    FACTUAL = "factual"                # 事实型 (0.8/0.2)
    CONCEPTUAL = "conceptual"          # 概念型 (0.2/0.8)
    COMPLEX = "complex"                # 复杂型 (0.5/0.5)
    AMBIGUOUS = "ambiguous"            # 歧义型 (0.3/0.7)
```

### 4. 行为自进化：动态提示词系统

FinchBot 的提示词系统采用**文件系统 + 模块化组装**的设计。

#### Bootstrap 文件系统

```
~/.finchbot/
├── config.json              # 主配置文件
└── workspace/
    ├── bootstrap/           # Bootstrap 文件目录
    │   ├── SYSTEM.md        # 角色设定
    │   ├── MEMORY_GUIDE.md  # 记忆使用指南
    │   ├── SOUL.md          # 灵魂设定（性格特征）
    │   └── AGENT_CONFIG.md  # Agent 配置
    ├── config/              # 配置目录
    │   └── mcp.json         # MCP 服务器配置
    ├── generated/           # 自动生成文件
    │   ├── TOOLS.md         # 工具文档
    │   └── CAPABILITIES.md  # 能力信息
    ├── skills/              # 自定义技能
    ├── memory/              # 记忆存储
    └── sessions/            # 会话数据
```

#### 提示词加载流程

```mermaid
flowchart TD
    classDef startEnd fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c;
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef file fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    A([Agent 启动]):::startEnd --> B[加载 Bootstrap 文件]:::process
    
    B --> C[bootstrap/SYSTEM.md]:::file
    B --> D[bootstrap/MEMORY_GUIDE.md]:::file
    B --> E[bootstrap/SOUL.md]:::file
    B --> F[bootstrap/AGENT_CONFIG.md]:::file

    C --> G[组装提示词]:::process
    D --> G
    E --> G
    F --> G

    G --> H[加载常驻技能]:::process
    H --> I[构建技能摘要 XML]:::process
    I --> J[生成工具文档 TOOLS.md]:::process
    J --> K[生成能力文档 CAPABILITIES.md]:::process
    K --> L[注入运行时信息]:::process
    L --> M[完整系统提示]:::output

    M --> N([发送给 LLM]):::startEnd
```

#### 热加载机制

- **用户可定制**：通过 Bootstrap 文件系统自定义 Agent 行为
- **Agent 可调整**：智能体可根据交互反馈优化自身提示词
- **立即生效**：修改提示词后下次对话自动加载，无需重启

### 5. 通道系统：多平台消息支持

FinchBot 集成 [LangBot](https://github.com/langbot-app/LangBot) 实现生产级多平台消息支持。

**为什么选择 LangBot？**
- 15k+ GitHub Stars，活跃维护
- 支持 12+ 平台：QQ、微信、企业微信、飞书、钉钉、Discord、Telegram、Slack、LINE、KOOK、Satori
- 内置 WebUI，可视化配置
- 插件生态，支持 MCP 等扩展

```mermaid
flowchart LR
    classDef bus fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef manager fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef channel fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    FinchBot[FinchBot<br/>Agent 核心]:::bus <--> LangBot[LangBot<br/>平台层]:::manager

    subgraph Platforms [支持平台]
        direction LR
        QQ[QQ]:::channel
        WeChat[微信]:::channel
        Feishu[飞书]:::channel
        DingTalk[钉钉]:::channel
        Discord[Discord]:::channel
        Telegram[Telegram]:::channel
        Slack[Slack]:::channel
    end

    LangBot <--> Platforms
```

#### LangBot 快速开始

```bash
# 安装 LangBot
uvx langbot

# 访问 WebUI http://localhost:5300
# 配置你的平台并连接到 FinchBot
```

更多详情请参阅 [LangBot 文档](https://docs.langbot.app)。

### 6. LangChain 1.2 架构实践

FinchBot 基于 **LangChain v1.2** 和 **LangGraph v1.0** 构建，采用最新的 Agent 架构。

```python
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

def create_finch_agent(
    model: BaseChatModel,
    workspace: Path,
    tools: Sequence[BaseTool] | None = None,
    use_persistent: bool = True,
) -> tuple[CompiledStateGraph, SqliteSaver | MemorySaver]:

    # 1. 初始化检查点（持久化状态）
    if use_persistent:
        checkpointer = SqliteSaver.from_conn_string(str(db_path))
    else:
        checkpointer = MemorySaver()

    # 2. 构建系统提示
    system_prompt = build_system_prompt(workspace)

    # 3. 创建 Agent（使用 LangChain 官方 API）
    agent = create_agent(
        model=model,
        tools=list(tools) if tools else None,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )

    return agent, checkpointer
```

#### 支持的 LLM 提供商

|  提供商  | 模型                        | 特点             |
| :-------: | :-------------------------- | :--------------- |
|  OpenAI  | GPT-5, GPT-5.2, O3-mini     | 综合能力最强     |
| Anthropic | Claude Sonnet 4.5, Opus 4.6 | 安全性高，长文本 |
| DeepSeek | DeepSeek Chat, Reasoner     | 国产，性价比高   |
|  Gemini  | Gemini 2.5 Flash            | Google 最新      |
|   Groq   | Llama 4 Scout/Maverick      | 极速推理         |
| Moonshot | Kimi K1.5/K2.5              | 长文本，国产     |

---

## 快速开始

### 前置要求

|   项目   | 要求                    |
| :------: | :---------------------- |
| 操作系统 | Windows / Linux / macOS |
|  Python  | 3.13+                   |
| 包管理器 | uv (推荐)               |

### 安装步骤

```bash
# 克隆仓库（二选一）
# Gitee（国内推荐）
git clone https://gitee.com/xt765/finchbot.git
# 或 GitHub
git clone https://github.com/xt765/finchbot.git

cd finchbot

# 安装依赖
uv sync
```

> **注意**：嵌入模型（约 95MB）会在首次运行时（如运行 `finchbot chat`）自动下载到本地。无需手动干预。

<details>
<summary>开发环境安装</summary>

如需参与开发，安装开发依赖：

```bash
uv sync --extra dev
```

包含：pytest、ruff、basedpyright

</details>

### 最佳实践：四步上手

```bash
# 第一步：配置 API 密钥和默认模型
uv run finchbot config

# 第二步：管理你的会话
uv run finchbot sessions

# 第三步：开始对话
uv run finchbot chat

# 第四步：管理定时任务
uv run finchbot cron
```

就这么简单！这四个命令覆盖了完整的工作流程：

- `finchbot config` — 交互式配置 LLM 提供商、API 密钥和设置
- `finchbot sessions` — 全屏会话管理器，创建、重命名、删除会话
- `finchbot chat` — 开始或继续交互式对话
- `finchbot cron` — 交互式定时任务管理器，支持键盘导航

### Docker 部署

FinchBot 提供官方 Docker 支持，一键部署：

```bash
# 克隆仓库
git clone https://gitee.com/xt765/finchbot.git
cd finchbot

# 创建 .env 文件配置 API 密钥
cp .env.example .env
# 编辑 .env 填入你的 API 密钥

# 构建并运行
docker-compose up -d

# 访问 Web 界面
# http://localhost:8000
```

| 特性 | 说明 |
| :--: | :--- |
| **一键部署** | `docker-compose up -d` |
| **持久化存储** | 通过卷持久化工作区和模型缓存 |
| **健康检查** | 内置容器健康监控 |
| **多架构支持** | 支持 x86_64 和 ARM64 |

### 备选方案：环境变量

```bash
# 或直接设置环境变量
export OPENAI_API_KEY="your-api-key"
uv run finchbot chat
```

### 日志级别控制

```bash
# 默认：显示 WARNING 及以上日志
finchbot chat

# 显示 INFO 及以上日志
finchbot -v chat

# 显示 DEBUG 及以上日志（调试模式）
finchbot -vv chat
```

### 可选：下载本地嵌入模型

```bash
# 用于记忆系统的语义搜索（可选但推荐）
uv run finchbot models download
```

### 创建自定义技能

```bash
# 创建技能目录
mkdir -p ~/.finchbot/workspace/skills/my-skill

# 创建技能文件
cat > ~/.finchbot/workspace/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: 我的自定义技能
metadata:
  finchbot:
    emoji: ✨
    always: false
---

# 我的自定义技能

当用户请求 XXX 时，我应该...
EOF
```

---

## 技术栈

|    层级    | 技术              |  版本  |
| :--------: | :---------------- | :-----: |
|  基础语言  | Python            |  3.13+  |
| Agent 框架 | LangChain         | 1.2.10+ |
|  状态管理  | LangGraph         | 1.0.8+ |
|  数据验证  | Pydantic          |   v2   |
|  向量存储  | ChromaDB          | 0.5.0+ |
|  本地嵌入  | FastEmbed         | 0.4.0+ |
|  搜索增强  | BM25              | 0.2.2+ |
|  CLI 框架  | Typer             | 0.23.0+ |
|   富文本   | Rich              | 14.3.0+ |
|    日志    | Loguru            | 0.7.3+ |
|  配置管理  | Pydantic Settings | 2.12.0+ |
| Web 后端  | FastAPI           | 0.115.0+ |
| Web 前端  | React + Vite      | Latest  |

---

## 扩展指南

### 添加新工具

继承 `FinchTool` 基类，实现 `_run()` 方法，然后注册到 `ToolRegistry`。

### 添加 MCP 工具

在 `finchbot config` 中配置 MCP 服务器，或直接编辑配置文件。MCP 工具通过 `langchain-mcp-adapters` 自动加载。

### 添加新技能

在 `~/.finchbot/workspace/skills/{skill-name}/` 下创建 `SKILL.md` 文件。

### 添加新的 LLM 提供商

在 `providers/factory.py` 中添加新的 Provider 类。

### 添加新语言

在 `i18n/locales/` 下添加新的 `.toml` 文件。

### 多平台消息支持

使用 [LangBot](https://github.com/langbot-app/LangBot) 实现多平台支持。详见 [LangBot 文档](https://docs.langbot.app)。

---

## 项目优势

| 能力自扩展 | 任务自调度 | 记忆自管理 | 行为自进化 |
|:---:|:---:|:---:|:---:|
| 内置工具 + MCP 配置 + 技能创建 | 后台任务 + 定时任务 | Agentic RAG + 加权 RRF | 动态提示词 + 热加载 |
| 智能体遇到能力边界时自主扩展 | 智能体自主设定后台/定时任务 | 智能体自主记忆、检索、遗忘 | 智能体和用户都可修改提示词 |

| 安全自主 | 隐私优先 | 生产级稳定 | 多平台支持 |
|:---:|:---:|:---:|:---:|
| 文件操作限制在 workspace | FastEmbed 本地生成向量 | 双重检查锁 + 自动重试 | 通过 LangBot 支持 12+ 平台 |
| 危险 Shell 命令被阻止 | 无需上传云端数据 | 超时控制机制 | QQ/微信/飞书/钉钉/Discord/Telegram/Slack |

---

## 文档

[使用指南](docs/zh-CN/guide/usage.md) • [API 文档](docs/zh-CN/api.md) • [配置指南](docs/zh-CN/config.md) • [扩展指南](docs/zh-CN/guide/extension.md) • [系统架构](docs/zh-CN/architecture.md) • [部署指南](docs/zh-CN/deployment.md) • [开发环境](docs/zh-CN/development.md) • [贡献指南](docs/zh-CN/contributing.md)

---

## 贡献

欢迎提交 Issue 和 Pull Request。请阅读 [贡献指南](docs/zh-CN/contributing.md) 了解更多信息。

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## Star History

如果这个项目对你有帮助，请给个 Star ⭐️

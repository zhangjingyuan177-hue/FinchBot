# FinchBot — A Lightweight, Flexible, Self-Extending AI Agent Framework

<p align="center">
  <img src="docs/image/image.png" alt="FinchBot Logo" width="600">
</p>

<p align="center">
  <em>Built on LangChain v1.2 & LangGraph v1.0<br>
  with persistent memory, dynamic prompts, autonomous capability extension</em>
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
  <img src="https://img.shields.io/badge/Gitee-Officially_Recommended-red?style=flat-square&logo=gitee&logoColor=white" alt="Gitee Recommended">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Ruff-Formatter-orange?style=flat-square&logo=ruff" alt="Ruff">
  <img src="https://img.shields.io/badge/Basedpyright-TypeCheck-purple?style=flat-square&logo=python" alt="Basedpyright">
  <img src="https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square&logo=open-source-initiative" alt="License">
</p>

**FinchBot** is an AI Agent framework that empowers agents with true autonomy, built on **LangChain v1.2** and **LangGraph v1.0**. With fully async architecture, agents gain the ability to self-decide, self-extend, and self-evolve:

1. **Capability Self-Extension** — Agent can use built-in tools to configure MCP and create skills when hitting capability boundaries
2. **Task Self-Scheduling** — Agent can self-set background tasks and scheduled execution without blocking conversations
3. **Memory Self-Management** — Agent can self-remember, self-retrieve, and self-forget with Agentic RAG + Weighted RRF hybrid retrieval
4. **Behavior Self-Evolution** — Both Agent and users can self-modify prompts, continuously iterating and optimizing behavior

---

## The Capability Boundary Problem

| What User Asks | Traditional AI Response | FinchBot Response |
|:---|:---|:---|
| "Analyze this database" | "I don't have database tools" | Self-configures SQLite MCP, then analyzes |
| "Learn to do X" | "Wait for developer to add feature" | Self-creates skill via skill-creator |
| "Monitor this for 24 hours" | "I can only respond when you ask" | Creates scheduled task, monitors autonomously |
| "Process this large file" | Blocks conversation, user waits | Runs in background, user continues |
| "Remember my preferences" | "I'll forget next conversation" | Persistent memory with Agentic RAG + Weighted RRF |
| "Adjust your behavior" | "Prompts are fixed" | Dynamically modifies prompts, hot reload |

---

## System Architecture

**Core Philosophy**: FinchBot agents don't just respond — they self-execute, self-plan, and self-extend.

### Autonomy Pyramid

```mermaid
flowchart TB
    subgraph L4["Extension Layer - Self-Extend Capabilities"]
        direction LR
        E1["MCP Auto-Config"]
        E2["Skill Creation"]
        E3["Dynamic Loading"]
    end

    subgraph L3["Planning Layer - Self-Create Plans"]
        direction LR
        P1["Cron Tasks"]
        P2["Heartbeat Monitor"]
        P3["Auto Trigger"]
    end

    subgraph L2["Execution Layer - Self-Execute Tasks"]
        direction LR
        X1["Background Tasks"]
        X2["Async Processing"]
        X3["Non-Blocking"]
    end

    subgraph L1["Response Layer - Respond to Requests"]
        direction LR
        R1["Dialog System"]
        R2["Tool Calls"]
        R3["Context Memory"]
    end

    L4 --> L3 --> L2 --> L1

    style L1 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
    style L2 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    style L3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c
    style L4 fill:#fff9c4,stroke:#f9a825,stroke-width:2px,color:#f57f17
```

| Layer | Capability | Implementation | User Value |
|:---:|:---|:---|:---|
| **Response Layer** | Respond to user requests | Dialog system + Tool calls | Basic interaction |
| **Execution Layer** | Self-execute tasks | Background task system | Non-blocking dialog |
| **Planning Layer** | Self-create plans | Scheduled tasks + Heartbeat | Automated execution |
| **Extension Layer** | Self-extend capabilities | MCP config + Skill creation | Infinite extension |

### Overall Architecture

```mermaid
graph TB
    classDef uiLayer fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c;
    classDef coreLayer fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef infraLayer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    subgraph UI [User Interaction Layer]
        CLI[CLI Interface]:::uiLayer
        Channels[Multi-platform Channels<br/>Discord/DingTalk/Feishu/WeChat/Email]:::uiLayer
    end

    subgraph Core [Agent Core]
        Agent[LangGraph Agent<br/>Decision Engine]:::coreLayer
        Context[ContextBuilder<br/>Context Building]:::coreLayer
        Tools[ToolRegistry<br/>15 Built-in Tools + MCP]:::coreLayer
        Memory[MemoryManager<br/>Dual-layer Memory]:::coreLayer
    end

    subgraph Infra [Infrastructure Layer]
        Storage[Dual-layer Storage<br/>SQLite + VectorStore]:::infraLayer
        LLM[LLM Providers<br/>OpenAI/Anthropic/DeepSeek]:::infraLayer
    end

    CLI --> Agent
    Channels --> Agent

    Agent --> Context
    Agent <--> Tools
    Agent <--> Memory

    Memory --> Storage
    Agent --> LLM
```

### Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Channel
    participant B as MessageBus
    participant F as AgentFactory
    participant A as Agent
    participant M as MemoryManager
    participant T as Tools
    participant L as LLM

    U->>C: Send Message
    C->>B: InboundMessage
    B->>F: Get/Create Agent
    F->>A: Return Compiled Agent
  
    Note over A: Build Context
    A->>M: Recall Relevant Memories
    M-->>A: Return Context
  
    A->>L: Send Request
    L-->>A: Stream Response
  
    alt Tool Call Needed
        A->>T: Execute Tool
        T-->>A: Return Result
        A->>L: Continue with Result
        L-->>A: Final Response
    end
  
    A->>M: Store New Memories
    A->>B: OutboundMessage
    B->>C: Route to Channel
    C->>U: Display Response
```

### Safety Mechanisms

**Agent autonomy doesn't mean agent anarchy.** FinchBot implements multiple safety layers:

| Safety Mechanism | Status | What It Does |
|:---|:---:|:---|
| **Path Restrictions** | ✅ Implemented | File operations limited to workspace directory |
| **Shell Command Blacklist** | ✅ Implemented | Blocks dangerous commands like `rm -rf`, `format`, `shutdown` |
| **Tool Registration** | ✅ Implemented | Only registered tools can be executed |

**Philosophy**: Give agents the freedom to solve problems, but within well-defined boundaries.

---

## Core Components

### 1. Capability Self-Extension: Built-in Tools + MCP Config + Skill Creation

FinchBot provides a three-layer capability extension mechanism, allowing agents to self-extend when hitting capability boundaries.

#### Built-in Tools

|      Category      | Tool              | Function                      |
| :----------------: | :---------------- | :---------------------------- |
| **File Ops** | `read_file`     | Read local files              |
|                    | `write_file`    | Write local files             |
|                    | `edit_file`     | Edit file content             |
|                    | `list_dir`      | List directory contents       |
| **Network** | `web_search`    | Web search (Tavily/Brave/DDG) |
|                    | `web_extract`   | Web content extraction        |
|  **Memory**  | `remember`      | Proactively store memories    |
|                    | `recall`        | Retrieve memories             |
|                    | `forget`        | Delete/archive memories       |
|  **System**  | `exec`          | Secure shell execution        |
|                    | `session_title` | Manage session titles         |
|  **Configuration**  | `configure_mcp` | Dynamically configure MCP servers (enable/disable/add/update/remove/list) |
|                    | `refresh_capabilities` | Refresh capabilities file |
|                    | `get_capabilities` | Get current capabilities  |
|                    | `get_mcp_config_path` | Get MCP config path   |

#### Web Search: Three-Engine Fallback Design

```mermaid
flowchart TD
    classDef check fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef engine fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef fallback fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;

    Start[Web Search Request]:::check
    
    Check1{TAVILY_API_KEY<br/>Set?}:::check
    Tavily[Tavily<br/>Best Quality<br/>AI-Optimized]:::engine
    
    Check2{BRAVE_API_KEY<br/>Set?}:::check
    Brave[Brave Search<br/>Privacy Friendly<br/>Large Free Tier]:::engine
    
    DDG[DuckDuckGo<br/>Zero Config<br/>Always Available]:::fallback

    Start --> Check1
    Check1 -->|Yes| Tavily
    Check1 -->|No| Check2
    Check2 -->|Yes| Brave
    Check2 -->|No| DDG
```

| Priority |         Engine         |   API Key   | Features                                |
| :------: | :--------------------: | :----------: | :-------------------------------------- |
|    1    |    **Tavily**    |   Required   | Best quality, AI-optimized, deep search |
|    2    | **Brave Search** |   Required   | Large free tier, privacy-friendly       |
|    3    |  **DuckDuckGo**  | Not required | Always available, zero config           |

**How it works**:

1. If `TAVILY_API_KEY` is set → Use Tavily (best quality)
2. Else if `BRAVE_API_KEY` is set → Use Brave Search
3. Else → Use DuckDuckGo (no API key needed, always works)

This design ensures **web search works out of the box** even without any API key configuration!

#### MCP Configuration

Agents can autonomously manage MCP servers through the `configure_mcp` tool:

| Operation | Description |
| :--- | :--- |
| `add` | Add new MCP server |
| `update` | Update existing server configuration |
| `remove` | Delete MCP server |
| `enable` | Enable disabled MCP server |
| `disable` | Temporarily disable MCP server |
| `list` | List all configured servers |

**Dynamic Prompt Updates**:

When MCP configuration changes, the Agent can refresh capability descriptions through `refresh_capabilities`, ensuring the system prompt always reflects current capabilities.

```mermaid
flowchart LR
    classDef config fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef system fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef prompt fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;

    MCP[MCP Config<br/>configure_mcp]:::config --> Refresh[refresh_capabilities]:::system --> Builder[CapabilitiesBuilder<br/>Regenerate]:::system --> Write[CAPABILITIES.md]:::prompt --> Load[Next Session<br/>Auto-Load]:::prompt
```

#### Skill Creation

FinchBot includes a built-in **skill-creator** skill, allowing agents to autonomously create new skills:

```
User: Help me create a translation skill that can translate Chinese to English

Agent: Okay, I'll create a translation skill for you...
       [Invokes skill-creator skill]
       ✅ Created skills/translator/SKILL.md
       You can now use the translation feature directly!
```

No manual file creation, no coding—**extend Agent capabilities with just one sentence**!

#### Skill File Structure

```
skills/
├── skill-creator/        # Skill creator (Built-in) - Core of out-of-the-box
│   └── SKILL.md
├── summarize/            # Intelligent summarization (Built-in)
│   └── SKILL.md
├── weather/              # Weather query (Built-in)
│   └── SKILL.md
└── my-custom-skill/      # Agent auto-created or user-defined
    └── SKILL.md
```

#### Core Design Highlights

|            Feature            | Description                                       |
| :---------------------------: | :------------------------------------------------ |
|  **Agent Auto-Create**  | Tell Agent your needs, auto-generates skill files |
|  **Dual Skill Source**  | Workspace skills first, built-in skills fallback  |
|  **Dependency Check**  | Auto-check CLI tools and environment variables    |
| **Cache Invalidation** | Smart caching based on file modification time     |
| **Progressive Loading** | Always-on skills first, others on demand          |

### 2. Task Self-Scheduling: Background Tasks + Scheduled Tasks

#### Background Task System

FinchBot implements a **four-tool pattern** for asynchronous task execution:

| Tool | Function | Agent Autonomy |
| :--- | :--- | :--- |
| `start_background_task` | Start background task | Agent self-determines if background execution needed |
| `check_task_status` | Check task status | Agent self-decides when to check |
| `get_task_result` | Get task result | Agent self-decides when to get result |
| `cancel_task` | Cancel task | Agent self-decides whether to cancel |

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant BG as Background Task System
    participant S as Subagent

    U->>A: Execute long task
    A->>BG: start_background_task
    BG->>S: Create independent Agent
    BG-->>A: Return job_id
    A-->>U: Task started (ID: xxx)
    
    Note over U,A: User continues dialog...
    
    U->>A: Other questions
    A-->>U: Normal response
    
    U->>A: Task progress?
    A->>BG: check_task_status
    BG-->>A: running
    A-->>U: Still executing...
    
    S-->>BG: Task complete
    U->>A: Get result
    A->>BG: get_task_result
    BG-->>A: Return result
    A-->>U: Task result display
```

#### Scheduled Task System

Support for **Cron expressions** in scheduled tasks:

| Expression | Description |
| :--- | :--- |
| `0 9 * * *` | Daily at 9:00 AM |
| `0 */2 * * *` | Every 2 hours |
| `30 18 * * 1-5` | Weekdays at 6:30 PM |
| `0 0 1 * *` | First day of month at midnight |

**Interactive CLI Management**:

| Key | Action |
| :---: | :--- |
| ↑ / ↓ | Navigate task list |
| Enter | View task details |
| n | Create new task |
| d | Delete selected task |
| e | Enable/disable task |
| r | Execute immediately |
| q | Quit management |

#### Session Title: Smart Naming, Out of the Box

The `session_title` tool embodies FinchBot's out-of-the-box philosophy:

|         Method         | Description                                                        | Example                                  |
| :---------------------: | :----------------------------------------------------------------- | :--------------------------------------- |
| **Auto Generate** | After 2-3 turns, AI automatically generates title based on content | "Python Async Programming Discussion"    |
| **Agent Modify** | Tell Agent "Change session title to XXX"                           | Agent calls tool to modify automatically |
| **Manual Rename** | Press `r` key in session manager to rename                       | User manually enters new title           |

This design lets users **manage sessions without technical details**—whether automatic or manual.

### 3. Memory Self-Management: Agentic RAG + Weighted RRF Hybrid Retrieval

FinchBot implements an advanced **dual-layer memory architecture** that solves LLM context window limits and long-term forgetting issues.

#### Why Agentic RAG?

|          Dimension          | Traditional RAG         | Agentic RAG (FinchBot)                       |
| :--------------------------: | :---------------------- | :------------------------------------------- |
| **Retrieval Trigger** | Fixed pipeline          | Agent autonomous decision                    |
| **Retrieval Strategy** | Single vector retrieval | Hybrid retrieval + dynamic weight adjustment |
| **Memory Management** | Passive storage         | Active remember/recall/forget                |
|   **Classification**   | None                    | Auto-classification + importance scoring     |
|  **Update Mechanism**  | Full rebuild            | Incremental sync                             |

#### Dual-Layer Storage Architecture

```mermaid
flowchart TB
    classDef businessLayer fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef serviceLayer fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef storageLayer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    MM[MemoryManager<br/>remember/recall/forget]:::businessLayer

    RS[RetrievalService<br/>Hybrid Retrieval + RRF]:::serviceLayer
    CS[ClassificationService<br/>Auto Classification]:::serviceLayer
    IS[ImportanceScorer<br/>Importance Scoring]:::serviceLayer
    ES[EmbeddingService<br/>FastEmbed Local]:::serviceLayer

    SQLite[(SQLiteStore<br/>Source of Truth<br/>Precise Query)]:::storageLayer
    Vector[(VectorStore<br/>ChromaDB<br/>Semantic Search)]:::storageLayer
    DS[DataSyncManager<br/>Incremental Sync]:::storageLayer

    MM --> RS & CS & IS
    RS --> SQLite & Vector
    CS --> SQLite
    IS --> SQLite
    ES --> Vector
    
    SQLite <--> DS <--> Vector
```

#### Hybrid Retrieval Strategy

FinchBot uses **Weighted RRF (Weighted Reciprocal Rank Fusion)** strategy:

```python
class QueryType(StrEnum):
    """Query type determines retrieval weights"""
    KEYWORD_ONLY = "keyword_only"      # Pure keyword (1.0/0.0)
    SEMANTIC_ONLY = "semantic_only"    # Pure semantic (0.0/1.0)
    FACTUAL = "factual"                # Factual (0.8/0.2)
    CONCEPTUAL = "conceptual"          # Conceptual (0.2/0.8)
    COMPLEX = "complex"                # Complex (0.5/0.5)
    AMBIGUOUS = "ambiguous"            # Ambiguous (0.3/0.7)
```

### 4. Behavior Self-Evolution: Dynamic Prompt System

FinchBot's prompt system uses **file system + modular assembly** design.

#### Bootstrap File System

```
~/.finchbot/
├── config.json              # Main configuration file
└── workspace/
    ├── bootstrap/           # Bootstrap files directory
    │   ├── SYSTEM.md        # Role definition
    │   ├── MEMORY_GUIDE.md  # Memory usage guide
    │   ├── SOUL.md          # Personality settings
    │   └── AGENT_CONFIG.md  # Agent configuration
    ├── config/              # Configuration directory
    │   └── mcp.json         # MCP server configuration
    ├── generated/           # Auto-generated files
    │   ├── TOOLS.md         # Tool documentation
    │   └── CAPABILITIES.md  # Capabilities info
    ├── skills/              # Custom skills
    ├── memory/              # Memory storage
    └── sessions/            # Session data
```

#### Prompt Loading Flow

```mermaid
flowchart TD
    classDef startEnd fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c;
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef file fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    A([Agent Startup]):::startEnd --> B[Load Bootstrap Files]:::process
    
    B --> C[bootstrap/SYSTEM.md]:::file
    B --> D[bootstrap/MEMORY_GUIDE.md]:::file
    B --> E[bootstrap/SOUL.md]:::file
    B --> F[bootstrap/AGENT_CONFIG.md]:::file

    C --> G[Assemble Prompt]:::process
    D --> G
    E --> G
    F --> G

    G --> H[Load Always-on Skills]:::process
    H --> I[Build Skill Summary XML]:::process
    I --> J[Generate Tool Docs TOOLS.md]:::process
    J --> K[Generate Capabilities CAPABILITIES.md]:::process
    K --> L[Inject Runtime Info]:::process
    L --> M[Complete System Prompt]:::output

    M --> N([Send to LLM]):::startEnd
```

#### Hot Reload Mechanism

- **User Customizable**: Customize Agent behavior through Bootstrap file system
- **Agent Adjustable**: Agent can optimize its own prompts based on interaction feedback
- **Immediate Effect**: Modified prompts auto-load on next conversation, no restart needed

### 5. Channel System: Multi-Platform Messaging

FinchBot integrates with [LangBot](https://github.com/langbot-app/LangBot) for production-grade multi-platform messaging.

**Why LangBot?**
- 15k+ GitHub Stars, actively maintained
- Supports 12+ platforms: QQ, WeChat, WeCom, Feishu, DingTalk, Discord, Telegram, Slack, LINE, KOOK, Satori
- Built-in WebUI for easy configuration
- Plugin ecosystem with MCP support

```mermaid
flowchart LR
    classDef bus fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef manager fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef channel fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    FinchBot[FinchBot<br/>Agent Core]:::bus <--> LangBot[LangBot<br/>Platform Layer]:::manager

    subgraph Platforms [Supported Platforms]
        direction LR
        QQ[QQ]:::channel
        WeChat[WeChat]:::channel
        Feishu[Feishu]:::channel
        DingTalk[DingTalk]:::channel
        Discord[Discord]:::channel
        Telegram[Telegram]:::channel
        Slack[Slack]:::channel
    end

    LangBot <--> Platforms
```

#### Quick Start with LangBot

```bash
# Install LangBot
uvx langbot

# Access WebUI at http://localhost:5300
# Configure your platforms and connect to FinchBot
```

For more details, see [LangBot Documentation](https://docs.langbot.app).

### 6. LangChain v1.2 Architecture Practice

FinchBot is built on **LangChain v1.2** and **LangGraph v1.0**, using the latest Agent architecture.

```python
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

def create_finch_agent(
    model: BaseChatModel,
    workspace: Path,
    tools: Sequence[BaseTool] | None = None,
    use_persistent: bool = True,
) -> tuple[CompiledStateGraph, SqliteSaver | MemorySaver]:

    # 1. Initialize checkpoint (persistent state)
    if use_persistent:
        checkpointer = SqliteSaver.from_conn_string(str(db_path))
    else:
        checkpointer = MemorySaver()

    # 2. Build system prompt
    system_prompt = build_system_prompt(workspace)

    # 3. Create Agent (using LangChain official API)
    agent = create_agent(
        model=model,
        tools=list(tools) if tools else None,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )

    return agent, checkpointer
```

#### Supported LLM Providers

| Provider | Models                      | Features                  |
| :-------: | :-------------------------- | :------------------------ |
|  OpenAI  | GPT-5, GPT-5.2, O3-mini     | Best overall capability   |
| Anthropic | Claude Sonnet 4.5, Opus 4.6 | High safety, long context |
| DeepSeek | DeepSeek Chat, Reasoner     | Chinese, cost-effective   |
|  Gemini  | Gemini 2.5 Flash            | Google's latest           |
|   Groq   | Llama 4 Scout/Maverick      | Ultra-fast inference      |
| Moonshot | Kimi K1.5/K2.5              | Long context, Chinese     |

---

## Quick Start

### Prerequisites

|      Item      | Requirement             |
| :-------------: | :---------------------- |
|       OS       | Windows / Linux / macOS |
|     Python     | 3.13+                   |
| Package Manager | uv (Recommended)        |

### Installation

```bash
# Clone repository (choose one)
# Gitee (recommended for users in China)
git clone https://gitee.com/xt765/finchbot.git
# or GitHub
git clone https://github.com/xt765/finchbot.git

cd finchbot

# Install dependencies
uv sync
```

> **Note**: The embedding model (~95MB) will be automatically downloaded to the local cache when you run the application for the first time (e.g., `finchbot chat`). No manual intervention required.

<details>
<summary>Development Installation</summary>

For development, install with dev dependencies:

```bash
uv sync --extra dev
```

This includes: pytest, ruff, basedpyright

</details>

### Best Practice: Four Commands to Get Started

```bash
# Step 1: Configure API keys and default model
uv run finchbot config

# Step 2: Manage your sessions
uv run finchbot sessions

# Step 3: Start chatting
uv run finchbot chat

# Step 4: Manage scheduled tasks
uv run finchbot cron
```

That's it! These four commands cover the complete workflow:

- `finchbot config` — Interactive configuration for LLM providers, API keys, and settings
- `finchbot sessions` — Full-screen session manager for creating, renaming, deleting sessions
- `finchbot chat` — Start or continue an interactive conversation
- `finchbot cron` — Interactive scheduled task manager with keyboard navigation

### Docker Deployment

FinchBot provides official Docker support for easy deployment:

```bash
# Clone repository
git clone https://github.com/xt765/finchbot.git
cd finchbot

# Create .env file with your API keys
cp .env.example .env
# Edit .env and add your API keys

# Build and run
docker-compose up -d

# Access the Web interface
# http://localhost:8000
```

| Feature | Description |
| :-----: | :---------- |
| **One-command Deploy** | `docker-compose up -d` |
| **Persistent Storage** | Workspace and model cache via volumes |
| **Health Check** | Built-in container health monitoring |
| **Multi-arch Support** | Works on x86_64 and ARM64 |

### Alternative: Environment Variables

```bash
# Or set environment variables directly
export OPENAI_API_KEY="your-api-key"
uv run finchbot chat
```

### Log Level Control

```bash
# Default: Show WARNING and above logs
finchbot chat

# Show INFO and above logs
finchbot -v chat

# Show DEBUG and above logs (debug mode)
finchbot -vv chat
```

### Optional: Download Local Embedding Model

```bash
# For memory system semantic search (optional but recommended)
uv run finchbot models download
```

### Create Custom Skill

```bash
# Create skill directory
mkdir -p ~/.finchbot/workspace/skills/my-skill

# Create skill file
cat > ~/.finchbot/workspace/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: My custom skill
metadata:
  finchbot:
    emoji: ✨
    always: false
---

# My Custom Skill

When user requests XXX, I should...
EOF
```

---

## Tech Stack

|       Layer       | Technology        | Version |
| :----------------: | :---------------- | :------: |
|   Core Language   | Python            |  3.13+  |
|  Agent Framework  | LangChain         | 1.2.10+ |
|  State Management  | LangGraph         |  1.0.8+  |
|  Data Validation  | Pydantic          |    v2    |
|   Vector Storage   | ChromaDB          |  0.5.0+  |
|  Local Embedding  | FastEmbed         |  0.4.0+  |
| Search Enhancement | BM25              |  0.2.2+  |
|   CLI Framework   | Typer             | 0.23.0+ |
|     Rich Text     | Rich              | 14.3.0+ |
|      Logging      | Loguru            |  0.7.3+  |
|   Configuration   | Pydantic Settings | 2.12.0+ |
|    Web Backend    | FastAPI           | 0.115.0+ |
|    Web Frontend    | React + Vite      |  Latest  |

---

## Extension Guide

### Adding New Tools

Inherit `FinchTool` base class, implement `_run()` method, then register with `ToolRegistry`.

### Adding MCP Tools

Configure MCP servers in `finchbot config` or directly in the config file. MCP tools are automatically loaded via `langchain-mcp-adapters`.

### Adding New Skills

Create a `SKILL.md` file in `~/.finchbot/workspace/skills/{skill-name}/`.

### Adding New LLM Providers

Add a new Provider class in `providers/factory.py`.

### Adding New Languages

Add a new `.toml` file under `i18n/locales/`.

### Multi-Platform Messaging

Use [LangBot](https://github.com/langbot-app/LangBot) for multi-platform support. See the [LangBot Documentation](https://docs.langbot.app) for details.

---

## Key Advantages

| Capability Self-Extension | Task Self-Scheduling | Memory Self-Management | Behavior Self-Evolution |
|:---:|:---:|:---:|:---:|
| Built-in Tools + MCP Config + Skill Creation | Background Tasks + Scheduled Tasks | Agentic RAG + Weighted RRF | Dynamic Prompts + Hot Reload |
| Agent self-extends when hitting boundaries | Agent self-sets background/scheduled tasks | Agent self-remembers, retrieves, forgets | Both Agent and users can modify prompts |

| Safe Autonomy | Privacy First | Production Ready | Multi-Platform |
|:---:|:---:|:---:|:---:|
| File ops restricted to workspace | FastEmbed local vector generation | Double-checked locking + auto-retry | Via LangBot: 12+ platforms |
| Dangerous shell commands blocked | No cloud data upload | Timeout control mechanisms | QQ/WeChat/Feishu/DingTalk/Discord/Telegram/Slack |

---

## Documentation

[User Guide](docs/en-US/guide/usage.md) • [API Reference](docs/en-US/api.md) • [Configuration](docs/en-US/config.md) • [Extension Guide](docs/en-US/guide/extension.md) • [Architecture](docs/en-US/architecture.md) • [Deployment](docs/en-US/deployment.md) • [Development](docs/en-US/development.md) • [Contributing](docs/en-US/contributing.md)

---

## Contributing

Contributions are welcome! Please read the [Contributing Guide](docs/en-US/contributing.md) for more information.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Star History

If this project is helpful to you, please give it a Star ⭐️

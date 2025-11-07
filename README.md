# MemDocs - Persistent Memory for AI Projects

**Version:** 2.0.0
**Status:** Production Ready
**License:** Apache 2.0

---

## Overview

**MemDocs** (Memory Documentation) is a **git-native memory management system** that gives AI assistants persistent, project-specific memory. It generates structured, machine-readable documentation that lives in your repository—no cloud services, no recurring costs, just local/git-based storage that enhances AI context and team collaboration.

### The Problem MemDocs Solves

AI assistants like Claude have **no memory between sessions**. Every conversation starts from scratch, forcing you to repeatedly explain your codebase, architecture decisions, and project context.

MemDocs solves this by creating a **persistent memory layer** that:
- **Remembers your project** across sessions (via `.memdocs/` directory)
- **Shares memory with your team** (committed to git)
- **Costs nothing to store** (no vector databases, no embeddings API)
- **Works offline** (no cloud dependencies for retrieval)
- **Integrates with Empathy Framework** (Level 4 Anticipatory Intelligence)

---

## Key Features

### 🧠 Git-Native Memory
- All documentation stored in `.memdocs/` directory
- Committed alongside your code (same git workflow)
- Version controlled memory (track how project evolves)
- Team collaboration built-in (push/pull memory with code)

### 🎯 Smart Scoping
- **File-level** (default): Document individual files
- **Module-level**: Document entire directories
- **Repo-level**: Full codebase overview (use sparingly)
- **Auto-escalation**: Automatically increases scope for important changes

### 🤖 AI-Powered Summarization
- Uses Claude Sonnet 4.5 for intelligent summaries
- Extracts symbols, APIs, and architecture decisions
- Generates human-readable and machine-readable formats
- Token-efficient (only summarizes, doesn't embed)

### 🔗 Empathy Framework Integration
- Works seamlessly with [Empathy](https://github.com/Deep-Study-AI/empathy) framework
- Supports Level 4 Anticipatory Empathy workflows
- Bidirectional sync (MemDocs ↔ Empathy)
- Trust-building behaviors powered by persistent memory

### 🔒 Optional Privacy Guards
- PHI/PII detection and redaction (healthcare, finance)
- Configurable privacy modes: off, standard, strict
- HIPAA/GDPR-aware (optional, not required)

---

## Quick Start

### Installation

```bash
# From PyPI (when published)
pip install memdocs

# From source
git clone https://github.com/Deep-Study-AI/memdocs.git
cd memdocs
pip install -e .
```

### Basic Usage

```bash
# Initialize MemDocs in your project
cd your-project
memdocs init

# Document a single file (recommended)
memdocs review --path src/payments/charge.py

# Document a module
memdocs review --path src/payments/

# Full repository review (use sparingly)
memdocs review --repo . --force

# Search your project memory
memdocs search "payment processing"

# Show memory stats
memdocs stats
```

### Configuration

Create `.memdocs.yml` in your project root:

```yaml
version: 2

# Scope policy (controls memory granularity)
policies:
  default_scope: file          # file | module | repo
  max_files_without_force: 150

  # Auto-escalate for important changes
  escalate_on:
    - cross_module_changes      # Multi-module = bigger context needed
    - security_sensitive_paths  # auth/*, security/* = document thoroughly
    - public_api_signatures     # API changes = team needs to know

# Output configuration (git-committed memory)
outputs:
  docs_dir: .memdocs/docs       # Committed to git
  memory_dir: .memdocs/memory   # Committed to git
  formats:
    - json                      # index.json (machine-readable)
    - yaml                      # symbols.yaml (code map)
    - markdown                  # summary.md (human-readable)

# Privacy (optional, only enable if handling sensitive data)
privacy:
  phi_mode: "off"               # off | standard | strict
  pii_detection: false
  redaction_enabled: false

# AI configuration (Claude API)
ai:
  provider: anthropic           # anthropic | openai
  model: claude-sonnet-4-5-20250929  # Claude Sonnet 4.5 (latest)
  max_tokens: 8192
  temperature: 0.3              # Lower = more deterministic

# Exclude patterns (don't document these)
exclude:
  - node_modules/**
  - .venv/**
  - venv/**
  - __pycache__/**
  - "*.pyc"
  - .git/**
  - dist/**
  - build/**
  - "*.log"
  - "*.db"
```

---

## Use Cases

### 1. **Onboarding New Developers**
```bash
# New team member clones repo
git clone <your-repo>
cd your-repo

# MemDocs memory already there!
memdocs search "authentication flow"
memdocs search "database schema"
```

**Result**: Instant context about the project without asking teammates.

### 2. **AI Assistant Context**
```python
# In your AI workflow
from memdocs import MemDocs

mem = MemDocs(".")
context = mem.get_context_for_file("src/payments/charge.py")

# Pass to Claude
response = claude.messages.create(
    model="claude-sonnet-4-5-20250929",
    system=f"Project context:\n{context}",
    messages=[{"role": "user", "content": "Explain the charge flow"}]
)
```

**Result**: Claude remembers your project structure and decisions.

### 3. **Code Review Preparation**
```bash
# Before opening PR
memdocs review --path src/new-feature/ --on pr

# MemDocs generates:
# - Feature summary
# - API changes
# - Breaking changes
# - Migration notes
```

**Result**: Reviewers get structured context automatically.

### 4. **Empathy Framework Integration**
```python
from memdocs import MemDocs
from empathy import EmpathyAgent

# MemDocs provides persistent memory for Empathy agents
mem = MemDocs(".")
agent = EmpathyAgent(memory=mem)

# Agent can anticipate issues based on project history
predictions = agent.predict_issues(timeframe_days=90)
```

**Result**: Level 4 Anticipatory Empathy powered by project memory.

---

## Architecture

### Storage Structure

```
your-project/
├── .memdocs/
│   ├── docs/
│   │   ├── index.json          # Machine-readable index
│   │   ├── symbols.yaml        # Code symbols/API map
│   │   └── summary.md          # Human-readable summary
│   └── memory/
│       ├── graph.json          # Dependency graph
│       └── embeddings.json     # Optional: Semantic search
├── .memdocs.yml                # Configuration
└── src/
    └── ... your code ...
```

### How It Works

1. **Extract**: MemDocs uses tree-sitter to parse code (Python, JS, TS, Go, Rust, etc.)
2. **Analyze**: Identifies symbols, imports, APIs, architecture patterns
3. **Summarize**: Claude generates concise summaries with key insights
4. **Store**: Saves structured documentation in `.memdocs/` directory
5. **Retrieve**: Fast local search (no API calls, no embeddings)

### Token Efficiency

- **Summarization only**: Uses Claude to generate summaries (~1K tokens per file)
- **No embeddings**: Saves $$$ (no OpenAI embeddings API)
- **Local search**: Grep-based, instant, free
- **Optional embeddings**: Available if you need semantic search

---

## Integration with Empathy Framework

MemDocs and Empathy work together to create **Level 4 Anticipatory Intelligence**:

```python
from memdocs import MemDocs
from empathy import EmpathyAgent, Level4Framework

# MemDocs provides persistent memory
mem = MemDocs(".")

# Empathy uses memory for anticipatory behaviors
agent = EmpathyAgent(
    memory=mem,
    level=4,  # Anticipatory Empathy
    anticipation_window_days=90
)

# Example: Predict compliance issues before audit
compliance_agent = agent.create_compliance_agent(
    audit_type="joint_commission",
    hospital_id="hospital_123"
)

# Agent anticipates audit 90 days in advance
result = await compliance_agent.run()

# Result includes:
# - Predicted audit date
# - Current compliance gaps
# - Proactive action items
# - Documentation package (auto-generated)
```

**The Empathy-MemDocs Stack:**
- **MemDocs**: Persistent memory (what happened)
- **Empathy**: Anticipatory intelligence (what will happen)
- **Together**: AI that learns from your project and predicts future needs

---

## CLI Reference

### `memdocs init`
Initialize MemDocs in a project.

```bash
memdocs init [--force]
```

### `memdocs review`
Generate memory documentation.

```bash
# File-level (recommended)
memdocs review --path src/payments/charge.py

# Module-level
memdocs review --path src/payments/ --scope module

# Repository-level
memdocs review --repo . --force

# On specific event
memdocs review --path src/ --on pr      # Pull request
memdocs review --path src/ --on release  # Release
```

### `memdocs search`
Search project memory.

```bash
memdocs search "authentication"
memdocs search "database schema" --format json
```

### `memdocs stats`
Show memory statistics.

```bash
memdocs stats
memdocs stats --format json
```

### `memdocs sync`
Sync with Empathy framework.

```bash
memdocs sync --to empathy
```

---

## API Reference

### Python API

```python
from memdocs import MemDocs

# Initialize
mem = MemDocs(repo_path=".")

# Review a file
result = mem.review_file("src/payments/charge.py")

# Search memory
results = mem.search("payment processing")

# Get context for AI
context = mem.get_context_for_file("src/auth/login.py")

# Get dependency graph
graph = mem.get_dependency_graph()

# Stats
stats = mem.get_stats()
```

### Model Context Protocol (MCP)

MemDocs includes an MCP server for integration with Claude Desktop and other MCP clients:

```bash
# Start MCP server
memdocs mcp-server --port 3000

# In Claude Desktop config:
{
  "mcpServers": {
    "memdocs": {
      "command": "memdocs",
      "args": ["mcp-server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

---

## Comparison to Alternatives

| Feature | MemDocs | Vector DBs | GitHub Copilot | Cursor |
|---------|---------|------------|----------------|--------|
| **Storage** | Git-native | Cloud | Cloud | Cloud |
| **Cost** | Free | $$$$/month | $$$/month | $$/month |
| **Team sharing** | Built-in (git) | Separate sync | N/A | N/A |
| **Offline** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Privacy** | Local | Cloud | Cloud | Cloud |
| **Memory persistence** | ✅ Permanent | ✅ Permanent | ❌ Session-only | ⚠️ Limited |
| **Empathy integration** | ✅ Native | ❌ No | ❌ No | ❌ No |

---

## Roadmap

### v2.1 (Q1 2026)
- [ ] Multi-language support (Go, Rust, Java, C++)
- [ ] VSCode extension
- [ ] JetBrains plugin
- [ ] Automatic PR summaries

### v2.2 (Q2 2026)
- [ ] Semantic search (optional embeddings)
- [ ] Memory compression (summarize old memories)
- [ ] Team analytics (who documented what)

### v3.0 (Q3 2026)
- [ ] MemDocs Cloud (optional hosted version)
- [ ] Enterprise features (SSO, audit logs)
- [ ] Advanced Empathy integration

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Key areas needing help:**
- Multi-language AST parsing
- IDE plugins (VSCode, JetBrains)
- Documentation improvements
- Example projects

---

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## Support

- **Documentation**: https://docs.deepstudyai.com/memdocs
- **Issues**: https://github.com/Deep-Study-AI/memdocs/issues
- **Discord**: https://discord.gg/deepstudyai
- **Email**: patrick.roebuck@deepstudyai.com

---

## Credits

**Created by**: Patrick Roebuck (Deep Study AI, LLC)
**Inspired by**: The need for persistent AI memory without cloud lock-in
**Built with**: Claude Sonnet 4.5, tree-sitter, Python

**Special thanks** to the Empathy Framework team and early adopters who provided feedback.

---

**🧠 MemDocs: Because AI should remember your project, not forget it every session.**

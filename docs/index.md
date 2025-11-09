# MemDocs

**Persistent Memory for AI Projects**

MemDocs is a git-native memory management system that gives AI assistants persistent, project-specific memory. Generate structured, machine-readable documentation that lives in your repository.

## Why MemDocs?

AI assistants like Claude **have no memory between sessions**. Every conversation starts from scratch, forcing you to repeatedly explain your codebase.

MemDocs creates a **persistent memory layer** that:

- 🧠 **Remembers your project** across sessions
- 👥 **Shares memory with your team** (committed to git)
- 💰 **Costs nothing to store** (no vector databases, no embeddings API)
- ⚡ **Works offline** (no cloud dependencies for retrieval)
- 🤝 **Integrates with AI tools** (Cursor, Claude, Continue.dev)
- 🔒 **Privacy-first** (optional PHI/PII detection and redaction)

## Quick Start

```bash
# Install MemDocs
pip install memdocs

# Set your Claude API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Initialize in your project
cd your-project
memdocs init

# Document a file
memdocs review --path src/main.py

# Search your memory
memdocs query "authentication"

# Export for Cursor IDE
memdocs export cursor
```

**[Get started in 5 minutes →](getting-started.md)**

## Features

### 🎯 Smart Documentation

- **AI-powered**: Uses Claude Sonnet 4.5 for intelligent summarization
- **Scope-aware**: Automatically adjusts context (file/module/repo)
- **Auto-escalation**: Escalates scope for security-sensitive changes
- **Risk analysis**: Identifies potential issues and breaking changes

### 🔍 Semantic Search

- **Natural language**: Query with "how does auth work?"
- **Vector embeddings**: Local FAISS-based similarity search
- **Offline**: No API calls for searching (optional)
- **Fast**: Sub-second search on thousands of files

### 🔗 IDE Integration

- **Cursor**: Auto-loaded context for AI conversations
- **VS Code**: Continue.dev integration
- **Claude Desktop**: Export as markdown context
- **MCP Server**: Real-time memory serving (experimental)

### 🔒 Security & Privacy

- **Path validation**: Prevents directory traversal attacks
- **API key validation**: Strict regex patterns
- **Rate limiting**: Prevents API abuse (50 calls/minute)
- **Secret detection**: Finds and redacts API keys, passwords
- **PHI/PII protection**: HIPAA-aligned privacy controls

### 🚀 CI/CD Ready

- **GitHub Actions**: Auto-update docs on every commit
- **Pre-commit hooks**: Update before committing
- **Release automation**: Generate docs for releases
- **Artifact storage**: Save memory as build artifacts

## How It Works

```
1. Extract Code Structure        2. Generate Documentation
   ┌──────────────┐                  ┌──────────────────┐
   │  src/auth.py │                  │  Claude Sonnet   │
   │  - JWTAuth   │  ──────────────> │  4.5 analyzes    │
   │  - validate()│                  │  and summarizes  │
   └──────────────┘                  └──────────────────┘
         │                                    │
         │                                    ▼
         │                           ┌──────────────────┐
         │                           │  Structured Docs │
         │                           │  - Features      │
         │                           │  - Risks         │
         │                           │  - Impacts       │
         │                           └──────────────────┘
         │                                    │
         ▼                                    ▼
3. Generate Embeddings            4. Save to Git
   ┌──────────────┐                  ┌──────────────────┐
   │  sentence-   │                  │  .memdocs/       │
   │  transformers│  ──────────────> │  ├── docs/       │
   │  + FAISS     │                  │  └── memory/     │
   └──────────────┘                  └──────────────────┘
```

## Use Cases

### For Solo Developers

- 🧠 Never re-explain your codebase to AI
- 📍 Get accurate file:line references
- 🎯 Better AI suggestions based on your patterns
- ⚡ Faster development with persistent context

### For Teams

- 👥 Onboard new developers faster
- 📚 Share AI context across team
- 🔄 Keep documentation in sync with code
- 🎓 Learn from AI-generated insights

### For Open Source

- 📖 Auto-generate contributor docs
- 🔍 Make codebases more discoverable
- 🤝 Help AI assistants understand your project
- 📊 Track architectural evolution

## What Gets Generated

### Documentation (`docs/`)

- **index.json** - Structured data (features, impacts, risks)
- **symbols.yaml** - Code map (classes, functions, line numbers)
- **summary.md** - Human-readable summary

### Memory (`memory/`)

- **graph.json** - Feature relationship graph
- **embeddings-*.json** - Vector embeddings
- **faiss.index** - FAISS index for search
- **faiss_metadata.json** - Chunk metadata

All committed to git, shared with your team!

## Requirements

- **Python 3.10+**
- **Anthropic API key** ([get one here](https://console.anthropic.com/))
- **Git repository** (recommended but not required)

## Installation

### Basic Installation

```bash
pip install memdocs
```

### With Embeddings (Recommended)

```bash
pip install memdocs[embeddings]
```

### All Features

```bash
pip install memdocs[all]
```

**[Detailed installation guide →](installation.md)**

## Documentation

- **[Getting Started](getting-started.md)** - 5-minute tutorial
- **[Installation](installation.md)** - Platform-specific setup
- **[Configuration](configuration.md)** - Complete `.memdocs.yml` reference
- **[CLI Reference](cli-reference.md)** - All commands
- **[Architecture](architecture.md)** - How it works

### Guides

- **[GitHub Actions](guides/github-actions.md)** - CI/CD integration
- **[Cursor Integration](guides/cursor-integration.md)** - IDE setup

## Community

- **GitHub**: [Smart-AI-Memory/memdocs](https://github.com/Smart-AI-Memory/memdocs)
- **Issues**: [Report bugs](https://github.com/Smart-AI-Memory/memdocs/issues)
- **Discussions**: [Ask questions](https://github.com/Smart-AI-Memory/memdocs/discussions)
- **Contributing**: [Contribution guide](contributing.md)

## License

Apache 2.0 - See [LICENSE](https://github.com/Smart-AI-Memory/memdocs/blob/main/LICENSE)

## Acknowledgments

- **Anthropic** for Claude Sonnet 4.5
- **FAISS** for vector search
- **sentence-transformers** for embeddings
- **All contributors** who made this possible

---

**Ready to get started?** [Install MemDocs →](getting-started.md)

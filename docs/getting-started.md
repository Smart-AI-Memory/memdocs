# Getting Started with MemDocs

**Complete this tutorial in 5 minutes** and give your AI assistant persistent memory for your project.

## What You'll Learn

- Install MemDocs in your project
- Configure basic settings
- Generate your first documentation
- Query the AI memory
- Understand what gets created

## Prerequisites

- Python 3.10 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))
- A code project (any language)

## Step 1: Install MemDocs (30 seconds)

```bash
# Install from PyPI
pip install memdocs

# Verify installation
memdocs --version
```

**Expected output:**
```
MemDocs v2.0.0
```

## Step 2: Set Your API Key (15 seconds)

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or add to your shell profile for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
```

<details>
<summary>💡 **Don't have an API key yet?**</summary>

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key (starts with `sk-ant-`)

</details>

## Step 3: Initialize in Your Project (30 seconds)

```bash
# Navigate to your project
cd /path/to/your/project

# Initialize MemDocs
memdocs init
```

**What this does:**
- Creates `.memdocs.yml` configuration file
- Creates `.memdocs/` directory for memory storage
- Adds `.memdocs/` to `.gitignore` (memory is committed to git!)

**Expected output:**
```
✓ Created .memdocs.yml
✓ Created .memdocs/docs/
✓ Created .memdocs/memory/
✓ MemDocs initialized! Edit .memdocs.yml to customize.
```

## Step 4: Generate Your First Documentation (2 minutes)

Let's document a single file to see how MemDocs works:

```bash
# Document a specific file
memdocs review --path src/main.py
```

**What happens:**
1. MemDocs extracts code structure (classes, functions, imports)
2. Sends context to Claude Sonnet 4.5
3. Claude generates structured documentation
4. Saves multiple formats: JSON, YAML, Markdown
5. Creates searchable embeddings

**Expected output:**
```
============================================================
                       MemDocs Review
============================================================

→ Reviewing 1 path(s) for manual event
⠹ Extracting context from 1 path(s) 0:00:01
✓ Extracted context from 1 files
→ Determining scope
ℹ Scope: file (default)
⠇ Generating documentation with Claude Sonnet 4.5 0:00:05
✓ Documentation generated
→ Checking for PII/PHI
→ Writing documentation files
→ Writing memory files
⠼ Generating embeddings for semantic search 0:00:01
✓ Indexed 5 chunks, 5 embeddings
─────────────────────────────── Review Complete ────────────────────────────────
✓ Finished in 8.3s

               Generated Files
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Format       ┃ Path                       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ index.json   │ .memdocs/docs/index.json   │
├──────────────┼────────────────────────────┤
│ summary.md   │ .memdocs/docs/summary.md   │
├──────────────┼────────────────────────────┤
│ symbols.yaml │ .memdocs/docs/symbols.yaml │
├──────────────┼────────────────────────────┤
│ graph.json   │ .memdocs/memory/graph.json │
└──────────────┴────────────────────────────┘
```

## Step 5: View the Generated Documentation (30 seconds)

```bash
# View human-readable summary
cat .memdocs/docs/summary.md

# View code symbols (functions, classes)
cat .memdocs/docs/symbols.yaml

# View structured data (for AI/tools)
cat .memdocs/docs/index.json
```

**What you'll see:**
- Feature summaries with risk analysis
- API impacts and breaking changes
- Code symbols with line numbers
- Links to commits and issues

## Step 6: Query Your Project Memory (30 seconds)

```bash
# Search for specific topics
memdocs query "authentication"
memdocs query "database connections"
memdocs query "error handling"
```

**Example output:**
```
🔍 Searching for: "authentication"

Found 3 relevant matches:

1. src/auth/jwt.py:45 (Score: 0.92)
   JWT token validation and user authentication middleware.
   Implements secure token verification with expiry checks.

2. src/auth/users.py:23 (Score: 0.87)
   User authentication service with password hashing and session management.

3. config/security.py:12 (Score: 0.76)
   Security configuration including auth timeouts and token settings.
```

## Step 7: View Memory Statistics (15 seconds)

```bash
# See what's in memory
memdocs stats
```

**Example output:**
```
📊 MemDocs Statistics

Memory Status:
  Total Files Documented: 1
  Total Embeddings: 5
  Total Memory Size: 24.3 KB

Scope Levels:
  File-level: 1
  Module-level: 0
  Repo-level: 0

Last Updated: 2025-11-09 14:23:15
Git Commit: 79b58a1
```

## What's Next?

### Document More Files

```bash
# Document a whole directory
memdocs review --path src/

# Document specific modules
memdocs review --path src/auth/ src/api/ src/models/
```

### Customize Configuration

Edit `.memdocs.yml` to customize:
- Scope policies (file/module/repo level)
- Auto-escalation rules
- Privacy settings (PHI/PII detection)
- AI model and temperature

See [Configuration Reference](configuration.md) for details.

### Integrate with Your Workflow

- **Git Hooks**: Auto-update memory on commit ([guide](guides/github-actions.md))
- **CI/CD**: Generate docs in GitHub Actions ([guide](guides/github-actions.md))
- **Cursor/VS Code**: Load memory context automatically ([guide](guides/cursor-integration.md))
- **Empathy Framework**: Sync with Level 4 AI ([guide](guides/empathy-sync.md))

### Export for Your IDE

```bash
# Generate Cursor-compatible memory file
memdocs export cursor

# This creates .memdocs/cursor which Cursor can read
```

## Understanding the Memory Structure

```
.memdocs/
├── docs/               # Human & machine-readable docs (committed to git)
│   ├── index.json     # Structured data (features, impacts, risks)
│   ├── summary.md     # Human-readable summary
│   └── symbols.yaml   # Code map (classes, functions, line numbers)
├── memory/            # AI memory storage (committed to git)
│   ├── graph.json     # Feature relationship graph
│   ├── embeddings-*.json  # Vector embeddings for search
│   ├── faiss.index    # FAISS index for fast similarity search
│   └── faiss_metadata.json  # Metadata for embeddings
└── cursor             # Cursor IDE integration file
```

**Key insight:** All files are committed to git, so your entire team shares the same AI memory!

## Common Questions

### How much does this cost?

MemDocs uses Claude Sonnet 4.5. Typical costs:
- **Small file** (200 lines): ~$0.01
- **Medium file** (1000 lines): ~$0.05
- **Large file** (5000 lines): ~$0.20

Token usage is shown after each review.

### Can I use this without an API key?

No. MemDocs requires Claude Sonnet 4.5 for documentation generation. However:
- You only pay when generating/updating docs (not when querying)
- Local embeddings are free (no vector database costs)
- Memory storage is free (just git)

### Should I commit `.memdocs/` to git?

**YES!** This is the key benefit. Your entire team shares the same AI memory:
- New team members get instant context
- AI assistants have consistent understanding
- Documentation evolves with your code

### How often should I regenerate docs?

**Strategies:**
- **Manual**: Run `memdocs review` when you make significant changes
- **Pre-commit hook**: Auto-update on every commit ([setup guide](guides/github-actions.md))
- **CI/CD**: Generate docs in GitHub Actions on PR merge

## Troubleshooting

### API key not found

```bash
# Make sure your API key is set
echo $ANTHROPIC_API_KEY

# If empty, set it:
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Permission denied

```bash
# Make sure you have write access to the directory
ls -la .memdocs/

# If needed, fix permissions:
chmod -R u+w .memdocs/
```

### Out of memory / Large files

For very large files, use `--scope module` to increase context:

```bash
memdocs review --path src/ --scope module
```

## Next Steps

- **[Installation Guide](installation.md)** - Advanced installation options
- **[Configuration Reference](configuration.md)** - Complete config options
- **[CLI Reference](cli-reference.md)** - All commands and options
- **[Architecture](architecture.md)** - How MemDocs works under the hood

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

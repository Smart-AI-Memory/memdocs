# CLI Reference

Complete reference for all MemDocs command-line commands.

## Overview

MemDocs provides a command-line interface (CLI) for generating, querying, and managing AI memory for your projects.

**Global Usage:**
```bash
memdocs [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**
- `--version` - Show MemDocs version and exit
- `--help` - Show help message and exit

**Available Commands:**
- `init` - Initialize MemDocs in a project
- `review` - Generate documentation for code
- `query` - Search project memory
- `export` - Export memory for AI assistants
- `stats` - Show memory statistics
- `cleanup` - Clean up old memory data

---

## `memdocs init`

Initialize MemDocs in the current project.

### Synopsis

```bash
memdocs init [OPTIONS]
```

### Description

Creates the necessary configuration and directory structure for MemDocs in your project:

- Creates `.memdocs.yml` configuration file
- Creates `.memdocs/docs/` directory for documentation
- Creates `.memdocs/memory/` directory for AI memory
- Adds `.memdocs/` to `.gitignore` if it exists

### Options

*No options available*

### Examples

```bash
# Initialize in current directory
memdocs init

# Initialize from a subdirectory (creates config at project root)
cd src/
memdocs init
```

### Output

```
✓ Created .memdocs.yml
✓ Created .memdocs/docs/
✓ Created .memdocs/memory/
✓ MemDocs initialized! Edit .memdocs.yml to customize.
```

### See Also

- [Configuration Reference](configuration.md) - Customize `.memdocs.yml`
- [Getting Started](getting-started.md) - Complete tutorial

---

## `memdocs review`

Review code and generate documentation.

### Synopsis

```bash
memdocs review [OPTIONS]
```

### Description

Generates AI-powered documentation for specified files or directories. This is the core command for creating project memory.

**What it does:**
1. Extracts code structure (classes, functions, imports)
2. Determines appropriate scope (file/module/repo)
3. Sends context to Claude Sonnet 4.5
4. Generates structured documentation
5. Creates searchable embeddings
6. Saves to `.memdocs/` directory

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--path PATH` | path | None | File or directory to review (can specify multiple) |
| `--repo` | flag | False | Review entire repository (use sparingly) |
| `--on EVENT` | choice | `manual` | Event triggering review: `pr`, `commit`, `release`, `schedule`, `manual` |
| `--emit MODE` | choice | `both` | What to generate: `docs`, `memory`, `both` |
| `--rules LEVEL` | choice | `standard` | Rule strictness: `strict`, `standard`, `permissive` |
| `--max-files N` | integer | 150 | Maximum files without `--force` |
| `--force` | flag | False | Override file count limits |
| `--escalate-on RULES` | text | None | Comma-separated escalation rules |
| `--config PATH` | path | `.memdocs.yml` | Configuration file path |
| `--output-dir PATH` | path | `.memdocs/` | Override output directory |

### Event Types (`--on`)

- **`pr`** - Pull request review
- **`commit`** - Commit-based review
- **`release`** - Release documentation
- **`schedule`** - Scheduled review (CI/CD)
- **`manual`** - Manual review (default)

### Emit Modes (`--emit`)

- **`docs`** - Generate only documentation files
- **`memory`** - Generate only memory/embeddings
- **`both`** - Generate both (default)

### Rule Levels (`--rules`)

- **`strict`** - Strict validation, fail on warnings
- **`standard`** - Normal validation (default)
- **`permissive`** - Lenient validation, warnings only

### Examples

#### Basic File Review

```bash
# Review a single file
memdocs review --path src/main.py

# Review multiple files
memdocs review --path src/auth.py src/api.py
```

#### Directory Review

```bash
# Review entire directory
memdocs review --path src/

# Review multiple directories
memdocs review --path src/auth/ src/api/
```

#### Repository Review

```bash
# Review entire repository (requires --force for large repos)
memdocs review --repo

# Force review of large repository
memdocs review --repo --force
```

#### Event-Based Review

```bash
# Generate docs for PR review
memdocs review --path src/ --on pr

# Generate docs on release
memdocs review --path . --on release
```

#### Emit Control

```bash
# Generate only documentation (skip embeddings)
memdocs review --path src/ --emit docs

# Generate only memory/embeddings (skip docs)
memdocs review --path src/ --emit memory
```

#### Escalation Rules

```bash
# Auto-escalate for security files
memdocs review --path src/ --escalate-on security_sensitive_paths

# Multiple escalation rules
memdocs review --path src/ --escalate-on cross_module_changes,public_api_signatures
```

**Available escalation rules:**
- `cross_module_changes` - Multi-module changes
- `security_sensitive_paths` - Security-critical files
- `public_api_signatures` - Public API changes
- `breaking_changes` - Breaking changes detected
- `test_failures` - Test failures detected

### Output

```
============================================================
                       MemDocs Review
============================================================

→ Reviewing 3 path(s) for manual event
⠹ Extracting context from 3 path(s) 0:00:02
✓ Extracted context from 3 files
→ Determining scope
ℹ Scope: file (default)
⠇ Generating documentation with Claude Sonnet 4.5 0:00:08
✓ Documentation generated
→ Checking for PII/PHI
→ Writing documentation files
→ Writing memory files
⠼ Generating embeddings for semantic search 0:00:03
✓ Indexed 15 chunks, 15 embeddings
─────────────────────────────── Review Complete ────────────────────────────────
✓ Finished in 14.2s

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

### Exit Codes

- `0` - Success
- `1` - General error (missing files, API error, etc.)
- `2` - Configuration error
- `3` - API key not found
- `4` - Too many files (requires `--force`)

### See Also

- [Configuration Reference](configuration.md#policies) - Scope policies
- [Getting Started](getting-started.md#step-4) - First review walkthrough

---

## `memdocs query`

Query project memory using natural language.

### Synopsis

```bash
memdocs query [OPTIONS] QUERY
```

### Description

Search your project's AI memory using natural language queries. Uses semantic search over generated embeddings to find relevant code and documentation.

**How it works:**
1. Converts your query to embedding vector
2. Searches FAISS index for similar code/docs
3. Returns top-k matches with relevance scores
4. Shows file paths and line numbers

**Requires:** `memdocs[embeddings]` installation

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY` | string | Yes | Natural language search query |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--k INTEGER` | integer | 5 | Number of results to return |
| `--memory-dir PATH` | path | `.memdocs/memory` | Memory directory path |

### Examples

```bash
# Basic query
memdocs query "authentication"

# Get more results
memdocs query "payment processing" --k 10

# Query specific memory directory
memdocs query "error handling" --memory-dir /path/to/.memdocs/memory
```

### Output

```
🔍 Searching for: "authentication"

Found 5 relevant matches:

1. src/auth/jwt.py:45 (Score: 0.92)
   JWT token validation and user authentication middleware.
   Implements secure token verification with expiry checks.

2. src/auth/users.py:23 (Score: 0.87)
   User authentication service with password hashing and session management.

3. config/security.py:12 (Score: 0.76)
   Security configuration including auth timeouts and token settings.

4. src/api/middleware.py:67 (Score: 0.71)
   Authentication middleware for API endpoints.

5. tests/test_auth.py:33 (Score: 0.68)
   Integration tests for authentication flow.
```

### Exit Codes

- `0` - Success
- `1` - No results found
- `2` - Memory directory not found
- `3` - Embeddings not generated (run `memdocs review` first)

### See Also

- [Installation](installation.md#with-local-search-recommended) - Install with embeddings support
- [Getting Started](getting-started.md#step-6) - Query examples

---

## `memdocs export`

Export documentation for AI assistants.

### Synopsis

```bash
memdocs export [OPTIONS] FORMAT
```

### Description

Export project memory in formats compatible with popular AI assistants and IDEs.

**Supported formats:**
- **`cursor`** - Cursor IDE (`.cursorrules` file)
- **`claude`** - Claude Desktop/Web (Markdown)
- **`continue`** - Continue.dev extension

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FORMAT` | choice | Yes | Export format: `cursor`, `claude`, `continue` |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output PATH` | path | Auto | Output file path |
| `--docs-dir PATH` | path | `.memdocs/docs` | Documentation directory |
| `--include-symbols` | flag | True | Include code symbols in export |
| `--no-symbols` | flag | False | Exclude code symbols from export |

### Examples

```bash
# Export for Cursor IDE
memdocs export cursor

# Export for Claude with custom path
memdocs export claude --output .claude-context.md

# Export without code symbols
memdocs export cursor --no-symbols

# Export from custom docs directory
memdocs export continue --docs-dir /path/to/.memdocs/docs
```

### Output Locations

| Format | Default Output Path |
|--------|-------------------|
| `cursor` | `.memdocs/cursor` |
| `claude` | `.memdocs/claude-context.md` |
| `continue` | `.memdocs/continue.json` |

### Export Formats

#### Cursor Format

Generates `.cursorrules` file that Cursor IDE automatically reads:

```markdown
# Project Memory (Auto-generated by MemDocs)

## 📚 Documentation

[Summary of features and changes]

## 🗺️ Code Map

[Classes, functions, and symbols with line numbers]

## 🔗 Memory Graph

[Feature relationships and dependencies]
```

#### Claude Format

Generates Markdown context file for Claude Desktop:

```markdown
# Project Context for Claude

## Overview
[Project summary]

## Recent Changes
[Features and impacts]

## Code Structure
[Symbols and organization]
```

#### Continue Format

Generates JSON configuration for Continue.dev:

```json
{
  "name": "Project Memory",
  "description": "AI-generated project documentation",
  "files": ["..."],
  "symbols": ["..."],
  "features": ["..."]
}
```

### Exit Codes

- `0` - Success
- `1` - Export failed
- `2` - Docs directory not found
- `3` - Invalid format

### See Also

- [Cursor Integration Guide](guides/cursor-integration.md) - Setup for Cursor IDE
- [Getting Started](getting-started.md#step-7) - Export examples

---

## `memdocs stats`

Show memory and documentation statistics.

### Synopsis

```bash
memdocs stats [OPTIONS]
```

### Description

Display statistics about your project's AI memory, including:
- Number of documented files
- Total embeddings
- Memory size
- Scope distribution
- Last update time

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--docs-dir PATH` | path | `.memdocs/docs` | Documentation directory |
| `--memory-dir PATH` | path | `.memdocs/memory` | Memory directory |
| `--format FORMAT` | choice | `table` | Output format: `table`, `json` |

### Examples

```bash
# Show stats in table format (default)
memdocs stats

# Show stats as JSON
memdocs stats --format json

# Stats from custom directories
memdocs stats --docs-dir /path/to/docs --memory-dir /path/to/memory
```

### Output (Table Format)

```
📊 MemDocs Statistics

Memory Status:
  Total Files Documented: 42
  Total Embeddings: 156
  Total Memory Size: 1.2 MB

Scope Levels:
  File-level: 38
  Module-level: 4
  Repo-level: 0

Recent Activity:
  Last Updated: 2025-11-09 14:23:15
  Git Commit: 79b58a1
  Total Reviews: 42

Documentation:
  JSON files: 42
  YAML files: 42
  Markdown files: 42

Embeddings:
  Total vectors: 156
  Dimensions: 384
  Index size: 234 KB
```

### Output (JSON Format)

```json
{
  "memory": {
    "total_files": 42,
    "total_embeddings": 156,
    "total_size_bytes": 1258291
  },
  "scope_distribution": {
    "file": 38,
    "module": 4,
    "repo": 0
  },
  "last_updated": "2025-11-09T14:23:15Z",
  "git_commit": "79b58a1",
  "documentation": {
    "json_files": 42,
    "yaml_files": 42,
    "markdown_files": 42
  },
  "embeddings": {
    "total_vectors": 156,
    "dimensions": 384,
    "index_size_bytes": 239616
  }
}
```

### Exit Codes

- `0` - Success
- `1` - Stats unavailable
- `2` - Directories not found

### See Also

- [Getting Started](getting-started.md#step-7) - View stats example

---

## `memdocs cleanup`

Cleanup old embeddings and memory data.

### Synopsis

```bash
memdocs cleanup [OPTIONS]
```

### Description

Remove old or stale memory data to free up disk space:
- Removes orphaned embeddings (files no longer in repo)
- Removes duplicate entries
- Compacts FAISS index
- Removes old revisions

**Warning:** This operation cannot be undone. Consider backing up `.memdocs/` first.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--memory-dir PATH` | path | `.memdocs/memory` | Memory directory |
| `--dry-run` | flag | False | Show what would be removed (don't actually delete) |
| `--force` | flag | False | Skip confirmation prompt |

### Examples

```bash
# Preview cleanup (dry run)
memdocs cleanup --dry-run

# Cleanup with confirmation
memdocs cleanup

# Cleanup without confirmation
memdocs cleanup --force

# Cleanup custom memory directory
memdocs cleanup --memory-dir /path/to/memory
```

### Output

```
🧹 Cleaning up MemDocs memory...

Found:
  - 3 orphaned embedding files
  - 12 duplicate entries
  - 145 KB of old revisions

This will free 167 KB of disk space.

Proceed with cleanup? [y/N]: y

✓ Removed 3 orphaned files
✓ Removed 12 duplicates
✓ Removed old revisions
✓ Compacted FAISS index
✓ Cleanup complete! Freed 167 KB
```

### Exit Codes

- `0` - Success
- `1` - Cleanup failed
- `2` - User cancelled

---

## Environment Variables

MemDocs supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (required) | None |
| `MEMDOCS_CONFIG` | Path to config file | `.memdocs.yml` |
| `MEMDOCS_SCOPE` | Override default scope | From config |
| `MEMDOCS_NO_CACHE` | Disable API response caching | `false` |
| `MEMDOCS_LOG_LEVEL` | Logging level | `INFO` |

### Examples

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Use custom config
export MEMDOCS_CONFIG="/path/to/config.yml"
memdocs review --path src/

# Override scope
export MEMDOCS_SCOPE="module"
memdocs review --path src/

# Enable debug logging
export MEMDOCS_LOG_LEVEL="DEBUG"
memdocs review --path src/
```

---

## Common Workflows

### Daily Development

```bash
# Document files you're working on
memdocs review --path src/auth/users.py

# Query for related code
memdocs query "user authentication"

# Check memory stats
memdocs stats
```

### Pull Request Workflow

```bash
# Document changed files
memdocs review --path src/ --on pr

# Export for reviewers
memdocs export claude --output PR_CONTEXT.md

# Commit memory updates
git add .memdocs/
git commit -m "docs: Update AI memory"
```

### Release Workflow

```bash
# Document entire codebase
memdocs review --repo --on release --force

# Export for documentation
memdocs export cursor

# Check coverage
memdocs stats --format json > memory-stats.json
```

### Cleanup Workflow

```bash
# Preview cleanup
memdocs cleanup --dry-run

# Perform cleanup
memdocs cleanup

# Verify stats
memdocs stats
```

---

## Troubleshooting

### Command Not Found

**Problem:** `memdocs: command not found`

**Solution:**
```bash
# Make sure memdocs is installed
pip show memdocs

# If not installed
pip install memdocs

# If installed but not in PATH
python -m memdocs --help
```

### API Key Errors

**Problem:** `Error: ANTHROPIC_API_KEY not set`

**Solution:**
```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Verify it's set
echo $ANTHROPIC_API_KEY
```

### Too Many Files Error

**Problem:** `Error: Too many files (150 > 150). Use --force`

**Solution:**
```bash
# Either use --force
memdocs review --path src/ --force

# Or increase limit in config
# Edit .memdocs.yml:
# policies:
#   max_files_without_force: 500
```

### Memory Not Found

**Problem:** `Error: Memory directory not found`

**Solution:**
```bash
# Run review first to generate memory
memdocs review --path src/

# Or check if .memdocs/ exists
ls -la .memdocs/
```

---

## Next Steps

- **[Configuration Reference](configuration.md)** - Customize behavior
- **[Architecture](architecture.md)** - How MemDocs works
- **[GitHub Actions Guide](guides/github-actions.md)** - CI/CD integration

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

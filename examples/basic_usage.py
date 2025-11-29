"""
MemDocs Basic Usage Examples

This example demonstrates how to use MemDocs via CLI and Python API.

MemDocs is primarily a CLI tool. For programmatic access, use the MemoryIndexer
class or integrate with Claude Desktop via the MCP server.
"""

import subprocess
import sys
from pathlib import Path


def example_cli_workflow():
    """Example: Using MemDocs CLI (Primary Interface)"""
    print("=" * 80)
    print("Example 1: CLI Workflow")
    print("=" * 80)
    print()

    print("MemDocs is primarily used via CLI commands:\n")

    print("1. Initialize MemDocs in your project:")
    print("   $ memdocs init")
    print("   Creates .memdocs/ directory and .memdocs.yml config\n")

    print("2. Review files to generate documentation:")
    print("   $ memdocs review --path src/")
    print("   Analyzes code and generates AI-powered summaries\n")

    print("3. Query project memory:")
    print("   $ memdocs query 'authentication flow'")
    print("   Search documentation using natural language\n")

    print("4. Get project statistics:")
    print("   $ memdocs stats")
    print("   View coverage, symbols, and memory stats\n")

    print("5. Export for AI assistants:")
    print("   $ memdocs export cursor")
    print("   Generate .cursorrules for Cursor IDE")
    print("   $ memdocs export claude")
    print("   Generate .clinerules for Claude Code\n")
    print()


def example_python_api():
    """Example: Using Python API for Querying Memory"""
    print("=" * 80)
    print("Example 2: Python API - Query Memory")
    print("=" * 80)
    print()

    print("For programmatic access, use the MemoryIndexer class:\n")

    code = '''from pathlib import Path
from memdocs.index import MemoryIndexer

# Initialize indexer (assumes memory already created via CLI)
indexer = MemoryIndexer(
    memory_dir=Path(".memdocs/memory"),
    use_embeddings=True  # Requires optional [embeddings] dependencies
)

# Query project memory
results = indexer.query_memory("payment processing", k=5)

for result in results:
    print(f"File: {result['metadata']['file']}")
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['text'][:100]}...")
    print()

# Get statistics
stats = indexer.get_stats()
print(f"Total indexed: {stats.get('total_vectors', 0)} chunks")
'''

    print(code)
    print()


def example_working_with_schemas():
    """Example: Working with MemDocs Data Schemas"""
    print("=" * 80)
    print("Example 3: Working with Schemas")
    print("=" * 80)
    print()

    print("Read and parse MemDocs output files:\n")

    code = '''import json
import yaml
from pathlib import Path
from memdocs.schemas import DocumentIndex, Symbol

# Read JSON index
docs_dir = Path(".memdocs/docs")
with open(docs_dir / "index.json") as f:
    index_data = json.load(f)
    doc_index = DocumentIndex(**index_data)

print(f"Commit: {doc_index.commit}")
print(f"Timestamp: {doc_index.timestamp}")
print(f"Files: {len(doc_index.files)}")

# Read symbols YAML
with open(docs_dir / "symbols.yaml") as f:
    symbols_data = yaml.safe_load(f)

for symbol in symbols_data.get("symbols", []):
    print(f"{symbol['kind']}: {symbol['name']} ({symbol['file']})")

# Read markdown summary
summary = (docs_dir / "summary.md").read_text()
print("\\nSummary (first 200 chars):")
print(summary[:200])
'''

    print(code)
    print()


def example_mcp_integration():
    """Example: Claude Desktop Integration via MCP"""
    print("=" * 80)
    print("Example 4: Claude Desktop Integration (MCP)")
    print("=" * 80)
    print()

    print("Configure Claude Desktop to use MemDocs MCP server:\n")

    config = '''{
  "mcpServers": {
    "memdocs": {
      "command": "python",
      "args": ["-m", "memdocs.mcp_server"],
      "env": {
        "REPO_PATH": "/path/to/your/project"
      }
    }
  }
}'''

    print("Add to ~/Library/Application Support/Claude/claude_desktop_config.json:\n")
    print(config)
    print()
    print("Claude Desktop will then have access to these tools:")
    print("  - search_memory: Semantic search of project docs")
    print("  - get_symbols: Retrieve code symbols (classes, functions)")
    print("  - get_documentation: Get full documentation")
    print("  - get_summary: Human-readable project summary")
    print("  - query_analysis: Advanced analysis (if Empathy Framework enabled)")
    print()


def example_configuration():
    """Example: Customizing MemDocs Configuration"""
    print("=" * 80)
    print("Example 5: Configuration")
    print("=" * 80)
    print()

    print("Customize behavior via .memdocs.yml:\n")

    config = '''version: 1

# Scope policy
policies:
  default_scope: file          # file | module | repo
  max_files_without_force: 150
  escalate_on:
    - cross_module_changes
    - security_sensitive_paths

# Output configuration
outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory
  formats:
    - json
    - yaml
    - markdown

# Privacy (for sensitive data)
privacy:
  phi_mode: "standard"          # off | standard | strict
  scrub:
    - email
    - phone
    - ssn
    - mrn
  audit_redactions: true

# AI configuration
ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  max_tokens: 8192
  temperature: 0.3

# Exclude patterns
exclude:
  - node_modules/**
  - .venv/**
  - "*.pyc"
'''

    print(config)
    print()


def example_ci_cd_integration():
    """Example: CI/CD Integration"""
    print("=" * 80)
    print("Example 6: CI/CD Integration")
    print("=" * 80)
    print()

    print("Integrate MemDocs into your CI/CD pipeline:\n")

    workflow = '''# .github/workflows/memdocs.yml
name: Update Project Memory

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  update-memory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for git diffs

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install MemDocs
        run: pip install memdocs

      - name: Review changes
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: memdocs review --path src/

      - name: Commit updated memory
        run: |
          git config user.name "github-actions"
          git config user.email "github-actions@github.com"
          git add .memdocs/
          git commit -m "Update project memory [skip ci]" || true
          git push
'''

    print(workflow)
    print()


def run_live_example():
    """Run a live example if ANTHROPIC_API_KEY is set"""
    print("=" * 80)
    print("Example 7: Live Demo (if configured)")
    print("=" * 80)
    print()

    # Check if API key is configured
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set. Skipping live demo.")
        print("   Set your API key to run live examples:")
        print("   $ export ANTHROPIC_API_KEY='sk-ant-...'")
        print()
        return

    print("Running live CLI commands...\n")

    try:
        # Check if memdocs is installed
        result = subprocess.run(
            ["memdocs", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print("⚠️  MemDocs not installed. Install with: pip install memdocs")
            print()
            return

        print(f"✓ MemDocs version: {result.stdout.strip()}\n")

        # Show stats if available
        result = subprocess.run(
            ["memdocs", "stats"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("Current project stats:")
            print(result.stdout)
        else:
            print("ℹ️  No memory created yet. Run 'memdocs init' to get started.")

    except FileNotFoundError:
        print("⚠️  MemDocs not found in PATH")
    except Exception as e:
        print(f"⚠️  Error: {e}")

    print()


def main():
    """Run all examples"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "MemDocs Usage Examples" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("MemDocs: Git-native memory management for AI projects")
    print()

    try:
        example_cli_workflow()
        example_python_api()
        example_working_with_schemas()
        example_mcp_integration()
        example_configuration()
        example_ci_cd_integration()
        run_live_example()

        print("=" * 80)
        print("✓ All examples shown successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Install MemDocs: pip install memdocs")
        print("  2. Set API key: export ANTHROPIC_API_KEY='sk-ant-...'")
        print("  3. Initialize: memdocs init")
        print("  4. Review code: memdocs review --path src/")
        print("  5. Read docs: https://github.com/Smart-AI-Memory/memdocs")
        print()

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

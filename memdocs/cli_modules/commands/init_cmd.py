"""
Init command - Initialize MemDocs in the current project.
"""

import os
import sys
from pathlib import Path

import click

from memdocs import cli_output as out
from memdocs.security import PathValidator


@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Reinitialize even if already initialized",
)
def init(force: bool) -> None:
    """Initialize MemDocs in the current project.

    Examples:

        memdocs init
        memdocs init --force
    """
    try:
        out.print_header("MemDocs Initialization")

        # Validate we're in a writable directory
        cwd = Path.cwd()
        if not os.access(cwd, os.W_OK):
            out.error("Current directory is not writable")
            sys.exit(1)

        config_path = Path(".memdocs.yml")
        docs_dir = Path(".memdocs/docs")
        memory_dir = Path(".memdocs/memory")

        # Validate paths are safe (no traversal)
        try:
            PathValidator.validate_path(config_path, base_dir=cwd)
            PathValidator.validate_path(docs_dir, base_dir=cwd)
            PathValidator.validate_path(memory_dir, base_dir=cwd)
        except Exception as e:
            out.error(f"Path validation failed: {e}")
            sys.exit(1)

        # Check if already initialized
        if config_path.exists() and not force:
            out.warning("MemDocs already initialized")
            out.info("Use [cyan]--force[/cyan] to reinitialize")
            sys.exit(0)

        # Create directories
        out.step("Creating directory structure")
        docs_dir.mkdir(parents=True, exist_ok=True)
        memory_dir.mkdir(parents=True, exist_ok=True)
        out.success("Directories created")

        # Create config file
        out.step("Creating configuration file")
        default_config = """version: 1

# Scope policy (controls memory granularity)
policies:
  default_scope: file          # file | module | repo
  max_files_without_force: 150

  # Auto-escalate for important changes
  escalate_on:
    - cross_module_changes      # Multi-module = bigger context
    - security_sensitive_paths  # auth/*, security/* = thorough docs
    - public_api_signatures     # API changes = team awareness

# Output configuration (git-committed memory)
outputs:
  docs_dir: .memdocs/docs       # Committed to git
  memory_dir: .memdocs/memory   # Committed to git
  formats:
    - json                      # index.json (machine-readable)
    - yaml                      # symbols.yaml (code map)
    - markdown                  # summary.md (human-readable)

# AI configuration (Claude API)
ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929  # Claude Sonnet 4.5 (latest)
  max_tokens: 8192
  temperature: 0.3              # Lower = more deterministic

# Privacy (optional, for sensitive codebases)
privacy:
  phi_mode: "off"               # off | standard | strict
  pii_detection: false
  redaction_enabled: false
  scrub: []

# Exclude patterns
exclude:
  - node_modules/**
  - .venv/**
  - __pycache__/**
  - "*.pyc"
  - dist/**
  - build/**
"""
        config_path.write_text(default_config, encoding="utf-8")
        out.success(f"Configuration created: [green]{config_path}[/green]")

        # Create .gitignore entry suggestion
        gitignore_path = Path(".gitignore")
        gitignore_entry = (
            "\n# MemDocs (commit docs and memory, ignore temp files)\n.memdocs/.coverage.*\n"
        )

        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text(encoding="utf-8")
            if ".memdocs/" not in gitignore_content:
                out.console.print()
                out.info("Consider adding to [cyan].gitignore[/cyan]:")
                out.console.print(gitignore_entry)
        else:
            out.console.print()
            out.info("Consider creating [cyan].gitignore[/cyan] with:")
            out.console.print(gitignore_entry)

        # Print summary
        out.print_rule("Initialization Complete", style="green")
        out.console.print()

        table = out.create_table(title="Created Files", show_lines=True)
        table.add_column("File", style="cyan")
        table.add_column("Purpose", style="green")

        table.add_row(str(config_path), "Configuration file")
        table.add_row(str(docs_dir), "Documentation output directory")
        table.add_row(str(memory_dir), "Memory storage directory")

        out.print_table(table)

        # Next steps
        out.console.print()
        out.panel(
            """1. Set your API key: [cyan]export ANTHROPIC_API_KEY="your-key"[/cyan]
2. Document a file: [cyan]memdocs review --path src/main.py[/cyan]
3. Query memory: [cyan]memdocs query "authentication"[/cyan]
4. View stats: [cyan]memdocs stats[/cyan]""",
            title="Next Steps",
            style="blue",
        )

    except Exception as e:
        out.console.print()
        out.error(f"Initialization failed: {e}")
        sys.exit(1)

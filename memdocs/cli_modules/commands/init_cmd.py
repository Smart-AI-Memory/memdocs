"""
Init command - Initialize MemDocs in the current project.
"""

import json
import os
import sys
from pathlib import Path

import click

from memdocs import cli_output as out
from memdocs.security import PathValidator


def _detect_source_directory(cwd: Path) -> str:
    """Detect the main source directory for the project."""
    common_dirs = ["src", "lib", "app", "pkg", cwd.name]

    for dir_name in common_dirs:
        if (cwd / dir_name).is_dir():
            return f"{dir_name}/"

    # Default to current directory
    return "./"


def _setup_mcp_infrastructure(cwd: Path) -> None:
    """Set up VS Code tasks and settings for MCP auto-start."""
    vscode_dir = cwd / ".vscode"
    tasks_file = vscode_dir / "tasks.json"
    settings_file = vscode_dir / "settings.json"

    # Create .vscode directory
    out.step("Setting up VS Code MCP integration")
    vscode_dir.mkdir(exist_ok=True)

    # Detect source directory
    source_dir = _detect_source_directory(cwd)

    # Create tasks.json
    tasks_config = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "MemDocs MCP Server",
                "type": "shell",
                "command": "memdocs",
                "args": ["serve", "--mcp"],
                "isBackground": True,
                "problemMatcher": [],
                "runOptions": {
                    "runOn": "folderOpen"
                },
                "presentation": {
                    "echo": False,
                    "reveal": "never",
                    "focus": False,
                    "panel": "shared",
                    "showReuseMessage": False,
                    "clear": False
                }
            },
            {
                "label": "Update MemDocs Memory",
                "type": "shell",
                "command": "memdocs",
                "args": ["review", "--path", source_dir],
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared"
                }
            },
            {
                "label": "Export MemDocs for Cursor",
                "type": "shell",
                "command": "memdocs",
                "args": ["export", "cursor"],
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared"
                }
            },
            {
                "label": "MemDocs Stats",
                "type": "shell",
                "command": "memdocs",
                "args": ["stats"],
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": True,
                    "panel": "shared"
                }
            }
        ]
    }

    tasks_file.write_text(json.dumps(tasks_config, indent=2), encoding="utf-8")
    out.success(f"Created [green]{tasks_file}[/green]")

    # Create settings.json for auto-start
    settings_config = {
        "task.autoDetect": "on",
        "task.allowAutomaticTasks": "on"
    }

    # Merge with existing settings if they exist
    if settings_file.exists():
        try:
            existing_settings = json.loads(settings_file.read_text(encoding="utf-8"))
            existing_settings.update(settings_config)
            settings_config = existing_settings
        except json.JSONDecodeError:
            pass  # Use new settings if existing file is invalid

    settings_file.write_text(json.dumps(settings_config, indent=2), encoding="utf-8")
    out.success(f"Created [green]{settings_file}[/green]")

    out.success("MCP auto-start configured for VS Code/Cursor")


@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Reinitialize even if already initialized",
)
@click.option(
    "--with-mcp",
    is_flag=True,
    help="Setup VS Code tasks for MCP auto-start",
)
def init(force: bool, with_mcp: bool) -> None:
    """Initialize MemDocs in the current project.

    Examples:

        memdocs init
        memdocs init --force
        memdocs init --with-mcp
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

        # Set up MCP infrastructure if requested
        if with_mcp:
            out.console.print()
            _setup_mcp_infrastructure(cwd)

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

        if with_mcp:
            table.add_row(".vscode/tasks.json", "VS Code tasks for MCP")
            table.add_row(".vscode/settings.json", "VS Code auto-start settings")

        out.print_table(table)

        # Next steps
        out.console.print()

        if with_mcp:
            next_steps = """1. Set your API key: [cyan]export ANTHROPIC_API_KEY="your-key"[/cyan]
2. Document a file: [cyan]memdocs review --path src/main.py[/cyan]
3. Query memory: [cyan]memdocs query "authentication"[/cyan]
4. View stats: [cyan]memdocs stats[/cyan]
5. Open in VS Code/Cursor - MCP server will auto-start! 🚀"""
        else:
            next_steps = """1. Set your API key: [cyan]export ANTHROPIC_API_KEY="your-key"[/cyan]
2. Document a file: [cyan]memdocs review --path src/main.py[/cyan]
3. Query memory: [cyan]memdocs query "authentication"[/cyan]
4. View stats: [cyan]memdocs stats[/cyan]
5. Optional: Setup MCP server: [cyan]memdocs init --with-mcp[/cyan]"""

        out.panel(
            next_steps,
            title="Next Steps",
            style="blue",
        )

    except Exception as e:
        out.console.print()
        out.error(f"Initialization failed: {e}")
        sys.exit(1)

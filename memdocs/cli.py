"""
Command-line interface for doc-intelligence.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

import click
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from memdocs import __version__  # noqa: E402
from memdocs import cli_output as out  # noqa: E402
from memdocs.extract import Extractor  # noqa: E402
from memdocs.guard import create_guard_from_config  # noqa: E402
from memdocs.index import MemoryIndexer  # noqa: E402
from memdocs.policy import PolicyEngine  # noqa: E402
from memdocs.schemas import DocIntConfig, SymbolsOutput  # noqa: E402
from memdocs.summarize import Summarizer  # noqa: E402


def load_config(config_path: Path) -> DocIntConfig:
    """Load configuration from file.

    Args:
        config_path: Path to config file

    Returns:
        Loaded configuration
    """
    if not config_path.exists():
        return DocIntConfig()  # Use defaults

    with open(config_path, encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    return DocIntConfig(**config_dict)


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """MemDocs: Persistent memory management for AI projects."""
    ctx.ensure_object(dict)


@main.command()
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

        config_path = Path(".memdocs.yml")
        docs_dir = Path(".memdocs/docs")
        memory_dir = Path(".memdocs/memory")

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


@main.command()
@click.option(
    "--path",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help="File or directory path to review (can specify multiple)",
)
@click.option(
    "--repo",
    is_flag=True,
    help="Review entire repository (use sparingly)",
)
@click.option(
    "--on",
    "event",
    type=click.Choice(["pr", "commit", "release", "schedule", "manual"]),
    default="manual",
    help="Event type triggering review",
)
@click.option(
    "--emit",
    type=click.Choice(["docs", "memory", "both"]),
    default="both",
    help="What to generate (docs, memory, or both)",
)
@click.option(
    "--rules",
    type=click.Choice(["strict", "standard", "permissive"]),
    default="standard",
    help="Rule strictness level",
)
@click.option(
    "--max-files",
    type=int,
    default=150,
    help="Maximum files without --force",
)
@click.option(
    "--force",
    is_flag=True,
    help="Override file count limits",
)
@click.option(
    "--escalate-on",
    type=str,
    help="Comma-separated escalation rules",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default=Path(".memdocs.yml"),
    help="Configuration file path",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Override output directory",
)
@click.pass_context
def review(
    ctx: click.Context,
    path: tuple[Path, ...],
    repo: bool,
    event: str,
    emit: str,
    rules: str,
    max_files: int,
    force: bool,
    escalate_on: str | None,
    config: Path,
    output_dir: Path | None,
) -> None:
    """Review code and generate documentation.

    Examples:

        # File-level review (default)
        memdocs review --path src/payments/charge.py --on pr

        # Module-level review
        memdocs review --path src/payments/** --on release

        # Repository-wide (with force)
        memdocs review --repo . --force
    """
    start_time = time.time()

    try:
        # Load configuration
        doc_config = load_config(config)

        # Override config with CLI args
        if max_files:
            doc_config.policies.max_files_without_force = max_files
        if escalate_on:
            doc_config.policies.escalate_on = escalate_on.split(",")
        if output_dir:
            doc_config.outputs.docs_dir = output_dir / "docs"
            doc_config.outputs.memory_dir = output_dir / "memory"

        # Determine paths
        if repo:
            paths = [Path(".")]
        elif path:
            paths = list(path)
        else:
            out.error("Must specify --path or --repo")
            sys.exit(1)

        out.print_header("MemDocs Review")
        out.step(f"Reviewing {len(paths)} path(s) for [cyan]{event}[/cyan] event")

        # Extract context
        with out.spinner(f"Extracting context from {len(paths)} path(s)"):
            extractor = Extractor(repo_path=Path("."))
            context = extractor.extract_context(paths)

        out.success(f"Extracted context from {len(context.files)} files")

        # Apply policy
        out.step("Determining scope")
        policy_engine = PolicyEngine(doc_config)
        scope = policy_engine.determine_scope(paths, context, force=force)

        # Show warnings
        warnings = policy_engine.validate_scope(scope)
        for warning in warnings:
            out.warning(warning)

        scope_status = "escalated" if scope.escalated else "as requested"
        out.info(f"Scope: [bold]{scope.level.value}[/bold] ({scope_status})")

        # PII/PHI guard
        guard = create_guard_from_config(
            mode=doc_config.privacy.phi_mode,
            scrub_types=doc_config.privacy.scrub,
            audit_dir=doc_config.outputs.docs_dir.parent / "audit",
        )

        # Summarize with AI
        with out.spinner("Generating documentation with Claude Sonnet 4.5"):
            summarizer = Summarizer(model=doc_config.ai.model)
            doc_index, markdown_summary = summarizer.summarize(context, scope)

        out.success("Documentation generated")

        # Redact PII/PHI from outputs
        out.step("Checking for PII/PHI")
        redacted_markdown, markdown_redactions = guard.redact(
            markdown_summary, doc_id=doc_index.commit or "unknown"
        )

        if markdown_redactions:
            out.warning(f"Redacted {len(markdown_redactions)} PII/PHI items from outputs")

        # Write outputs
        outputs = {}

        if emit in ("docs", "both"):
            out.step("Writing documentation files")
            outputs.update(_write_docs(doc_config, doc_index, redacted_markdown, context))

        if emit in ("memory", "both"):
            out.step("Writing memory files")
            outputs.update(_write_memory(doc_config, doc_index))

            # Generate embeddings (optional, v1.1)
            try:
                indexer = MemoryIndexer(
                    memory_dir=doc_config.outputs.memory_dir, use_embeddings=True
                )

                if indexer.use_embeddings:
                    with out.spinner("Generating embeddings for semantic search"):
                        index_stats = indexer.index_document(doc_index, redacted_markdown)

                    if index_stats["indexed"]:
                        out.success(
                            f"Indexed {index_stats['chunks']} chunks, {index_stats['embeddings_generated']} embeddings"
                        )
                    else:
                        out.warning(
                            "Embeddings disabled (install with: pip install 'memdocs[embeddings]')"
                        )
                else:
                    out.info("Skipping embeddings (optional dependency not installed)")
            except Exception as embed_error:
                out.warning(f"Embedding generation failed: {embed_error}")
                # Continue anyway - embeddings are optional

        # Build result
        duration_ms = (time.time() - start_time) * 1000

        # Print summary
        out.print_rule("Review Complete", style="green")
        out.success(f"Finished in {out.format_duration(duration_ms)}")

        # Outputs table
        if outputs:
            out.console.print()
            table = out.create_table(title="Generated Files", show_lines=True)
            table.add_column("Format", style="cyan")
            table.add_column("Path", style="green")

            for format_name, file_path in outputs.items():
                table.add_row(format_name, str(file_path))

            out.print_table(table)

        # Audit summary
        audit_summary = guard.get_audit_summary()
        if audit_summary["total_redactions"] > 0:
            out.console.print()
            out.warning(f"Privacy redactions: {audit_summary['total_redactions']}")
            for redaction_type, count in audit_summary["by_type"].items():
                out.print_key_value(f"  {redaction_type}", count, key_style="yellow")

    except Exception as e:
        out.console.print()
        out.error(f"Review failed: {e}")
        if ctx.obj.get("debug"):
            raise
        sys.exit(1)


def _write_docs(
    config: DocIntConfig,
    doc_index: Any,
    markdown: str,
    context: Any,
) -> dict[str, Path]:
    """Write documentation outputs.

    Args:
        config: Configuration
        doc_index: Document index
        markdown: Markdown summary
        context: Extracted context

    Returns:
        Dict of format -> file path
    """
    outputs = {}
    docs_dir = config.outputs.docs_dir
    docs_dir.mkdir(parents=True, exist_ok=True)

    # index.json
    if "json" in config.outputs.formats:
        index_path = docs_dir / "index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(doc_index.model_dump(mode="json"), f, indent=2, default=str)
        outputs["index.json"] = index_path

    # summary.md
    if "markdown" in config.outputs.formats:
        summary_path = docs_dir / "summary.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        outputs["summary.md"] = summary_path

    # symbols.yaml
    if "yaml" in config.outputs.formats:
        symbols_path = docs_dir / "symbols.yaml"
        all_symbols = [symbol for file_ctx in context.files for symbol in file_ctx.symbols]
        symbols_output = SymbolsOutput(symbols=all_symbols)
        with open(symbols_path, "w", encoding="utf-8") as f:
            yaml.dump(symbols_output.model_dump(mode="json"), f, default_flow_style=False)
        outputs["symbols.yaml"] = symbols_path

    return outputs


def _write_memory(config: DocIntConfig, doc_index: Any) -> dict[str, Path]:
    """Write memory outputs (embeddings, graph).

    Args:
        config: Configuration
        doc_index: Document index

    Returns:
        Dict of format -> file path
    """
    outputs = {}
    memory_dir = config.outputs.memory_dir
    memory_dir.mkdir(parents=True, exist_ok=True)

    # graph.json (commit → feature → files relationships)
    graph_path = memory_dir / "graph.json"
    graph = {
        "commit": doc_index.commit,
        "features": [{"id": f.id, "title": f.title} for f in doc_index.features],
        "files": [str(f) for f in doc_index.refs.files_changed],
        "timestamp": doc_index.timestamp.isoformat(),
    }
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    outputs["graph.json"] = graph_path

    # embeddings.idx (placeholder for v1.1)
    # TODO: Implement embedding generation

    return outputs


@main.command()
@click.argument("format", type=click.Choice(["cursor", "claude", "continue"]))
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--docs-dir",
    type=click.Path(path_type=Path),
    default=Path(".memdocs/docs"),
    help="Documentation directory",
)
@click.option(
    "--include-symbols/--no-symbols",
    default=True,
    help="Include code symbols in export",
)
def export(format: str, output: Path | None, docs_dir: Path, include_symbols: bool) -> None:
    """Export docs for AI assistants.

    Examples:

        memdocs export cursor --output .cursorrules
        memdocs export claude --output .claude-context.md
        memdocs export continue
    """
    out.print_header("MemDocs Export")
    out.step(f"Exporting to [cyan]{format}[/cyan] format")

    if not docs_dir.exists():
        out.error(f"Docs directory not found: {docs_dir}")
        out.info("Run [cyan]memdocs review[/cyan] first to generate docs")
        sys.exit(1)

    # Load summary
    summary_path = docs_dir / "summary.md"
    if not summary_path.exists():
        out.error("summary.md not found")
        out.info("Run [cyan]memdocs review[/cyan] first")
        sys.exit(1)

    summary = summary_path.read_text(encoding="utf-8")

    # Load symbols if requested
    symbols_section = ""
    if include_symbols:
        symbols_path = docs_dir / "symbols.yaml"
        if symbols_path.exists():
            with open(symbols_path, encoding="utf-8") as f:
                symbols_data = yaml.safe_load(f)

            if symbols_data and "symbols" in symbols_data:
                symbols_section = "\n\n## 🗺️ Code Map\n\n"
                symbols_by_file = {}

                # Group symbols by file
                for symbol in symbols_data["symbols"]:
                    file_path = str(symbol.get("file", "unknown"))
                    if file_path not in symbols_by_file:
                        symbols_by_file[file_path] = []
                    symbols_by_file[file_path].append(symbol)

                # Format by file
                for file_path, symbols in sorted(symbols_by_file.items()):
                    symbols_section += f"\n### {file_path}\n\n"
                    for sym in symbols:
                        kind = sym.get("kind", "unknown")
                        name = sym.get("name", "unknown")
                        line = sym.get("line", 0)
                        sig = sym.get("signature", "")

                        if sig:
                            symbols_section += (
                                f"- **{kind}** `{name}` (line {line})\n  ```\n  {sig}\n  ```\n"
                            )
                        else:
                            symbols_section += f"- **{kind}** `{name}` (line {line})\n"

    # Load graph
    graph_section = ""
    graph_path = docs_dir.parent / "memory" / "graph.json"
    if graph_path.exists():
        with open(graph_path, encoding="utf-8") as f:
            graph_data = json.load(f)

        graph_section = "\n\n## 🔗 Memory Graph\n\n"
        if "features" in graph_data:
            graph_section += "**Recent Features:**\n"
            for feature in graph_data.get("features", [])[:5]:
                graph_section += f"- {feature.get('title', 'Untitled')}\n"

    # Format based on target
    if format == "cursor":
        output_path = output or Path(".cursorrules")
        from datetime import datetime

        content = f"""# Project Memory (Auto-generated by doc-intelligence)
# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📚 Documentation

{summary}
{symbols_section}
{graph_section}

---

## 💡 Tips for Cursor

- Ask: "What does [function_name] do?"
- Ask: "Where is [feature] implemented?"
- Ask: "Explain the architecture"
- Reference symbols by file:line (e.g., src/auth/jwt.py:33)

---

*Generated by [doc-intelligence](https://github.com/deepstudyai/memdocs)*
*Regenerate with: `memdocs export cursor`*
"""

    elif format == "continue":
        output_path = output or Path(".continue/context.md")
        content = f"""# Project Context

{summary}
{symbols_section}
{graph_section}
"""

    else:  # claude
        output_path = output or Path(".claude-context.md")
        content = f"""{summary}
{symbols_section}
{graph_section}
"""

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with out.spinner(f"Writing {format} export"):
        output_path.write_text(content, encoding="utf-8")

    out.print_rule("Export Complete", style="green")
    out.success(f"Exported to [green]{output_path}[/green]")

    if include_symbols and symbols_section:
        symbol_count = len(symbols_data.get("symbols", []))
        out.info(f"Included {symbol_count} code symbols")


@main.command()
@click.argument("query", type=str)
@click.option(
    "--k",
    type=int,
    default=5,
    help="Number of results to return",
)
@click.option(
    "--memory-dir",
    type=click.Path(path_type=Path),
    default=Path(".memdocs/memory"),
    help="Memory directory",
)
def query(query: str, k: int, memory_dir: Path) -> None:
    """Query project memory using natural language.

    Examples:

        memdocs query "How does authentication work?"
        memdocs query "payment timeout implementation" --k 10
    """
    try:
        # Initialize indexer
        out.print_header("MemDocs Query")
        out.step(f'Searching for: [cyan]"{query}"[/cyan]')

        indexer = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)

        if not indexer.use_embeddings:
            out.error("Embeddings not available")
            out.info("Install with: [cyan]pip install 'memdocs[embeddings]'[/cyan]")
            sys.exit(1)

        # Check if index exists
        stats = indexer.get_stats()
        if stats["total"] == 0:
            out.warning("Memory index is empty")
            out.info("Run [cyan]memdocs review[/cyan] first to generate docs")
            sys.exit(1)

        out.info(f"Index contains {stats['active']} active entries")

        # Query memory
        with out.spinner("Searching memory"):
            results = indexer.query_memory(query, k=k)

        if not results:
            out.warning("No results found")
            return

        # Display results in table
        out.print_rule(f"Found {len(results)} Results", style="green")
        out.console.print()

        table = out.create_table(title="Search Results", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Score", style="cyan", width=8)
        table.add_column("Features", style="green")
        table.add_column("Files", style="blue")

        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            score = result["score"]
            features = ", ".join(meta.get("features", ["Untitled"]))[:50]
            files = ", ".join(meta.get("file_paths", []))[:60]

            table.add_row(str(i), f"{score:.3f}", features, files)

        out.print_table(table)

        # Show preview of top result
        if results:
            out.console.print()
            top_result = results[0]
            preview = top_result["metadata"].get("chunk_text", "No preview")[:200]
            out.panel(preview, title="Top Result Preview", style="green")

    except Exception as e:
        out.console.print()
        out.error(f"Query failed: {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--docs-dir",
    type=click.Path(path_type=Path),
    default=Path(".memdocs/docs"),
    help="Documentation directory",
)
@click.option(
    "--memory-dir",
    type=click.Path(path_type=Path),
    default=Path(".memdocs/memory"),
    help="Memory directory",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def stats(docs_dir: Path, memory_dir: Path, format: str) -> None:
    """Show memory and documentation statistics.

    Examples:

        memdocs stats
        memdocs stats --format json
    """
    try:
        out.print_header("MemDocs Statistics")

        # Docs stats
        docs_stats = {
            "exists": docs_dir.exists(),
            "total_files": 0,
            "formats": [],
        }

        if docs_dir.exists():
            docs_stats["total_files"] = len(list(docs_dir.rglob("*")))
            if (docs_dir / "index.json").exists():
                docs_stats["formats"].append("json")
            if (docs_dir / "summary.md").exists():
                docs_stats["formats"].append("markdown")
            if (docs_dir / "symbols.yaml").exists():
                docs_stats["formats"].append("yaml")

        # Memory stats
        memory_stats = {
            "exists": memory_dir.exists(),
            "embeddings": False,
            "graph": False,
        }

        if memory_dir.exists():
            memory_stats["embeddings"] = (memory_dir / "embeddings.json").exists()
            memory_stats["graph"] = (memory_dir / "graph.json").exists()

        # Embedding index stats
        index_stats = None
        try:
            indexer = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)
            if indexer.use_embeddings:
                index_stats = indexer.get_stats()
        except Exception:
            pass

        if format == "json":
            # JSON output
            output = {
                "docs": docs_stats,
                "memory": memory_stats,
                "index": index_stats,
            }
            out.console.print_json(data=output)
        else:
            # Table output
            out.console.print()

            # Documentation table
            docs_table = out.create_table(title="Documentation", show_lines=True)
            docs_table.add_column("Property", style="cyan")
            docs_table.add_column("Value", style="green")

            docs_table.add_row("Directory", str(docs_dir))
            docs_table.add_row("Exists", "✓" if docs_stats["exists"] else "✗")
            docs_table.add_row("Total Files", str(docs_stats["total_files"]))
            docs_table.add_row("Formats", ", ".join(docs_stats["formats"]) or "None")

            out.print_table(docs_table)
            out.console.print()

            # Memory table
            memory_table = out.create_table(title="Memory", show_lines=True)
            memory_table.add_column("Property", style="cyan")
            memory_table.add_column("Value", style="green")

            memory_table.add_row("Directory", str(memory_dir))
            memory_table.add_row("Exists", "✓" if memory_stats["exists"] else "✗")
            memory_table.add_row("Embeddings", "✓" if memory_stats["embeddings"] else "✗")
            memory_table.add_row("Graph", "✓" if memory_stats["graph"] else "✗")

            out.print_table(memory_table)

            # Index stats
            if index_stats:
                out.console.print()
                index_table = out.create_table(title="Embedding Index", show_lines=True)
                index_table.add_column("Property", style="cyan")
                index_table.add_column("Value", style="green")

                index_table.add_row("Total Entries", str(index_stats.get("total", 0)))
                index_table.add_row("Active Entries", str(index_stats.get("active", 0)))
                index_table.add_row("Dimensions", str(index_stats.get("dimensions", 0)))

                out.print_table(index_table)

    except Exception as e:
        out.console.print()
        out.error(f"Stats failed: {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--older-than",
    type=str,
    default="90d",
    help="Cleanup items older than (e.g., 90d, 1y)",
)
@click.option(
    "--memory-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path(".memdocs/memory"),
    help="Memory directory",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without deleting",
)
def cleanup(older_than: str, memory_dir: Path, dry_run: bool) -> None:
    """Cleanup old embeddings and memory data.

    Examples:

        memdocs cleanup --older-than 90d
        memdocs cleanup --older-than 1y --dry-run
    """
    out.warning("Cleanup not yet implemented (v2.1 feature)")
    out.info(f"Would delete items older than: {older_than}")


if __name__ == "__main__":
    main()

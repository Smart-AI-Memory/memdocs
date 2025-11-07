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

from memdocs import __version__
from memdocs.extract import Extractor
from memdocs.guard import create_guard_from_config
from memdocs.index import MemoryIndexer
from memdocs.policy import PolicyEngine
from memdocs.schemas import DocIntConfig, EventType, ReviewResult, ScopeLevel, SymbolsOutput
from memdocs.summarize import Summarizer


def load_config(config_path: Path) -> DocIntConfig:
    """Load configuration from file.

    Args:
        config_path: Path to config file

    Returns:
        Loaded configuration
    """
    if not config_path.exists():
        return DocIntConfig()  # Use defaults

    with open(config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    return DocIntConfig(**config_dict)


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Doc-Intelligence: Generate machine-friendly docs for AI assistants."""
    ctx.ensure_object(dict)


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
            click.echo("Error: Must specify --path or --repo", err=True)
            sys.exit(1)

        click.echo(f"🔍 Reviewing {len(paths)} path(s) for {event} event...")

        # Extract context
        extractor = Extractor(repo_path=Path("."))
        context = extractor.extract_context(paths)

        click.echo(f"📊 Extracted context from {len(context.files)} files")

        # Apply policy
        policy_engine = PolicyEngine(doc_config)
        scope = policy_engine.determine_scope(paths, context, force=force)

        # Show warnings
        warnings = policy_engine.validate_scope(scope)
        for warning in warnings:
            click.echo(f"⚠️  {warning}", err=True)

        click.echo(
            f"📏 Scope: {scope.level.value} "
            f"({'escalated' if scope.escalated else 'as requested'})"
        )

        # PII/PHI guard
        guard = create_guard_from_config(
            mode=doc_config.privacy.phi_mode,
            scrub_types=doc_config.privacy.scrub,
            audit_dir=doc_config.outputs.docs_dir.parent / "audit",
        )

        # Summarize with AI
        click.echo("🤖 Generating documentation with AI...")
        summarizer = Summarizer(model=doc_config.ai.model)
        doc_index, markdown_summary = summarizer.summarize(context, scope)

        # Redact PII/PHI from outputs
        redacted_markdown, markdown_redactions = guard.redact(
            markdown_summary, doc_id=doc_index.commit or "unknown"
        )

        if markdown_redactions:
            click.echo(
                f"🔒 Redacted {len(markdown_redactions)} PII/PHI items from outputs"
            )

        # Write outputs
        outputs = {}

        if emit in ("docs", "both"):
            outputs.update(_write_docs(doc_config, doc_index, redacted_markdown, context))

        if emit in ("memory", "both"):
            outputs.update(_write_memory(doc_config, doc_index))

            # Generate embeddings (optional, v1.1)
            try:
                click.echo("🔮 Generating embeddings for semantic search...")
                indexer = MemoryIndexer(
                    memory_dir=doc_config.outputs.memory_dir,
                    use_embeddings=True
                )

                if indexer.use_embeddings:
                    index_stats = indexer.index_document(doc_index, redacted_markdown)
                    if index_stats["indexed"]:
                        click.echo(f"✅ Indexed {index_stats['chunks']} chunks, {index_stats['embeddings_generated']} embeddings")
                    else:
                        click.echo("⚠️  Embeddings disabled (install with: pip install 'memdocs[embeddings]')")
                else:
                    click.echo("ℹ️  Skipping embeddings (optional dependency not installed)")
            except Exception as embed_error:
                click.echo(f"⚠️  Embedding generation failed: {embed_error}", err=True)
                # Continue anyway - embeddings are optional

        # Build result
        duration_ms = (time.time() - start_time) * 1000

        result = ReviewResult(
            success=True,
            scope=scope,
            outputs=outputs,
            warnings=warnings,
            duration_ms=duration_ms,
        )

        # Print summary
        click.echo("\n✅ Review complete!")
        click.echo(f"⏱️  Duration: {duration_ms:.0f}ms")
        click.echo("\n📁 Outputs:")
        for format_name, file_path in outputs.items():
            click.echo(f"  - {format_name}: {file_path}")

        # Audit summary
        audit_summary = guard.get_audit_summary()
        if audit_summary["total_redactions"] > 0:
            click.echo(f"\n🔒 Redactions: {audit_summary['total_redactions']}")
            for redaction_type, count in audit_summary["by_type"].items():
                click.echo(f"  - {redaction_type}: {count}")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
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
        "features": [
            {"id": f.id, "title": f.title}
            for f in doc_index.features
        ],
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
    type=click.Path(exists=True, path_type=Path),
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
    if not docs_dir.exists():
        click.echo(f"Error: Docs directory not found: {docs_dir}", err=True)
        sys.exit(1)

    # Load summary
    summary_path = docs_dir / "summary.md"
    if not summary_path.exists():
        click.echo("Error: summary.md not found. Run 'memdocs review' first.", err=True)
        sys.exit(1)

    summary = summary_path.read_text(encoding="utf-8")

    # Load symbols if requested
    symbols_section = ""
    if include_symbols:
        symbols_path = docs_dir / "symbols.yaml"
        if symbols_path.exists():
            with open(symbols_path, "r", encoding="utf-8") as f:
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
                            symbols_section += f"- **{kind}** `{name}` (line {line})\n  ```\n  {sig}\n  ```\n"
                        else:
                            symbols_section += f"- **{kind}** `{name}` (line {line})\n"

    # Load graph
    graph_section = ""
    graph_path = docs_dir.parent / "memory" / "graph.json"
    if graph_path.exists():
        with open(graph_path, "r", encoding="utf-8") as f:
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

    output_path.write_text(content, encoding="utf-8")
    click.echo(f"✅ Exported to {output_path}")

    if include_symbols and symbols_section:
        symbol_count = len(symbols_data.get("symbols", []))
        click.echo(f"   Included {symbol_count} code symbols")


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
    type=click.Path(exists=True, path_type=Path),
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
        indexer = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)

        if not indexer.use_embeddings:
            click.echo(
                "❌ Embeddings not available. Install with: pip install 'memdocs[embeddings]'",
                err=True,
            )
            sys.exit(1)

        # Check if index exists
        stats = indexer.get_stats()
        if stats["total"] == 0:
            click.echo("⚠️  Memory index is empty. Run 'memdocs review' first to generate docs.")
            sys.exit(1)

        click.echo(f"🔍 Searching memory for: \"{query}\"")
        click.echo(f"📊 Index stats: {stats['active']} active entries\n")

        # Query memory
        results = indexer.query_memory(query, k=k)

        if not results:
            click.echo("No results found.")
            return

        # Display results
        click.echo(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            score = result["score"]

            click.echo(f"{i}. [{score:.3f}] {', '.join(meta.get('features', ['Untitled']))}")
            click.echo(f"   Files: {', '.join(meta.get('file_paths', []))}")
            click.echo(f"   Preview: {meta.get('chunk_text', 'No preview')[:100]}...")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
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
    click.echo(f"🗑️  Cleanup not yet implemented (v1.1 feature)")
    click.echo(f"Would delete items older than: {older_than}")


if __name__ == "__main__":
    main()

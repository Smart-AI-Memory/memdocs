"""
Review command - Review code and generate documentation.
"""

import sys
import time
from pathlib import Path

import click

from memdocs import cli_output as out
from memdocs.cli_modules.utils import _write_docs, _write_memory, load_config
from memdocs.guard import create_guard_from_config
from memdocs.security import ConfigValidator


def _get_cli_classes():
    """Lazy import to avoid circular dependency."""
    from memdocs import cli
    return cli.Extractor, cli.MemoryIndexer, cli.PolicyEngine, cli.Summarizer


@click.command()
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

        # Override config with CLI args (with validation)
        if max_files:
            validated_max_files = ConfigValidator.validate_positive_int(
                max_files, "max_files"
            )
            doc_config.policies.max_files_without_force = validated_max_files
        if escalate_on:
            # Validate and sanitize escalation rules
            rules = [rule.strip() for rule in escalate_on.split(",") if rule.strip()]
            doc_config.policies.escalate_on = rules
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

        # Get CLI classes (lazy import)
        Extractor, MemoryIndexer, PolicyEngine, Summarizer = _get_cli_classes()

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
            summarizer = Summarizer(model=doc_config.ai.model, max_tokens=doc_config.ai.max_tokens)
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

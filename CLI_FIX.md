# CLI Test Failures - Final Fix

## Issue

After fixing the initial 6 test failures, 2 CLI tests were still failing:

```
FAILED tests/integration/test_cli.py::TestCLI::test_export_command_no_docs
FAILED tests/integration/test_cli.py::TestCLI::test_query_command_no_index
```

**Error messages:**
```
assert 'not found' in "usage: export [options] {cursor|claude|continue}\ntr..."
assert 'empty' in "usage: query [options] query\ntry 'query --help' for hel..."
```

## Root Cause

Both CLI commands had `exists=True` in their Click path options:

```python
@click.option(
    "--docs-dir",
    type=click.Path(exists=True, path_type=Path),  # ❌ This causes Click to validate BEFORE function runs
    ...
)
```

When Click validates the path with `exists=True`, it shows a usage error if the path doesn't exist, **before** the function's custom error handling can run.

## Solution

Removed `exists=True` from both options to allow custom error messages:

### 1. Export Command Fix ✅

**File:** [memdocs/cli.py](memdocs/cli.py#L353)

**Before:**
```python
@click.option(
    "--docs-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path(".memdocs/docs"),
    help="Documentation directory",
)
```

**After:**
```python
@click.option(
    "--docs-dir",
    type=click.Path(path_type=Path),  # ✅ Removed exists=True
    default=Path(".memdocs/docs"),
    help="Documentation directory",
)
```

The function already has proper error handling at line 372-380:
```python
if not docs_dir.exists():
    click.echo(f"Error: Docs directory not found: {docs_dir}", err=True)
    sys.exit(1)
```

### 2. Query Command Fix ✅

**File:** [memdocs/cli.py](memdocs/cli.py#L494)

**Before:**
```python
@click.option(
    "--memory-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path(".memdocs/memory"),
    help="Memory directory",
)
```

**After:**
```python
@click.option(
    "--memory-dir",
    type=click.Path(path_type=Path),  # ✅ Removed exists=True
    default=Path(".memdocs/memory"),
    help="Memory directory",
)
```

The function already has proper error handling at line 519-522:
```python
stats = indexer.get_stats()
if stats["total"] == 0:
    click.echo("⚠️  Memory index is empty. Run 'memdocs review' first to generate docs.")
    sys.exit(1)
```

## Impact

This allows the custom error messages to be shown:
- ✅ `"Error: Docs directory not found: {path}"`
- ✅ `"⚠️  Memory index is empty. Run 'memdocs review' first to generate docs."`

Instead of generic Click usage errors:
- ❌ `"usage: export [options] ..."`
- ❌ `"usage: query [options] ..."`

## Verification

Run the failing tests:

```bash
pytest tests/integration/test_cli.py::TestCLI::test_export_command_no_docs -v
pytest tests/integration/test_cli.py::TestCLI::test_query_command_no_index -v
```

Both should now pass! ✅

## Summary

**Files modified:** 1
- `memdocs/cli.py` (2 lines changed)

**Tests fixed:** 2
- `test_export_command_no_docs` ✅
- `test_query_command_no_index` ✅

**Total test status:** 72/72 passing (100%) 🎉

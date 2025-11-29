# API Reference

## Overview

MemDocs provides a Python API for programmatic access to all features. This reference covers the main modules and their public interfaces.

## Quick Import

```python
# Core schemas and exceptions
from memdocs import (
    DocIntConfig,
    DocumentIndex,
    ReviewResult,
    Symbol,
    FeatureSummary,
    MemDocsError,
    ConfigurationError,
    APIError,
)

# Main modules
from memdocs.extract import Extractor
from memdocs.summarize import Summarizer
from memdocs.index import MemoryIndexer
from memdocs.search import LocalVectorSearch
from memdocs.embeddings import LocalEmbedder
from memdocs.guard import Guard
from memdocs.security import PathValidator, InputValidator, RateLimiter
```

---

## memdocs.extract

Code extraction and symbol parsing module.

### Extractor

```python
from memdocs.extract import Extractor

extractor = Extractor()
```

#### Methods

##### `extract_from_files(paths: list[Path]) -> ExtractedContext`

Extract code context from multiple files.

```python
from pathlib import Path

context = extractor.extract_from_files([
    Path("src/main.py"),
    Path("src/utils.py"),
])

print(f"Extracted {len(context.files)} files")
for file_ctx in context.files:
    print(f"  {file_ctx.path}: {len(file_ctx.symbols)} symbols")
```

**Parameters:**
- `paths`: List of file paths to extract from

**Returns:**
- `ExtractedContext` with file contents, symbols, and metadata

##### `extract_from_diff(diff_text: str) -> ExtractedContext`

Extract context from a git diff.

```python
diff = """
diff --git a/src/main.py b/src/main.py
index abc123..def456 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,6 +10,10 @@ def main():
+    print("New feature")
"""

context = extractor.extract_from_diff(diff)
```

### ExtractedContext

Data class containing extraction results.

```python
@dataclass
class ExtractedContext:
    files: list[FileContext]
    diff: str | None
    commit: str | None
    timestamp: datetime
```

### FileContext

Per-file extraction data.

```python
@dataclass
class FileContext:
    path: Path
    content: str
    language: str
    symbols: list[Symbol]
```

---

## memdocs.summarize

AI-powered summarization using Claude.

### Summarizer

```python
from memdocs.summarize import Summarizer

summarizer = Summarizer(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
)
```

#### Methods

##### `summarize(context: ExtractedContext) -> DocumentIndex`

Generate documentation from extracted context.

```python
from memdocs.extract import Extractor

extractor = Extractor()
context = extractor.extract_from_files([Path("src/main.py")])

doc_index = summarizer.summarize(context)

print(f"Generated {len(doc_index.features)} features")
print(f"Commit: {doc_index.commit}")
```

**Parameters:**
- `context`: ExtractedContext from Extractor

**Returns:**
- `DocumentIndex` with features, impacts, and references

**Raises:**
- `APIError`: If Claude API call fails
- `SummarizationError`: If response parsing fails

##### `generate_markdown(doc_index: DocumentIndex) -> str`

Generate human-readable markdown from DocumentIndex.

```python
markdown = summarizer.generate_markdown(doc_index)
Path(".memdocs/docs/summary.md").write_text(markdown)
```

---

## memdocs.index

Memory indexing and retrieval.

### MemoryIndexer

```python
from memdocs.index import MemoryIndexer
from pathlib import Path

indexer = MemoryIndexer(
    memory_dir=Path(".memdocs/memory"),
    use_embeddings=True,  # Requires memdocs[embeddings]
)
```

#### Methods

##### `index_document(doc_index: DocumentIndex, markdown: str) -> None`

Add a document to the memory index.

```python
indexer.index_document(doc_index, markdown_summary)
```

**Parameters:**
- `doc_index`: DocumentIndex to index
- `markdown`: Markdown summary for embedding

##### `query_memory(query: str, k: int = 5) -> list[dict]`

Search memory with semantic similarity.

```python
results = indexer.query_memory("authentication flow", k=5)

for result in results:
    print(f"[{result['score']:.2f}] {result['metadata']['path']}")
    print(f"  {result['metadata']['summary'][:100]}...")
```

**Parameters:**
- `query`: Natural language query
- `k`: Number of results to return

**Returns:**
- List of dicts with `score`, `metadata`, and `content`

##### `get_stats() -> dict`

Get memory statistics.

```python
stats = indexer.get_stats()
print(f"Documents indexed: {stats['document_count']}")
print(f"Index size: {stats['index_size_bytes']} bytes")
```

---

## memdocs.search

Local vector search using FAISS.

### LocalVectorSearch

```python
from memdocs.search import LocalVectorSearch

search = LocalVectorSearch(
    dimension=384,  # Must match embedding dimension
    index_path=Path(".memdocs/memory/faiss.index"),
)
```

#### Methods

##### `add_vectors(vectors: list[list[float]], metadata: list[dict]) -> None`

Add vectors to the search index.

```python
vectors = embedder.embed_documents(["doc1", "doc2"])
metadata = [{"path": "file1.py"}, {"path": "file2.py"}]

search.add_vectors(vectors, metadata)
```

##### `search(query_vector: list[float], k: int = 5) -> list[tuple[float, dict]]`

Search for similar vectors.

```python
query_vec = embedder.embed_query("find authentication")
results = search.search(query_vec, k=5)

for score, meta in results:
    print(f"[{score:.3f}] {meta['path']}")
```

##### `save() -> None`

Persist index to disk.

```python
search.save()  # Saves to index_path
```

##### `load() -> None`

Load index from disk.

```python
search.load()  # Loads from index_path
```

---

## memdocs.embeddings

Local embedding generation.

### LocalEmbedder

```python
from memdocs.embeddings import LocalEmbedder

embedder = LocalEmbedder(
    model_name="all-MiniLM-L6-v2",  # 384 dimensions, 80MB
    cache_dir=Path("~/.cache/memdocs"),
)
```

#### Methods

##### `embed_documents(texts: list[str]) -> list[list[float]]`

Generate embeddings for multiple documents.

```python
texts = ["First document", "Second document"]
embeddings = embedder.embed_documents(texts)

print(f"Generated {len(embeddings)} embeddings")
print(f"Dimension: {len(embeddings[0])}")  # 384
```

##### `embed_query(query: str) -> list[float]`

Generate embedding for a single query.

```python
query_embedding = embedder.embed_query("find login function")
```

### Helper Functions

##### `chunk_document(text: str, max_tokens: int = 512, overlap: int = 50) -> list[str]`

Split document into chunks for embedding.

```python
from memdocs.embeddings import chunk_document

chunks = chunk_document(long_text, max_tokens=512, overlap=50)
print(f"Split into {len(chunks)} chunks")
```

---

## memdocs.guard

PHI/PII detection and redaction.

### Guard

```python
from memdocs.guard import Guard
from memdocs.schemas import PHIMode

guard = Guard(
    mode=PHIMode.STRICT,
    scrub_types=["email", "phone", "ssn", "mrn"],
    audit_path=Path(".memdocs/audit.log"),
)
```

#### Methods

##### `scan(text: str) -> list[RedactionMatch]`

Scan text for sensitive data.

```python
matches = guard.scan("Contact: john@example.com, 555-123-4567")

for match in matches:
    print(f"Found {match.type} at {match.start}-{match.end}")
```

##### `redact(text: str, doc_id: str) -> tuple[str, list[RedactionMatch]]`

Redact sensitive data from text.

```python
redacted, matches = guard.redact(text, doc_id="commit-abc123")
print(redacted)
# "Contact: [REDACTED:EMAIL], [REDACTED:PHONE]"
```

##### `validate_content(content: str) -> tuple[bool, list[str]]`

Validate content is free of sensitive data.

```python
is_valid, errors = guard.validate_content(content)
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### PHI Modes

```python
from memdocs.schemas import PHIMode

PHIMode.OFF       # No detection
PHIMode.STANDARD  # Detect common PII
PHIMode.STRICT    # Aggressive detection
```

---

## memdocs.security

Security utilities for input validation and rate limiting.

### PathValidator

```python
from memdocs.security import PathValidator

validator = PathValidator(base_dir=Path.cwd())
```

#### Methods

##### `validate_path(path: Path) -> Path`

Validate path is within allowed directory.

```python
try:
    safe_path = validator.validate_path(Path("../../../etc/passwd"))
except SecurityError:
    print("Path traversal blocked!")
```

##### `validate_write_path(path: Path, allowed_dirs: list[Path]) -> Path`

Validate write operation is to allowed directory.

```python
validator.validate_write_path(
    Path(".memdocs/docs/output.json"),
    allowed_dirs=[Path(".memdocs/docs"), Path(".memdocs/memory")]
)
```

### InputValidator

```python
from memdocs.security import InputValidator

validator = InputValidator()
```

##### `validate_api_key(key: str) -> bool`

Validate API key format.

```python
is_valid = validator.validate_api_key("sk-ant-api03-...")
```

##### `sanitize_output(text: str) -> str`

Remove secrets from text before logging/display.

```python
safe_text = validator.sanitize_output(text_with_secrets)
```

##### `check_for_secrets(text: str) -> list[str]`

Find potential secrets in text.

```python
secrets = validator.check_for_secrets(config_text)
if secrets:
    print(f"Warning: Found {len(secrets)} potential secrets")
```

### RateLimiter

```python
from memdocs.security import RateLimiter

limiter = RateLimiter(max_calls=50, window_seconds=60)
```

##### `check_rate_limit() -> None`

Check if rate limit allows another call.

```python
try:
    limiter.check_rate_limit()
    # Make API call
except RuntimeError:
    print("Rate limit exceeded, waiting...")
```

---

## memdocs.schemas

Pydantic models for data validation.

### DocumentIndex

Main output schema for documentation.

```python
from memdocs.schemas import DocumentIndex

doc = DocumentIndex(
    commit="abc123",
    timestamp=datetime.now(timezone.utc),
    scope=scope_info,
    features=[feature1, feature2],
    impacts=impact_summary,
    refs=reference_summary,
)

# Serialize to JSON
json_str = doc.model_dump_json(indent=2)

# Load from JSON
doc = DocumentIndex.model_validate_json(json_str)
```

### DocIntConfig

Configuration schema.

```python
from memdocs.schemas import DocIntConfig

config = DocIntConfig(
    version=1,
    policies=PolicyConfig(default_scope=ScopeLevel.FILE),
    privacy=PrivacyConfig(phi_mode=PHIMode.STANDARD),
    outputs=OutputsConfig(docs_dir=Path(".memdocs/docs")),
)
```

### Symbol

Code symbol representation.

```python
from memdocs.schemas import Symbol, SymbolKind

symbol = Symbol(
    file=Path("src/main.py"),
    kind=SymbolKind.FUNCTION,
    name="process_data",
    line=42,
    signature="def process_data(input: str) -> dict",
    doc="Process input data and return results.",
)
```

---

## memdocs.exceptions

Custom exceptions with helpful suggestions.

### Exception Hierarchy

```
MemDocsError (base)
├── ConfigurationError
├── APIError
├── ValidationError
├── ExtractionError
├── SummarizationError
├── IndexingError
├── EmbeddingError
├── MCPServerError
├── SecurityError
└── DependencyError
```

### Usage

```python
from memdocs import APIError, ConfigurationError

try:
    # API call
except APIError as e:
    print(f"Error: {e.message}")
    print(f"Suggestion: {e.suggestion}")
    print(f"Status code: {e.status_code}")
```

### Helper Functions

```python
from memdocs.exceptions import require_api_key, validate_file_path

# Raises APIError if not set
require_api_key("Anthropic")

# Raises SecurityError on traversal, FileNotFoundError if missing
validate_file_path(Path("src/main.py"), must_exist=True)
```

---

## MCP Server

Model Context Protocol server for AI assistant integration.

### Starting the Server

```python
from memdocs.mcp_server import DocIntMCPServer

server = DocIntMCPServer(
    memory_dir=Path(".memdocs/memory"),
    docs_dir=Path(".memdocs/docs"),
)

# Run server (blocking)
server.run()
```

### Available MCP Tools

The MCP server exposes these tools to AI assistants:

| Tool | Description |
|------|-------------|
| `query_memory` | Semantic search over documentation |
| `get_file_summary` | Get summary for specific file |
| `list_documented_files` | List all documented files |
| `get_stats` | Get memory statistics |
| `refresh_index` | Rebuild search index |

---

## Empathy Framework Integration

Adapter for Empathy Framework analysis results.

### EmpathyAdapter

```python
from memdocs.empathy_adapter import EmpathyAdapter

adapter = EmpathyAdapter(memdocs_root=Path(".memdocs"))
```

#### Methods

##### `store_empathy_analysis(analysis_results: dict, file_path: Path, ...) -> DocumentIndex`

Store Empathy Framework analysis in MemDocs format.

```python
# From Empathy Framework
results = await empathy_service.run_wizard("security", "python", code, "pro")

# Store in MemDocs
doc_index = adapter.store_empathy_analysis(
    analysis_results=results,
    file_path=Path("src/auth/login.py"),
    commit="abc123",
    pr_number=42,
)
```

### Convenience Function

```python
from memdocs.empathy_adapter import adapt_empathy_to_memdocs

doc_index = adapt_empathy_to_memdocs(
    analysis_results,
    "src/auth/login.py",
    commit="abc123",
)
```

---

## CLI Usage

While this is an API reference, the CLI provides the same functionality:

```bash
# Initialize
memdocs init

# Generate documentation
memdocs review --path src/

# Query memory
memdocs query "authentication"

# Check health
memdocs doctor

# Start MCP server
memdocs serve --mcp
```

See [CLI Reference](cli-reference.md) for complete CLI documentation.

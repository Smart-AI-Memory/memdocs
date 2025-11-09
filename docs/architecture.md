# Architecture

Deep dive into how MemDocs works under the hood.

## Overview

MemDocs is a **git-native AI memory system** that generates structured, machine-readable documentation from your codebase. It combines static code analysis, AI-powered summarization, and vector embeddings to create persistent context for AI assistants.

**Core principles:**
- **Git-native**: All memory is version-controlled and committed
- **Offline-first**: No cloud services required for retrieval
- **Cost-efficient**: Only pay for generation, not storage or retrieval
- **Team-shared**: Everyone gets the same AI context

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                     (CLI / Python API)                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Command Layer                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  init    │  review  │  query   │  export  │  stats   │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Core Services                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Extractor  │  Summarizer  │  Search  │  Embeddings   │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────┬───────────────────────────────┬───────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│   External Services     │   │      Storage Layer              │
│  ┌──────────────────┐   │   │  ┌────────────────────────┐    │
│  │ Claude Sonnet 4.5│   │   │  │  .memdocs/             │    │
│  │ (Anthropic API)  │   │   │  │  ├── docs/             │    │
│  └──────────────────┘   │   │  │  │   ├── index.json    │    │
│                         │   │  │  │   ├── symbols.yaml  │    │
│                         │   │  │  │   └── summary.md    │    │
│                         │   │  │  └── memory/           │    │
│                         │   │  │      ├── graph.json    │    │
│                         │   │  │      ├── faiss.index   │    │
│                         │   │  │      └── embeddings/   │    │
│                         │   │  └────────────────────────┘    │
└─────────────────────────┘   └─────────────────────────────────┘
```

## Component Details

### 1. Command Layer

**Location:** `memdocs/cli.py`

Entry point for all user interactions. Handles:
- Command parsing and validation
- Configuration loading
- Error handling and user feedback
- Progress display

**Technologies:**
- **Click** - CLI framework
- **Rich** - Terminal formatting
- **Pydantic** - Configuration validation

### 2. Code Extractor

**Location:** `memdocs/extract.py`, `memdocs/symbol_extractor.py`

Analyzes source code to extract structure and context.

**Process:**
1. Read files from disk
2. Parse with language-specific parsers (AST for Python, Tree-sitter for others)
3. Extract symbols (classes, functions, imports)
4. Build dependency graph
5. Generate context summary

**Outputs:**
- Symbol list (classes, functions, methods)
- Import graph
- Code metrics (lines, complexity)
- Context text for AI

**Technologies:**
- **Python AST** - Python code parsing
- **Pygments** - Syntax highlighting and lexing
- **pathlib** - Path handling

### 3. AI Summarizer

**Location:** `memdocs/summarize.py`

Generates documentation using Claude Sonnet 4.5.

**Process:**
1. Receive extracted context
2. Build prompt with scope-appropriate context
3. Call Claude API with structured output
4. Parse response into DocumentIndex schema
5. Validate and sanitize output

**Features:**
- **Scope-aware**: Adjusts context window based on scope (file/module/repo)
- **Auto-escalation**: Escalates scope for security-sensitive changes
- **Rate limiting**: Prevents API abuse (50 calls/minute)
- **Token counting**: Uses tiktoken for accurate cost estimation

**Technologies:**
- **Anthropic SDK** - Claude API client
- **tiktoken** - Token counting
- **Pydantic** - Schema validation

### 4. Embedding Generator

**Location:** `memdocs/embeddings.py`

Creates vector embeddings for semantic search.

**Process:**
1. Chunk documentation into segments
2. Generate embeddings with sentence-transformers
3. Build FAISS index for fast similarity search
4. Save index and metadata to disk

**Index Structure:**
```
.memdocs/memory/
├── embeddings-{commit}.json  # Embedding vectors + metadata
├── faiss.index               # FAISS index for fast search
└── faiss_metadata.json       # Chunk-to-file mappings
```

**Technologies:**
- **sentence-transformers** - Embedding generation
- **FAISS** - Vector similarity search
- **NumPy** - Vector operations

### 5. Search Engine

**Location:** `memdocs/search.py`

Semantic search over project memory.

**Process:**
1. Convert query to embedding vector
2. Search FAISS index for similar vectors
3. Return top-k matches with relevance scores
4. Display results with file paths and line numbers

**Search Algorithm:**
- **L2 distance** - Euclidean distance for similarity
- **Top-k retrieval** - Returns k most similar chunks
- **Metadata enrichment** - Adds file paths and context

### 6. Storage Layer

**Location:** `.memdocs/` directory

All memory is stored locally and committed to git.

#### Documentation (`docs/`)

**Purpose:** Human and machine-readable documentation

**Files:**
- `index.json` - Structured data (features, impacts, risks)
- `symbols.yaml` - Code map (classes, functions, line numbers)
- `summary.md` - Human-readable summary

**Schema:** See [DocumentIndex](#documentindex-schema)

#### Memory (`memory/`)

**Purpose:** AI memory storage (embeddings, graph)

**Files:**
- `graph.json` - Feature relationship graph
- `embeddings-{commit}.json` - Vector embeddings
- `faiss.index` - FAISS index for search
- `faiss_metadata.json` - Chunk metadata

## Data Flow

### Review Flow (Generate Documentation)

```
┌─────────┐
│  User   │
└────┬────┘
     │ memdocs review --path src/
     ▼
┌─────────────────┐
│  CLI Parser     │ Validate arguments, load config
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Extractor      │ Parse code, extract symbols
└────┬────────────┘
     │ ExtractedContext
     ▼
┌─────────────────┐
│  Scope Detector │ Determine file/module/repo scope
└────┬────────────┘
     │ ScopeInfo
     ▼
┌─────────────────┐
│  Summarizer     │ Call Claude API
└────┬────────────┘
     │ DocumentIndex
     ▼
┌─────────────────┐
│  Privacy Guard  │ Detect/redact PHI/PII (optional)
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Writer         │ Save JSON, YAML, Markdown
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Embeddings     │ Generate vectors, build FAISS index
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Git Commit     │ Commit to .memdocs/ (user action)
└─────────────────┘
```

### Query Flow (Search Memory)

```
┌─────────┐
│  User   │
└────┬────┘
     │ memdocs query "authentication"
     ▼
┌─────────────────┐
│  CLI Parser     │ Parse query
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Embeddings     │ Convert query to vector
└────┬────────────┘
     │ Query vector
     ▼
┌─────────────────┐
│  FAISS Search   │ Find similar vectors
└────┬────────────┘
     │ Top-k matches
     ▼
┌─────────────────┐
│  Metadata       │ Enrich with file paths
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Display        │ Show results with scores
└─────────────────┘
```

## Data Schemas

### DocumentIndex Schema

**File:** `memdocs/schemas.py`

```python
class DocumentIndex(BaseModel):
    """Main documentation index structure."""
    commit: str                    # Git commit hash
    timestamp: datetime            # Generation time
    scope: ScopeInfo              # Scope information
    features: list[FeatureSummary] # Feature list
    impacts: ImpactSummary        # Impact analysis
    refs: ReferenceSummary        # References (PRs, issues, commits)
```

### FeatureSummary Schema

```python
class FeatureSummary(BaseModel):
    """Individual feature description."""
    id: str                       # feat-001, feat-002, etc.
    title: str                    # Feature title
    description: str              # Detailed description
    risk: list[str]              # Risk tags (security, breaking, etc.)
    tags: list[str]              # Feature tags
```

### ScopeInfo Schema

```python
class ScopeInfo(BaseModel):
    """Scope metadata."""
    paths: list[str]              # Files in scope
    level: str                    # file | module | repo
    file_count: int               # Number of files
    escalated: bool               # Was scope escalated?
    escalation_reason: str | None # Why escalated
```

### Symbol Schema

```python
class Symbol(BaseModel):
    """Code symbol (class, function, etc.)."""
    name: str                     # Symbol name
    kind: str                     # class | function | method
    file: str                     # Source file path
    line: int                     # Line number
    signature: str | None         # Function signature
    doc: str | None               # Docstring
    methods: list[str]            # Method names (for classes)
```

## Scope Management

MemDocs uses a **scope policy system** to determine how much context to include.

### Scope Levels

| Level | Context | Token Usage | Use Case |
|-------|---------|-------------|----------|
| **file** | Single file only | ~2K tokens | Individual feature development |
| **module** | Related files in module | ~8K tokens | Multi-file refactoring |
| **repo** | Entire repository | ~32K+ tokens | Architectural changes |

### Auto-Escalation

Scope automatically escalates when:

1. **Cross-module changes** - Files from multiple modules modified
2. **Security-sensitive paths** - Files in `auth/`, `security/`, etc.
3. **Public API changes** - Public functions/classes modified
4. **Breaking changes** - Backward-incompatible changes detected

**Configuration:**
```yaml
policies:
  default_scope: file
  escalate_on:
    - cross_module_changes
    - security_sensitive_paths
    - public_api_signatures
```

## Security Architecture

**Location:** `memdocs/security.py`

### Path Validation

Prevents path traversal attacks:
```python
PathValidator.validate_path(path, base_dir=project_root)
```

**Checks:**
- No `..` patterns
- No null bytes
- Stays within base directory
- Resolves symlinks

### Input Validation

Validates all user inputs:
```python
InputValidator.validate_api_key(api_key)
InputValidator.validate_model_name(model)
```

**Patterns:**
- API keys: `^sk-ant-[a-zA-Z0-9_-]{95,}$`
- Model names: Whitelist of supported models
- File sizes: Max 10MB by default

### Rate Limiting

Prevents API abuse:
```python
rate_limiter = RateLimiter(max_calls=50, window_seconds=60)
rate_limiter.check_rate_limit()  # Raises if exceeded
```

**Implementation:** Sliding window algorithm

### Secret Detection

Detects and redacts secrets:
```python
secrets = InputValidator.check_for_secrets(text)
sanitized = InputValidator.sanitize_output(text)
```

**Patterns detected:**
- API keys
- Passwords
- Credit cards
- Email addresses
- Phone numbers

## Privacy Guard (PHI/PII)

**Location:** `memdocs/guard.py`

For medical/healthcare applications with sensitive data.

### PHI Modes

- **off** - No privacy protection (default)
- **standard** - Detect and warn about PHI/PII
- **strict** - Automatically redact PHI/PII

### Redaction Process

1. Scan text with regex patterns
2. Identify PHI/PII (names, MRNs, SSNs, etc.)
3. Replace with `[REDACTED-{type}]`
4. Log redactions for audit (if enabled)

**Patterns:**
- Social Security Numbers
- Medical Record Numbers
- Phone numbers
- Email addresses
- Dates of birth
- Physical addresses

## Embeddings Architecture

### Embedding Model

**Default:** `all-MiniLM-L6-v2` (sentence-transformers)

**Characteristics:**
- **Dimensions:** 384
- **Speed:** ~1000 sentences/sec on CPU
- **Quality:** Good for semantic search
- **Size:** 80MB model

**Alternative:** `all-mpnet-base-v2` (higher quality, slower)

### FAISS Index

**Index Type:** `IndexFlatL2` (exact L2 distance)

**Why L2?**
- Exact search (no approximation)
- Fast for small-to-medium datasets (< 1M vectors)
- No training required

**For large projects:** Can switch to `IndexIVFFlat` (approximate search)

### Chunking Strategy

Documents are chunked for embeddings:

**Chunk size:** ~500 tokens
**Overlap:** 50 tokens
**Method:** Sentence-aware (don't split mid-sentence)

**Why?**
- Better search relevance (smaller chunks)
- Fits within embedding model limits
- Overlap ensures context continuity

## Performance Characteristics

### Review Performance

**Small file** (< 500 lines):
- Extraction: ~0.5s
- Claude API: ~5s
- Embeddings: ~1s
- **Total: ~6.5s**

**Medium file** (500-2000 lines):
- Extraction: ~1s
- Claude API: ~8s
- Embeddings: ~2s
- **Total: ~11s**

**Large repository** (100 files):
- Extraction: ~10s
- Claude API: ~15s
- Embeddings: ~20s
- **Total: ~45s**

### Query Performance

**Search speed:** ~0.1s for 1000 vectors (FAISS on CPU)
**Scaling:** Linear with vector count (O(n) for exact search)

**Optimization for large projects:**
- Use `IndexIVFFlat` (approximate search)
- Reduce embedding dimensions
- Filter by file paths first

### Storage Requirements

**Per file documented:**
- Documentation: ~10-20 KB
- Embeddings: ~5-10 KB
- FAISS index: ~1.5 KB per vector

**Example project (100 files):**
- Docs: ~1.5 MB
- Embeddings: ~0.8 MB
- FAISS: ~0.2 MB
- **Total: ~2.5 MB**

## Error Handling

### Error Hierarchy

```python
MemDocsError                   # Base exception
├── ConfigError               # Configuration issues
├── APIError                  # Claude API errors
├── SecurityError             # Security violations
├── ValidationError           # Input validation errors
└── StorageError              # File I/O errors
```

### Graceful Degradation

- **API failures** - Retry with exponential backoff
- **Rate limits** - Wait and retry automatically
- **Embedding failures** - Continue without search (docs still generated)
- **PHI detection failures** - Warn but don't block

## Extensibility

### Custom Embeddings

Swap embedding models:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')
embeddings = EmbeddingGenerator(model=model)
```

### Custom Summarizers

Implement custom summarization:

```python
from memdocs.summarize import BaseSummarizer

class CustomSummarizer(BaseSummarizer):
    def summarize(self, context: ExtractedContext) -> DocumentIndex:
        # Custom logic here
        pass
```

### Custom Extractors

Add support for new languages:

```python
from memdocs.extract import BaseExtractor

class RustExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> ExtractedContext:
        # Rust parsing logic
        pass
```

## Testing Architecture

### Unit Tests

**Coverage:** 73% overall
- Core modules: 85-95%
- CLI: 86%
- Security: 90%+

**Framework:** pytest
**Mocking:** pytest-mock, unittest.mock

### Integration Tests

**API tests:** Require `ANTHROPIC_API_KEY`
**Skip strategy:** `@pytest.mark.skipif` for API tests

### Test Structure

```
tests/
├── unit/                 # Unit tests (fast, no API calls)
│   ├── test_extract.py
│   ├── test_security.py
│   └── test_embeddings.py
├── integration/          # Integration tests (require API)
│   └── test_summarize_integration.py
└── fixtures/             # Test data
    └── sample_files/
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - Run pytest (non-API tests)
      - Generate coverage report
      - Run mypy type checking
      - Run ruff linting
      - Upload coverage to Codecov
```

**See:** `.github/workflows/ci.yml`

## Deployment

### PyPI Package

**Package:** `memdocs`
**Versioning:** Semantic versioning (2.0.0)
**Build:** `python -m build`
**Upload:** `twine upload dist/*`

### Dependencies

**Core:**
- `anthropic>=0.39.0`
- `click>=8.1.0`
- `pydantic>=2.0.0`
- `pyyaml>=6.0.0`
- `rich>=13.0.0`

**Optional (embeddings):**
- `sentence-transformers>=2.2.0`
- `faiss-cpu>=1.7.0`
- `numpy>=1.24.0`

## Future Architecture Plans

### MCP Server Integration

**Model Context Protocol (MCP):** Standard for AI context sharing

**Status:** Implemented in `memdocs/mcp_server.py`

**Features:**
- Serve memory over MCP protocol
- Real-time updates
- Multi-client support

### Distributed Memory

**Vision:** Share memory across teams/projects

**Ideas:**
- Memory registry service
- Cross-project search
- Team memory profiles

### Cloud-Optional Storage

**Vision:** Optional cloud backup for large teams

**Ideas:**
- S3/GCS storage backend
- Encrypted cloud sync
- On-prem deployment

## References

- **Claude API:** [docs.anthropic.com](https://docs.anthropic.com/)
- **FAISS:** [github.com/facebookresearch/faiss](https://github.com/facebookresearch/faiss)
- **Sentence Transformers:** [sbert.net](https://www.sbert.net/)
- **Pydantic:** [docs.pydantic.dev](https://docs.pydantic.dev/)

---

**Questions?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

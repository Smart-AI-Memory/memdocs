# Configuration Reference

Complete reference for `.memdocs.yml` configuration file.

## Overview

The `.memdocs.yml` file controls how MemDocs generates and manages AI memory for your project. It's created automatically when you run `memdocs init`.

**Location:** `.memdocs.yml` in your project root

## Configuration Schema

```yaml
version: 1

# Scope policy (controls memory granularity)
policies:
  default_scope: file          # file | module | repo
  max_files_without_force: 150

  # Auto-escalate for important changes
  escalate_on:
    - cross_module_changes      # Multi-module = bigger context needed
    - security_sensitive_paths  # auth/*, security/* = document thoroughly
    - public_api_signatures     # API changes = team needs to know

# Output configuration (git-committed memory)
outputs:
  docs_dir: .memdocs/docs       # Committed to git
  memory_dir: .memdocs/memory   # Committed to git
  formats:
    - json                      # index.json (machine-readable)
    - yaml                      # symbols.yaml (code map)
    - markdown                  # summary.md (human-readable)

# Privacy (optional, only enable if handling sensitive data)
privacy:
  phi_mode: "off"               # off | standard | strict
  scrub:                        # Types of sensitive data to redact
    - email
    - phone
    - ssn
    - mrn
  audit_redactions: true        # Log all redactions for compliance

# AI configuration (Claude API)
ai:
  provider: anthropic           # anthropic | openai
  model: claude-sonnet-4-5-20250929  # Claude Sonnet 4.5 (latest)
  max_tokens: 8192
  temperature: 0.3              # Lower = more deterministic

# Empathy Framework integration (optional)
empathy:
  enabled: true
  sync_on_review: true          # Auto-sync with Empathy after reviews
  level: 4                      # Anticipatory Empathy level

# Exclude patterns (don't document these)
exclude:
  - node_modules/**
  - .venv/**
  - venv/**
  - __pycache__/**
  - "*.pyc"
  - .git/**
  - dist/**
  - build/**
  - "*.log"
  - "*.db"
  - coverage/**
  - htmlcov/**
  - .pytest_cache/**
  - "*.egg-info/**"
```

## Section Reference

### `version`

**Type:** `integer`
**Required:** Yes
**Default:** `1`

Schema version for future compatibility. Currently only version `1` is supported.

```yaml
version: 1
```

---

### `policies` - Scope Management

Controls how MemDocs determines the context window for documentation generation.

#### `policies.default_scope`

**Type:** `string`
**Required:** No
**Default:** `"file"`
**Options:** `file`, `module`, `repo`

The default scope level for documentation generation:

- **`file`**: Document individual files in isolation
  - **Best for:** Individual feature development
  - **Token usage:** Low (~2K tokens)
  - **Use when:** Making focused changes to single files

- **`module`**: Document entire modules/packages together
  - **Best for:** Multi-file refactoring
  - **Token usage:** Medium (~8K tokens)
  - **Use when:** Changes span multiple related files

- **`repo`**: Document entire repository
  - **Best for:** Major architectural changes
  - **Token usage:** High (~32K+ tokens)
  - **Use when:** Making cross-cutting changes

```yaml
policies:
  default_scope: file  # Start narrow, escalate as needed
```

#### `policies.max_files_without_force`

**Type:** `integer`
**Required:** No
**Default:** `150`

Maximum number of files to process without requiring `--force` flag. Prevents accidental expensive API calls on large repositories.

```yaml
policies:
  max_files_without_force: 150
```

#### `policies.escalate_on`

**Type:** `list[string]`
**Required:** No
**Default:** `[]`

Automatically escalate scope when certain conditions are met:

**Available escalation triggers:**

- **`cross_module_changes`**: Changes affect multiple modules/packages
- **`security_sensitive_paths`**: Changes touch security-critical files (auth/*, security/*, etc.)
- **`public_api_signatures`**: Changes modify public API functions/classes
- **`breaking_changes`**: Changes that could break compatibility
- **`test_failures`**: Test failures detected
- **`large_file_changes`**: Files > 1000 lines modified

```yaml
policies:
  escalate_on:
    - cross_module_changes      # Auto-escalate for multi-module changes
    - security_sensitive_paths  # Always use module scope for security
    - public_api_signatures     # API changes need full context
```

---

### `outputs` - Documentation Output

Controls where and how documentation is saved.

#### `outputs.docs_dir`

**Type:** `string`
**Required:** No
**Default:** `.memdocs/docs`

Directory for human and machine-readable documentation. **This directory is committed to git.**

```yaml
outputs:
  docs_dir: .memdocs/docs  # Committed to git
```

#### `outputs.memory_dir`

**Type:** `string`
**Required:** No
**Default:** `.memdocs/memory`

Directory for AI memory storage (embeddings, graph, metadata). **This directory is committed to git.**

```yaml
outputs:
  memory_dir: .memdocs/memory  # Committed to git
```

#### `outputs.formats`

**Type:** `list[string]`
**Required:** No
**Default:** `["json", "yaml", "markdown"]`
**Options:** `json`, `yaml`, `markdown`

Output formats to generate:

- **`json`**: Machine-readable structured data (`index.json`)
  - Features, impacts, risks, references
  - Used by tools and CI/CD

- **`yaml`**: Code symbols map (`symbols.yaml`)
  - Classes, functions, methods with line numbers
  - Used for code navigation

- **`markdown`**: Human-readable summary (`summary.md`)
  - Feature descriptions
  - Impact analysis
  - Risk assessment

```yaml
outputs:
  formats:
    - json      # For tools/automation
    - yaml      # For code navigation
    - markdown  # For humans
```

---

### `privacy` - PHI/PII Protection

**IMPORTANT:** Only enable if your project handles Protected Health Information (PHI) or Personally Identifiable Information (PII). This feature is designed for HIPAA compliance and medical AI applications.

#### `privacy.phi_mode`

**Type:** `string`
**Required:** No
**Default:** `"off"`
**Options:** `off`, `standard`, `strict`

Privacy guard mode:

- **`off`**: No privacy protection (default)
- **`standard`**: Detect and warn about PHI/PII
- **`strict`**: Automatically redact PHI/PII from documentation

```yaml
privacy:
  phi_mode: "strict"  # For medical/healthcare projects
```

#### `privacy.scrub`

**Type:** `list[string]`
**Required:** No
**Default:** `[]`
**Options:** `email`, `phone`, `ssn`, `mrn`, `credit_card`, `address`, `dob`

Types of sensitive data to detect/redact:

```yaml
privacy:
  scrub:
    - email         # Email addresses
    - phone         # Phone numbers
    - ssn           # Social Security Numbers
    - mrn           # Medical Record Numbers
    - credit_card   # Credit card numbers
    - address       # Physical addresses
    - dob           # Dates of birth
```

#### `privacy.audit_redactions`

**Type:** `boolean`
**Required:** No
**Default:** `false`

Log all redactions for compliance audit trails. Creates `.memdocs/redactions.log` with:
- Timestamp
- File path
- Line number
- Type of data redacted

```yaml
privacy:
  audit_redactions: true  # For HIPAA compliance
```

---

### `ai` - AI Model Configuration

Controls the AI model used for documentation generation.

#### `ai.provider`

**Type:** `string`
**Required:** No
**Default:** `"anthropic"`
**Options:** `anthropic`, `openai`

AI provider to use. Currently only `anthropic` (Claude) is fully supported.

```yaml
ai:
  provider: anthropic
```

#### `ai.model`

**Type:** `string`
**Required:** No
**Default:** `"claude-sonnet-4-5-20250929"`

Claude model to use:

**Supported models:**

- **`claude-sonnet-4-5-20250929`** (recommended)
  - Latest Sonnet 4.5
  - Best balance of quality and cost
  - 200K context window

- **`claude-sonnet-3-5-20241022`**
  - Previous Sonnet 3.5
  - Slightly cheaper
  - 200K context window

- **`claude-opus-4-20250514`**
  - Highest quality
  - More expensive
  - 200K context window

```yaml
ai:
  model: claude-sonnet-4-5-20250929  # Latest Sonnet 4.5
```

#### `ai.max_tokens`

**Type:** `integer`
**Required:** No
**Default:** `8192`
**Range:** `1024` - `200000`

Maximum tokens for AI response. Higher values allow more detailed documentation but cost more.

**Recommendations:**
- **Small files** (< 500 lines): `4096`
- **Medium files** (500-2000 lines): `8192`
- **Large files** (2000+ lines): `16384`

```yaml
ai:
  max_tokens: 8192  # Good for most files
```

#### `ai.temperature`

**Type:** `float`
**Required:** No
**Default:** `0.3`
**Range:** `0.0` - `1.0`

AI creativity/randomness:

- **`0.0`**: Completely deterministic (same input = same output)
- **`0.3`**: Recommended - consistent with slight variation
- **`0.7`**: More creative, less predictable
- **`1.0`**: Maximum creativity

```yaml
ai:
  temperature: 0.3  # Consistent, predictable output
```

---

### `empathy` - Empathy Framework Integration

Integration with the Empathy Framework for Level 4 Anticipatory Intelligence.

**Learn more:** [Empathy Framework Guide](guides/empathy-sync.md)

#### `empathy.enabled`

**Type:** `boolean`
**Required:** No
**Default:** `false`

Enable Empathy Framework integration.

```yaml
empathy:
  enabled: true
```

#### `empathy.sync_on_review`

**Type:** `boolean`
**Required:** No
**Default:** `false`

Automatically sync with Empathy Framework after each review.

```yaml
empathy:
  sync_on_review: true  # Auto-sync after documentation
```

#### `empathy.level`

**Type:** `integer`
**Required:** No
**Default:** `4`
**Range:** `1` - `5`

Empathy level (1-5):

- **Level 1**: Basic understanding
- **Level 2**: Contextual awareness
- **Level 3**: Predictive understanding
- **Level 4**: Anticipatory intelligence (recommended)
- **Level 5**: Proactive assistance

```yaml
empathy:
  level: 4  # Anticipatory intelligence
```

---

### `exclude` - File Exclusions

Patterns to exclude from documentation.

**Type:** `list[string]`
**Required:** No
**Default:** See example below

Glob patterns for files/directories to ignore:

```yaml
exclude:
  # Dependencies
  - node_modules/**
  - .venv/**
  - venv/**
  - vendor/**

  # Build artifacts
  - dist/**
  - build/**
  - "*.egg-info/**"
  - __pycache__/**
  - "*.pyc"

  # Version control
  - .git/**
  - .svn/**

  # IDE
  - .vscode/**
  - .idea/**

  # Logs and databases
  - "*.log"
  - "*.db"
  - "*.sqlite"

  # Test coverage
  - coverage/**
  - htmlcov/**
  - .pytest_cache/**
  - .coverage
```

**Pattern syntax:**
- `**` matches any number of directories
- `*` matches any characters except `/`
- `?` matches a single character
- Patterns are relative to project root

---

## Configuration Examples

### Minimal Configuration

For simple projects with no special requirements:

```yaml
version: 1

policies:
  default_scope: file

outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory

ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
```

### Standard Configuration (Recommended)

For most projects:

```yaml
version: 1

policies:
  default_scope: file
  max_files_without_force: 150
  escalate_on:
    - cross_module_changes
    - security_sensitive_paths

outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory
  formats:
    - json
    - yaml
    - markdown

ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  max_tokens: 8192
  temperature: 0.3

exclude:
  - node_modules/**
  - .venv/**
  - dist/**
  - "*.pyc"
```

### Enterprise Configuration

For large organizations with security and compliance requirements:

```yaml
version: 1

policies:
  default_scope: module  # Larger context by default
  max_files_without_force: 500
  escalate_on:
    - cross_module_changes
    - security_sensitive_paths
    - public_api_signatures
    - breaking_changes

outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory
  formats:
    - json
    - yaml
    - markdown

privacy:
  phi_mode: "strict"  # Auto-redact sensitive data
  scrub:
    - email
    - phone
    - ssn
    - credit_card
  audit_redactions: true  # Compliance logging

ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  max_tokens: 16384  # Larger context for complex files
  temperature: 0.2   # More deterministic

empathy:
  enabled: true
  sync_on_review: true
  level: 4

exclude:
  - node_modules/**
  - .venv/**
  - vendor/**
  - dist/**
  - build/**
  - "*.egg-info/**"
  - __pycache__/**
  - "*.pyc"
  - .git/**
  - coverage/**
  - htmlcov/**
  - .pytest_cache/**
  - "*.log"
  - "*.db"
```

### Monorepo Configuration

For repositories with multiple packages:

```yaml
version: 1

policies:
  default_scope: module  # Module scope for multi-package context
  max_files_without_force: 1000  # Large repos need higher limit
  escalate_on:
    - cross_module_changes  # Important for monorepos
    - public_api_signatures
    - breaking_changes

outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory
  formats:
    - json
    - yaml
    - markdown

ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  max_tokens: 16384  # Larger context for cross-package changes
  temperature: 0.3

# Exclude all package node_modules, dist, etc.
exclude:
  - "**/node_modules/**"
  - "**/.venv/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/__pycache__/**"
  - "**/*.pyc"
```

## Environment Variables

Some settings can be overridden with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (required) | None |
| `MEMDOCS_CONFIG` | Path to config file | `.memdocs.yml` |
| `MEMDOCS_SCOPE` | Override default scope | From config |
| `MEMDOCS_NO_CACHE` | Disable API caching | `false` |

**Example:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export MEMDOCS_SCOPE="module"
memdocs review --path src/
```

## Best Practices

### Scope Strategy

1. **Start with `file` scope** - Faster, cheaper, sufficient for most changes
2. **Escalate to `module`** - When refactoring spans multiple files
3. **Use `repo` scope sparingly** - Only for major architectural changes

### Token Optimization

- Use lower `max_tokens` for small files (save costs)
- Increase `max_tokens` for complex architectural documentation
- Monitor token usage with `memdocs stats`

### Security

- **Never commit API keys** - Use environment variables
- Enable `privacy.phi_mode` if handling sensitive data
- Use `audit_redactions` for compliance requirements

### Exclusions

- Exclude dependencies (`node_modules/`, `.venv/`)
- Exclude build artifacts (`dist/`, `build/`)
- Exclude IDE files (`.vscode/`, `.idea/`)
- Exclude test coverage reports

## Validation

MemDocs validates your configuration on startup:

```bash
# Check if config is valid
memdocs init --validate
```

**Common errors:**

- **Invalid scope level**: Must be `file`, `module`, or `repo`
- **Invalid model**: Model not supported by provider
- **Invalid temperature**: Must be between 0.0 and 1.0
- **Missing API key**: Set `ANTHROPIC_API_KEY` environment variable

## Next Steps

- **[Getting Started](getting-started.md)** - Quick tutorial
- **[CLI Reference](cli-reference.md)** - Command-line usage
- **[Architecture](architecture.md)** - How MemDocs works

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

# MemDocs Security Architecture

## Overview

MemDocs is designed with enterprise security as a core requirement, not an afterthought. This document describes the security architecture that enables MemDocs to pass enterprise audits where cloud-based alternatives cannot.

## Core Security Principles

### 1. Data Never Leaves Your Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Infrastructure                       │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Source    │───►│  MemDocs    │───►│  .memdocs/  │     │
│  │    Code     │    │   Engine    │    │   (Git)     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                            │                                │
│                            ▼                                │
│                     ┌─────────────┐                         │
│                     │   FAISS     │  ◄── Local Vector DB    │
│                     │   Index     │      (No cloud)         │
│                     └─────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Only summarization requests
                            ▼
                   ┌─────────────────┐
                   │  Claude API     │  ◄── Optional, can be
                   │  (Anthropic)    │      air-gapped
                   └─────────────────┘
```

### 2. Git-Native Storage

All MemDocs data is stored in the `.memdocs/` directory within your repository:

```
.memdocs/
├── docs/                    # Generated documentation
│   ├── index.json          # Machine-readable index
│   ├── symbols.yaml        # Code symbol map
│   └── summary.md          # Human-readable summary
└── memory/                  # Search index
    ├── faiss.index         # Vector embeddings (local)
    └── faiss_metadata.json # Metadata
```

**Security Benefits:**
- Version controlled (full audit trail)
- Access controlled by existing git permissions
- No separate database credentials to manage
- Portable (clone = complete memory)

### 3. Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Input Validation                                   │
│  ├── Path traversal prevention (PathValidator)              │
│  ├── File size limits (10MB default)                        │
│  ├── API key format validation                              │
│  └── Configuration schema validation                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Data Protection                                    │
│  ├── PHI/PII detection (Guard module)                       │
│  ├── Automatic redaction with audit trail                   │
│  ├── Secrets detection (API keys, passwords)                │
│  └── Sanitized output (no secrets in logs)                  │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Access Control                                     │
│  ├── Git-based permissions (inherited)                      │
│  ├── Rate limiting (50 calls/minute default)                │
│  ├── No network access for retrieval                        │
│  └── MCP server runs locally only                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Audit & Compliance                                 │
│  ├── Redaction audit logs (JSONL format)                    │
│  ├── Git history as audit trail                             │
│  ├── Structured exception handling                          │
│  └── No telemetry or analytics                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Security Details

### Input Validation (security.py)

**PathValidator:**
```python
# Prevents path traversal attacks
PathValidator.validate_path(path, base_dir=repo_root)
# Raises SecurityError if path escapes base directory

# Validates write operations to allowed directories only
PathValidator.validate_write_path(path, allowed_dirs=[docs_dir, memory_dir])
```

**InputValidator:**
```python
# API key format validation (Anthropic format: sk-ant-...)
InputValidator.validate_api_key(key)

# Secrets detection and redaction
InputValidator.sanitize_output(text)  # Removes API keys, passwords
InputValidator.check_for_secrets(text)  # Returns list of found patterns
```

### PHI/PII Protection (guard.py)

**Detected Patterns:**
| Type | Pattern | Example |
|------|---------|---------|
| Email | RFC 5322 compliant | user@example.com |
| Phone | US format with variants | (555) 123-4567 |
| SSN | XXX-XX-XXXX | 123-45-6789 |
| Credit Card | 16 digits with separators | 4111-1111-1111-1111 |
| IPv4 | Standard dotted notation | 192.168.1.1 |
| API Key | Common patterns | api_key=abc123... |
| MRN | Medical Record Number | MRN: ABC123456 |

**Redaction Modes:**
- `off`: No detection or redaction
- `standard`: Detect and redact common PII
- `strict`: Aggressive detection, audit all findings

**Audit Trail:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event": "redaction_applied",
  "doc_id": "abc123",
  "redactions": [
    {"type": "email", "location": "char:150-175", "context": "contact..."}
  ]
}
```

### Rate Limiting (security.py)

```python
# Default: 50 API calls per 60-second window
RateLimiter(max_calls=50, window_seconds=60)

# Raises RuntimeError if exceeded
rate_limiter.check_rate_limit()
```

### MCP Server Security (mcp_server.py)

The MCP server enables Claude Desktop integration while maintaining security:

- **Local only**: Runs via stdio, no network exposure
- **Read-only by default**: Only queries existing memory
- **Path validation**: All file access validated against repo root
- **No arbitrary code execution**: Tools are predefined and limited

## Data Flow Security

### Documentation Generation

```
1. User runs: memdocs review --path src/
                    │
2. PathValidator ───┼──► Validates path is within repo
                    │
3. Extractor ───────┼──► Reads files (size-limited)
                    │
4. Guard ───────────┼──► Scans for PHI/PII
                    │
5. Summarizer ──────┼──► Sends to Claude API (optional)
                    │                │
                    │                ▼
                    │         Sanitized code context only
                    │         (no secrets, redacted PII)
                    │
6. Index ───────────┼──► Stores locally in .memdocs/
                    │
7. Git ─────────────┴──► Commits with full audit trail
```

### Memory Retrieval (No Network Required)

```
1. User/AI queries: memdocs query "authentication"
                    │
2. LocalEmbedder ───┼──► Generates embedding locally
                    │    (sentence-transformers, no API)
                    │
3. FAISS ───────────┼──► Searches local index
                    │    (no external calls)
                    │
4. Results ─────────┴──► Returns matching documents
```

## Encryption

### At Rest
- Inherits repository encryption (git-crypt, SOPS compatible)
- FAISS index can be encrypted with repository
- No separate encryption keys to manage

### In Transit
- Claude API calls use TLS 1.3
- MCP server uses local stdio (no network)
- Git operations use SSH or HTTPS

## Secrets Management

### What MemDocs Never Stores
- API keys (environment variables only)
- User credentials
- Session tokens
- Encryption keys

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Required for summarization
EMPATHY_API_KEY=...           # Optional for Empathy integration
```

### Pre-commit Protection
```yaml
# .pre-commit-config.yaml includes:
- repo: https://github.com/Yelp/detect-secrets
  hooks:
    - id: detect-secrets
```

## Compliance Alignment

| Control | MemDocs Implementation |
|---------|----------------------|
| Access Control | Git permissions, no separate auth |
| Audit Logging | Git history + redaction audit logs |
| Data Encryption | Repository-level encryption support |
| Data Residency | 100% on-premise, git-native |
| Incident Response | Security policy in SECURITY.md |
| Vulnerability Management | GitHub Dependabot, pip-audit |

## Security Testing

### Automated (CI/CD)
- `pip-audit` for dependency CVEs
- `ruff` for code quality (security rules)
- `mypy` for type safety
- Pre-commit hooks for secrets detection

### Manual
- Path traversal testing
- Input fuzzing for validators
- PHI/PII detection accuracy

## Reporting Vulnerabilities

See [SECURITY.md](../../SECURITY.md) for:
- Responsible disclosure process
- Security contact: patrick.roebuck@pm.me
- Response timeline: 48 hours

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Anthropic Privacy Policy](https://www.anthropic.com/privacy)

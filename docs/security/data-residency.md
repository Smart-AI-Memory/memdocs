# Data Residency Guide

## Overview

MemDocs provides complete data residency control through its git-native architecture. This document explains where data resides, how it flows, and how to configure MemDocs for various regulatory requirements.

## Data Residency Summary

| Data Type | Location | Customer Control |
|-----------|----------|------------------|
| Source code | Customer git repository | 100% |
| Generated documentation | `.memdocs/docs/` in repository | 100% |
| Search embeddings | `.memdocs/memory/` in repository | 100% |
| Audit logs | `.memdocs/audit.log` | 100% |
| API calls (optional) | Anthropic servers (configurable) | Opt-in |

## Architecture: Data Never Leaves Your Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR INFRASTRUCTURE                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Git Repository                          │ │
│  │                                                            │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │ │
│  │  │   src/      │    │   tests/    │    │   docs/     │    │ │
│  │  │   (code)    │    │   (tests)   │    │   (docs)    │    │ │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    │ │
│  │                                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │                    .memdocs/                         │  │ │
│  │  │                                                      │  │ │
│  │  │  ┌─────────────┐    ┌─────────────┐                 │  │ │
│  │  │  │   docs/     │    │   memory/   │                 │  │ │
│  │  │  │  index.json │    │ faiss.index │  ◄── All local │  │ │
│  │  │  │  summary.md │    │ metadata    │                 │  │ │
│  │  │  └─────────────┘    └─────────────┘                 │  │ │
│  │  │                                                      │  │ │
│  │  │  ┌─────────────┐                                    │  │ │
│  │  │  │  audit.log  │  ◄── Redaction audit trail        │  │ │
│  │  │  └─────────────┘                                    │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                              │                                   │
│                              │ Optional API calls only           │
│                              ▼                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                   ┌───────────┴───────────┐
                   │  Can be disabled for  │
                   │  air-gapped operation │
                   └───────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │   Claude API     │
                    │   (Anthropic)    │
                    │                  │
                    │   US: us.api     │
                    │   EU: eu.api     │
                    └──────────────────┘
```

## Data Categories

### 1. Generated Documentation (Always Local)

**Location**: `.memdocs/docs/`

**Contents**:
- `index.json`: Structured documentation index
- `symbols.yaml`: Code symbol map (functions, classes)
- `summary.md`: Human-readable summary

**Residency**: 100% within your git repository. Version controlled with your code.

### 2. Search Embeddings (Always Local)

**Location**: `.memdocs/memory/`

**Contents**:
- `faiss.index`: FAISS vector index (binary)
- `faiss_metadata.json`: Document metadata

**Residency**: 100% local. Generated using sentence-transformers (local model). No data sent externally.

### 3. Audit Logs (Always Local)

**Location**: `.memdocs/audit.log`

**Contents**: JSONL format redaction events

**Residency**: 100% local. Never transmitted.

### 4. API Calls (Optional, Configurable)

**When Used**: Only during `memdocs review` with Claude summarization

**What's Sent**:
- Code structure and symbols
- Commit messages (sanitized)
- File paths

**What's NOT Sent**:
- Full file contents (only summaries)
- Detected PHI/PII (redacted before sending)
- Secrets (detected and removed)

## Regulatory Compliance Configurations

### GDPR (EU Data Protection)

```yaml
# .memdocs.yml for GDPR compliance
version: 1

privacy:
  phi_mode: "strict"
  scrub:
    - email
    - phone
  audit_redactions: true

# Option 1: Use EU API endpoint (if available)
ai:
  provider: anthropic
  endpoint: "https://eu.api.anthropic.com"  # Check Anthropic for availability

# Option 2: Disable API for full EU residency
# ai:
#   enabled: false
```

### US Healthcare (HIPAA)

See [hipaa-readiness.md](hipaa-readiness.md) for complete guide.

```yaml
# .memdocs.yml for HIPAA compliance
version: 1

privacy:
  phi_mode: "strict"
  scrub:
    - email
    - phone
    - ssn
    - mrn
  audit_redactions: true

exclude:
  - "**/patient*"
  - "**/medical*"
  - "**/*.hl7"
```

### Financial Services (PCI-DSS, SOX)

```yaml
# .memdocs.yml for financial compliance
version: 1

privacy:
  phi_mode: "strict"
  scrub:
    - credit_card
    - ssn
    - api_key
  audit_redactions: true

exclude:
  - "**/keys*"
  - "**/secrets*"
  - "**/*.pem"
  - "**/*.key"
```

### Government (FedRAMP, ITAR)

For classified or export-controlled environments:

```yaml
# .memdocs.yml for government use
version: 1

# Disable ALL external API calls
ai:
  enabled: false

privacy:
  phi_mode: "strict"
  audit_redactions: true

# Use local embeddings only
embeddings:
  provider: local
  model: "all-MiniLM-L6-v2"
```

## Air-Gapped Operation

For complete data isolation, MemDocs can run without any network access:

### Setup

```bash
# 1. Pre-download dependencies (on connected machine)
pip download memdocs[embeddings] -d ./wheels

# 2. Pre-download embedding model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
cp -r ~/.cache/huggingface ./model-cache

# 3. Transfer to air-gapped system
# (USB, secure file transfer, etc.)

# 4. Install on air-gapped system
pip install --no-index --find-links=./wheels memdocs[embeddings]

# 5. Set model cache location
export SENTENCE_TRANSFORMERS_HOME=./model-cache
```

### Usage

```bash
# All operations are local
memdocs init
memdocs review --path src/ --local-only
memdocs query "authentication"  # Uses local FAISS
```

## Multi-Region Deployment

For organizations with data residency requirements across regions:

```
┌─────────────────────────────────────────────────────────────────┐
│                       Organization                               │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   US Region     │  │   EU Region     │  │   APAC Region   │  │
│  │                 │  │                 │  │                 │  │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │
│  │  │ Git Repo  │  │  │  │ Git Repo  │  │  │  │ Git Repo  │  │  │
│  │  │ + .memdocs│  │  │  │ + .memdocs│  │  │  │ + .memdocs│  │  │
│  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │  │
│  │                 │  │                 │  │                 │  │
│  │  US API         │  │  EU API         │  │  Local only     │  │
│  │  (optional)     │  │  (optional)     │  │  (air-gapped)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Each region maintains complete data isolation with region-specific configuration.

## Data Flow Diagram

```
User Input                   Processing                    Storage
──────────                   ──────────                    ───────

memdocs review ──────────►  Extractor  ──────────────────►  .memdocs/docs/
    │                           │                              │
    │                           ▼                              │
    │                     PathValidator                        │
    │                     (security check)                     │
    │                           │                              │
    │                           ▼                              │
    │                        Guard                             │
    │                     (PHI/PII scan)                       │
    │                           │                              │
    │                           ▼                              │
    │              ┌────── Summarizer ──────┐                  │
    │              │    (if API enabled)    │                  │
    │              │           │            │                  │
    │              │           ▼            │                  │
    │              │   Claude API (TLS)     │                  │
    │              │   (sanitized input)    │                  │
    │              └────────────────────────┘                  │
    │                           │                              │
    │                           ▼                              │
    │                     LocalEmbedder ──────────────────►  .memdocs/memory/
    │                     (local model)                        │
    │                           │                              │
    │                           ▼                              │
    └──────────────────►  Git Commit  ◄────────────────────────┘
                        (audit trail)
```

## Verification Commands

### Verify No External Connections (Linux/Mac)

```bash
# Monitor network during operation
sudo tcpdump -i any host api.anthropic.com &

# Run memdocs in local-only mode
memdocs query "test"

# Should show NO packets to api.anthropic.com
```

### Verify Data Location

```bash
# All MemDocs data is in .memdocs/
find . -path "./.memdocs/*" -type f

# Expected output:
# ./.memdocs/docs/index.json
# ./.memdocs/docs/symbols.yaml
# ./.memdocs/docs/summary.md
# ./.memdocs/memory/faiss.index
# ./.memdocs/memory/faiss_metadata.json
# ./.memdocs/audit.log
```

### Verify Git History

```bash
# All changes are tracked
git log --oneline -- .memdocs/

# View specific change
git show <commit>:.memdocs/docs/index.json
```

## Contact

For data residency compliance questions:
- **Email**: patrick.roebuck@pm.me
- **Enterprise Support**: Available for licensed customers

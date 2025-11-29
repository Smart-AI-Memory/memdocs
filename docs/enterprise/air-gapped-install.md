# Air-Gapped Installation Guide

## Overview

MemDocs can operate in completely air-gapped environments with no network connectivity. This is a key enterprise differentiator for organizations with strict security requirements.

## What Works Without Network

| Feature | Network Required | Air-Gapped Alternative |
|---------|------------------|----------------------|
| Documentation generation | No (local) | Full functionality |
| Local embeddings | No (local model) | Full functionality |
| Vector search | No (FAISS local) | Full functionality |
| MCP server | No (stdio) | Full functionality |
| Claude summarization | Yes | Skip or pre-generate |
| Package installation | Yes | Offline wheels |

## Pre-Download Phase (Connected Machine)

### Step 1: Download Python Packages

```bash
# Create a directory for offline packages
mkdir -p ~/memdocs-offline/wheels

# Download MemDocs and all dependencies
pip download memdocs[embeddings] -d ~/memdocs-offline/wheels

# Verify downloads
ls ~/memdocs-offline/wheels/*.whl | wc -l
# Should be 30-50 wheel files
```

### Step 2: Download Embedding Model

The embedding model (~90MB) must be pre-downloaded:

```bash
# Download model to cache
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f'Model downloaded to: {model._model_card_text}')
"

# Copy model cache
mkdir -p ~/memdocs-offline/models
cp -r ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2 \
      ~/memdocs-offline/models/
```

### Step 3: Create Transfer Package

```bash
# Create tarball for transfer
cd ~/memdocs-offline
tar -czvf memdocs-offline-bundle.tar.gz wheels/ models/

# Verify size (should be ~150-200MB)
ls -lh memdocs-offline-bundle.tar.gz
```

### Step 4: Transfer to Air-Gapped System

Transfer `memdocs-offline-bundle.tar.gz` via:
- Approved USB device
- Secure file transfer (SFTP)
- Approved data diode
- Physical media (CD/DVD)

## Installation Phase (Air-Gapped Machine)

### Step 1: Extract Bundle

```bash
# Extract transfer package
mkdir -p ~/memdocs-install
cd ~/memdocs-install
tar -xzvf /path/to/memdocs-offline-bundle.tar.gz
```

### Step 2: Install MemDocs

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install from local wheels (no network)
pip install --no-index --find-links=./wheels memdocs

# Install embeddings support
pip install --no-index --find-links=./wheels \
    sentence-transformers faiss-cpu numpy
```

### Step 3: Configure Model Path

```bash
# Set environment variable for model location
export SENTENCE_TRANSFORMERS_HOME=~/memdocs-install/models

# Or add to shell profile
echo 'export SENTENCE_TRANSFORMERS_HOME=~/memdocs-install/models' >> ~/.bashrc

# Verify model is found
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model loaded successfully!')
print(f'Dimension: {model.get_sentence_embedding_dimension()}')
"
```

### Step 4: Verify Installation

```bash
# Check version
memdocs --version

# Verify no network calls (should work instantly)
time memdocs --help
```

## Configuration for Air-Gapped Operation

### Create Configuration File

```yaml
# .memdocs.yml
version: 1

# Disable external API calls
ai:
  provider: anthropic
  enabled: false  # No Claude API in air-gapped mode

# Use local embeddings only
policies:
  default_scope: file
  max_files_without_force: 150

# Full privacy mode
privacy:
  phi_mode: "strict"
  scrub:
    - email
    - phone
    - ssn
    - mrn
    - credit_card
    - api_key
  audit_redactions: true

outputs:
  docs_dir: .memdocs/docs
  memory_dir: .memdocs/memory
  formats:
    - json
    - yaml
    - markdown
```

## Usage in Air-Gapped Mode

### Initialize Repository

```bash
cd /path/to/your/repo
memdocs init

# Creates .memdocs/ directory and .memdocs.yml
```

### Generate Documentation (Local Only)

Without Claude API, documentation generation uses local extraction only:

```bash
# Extract symbols and structure (no API)
memdocs review --path src/ --local-only

# Output:
# ✓ Extracted 45 symbols from 12 files
# ✓ Generated documentation in .memdocs/docs/
# ⚠ AI summarization skipped (air-gapped mode)
```

### Build Search Index

```bash
# Index existing documentation
memdocs index --rebuild

# Creates FAISS index locally
# No network required
```

### Query Memory

```bash
# Semantic search uses local embeddings
memdocs query "authentication flow"

# Results:
# 1. [0.89] src/auth/login.py - User authentication
# 2. [0.76] src/middleware/auth.py - Auth middleware
# 3. [0.71] tests/test_auth.py - Auth tests
```

### MCP Server (Claude Desktop Alternative)

In air-gapped environments, you can still use the MCP server with local AI tools:

```bash
# Start MCP server (local stdio only)
memdocs serve --mcp

# Connect local AI assistant to MCP
# (Configuration varies by tool)
```

## Pre-Generated Documentation Strategy

For richer documentation in air-gapped environments, consider pre-generating with Claude before transfer:

### On Connected Machine

```bash
# Generate full documentation with Claude
memdocs review --path src/ --full

# This creates comprehensive summaries
# .memdocs/docs/summary.md includes AI insights
```

### Transfer Documentation

Include `.memdocs/` in your transfer:

```bash
# Add to transfer bundle
tar -czvf project-with-docs.tar.gz \
    src/ tests/ .memdocs/ .memdocs.yml
```

### On Air-Gapped Machine

```bash
# Extract project with pre-generated docs
tar -xzvf project-with-docs.tar.gz

# Documentation is ready to use
cat .memdocs/docs/summary.md

# Search still works locally
memdocs query "error handling"
```

## Verification

### Verify No Network Access

```bash
# Block all network (Linux)
sudo iptables -A OUTPUT -j DROP

# Run MemDocs operations
memdocs query "test"  # Should work instantly

# Restore network (if needed)
sudo iptables -D OUTPUT -j DROP
```

### Verify Local Model Usage

```bash
# Check model location
python -c "
import os
print(f'Model cache: {os.environ.get(\"SENTENCE_TRANSFORMERS_HOME\", \"default\")}')

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f'Model loaded from local cache')
"
```

### Verify Data Residency

```bash
# All data should be in .memdocs/
find . -path "./.memdocs/*" -type f | head -20

# No external state files
ls ~/.memdocs 2>/dev/null || echo "No external state (good!)"
```

## Troubleshooting

### "Model not found" Error

```bash
# Ensure environment variable is set
echo $SENTENCE_TRANSFORMERS_HOME

# Verify model files exist
ls -la $SENTENCE_TRANSFORMERS_HOME/models--sentence-transformers--all-MiniLM-L6-v2/
```

### "Package not found" During Install

```bash
# Verify wheel files are present
ls ./wheels/*.whl

# Check for missing dependencies
pip install --no-index --find-links=./wheels memdocs 2>&1 | grep "No matching"
```

### "Network unreachable" Errors

If you see network errors, verify configuration:

```yaml
# .memdocs.yml
ai:
  enabled: false  # Must be false for air-gapped
```

## Updates in Air-Gapped Environments

### Update Process

1. Download new version on connected machine
2. Create new offline bundle
3. Transfer via approved method
4. Install update: `pip install --no-index --find-links=./wheels --upgrade memdocs`

### Version Compatibility

- Check CHANGELOG.md for breaking changes
- Test in staging before production deployment
- Keep previous bundle for rollback

## Security Considerations

### Integrity Verification

```bash
# Generate checksums before transfer
sha256sum wheels/*.whl > checksums.txt

# Verify after transfer
sha256sum -c checksums.txt
```

### Approved Transfer Methods

Consult your organization's security policy for approved methods:
- Data diodes (one-way transfer)
- Approved removable media
- Secure file transfer protocols
- Physical media with chain of custody

## Support

For air-gapped deployment assistance:
- **Email**: patrick.roebuck@pm.me
- **Enterprise Support**: Priority support for licensed customers

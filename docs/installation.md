# Installation Guide

Complete guide to installing MemDocs with various configurations and environments.

## Quick Install

```bash
# Basic installation
pip install memdocs

# With all features
pip install memdocs[all]
```

## Installation Options

### Basic Installation

For core functionality only (generates docs, but no local search):

```bash
pip install memdocs
```

**What you get:**
- CLI commands (`init`, `review`, `export`, `stats`)
- Claude Sonnet 4.5 integration
- JSON, YAML, Markdown output
- Git integration

**What you don't get:**
- Local vector search (requires `embeddings` extra)
- Empathy Framework sync (manual setup required)

### With Local Search (Recommended)

For semantic search with local embeddings:

```bash
pip install memdocs[embeddings]
```

**Additional features:**
- FAISS vector search
- `memdocs query` command for semantic search
- Offline similarity search

**Additional dependencies:**
- `sentence-transformers`
- `faiss-cpu` (or `faiss-gpu` for GPU support)
- `numpy`

### All Features

Everything including development tools:

```bash
pip install memdocs[all]
```

**Includes:**
- All embeddings features
- Development tools (pytest, mypy, ruff, black)
- Documentation tools
- Pre-commit hooks

## Platform-Specific Instructions

### macOS

```bash
# Install Python 3.10+ (if not installed)
brew install python@3.10

# Install MemDocs
pip3 install memdocs[embeddings]

# Set API key permanently
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Linux (Ubuntu/Debian)

```bash
# Install Python 3.10+ (if not installed)
sudo apt update
sudo apt install python3.10 python3-pip

# Install MemDocs
pip3 install memdocs[embeddings]

# Set API key permanently
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Windows

```powershell
# Install Python 3.10+ from python.org

# Install MemDocs
pip install memdocs[embeddings]

# Set API key permanently (PowerShell)
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-your-key-here', 'User')
```

### Docker

```dockerfile
FROM python:3.10-slim

# Install MemDocs with all features
RUN pip install memdocs[all]

# Set API key (pass at runtime)
ENV ANTHROPIC_API_KEY=""

WORKDIR /workspace
ENTRYPOINT ["memdocs"]
```

**Usage:**
```bash
docker build -t memdocs .
docker run -v $(pwd):/workspace -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" memdocs review --path src/
```

## Development Installation

For contributing to MemDocs or local development:

```bash
# Clone the repository
git clone https://github.com/Smart-AI-Memory/memdocs.git
cd memdocs

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev,embeddings]"

# Install pre-commit hooks
pre-commit install

# Run tests
make test

# Run type checking
make mypy

# Format code
make format
```

## GPU Support for Embeddings

For faster embedding generation with GPU:

```bash
# Uninstall CPU version
pip uninstall faiss-cpu

# Install GPU version
pip install faiss-gpu

# Or install from conda
conda install -c pytorch faiss-gpu
```

**Requirements:**
- NVIDIA GPU with CUDA support
- CUDA 11.0 or higher

## Verifying Installation

```bash
# Check version
memdocs --version

# Check available commands
memdocs --help

# Test API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
echo "print('test')" > test.py
memdocs review --path test.py
rm test.py
```

**Expected output:**
```
MemDocs v2.0.0

Available commands:
  init    Initialize MemDocs in current project
  review  Generate documentation for files/directories
  query   Search project memory
  export  Export memory in different formats
  stats   Show memory statistics
```

## Configuration

### API Key Setup

MemDocs requires an Anthropic API key. You can provide it in three ways:

1. **Environment variable** (recommended):
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

2. **Shell profile** (persistent):
```bash
# For bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc

# For zsh (macOS default)
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

3. **In code** (for Python API usage):
```python
from memdocs import Summarizer

summarizer = Summarizer(api_key="sk-ant-your-key-here")
```

**Security note:** Never commit API keys to git! Add `.env` to `.gitignore` and use environment variables.

### Model Selection

By default, MemDocs uses Claude Sonnet 4.5. You can configure this in `.memdocs.yml`:

```yaml
ai:
  provider: anthropic
  model: claude-sonnet-4-5-20250929  # Latest Sonnet 4.5
  max_tokens: 8192
  temperature: 0.3
```

**Supported models:**
- `claude-sonnet-4-5-20250929` (recommended, latest)
- `claude-sonnet-3-5-20241022`
- `claude-opus-4-20250514`

## Upgrading

```bash
# Upgrade to latest version
pip install --upgrade memdocs

# Upgrade with all features
pip install --upgrade memdocs[all]

# Check new version
memdocs --version
```

## Uninstalling

```bash
# Remove package
pip uninstall memdocs

# Remove configuration and memory (optional)
rm -rf .memdocs/
rm .memdocs.yml
```

## Troubleshooting

### Import Error: No module named 'memdocs'

**Problem:** Python can't find the memdocs package.

**Solution:**
```bash
# Make sure you're using the same Python that installed memdocs
which python
pip show memdocs

# If different, reinstall with the correct pip
python -m pip install memdocs
```

### API Key Not Found

**Problem:** `Error: ANTHROPIC_API_KEY not set`

**Solution:**
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set it if empty
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
```

### FAISS Installation Fails

**Problem:** `ERROR: Could not build wheels for faiss-cpu`

**Solution 1:** Install prebuilt binaries:
```bash
# macOS
pip install faiss-cpu --no-cache-dir

# Linux
pip install faiss-cpu==1.7.4

# Or use conda
conda install -c conda-forge faiss-cpu
```

**Solution 2:** Install without embeddings (skip local search):
```bash
pip install memdocs
# Then use API-based search instead
```

### Permission Denied

**Problem:** `PermissionError: [Errno 13] Permission denied: '.memdocs/'`

**Solution:**
```bash
# Check directory permissions
ls -la .memdocs/

# Fix permissions
chmod -R u+w .memdocs/

# Or run with sudo (not recommended)
sudo pip install memdocs
```

### Slow Embedding Generation

**Problem:** Embeddings take too long to generate.

**Solutions:**
1. **Use GPU** (if available):
   ```bash
   pip uninstall faiss-cpu
   pip install faiss-gpu
   ```

2. **Use smaller model**:
   Edit `.memdocs.yml`:
   ```yaml
   embeddings:
     model: all-MiniLM-L6-v2  # Faster, smaller model
   ```

3. **Skip embeddings** for large files:
   ```bash
   memdocs review --path bigfile.py --no-embeddings
   ```

## System Requirements

### Minimum Requirements

- **Python:** 3.10 or higher
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 100MB for installation + memory storage
- **Network:** Required for Claude API calls

### Recommended Requirements

- **Python:** 3.11 or 3.12
- **RAM:** 8GB (for large projects with embeddings)
- **Disk:** 500MB+ for large projects
- **GPU:** NVIDIA GPU with CUDA (for fast embeddings)

## Dependencies

### Core Dependencies

- `anthropic>=0.39.0` - Claude API client
- `click>=8.1.0` - CLI framework
- `pydantic>=2.0.0` - Data validation
- `pyyaml>=6.0.0` - YAML parsing
- `rich>=13.0.0` - Terminal formatting

### Optional Dependencies

**Embeddings** (`memdocs[embeddings]`):
- `sentence-transformers>=2.2.0`
- `faiss-cpu>=1.7.0` (or `faiss-gpu`)
- `numpy>=1.24.0`

**Development** (`memdocs[dev]`):
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0`
- `mypy>=1.0.0`
- `ruff>=0.1.0`
- `black>=23.0.0`
- `pre-commit>=3.0.0`

## Next Steps

- **[Getting Started](getting-started.md)** - 5-minute tutorial
- **[Configuration](configuration.md)** - Configure `.memdocs.yml`
- **[CLI Reference](cli-reference.md)** - All commands and options

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

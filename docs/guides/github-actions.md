# GitHub Actions Integration

Automate MemDocs documentation generation in your CI/CD pipeline.

## Overview

Integrate MemDocs into GitHub Actions to:
- Auto-generate docs on every commit
- Update docs on pull requests
- Keep memory in sync with your codebase
- Prevent stale documentation

## Basic Workflow

### Auto-Update on Push

Create `.github/workflows/memdocs.yml`:

```yaml
name: Update MemDocs

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'lib/**'

jobs:
  update-memory:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git operations

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install MemDocs
        run: |
          pip install memdocs[embeddings]

      - name: Generate documentation
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          memdocs review --path src/ --on commit

      - name: Commit updated memory
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .memdocs/
          git diff --staged --quiet || git commit -m "docs: Update AI memory [skip ci]"
          git push
```

**Important:** Add `[skip ci]` to prevent infinite loops!

### PR Review Workflow

Create `.github/workflows/memdocs-pr.yml`:

```yaml
name: MemDocs PR Review

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'src/**'
      - 'lib/**'

jobs:
  review:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install MemDocs
        run: pip install memdocs[embeddings]

      - name: Review changed files
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Get changed files
          CHANGED_FILES=$(git diff --name-only origin/main...HEAD | grep -E '\.(py|js|ts)$' || true)

          if [ -n "$CHANGED_FILES" ]; then
            echo "Reviewing: $CHANGED_FILES"
            memdocs review --path $CHANGED_FILES --on pr
          else
            echo "No code files changed"
          fi

      - name: Upload memory as artifact
        uses: actions/upload-artifact@v4
        with:
          name: memdocs-pr-${{ github.event.pull_request.number }}
          path: .memdocs/
```

### Release Documentation

Create `.github/workflows/memdocs-release.yml`:

```yaml
name: Release Documentation

on:
  release:
    types: [published]

jobs:
  document-release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install MemDocs
        run: pip install memdocs[embeddings]

      - name: Generate complete documentation
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          memdocs review --repo --on release --force

      - name: Export for release
        run: |
          memdocs export cursor --output release-context.md
          memdocs stats --format json > memory-stats.json

      - name: Upload to release
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: ./release-context.md
          asset_name: ai-context.md
          asset_content_type: text/markdown
```

## Configuration

### Add API Key Secret

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Claude API key (starts with `sk-ant-`)
6. Click **Add secret**

### Optimize for Cost

Limit documentation to important changes:

```yaml
on:
  push:
    branches: [main]
    paths:
      # Only run on source code changes
      - 'src/**'
      - 'lib/**'
      # Ignore docs, tests, config
      - '!docs/**'
      - '!tests/**'
      - '!*.md'
```

### Skip CI on Memory Updates

Always add `[skip ci]` when committing memory:

```yaml
- name: Commit updated memory
  run: |
    git commit -m "docs: Update AI memory [skip ci]"
```

This prevents infinite workflow loops.

## Advanced Workflows

### Scheduled Documentation

Update docs weekly:

```yaml
on:
  schedule:
    # Run every Monday at 9 AM UTC
    - cron: '0 9 * * 1'
```

### Multi-Environment

Document different environments:

```yaml
jobs:
  document-staging:
    if: github.ref == 'refs/heads/staging'
    steps:
      - run: memdocs review --path src/ --output-dir .memdocs-staging/

  document-production:
    if: github.ref == 'refs/heads/main'
    steps:
      - run: memdocs review --path src/ --output-dir .memdocs-prod/
```

### Matrix Strategy

Document multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

## Best Practices

### 1. Use Path Filters

Only run on relevant file changes:

```yaml
on:
  push:
    paths:
      - 'src/**/*.py'
      - 'lib/**/*.js'
```

### 2. Cache Dependencies

Speed up workflow with caching:

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### 3. Fail Fast

Exit early if MemDocs fails:

```yaml
- name: Generate documentation
  run: |
    set -e  # Exit on error
    memdocs review --path src/
```

### 4. Conditional Commits

Only commit if memory changed:

```yaml
- name: Commit if changed
  run: |
    git add .memdocs/
    git diff --staged --quiet || git commit -m "docs: Update AI memory [skip ci]"
```

### 5. Use Artifacts

Save memory for debugging:

```yaml
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: memdocs-debug
    path: .memdocs/
```

## Troubleshooting

### API Key Not Found

**Problem:** `Error: ANTHROPIC_API_KEY not set`

**Solution:**
1. Check secret name matches exactly: `ANTHROPIC_API_KEY`
2. Verify secret is set in repository settings
3. Ensure you're using `secrets.ANTHROPIC_API_KEY` in workflow

### Permission Denied

**Problem:** `Permission denied: .memdocs/`

**Solution:**
```yaml
- name: Create memory directory
  run: mkdir -p .memdocs/docs .memdocs/memory
```

### Workflow Loop

**Problem:** Workflow triggers itself infinitely

**Solution:** Always use `[skip ci]` in commit messages:
```yaml
git commit -m "docs: Update memory [skip ci]"
```

### Rate Limit Exceeded

**Problem:** Too many API calls in CI

**Solution:** Use path filters and conditionals:
```yaml
on:
  push:
    paths:
      - 'src/**'  # Only source files
```

## Example: Complete Workflow

```yaml
name: MemDocs CI

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'lib/**'
  pull_request:
    types: [opened, synchronize]

jobs:
  update-memory:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-memdocs

      - name: Install MemDocs
        run: pip install memdocs[embeddings]

      - name: Generate documentation
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: memdocs review --path src/ lib/ --on commit

      - name: Commit updated memory
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .memdocs/
          git diff --staged --quiet || git commit -m "docs: Update AI memory [skip ci]"
          git push

  pr-review:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install MemDocs
        run: pip install memdocs[embeddings]

      - name: Review PR changes
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          CHANGED=$(git diff --name-only origin/main...HEAD | grep -E '\.(py|js|ts)$' || true)
          if [ -n "$CHANGED" ]; then
            memdocs review --path $CHANGED --on pr
          fi

      - name: Generate PR summary
        run: |
          memdocs export claude --output PR_SUMMARY.md

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('PR_SUMMARY.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });
```

## Next Steps

- [Pre-commit Hooks](pre-commit.md) - Local automation
- [Cursor Integration](cursor-integration.md) - IDE integration
- [CLI Reference](../cli-reference.md) - All commands

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

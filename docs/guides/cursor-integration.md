# Cursor IDE Integration

Give Cursor persistent memory of your project with MemDocs.

## Overview

Cursor IDE can read project context from special files to enhance AI conversations. MemDocs generates these files automatically, giving Cursor persistent memory of your codebase.

**Benefits:**
- 🧠 Cursor remembers your architecture across sessions
- 📍 AI knows exactly where code lives (file:line references)
- 🎯 Better code suggestions based on project patterns
- 👥 Team shares same AI context

## Quick Setup (2 minutes)

### 1. Generate Cursor Context

```bash
# Initialize MemDocs (if not already done)
memdocs init

# Document your codebase
memdocs review --path src/

# Export for Cursor
memdocs export cursor
```

This creates `.memdocs/cursor` file that Cursor automatically reads.

### 2. Configure Cursor

Cursor reads `.cursorrules` and `.memdocs/cursor` files automatically - no configuration needed!

**Files created:**
- `.memdocs/cursor` - Auto-generated project memory
- `.cursorrules` - (Optional) Custom instructions for Cursor

### 3. Restart Cursor

Close and reopen Cursor to load the new context.

## What Gets Included

The exported context includes:

### 1. Project Summary

High-level overview of your codebase:
```markdown
## Summary
- Payment processing system with Stripe integration
- RESTful API built with FastAPI
- PostgreSQL database with SQLAlchemy ORM
```

### 2. Code Map

Complete symbol index with line numbers:
```markdown
## Code Map

### src/payments/charge.py
- **class** `ChargeService` (line 45)
  - **method** `create_charge(amount, currency)` (line 67)
  - **method** `refund_charge(charge_id)` (line 89)
- **function** `validate_amount(amount)` (line 23)
```

### 3. Recent Changes

What changed recently:
```markdown
## Recent Changes
- Added webhook support for Stripe events
- Implemented retry logic for failed charges
- Added currency conversion for multi-currency support
```

### 4. Architecture Decisions

Important context about design:
```markdown
## Architecture
- Use async/await for all I/O operations
- Retry charges up to 3 times with exponential backoff
- Log all payment events to audit table
```

## Auto-Update Workflow

Keep Cursor's context fresh automatically.

### Option 1: Pre-commit Hook

Update context before every commit:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: memdocs-update
        name: Update MemDocs
        entry: bash -c 'memdocs review --path src/ && memdocs export cursor'
        language: system
        pass_filenames: false
        always_run: false
        files: '^src/.*\.(py|js|ts)$'
EOF

# Install hook
pre-commit install
```

Now context updates automatically when you commit code changes!

### Option 2: GitHub Actions

Update in CI/CD (see [GitHub Actions Guide](github-actions.md)):

```yaml
- name: Update Cursor context
  run: |
    memdocs review --path src/
    memdocs export cursor
    git add .memdocs/cursor
    git commit -m "docs: Update Cursor context [skip ci]"
```

### Option 3: Manual Updates

Update manually when needed:

```bash
# After making changes
memdocs review --path src/auth.py
memdocs export cursor

# Cursor will pick up changes automatically
```

## Advanced Configuration

### Custom Instructions

Create `.cursorrules` for project-specific instructions:

```markdown
# Project Rules for Cursor

## Code Style
- Use type hints for all function signatures
- Prefer async/await over callbacks
- Maximum line length: 100 characters

## Architecture
- All database access through repository pattern
- Use dependency injection for services
- Tests must achieve 90%+ coverage

## Specific to This Project
- Payment amounts are always in cents (integer)
- Use UTC for all timestamps
- Log all security events to audit table

## Common Patterns

### Creating a new API endpoint
1. Define Pydantic model in `schemas.py`
2. Add route in `routes.py`
3. Implement service in `services/`
4. Add tests in `tests/integration/`

### Database migrations
Use Alembic:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
```

Cursor reads both `.cursorrules` (your instructions) and `.memdocs/cursor` (auto-generated context).

### Exclude Sensitive Files

Don't include sensitive data in Cursor context:

```yaml
# .memdocs.yml
exclude:
  - secrets/**
  - .env*
  - credentials/**
  - "*/password*.py"
```

### Focus on Important Modules

Document only core modules:

```bash
# Document core business logic
memdocs review --path src/core/ src/services/

# Skip tests, migrations, etc.
```

## Usage in Cursor

### Ask Context-Aware Questions

With MemDocs context loaded, Cursor can answer:

**Q:** "How does authentication work?"

**A:** "Authentication is handled in `src/auth/jwt.py:45` by the `JWTAuthenticator` class. It validates tokens using RS256 and checks expiry. User sessions are stored in Redis with 24-hour TTL."

**Q:** "Where is the payment processing code?"

**A:** "Payment processing is in `src/payments/charge.py:67` in the `ChargeService.create_charge()` method. It integrates with Stripe API and includes retry logic for network failures."

### Get Better Code Suggestions

Cursor uses context to:
- Follow your project's patterns
- Reference existing utilities
- Use correct import paths
- Match your code style

### Navigate Code Faster

Ask Cursor for file locations:

**Q:** "Where is the user model defined?"

**A:** "`src/models/user.py:23` - The `User` class inherits from SQLAlchemy Base."

## Troubleshooting

### Cursor Not Using Context

**Problem:** Cursor seems unaware of your codebase

**Solutions:**
1. Verify `.memdocs/cursor` exists:
   ```bash
   ls -la .memdocs/cursor
   ```

2. Check file size (should be > 1KB):
   ```bash
   wc -c .memdocs/cursor
   ```

3. Regenerate context:
   ```bash
   memdocs export cursor --output .cursorrules
   ```

4. Restart Cursor completely

### Context Too Large

**Problem:** Context file exceeds Cursor's limits

**Solutions:**
1. Document only core modules:
   ```bash
   memdocs review --path src/core/ --emit docs
   ```

2. Exclude symbols:
   ```bash
   memdocs export cursor --no-symbols
   ```

3. Use module-level scope instead of repo:
   ```yaml
   # .memdocs.yml
   policies:
     default_scope: module
   ```

### Context Out of Date

**Problem:** Cursor has old information

**Solutions:**
1. Update and regenerate:
   ```bash
   memdocs review --path src/
   memdocs export cursor
   ```

2. Set up auto-update (pre-commit hook or GitHub Actions)

3. Add reminder to update weekly

### Sensitive Data in Context

**Problem:** Accidentally included secrets

**Solutions:**
1. Enable privacy guard:
   ```yaml
   # .memdocs.yml
   privacy:
     phi_mode: "strict"
     scrub:
       - email
       - phone
       - api_key
   ```

2. Regenerate context:
   ```bash
   memdocs review --path src/ --force
   memdocs export cursor
   ```

3. Add to `.gitignore` if needed:
   ```
   .memdocs/cursor
   ```

## Example Workflow

### Daily Development

```bash
# Morning: Update context with latest changes
git pull
memdocs review --path src/
memdocs export cursor

# During development: Cursor has full context
# (work in Cursor IDE)

# Before commit: Update context
memdocs review --path src/my_changes.py
memdocs export cursor
git add .
git commit -m "feat: Add new feature"
```

### Team Collaboration

```bash
# Commit your memory updates
git add .memdocs/
git commit -m "docs: Update AI memory"
git push

# Teammates pull and get same context
git pull
# Cursor automatically loads updated context
```

## Best Practices

### 1. Keep Context Fresh

Update context regularly:
- **Daily** - For active projects
- **Per feature** - Update when completing features
- **Pre-PR** - Update before pull requests

### 2. Review Before Committing

Check what's in the context:
```bash
cat .memdocs/cursor | head -50
```

Ensure no sensitive data is included.

### 3. Use .cursorrules for Conventions

Put coding standards in `.cursorrules`:
```markdown
## Code Conventions
- Use async/await
- Type hint everything
- Docstrings for public APIs
```

### 4. Document Core First

Start with most important modules:
```bash
memdocs review --path src/core/ src/api/ src/models/
```

### 5. Gitignore Strategy

**Recommended:** Commit `.memdocs/` to git (team shares context)

**Alternative:** Add to `.gitignore` (individual context)
```
.memdocs/
```

## Comparison with Other Methods

| Method | Pros | Cons |
|--------|------|------|
| **MemDocs** | Persistent, team-shared, auto-generated | Requires API key |
| **Manual .cursorrules** | Simple, no dependencies | Manual updates, inconsistent |
| **Cursor's @codebase** | Built-in | Ephemeral, not persistent across sessions |
| **Codebase indexing** | Automatic | Surface-level, no semantic understanding |

**Best approach:** Use MemDocs + custom `.cursorrules`

## Next Steps

- [GitHub Actions Guide](github-actions.md) - Automate updates
- [Configuration](../configuration.md) - Customize MemDocs
- [CLI Reference](../cli-reference.md) - All commands

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

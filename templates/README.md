# MemDocs Templates

Ready-to-use configuration templates for MemDocs integration.

## VS Code / Cursor Tasks

**File:** `.vscode/tasks.json`

Copy this file to your project's `.vscode/` directory to enable:

- **Auto-start MCP server** when opening project
- **Quick commands** for updating memory
- **Export commands** for Cursor/Claude
- **Stats command** for viewing memory status

### Installation

```bash
# Copy to your project
cp templates/.vscode/tasks.json /path/to/your-project/.vscode/

# Restart VS Code / Cursor
```

**Tasks available:**
- `MemDocs MCP Server` - Auto-starts on folder open
- `Update MemDocs Memory` - Manually update documentation
- `Export MemDocs for Cursor` - Export memory for Cursor IDE
- `MemDocs Stats` - View memory statistics

---

## Shell Hooks

Auto-start MemDocs MCP server when you `cd` into a project.

### Bash

**File:** `shell-hooks/bashrc.sh`

```bash
# Add to ~/.bashrc or ~/.bash_profile
cat templates/shell-hooks/bashrc.sh >> ~/.bashrc
source ~/.bashrc
```

### Zsh (macOS default)

**File:** `shell-hooks/zshrc.sh`

```bash
# Add to ~/.zshrc
cat templates/shell-hooks/zshrc.sh >> ~/.zshrc
source ~/.zshrc
```

### How it works

When you `cd` into a directory with `.memdocs.yml`:

1. Detects MemDocs configuration
2. Checks if MCP server is already running
3. Starts server in background if not running
4. Shows confirmation message

**Example:**
```bash
$ cd my-project/
🧠 MemDocs detected - starting MCP server...
✅ MemDocs MCP server started
   📍 Project: my-project
   🔗 Connected AI assistants will auto-load memory
```

---

## Claude Desktop Configuration

**Example configuration for `claude_desktop_config.json`:**

```json
{
  "mcpServers": {
    "memdocs": {
      "command": "memdocs",
      "args": ["serve", "--mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key-here"
      }
    }
  }
}
```

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/claude/claude_desktop_config.json`

---

## Git Hooks

Auto-update MemDocs memory on git operations.

### Post-Checkout Hook

```bash
#!/bin/bash
# .git/hooks/post-checkout

if [ -f ".memdocs.yml" ]; then
    echo "Updating MemDocs memory..."
    memdocs review --path src/ --silent
    memdocs export cursor --silent
fi
```

### Post-Merge Hook

```bash
#!/bin/bash
# .git/hooks/post-merge

if [ -f ".memdocs.yml" ]; then
    echo "Updating MemDocs memory after merge..."
    memdocs review --path src/ --silent
fi
```

### Installation

```bash
# Copy hooks to your project
cp templates/git-hooks/post-checkout .git/hooks/
cp templates/git-hooks/post-merge .git/hooks/

# Make executable
chmod +x .git/hooks/post-checkout
chmod +x .git/hooks/post-merge
```

---

## Systemd Service (Linux)

**File:** `systemd/memdocs-mcp.service`

Run MemDocs MCP server as a system service:

```bash
# Copy to user services
mkdir -p ~/.config/systemd/user/
cp templates/systemd/memdocs-mcp.service ~/.config/systemd/user/

# Edit to set your project path
nano ~/.config/systemd/user/memdocs-mcp.service

# Enable and start
systemctl --user enable memdocs-mcp
systemctl --user start memdocs-mcp

# Check status
systemctl --user status memdocs-mcp
```

---

## Docker Compose

**File:** `docker/docker-compose.yml`

Run MemDocs MCP server in Docker:

```bash
# Copy to your project
cp templates/docker/docker-compose.yml /path/to/your-project/

# Start server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop server
docker-compose down
```

---

## Usage Notes

### Auto-Start Priority

If you use multiple auto-start methods:

1. **VS Code tasks** - Best for per-project, IDE-specific
2. **Shell hooks** - Good for terminal-based workflows
3. **systemd service** - Best for always-running server
4. **Docker** - Best for containerized environments

**Recommendation:** Use **VS Code tasks** + **shell hooks** for most users.

### Avoiding Conflicts

If you have multiple auto-start methods, the server will only start once (checked by process name).

### Stopping Auto-Started Servers

```bash
# Find running servers
ps aux | grep "memdocs serve --mcp"

# Kill all MemDocs MCP servers
pkill -f "memdocs serve --mcp"
```

---

## See Also

- [MCP Setup Guide](../docs/guides/mcp-setup.md) - Detailed MCP configuration
- [Cursor Integration](../docs/guides/cursor-integration.md) - Cursor-specific tips
- [Architecture](../docs/architecture.md) - How MCP server works

---

**Questions?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

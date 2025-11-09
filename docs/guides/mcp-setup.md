# MCP Server Setup

Auto-load MemDocs memory into AI assistants using the Model Context Protocol (MCP).

## Overview

The **Model Context Protocol (MCP)** is a standard for serving context to AI assistants. MemDocs includes an MCP server that automatically serves your project memory to any MCP-compatible tool.

**Supported tools:**
- ✅ Claude Desktop
- ✅ Cursor IDE
- ✅ Continue.dev
- ✅ Any MCP-compatible client

## Quick Start

### 1. Start MCP Server

```bash
# Navigate to your project
cd your-project

# Start MCP server
memdocs serve --mcp
```

The server will:
- Auto-detect `.memdocs/` directory
- Load memory and embeddings
- Listen on default port (configurable)
- Serve context to connected clients

### 2. Connect Your AI Assistant

See platform-specific setup below:
- [Claude Desktop](#claude-desktop-setup)
- [Cursor IDE](#cursor-ide-setup)
- [VS Code + Continue.dev](#vs-code--continuedev-setup)

---

## Claude Desktop Setup

### Prerequisites

- Claude Desktop app ([download here](https://claude.ai/download))
- MemDocs installed (`pip install memdocs[embeddings]`)
- Project with `.memdocs/` directory

### Configuration

1. **Locate Claude Desktop config:**

   ```bash
   # macOS
   ~/Library/Application Support/Claude/claude_desktop_config.json

   # Windows
   %APPDATA%\Claude\claude_desktop_config.json

   # Linux
   ~/.config/claude/claude_desktop_config.json
   ```

2. **Add MemDocs MCP server:**

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

3. **Restart Claude Desktop**

4. **Test the integration:**

   Open Claude Desktop and ask:
   ```
   What files are documented in this project?
   ```

   Claude should be able to access your MemDocs memory!

### Per-Project Configuration

For project-specific MCP servers, use environment variables:

```json
{
  "mcpServers": {
    "memdocs-myproject": {
      "command": "memdocs",
      "args": ["serve", "--mcp", "--docs-dir", "/path/to/project/.memdocs/docs"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key-here",
        "MEMDOCS_PROJECT": "my-project"
      }
    }
  }
}
```

---

## Cursor IDE Setup

### Prerequisites

- Cursor IDE ([download here](https://cursor.sh))
- MemDocs installed
- Project with `.memdocs/` directory

### Option 1: VS Code Tasks (Recommended)

1. **Create `.vscode/tasks.json` in your project:**

   ```json
   {
     "version": "2.0.0",
     "tasks": [
       {
         "label": "MemDocs MCP Server",
         "type": "shell",
         "command": "memdocs",
         "args": ["serve", "--mcp"],
         "isBackground": true,
         "problemMatcher": [],
         "runOptions": {
           "runOn": "folderOpen"
         },
         "presentation": {
           "echo": false,
           "reveal": "never",
           "focus": false,
           "panel": "shared",
           "showReuseMessage": false,
           "clear": false
         }
       }
     ]
   }
   ```

2. **Enable auto-run:**

   Add to `.vscode/settings.json`:
   ```json
   {
     "task.autoStart": ["MemDocs MCP Server"]
   }
   ```

3. **Restart Cursor**

The MCP server will automatically start when you open the project!

### Option 2: Manual Start

```bash
# In terminal within Cursor
memdocs serve --mcp &
```

### Verify Connection

In Cursor's AI chat, ask:
```
Search MemDocs for "authentication"
```

---

## VS Code + Continue.dev Setup

### Prerequisites

- VS Code
- Continue.dev extension
- MemDocs installed

### Configuration

1. **Install Continue.dev extension**

2. **Open Continue settings** (Command Palette → "Continue: Open Config")

3. **Add MemDocs context provider:**

   ```json
   {
     "contextProviders": [
       {
         "name": "memdocs",
         "params": {
           "serverUrl": "http://localhost:8765",
           "type": "mcp"
         }
       }
     ]
   }
   ```

4. **Start MCP server:**

   Use VS Code tasks (same as Cursor setup above) or manual start.

---

## Auto-Start Strategies

### Option 1: Shell Hook (Automatic)

Add to your `.bashrc` or `.zshrc`:

```bash
# Auto-start MemDocs MCP server when entering project
function cd() {
  builtin cd "$@"

  # Check if .memdocs.yml exists
  if [ -f ".memdocs.yml" ]; then
    # Check if MCP server is already running
    if ! pgrep -f "memdocs serve --mcp" > /dev/null; then
      echo "Starting MemDocs MCP server..."
      memdocs serve --mcp --daemon &
    fi
  fi
}
```

**Reload shell:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

Now MCP server starts automatically when you `cd` into a MemDocs project!

### Option 2: VS Code Tasks (Per-Project)

See [Cursor IDE Setup](#cursor-ide-setup) above - same approach works for VS Code.

### Option 3: tmux/Screen Session

For persistent background server:

```bash
# Start in tmux session
tmux new-session -d -s memdocs "memdocs serve --mcp"

# Attach when needed
tmux attach -t memdocs

# Kill when done
tmux kill-session -t memdocs
```

### Option 4: systemd Service (Linux)

For always-running MCP server:

```ini
# ~/.config/systemd/user/memdocs-mcp.service
[Unit]
Description=MemDocs MCP Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/memdocs serve --mcp --docs-dir %h/projects/myproject/.memdocs/docs
Restart=on-failure
Environment="ANTHROPIC_API_KEY=your-key-here"

[Install]
WantedBy=default.target
```

**Enable and start:**
```bash
systemctl --user enable memdocs-mcp
systemctl --user start memdocs-mcp
```

---

## MCP Server Configuration

### Command-Line Options

```bash
memdocs serve --mcp [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `localhost` | Host to bind to |
| `--port` | `8765` | Port to listen on |
| `--docs-dir` | `.memdocs/docs` | Documentation directory |
| `--memory-dir` | `.memdocs/memory` | Memory directory |
| `--daemon` | `false` | Run in background |
| `--log-level` | `INFO` | Logging level (DEBUG, INFO, WARN, ERROR) |
| `--no-embeddings` | `false` | Disable embedding search |

### Examples

```bash
# Custom port
memdocs serve --mcp --port 9000

# Run in background
memdocs serve --mcp --daemon

# Debug mode
memdocs serve --mcp --log-level DEBUG

# Multiple projects (different ports)
memdocs serve --mcp --port 8765 --docs-dir ~/project1/.memdocs/docs &
memdocs serve --mcp --port 8766 --docs-dir ~/project2/.memdocs/docs &
```

---

## MCP Tools Available

When connected via MCP, AI assistants can use these tools:

### `search_memory`

Search project memory with natural language:

```json
{
  "tool": "search_memory",
  "params": {
    "query": "authentication flow",
    "k": 5
  }
}
```

### `get_symbols`

Get code symbols for a specific file:

```json
{
  "tool": "get_symbols",
  "params": {
    "file": "src/auth/jwt.py"
  }
}
```

### `get_documentation`

Get full documentation for a file:

```json
{
  "tool": "get_documentation",
  "params": {
    "file": "src/payments/charge.py"
  }
}
```

### `list_files`

List all documented files:

```json
{
  "tool": "list_files",
  "params": {}
}
```

### `get_stats`

Get memory statistics:

```json
{
  "tool": "get_stats",
  "params": {}
}
```

---

## Troubleshooting

### Server Won't Start

**Problem:** `Error: Cannot bind to port 8765`

**Solution:**
```bash
# Check if port is in use
lsof -i :8765

# Kill existing process
kill -9 <PID>

# Or use different port
memdocs serve --mcp --port 8766
```

### Client Can't Connect

**Problem:** Claude Desktop / Cursor can't reach MCP server

**Solutions:**

1. **Check server is running:**
   ```bash
   ps aux | grep "memdocs serve"
   ```

2. **Verify port:**
   ```bash
   curl http://localhost:8765/health
   # Should return: {"status": "ok"}
   ```

3. **Check firewall** (if using remote server)

4. **Review logs:**
   ```bash
   memdocs serve --mcp --log-level DEBUG
   ```

### Memory Not Loading

**Problem:** MCP server starts but memory not available

**Solutions:**

1. **Verify memory exists:**
   ```bash
   ls -la .memdocs/docs/
   ls -la .memdocs/memory/
   ```

2. **Regenerate memory:**
   ```bash
   memdocs review --path src/
   ```

3. **Check server logs for errors**

### Performance Issues

**Problem:** MCP server slow to respond

**Solutions:**

1. **Disable embeddings** (if not needed):
   ```bash
   memdocs serve --mcp --no-embeddings
   ```

2. **Reduce memory size**:
   - Document fewer files
   - Use file-level scope instead of module/repo

3. **Increase resources**:
   - Close other applications
   - Use faster storage (SSD)

---

## Advanced Usage

### Multi-Project Setup

Serve memory from multiple projects simultaneously:

```bash
#!/bin/bash
# start-all-mcp-servers.sh

memdocs serve --mcp --port 8765 --docs-dir ~/project1/.memdocs/docs --daemon
memdocs serve --mcp --port 8766 --docs-dir ~/project2/.memdocs/docs --daemon
memdocs serve --mcp --port 8767 --docs-dir ~/project3/.memdocs/docs --daemon

echo "Started MCP servers on ports 8765-8767"
```

**Configure in Claude Desktop:**
```json
{
  "mcpServers": {
    "project1": {
      "command": "memdocs",
      "args": ["serve", "--mcp", "--port", "8765", "--docs-dir", "/Users/you/project1/.memdocs/docs"]
    },
    "project2": {
      "command": "memdocs",
      "args": ["serve", "--mcp", "--port", "8766", "--docs-dir", "/Users/you/project2/.memdocs/docs"]
    }
  }
}
```

### Remote MCP Server

Serve memory over network:

```bash
# On server
memdocs serve --mcp --host 0.0.0.0 --port 8765

# On client (Claude Desktop config)
{
  "mcpServers": {
    "remote-memdocs": {
      "serverUrl": "http://your-server.com:8765",
      "type": "remote"
    }
  }
}
```

**Security note:** Use HTTPS and authentication for remote servers!

### Docker Deployment

```dockerfile
FROM python:3.11-slim

RUN pip install memdocs[embeddings]

WORKDIR /workspace

CMD ["memdocs", "serve", "--mcp", "--host", "0.0.0.0"]
```

```bash
docker run -v $(pwd)/.memdocs:/workspace/.memdocs -p 8765:8765 memdocs-mcp
```

---

## Best Practices

### 1. Use Tasks for Auto-Start

**Recommended:** VS Code tasks for per-project auto-start
- Automatically starts when opening project
- No global shell configuration needed
- Easy to disable per-project

### 2. Run in Background

**For long-term use:**
```bash
memdocs serve --mcp --daemon
```

Prevents terminal clutter and survives terminal closure.

### 3. Update Memory Regularly

MCP server loads memory on start. After updating docs:

```bash
# Kill existing server
pkill -f "memdocs serve --mcp"

# Restart
memdocs serve --mcp --daemon
```

Or use live reload (experimental):
```bash
memdocs serve --mcp --watch
```

### 4. Monitor Server Health

Add health check to your workflow:

```bash
# Check if server is responsive
curl -s http://localhost:8765/health || echo "MCP server down!"
```

---

## Next Steps

- **[VS Code Extension](vscode-extension.md)** - Enhanced UX with status indicators (coming soon)
- **[Claude Desktop Guide](claude-desktop.md)** - Advanced Claude integration tips
- **[Architecture](../architecture.md)** - How MCP server works internally

---

**Need help?** Open an issue at [github.com/Smart-AI-Memory/memdocs/issues](https://github.com/Smart-AI-Memory/memdocs/issues)

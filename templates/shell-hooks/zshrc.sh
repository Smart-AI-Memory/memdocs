#!/bin/zsh
# MemDocs Auto-Start Hook for Zsh
# Add this to your ~/.zshrc

# Auto-start MemDocs MCP server when entering a project with MemDocs
memdocs_auto_start() {
    # Check if .memdocs.yml exists in current directory
    if [ -f ".memdocs.yml" ]; then
        # Check if MCP server is already running for this project
        local project_dir=$(pwd)
        if ! pgrep -f "memdocs serve --mcp.*$project_dir" > /dev/null 2>&1; then
            echo "🧠 MemDocs detected - starting MCP server..."

            # Start MCP server in background
            (cd "$project_dir" && memdocs serve --mcp --daemon) &

            # Give it a moment to start
            sleep 1

            echo "✅ MemDocs MCP server started"
            echo "   📍 Project: $(basename $project_dir)"
            echo "   🔗 Connected AI assistants will auto-load memory"
        fi
    fi
}

# Hook into chpwd (zsh's directory change hook)
chpwd_functions+=(memdocs_auto_start)

# Also check when opening a new shell in a MemDocs project
memdocs_auto_start

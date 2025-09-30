#!/bin/bash

# Toggle script for switching between Python and JavaScript cc-sessions implementations

CLAUDE_DIR=".claude"
SESSIONS_DIR="sessions"
CC_SESSIONS_DIR="cc-sessions/cc_sessions"

# Check if we're in the project root
if [ ! -d "$CLAUDE_DIR" ] || [ ! -d "$SESSIONS_DIR" ]; then
    echo "Error: Must be run from project root (directory with .claude and sessions)"
    exit 1
fi

# Check which version is currently active
if [ -f "$CLAUDE_DIR/settings.json.js" ]; then
    # Python is active, switch to JavaScript
    echo "Switching from Python to JavaScript implementation..."

    # Switch settings files
    mv "$CLAUDE_DIR/settings.json" "$CLAUDE_DIR/settings.json.py"
    mv "$CLAUDE_DIR/settings.json.js" "$CLAUDE_DIR/settings.json"
    echo "✓ Switched settings.json to JavaScript version"

    # Remove Python symlinks and directory structure
    if [ -d "$SESSIONS_DIR/hooks" ]; then
        # Remove all symlinks in hooks directory
        find "$SESSIONS_DIR/hooks" -type l -delete
        # Remove any __pycache__ directories
        rm -rf "$SESSIONS_DIR/hooks/__pycache__"
        # Remove the hooks directory if it's now empty
        rmdir "$SESSIONS_DIR/hooks" 2>/dev/null || true
    else
        rm -f "$SESSIONS_DIR/hooks"
    fi
    rm -f "$SESSIONS_DIR/scripts"
    rm -f "$SESSIONS_DIR/statusline.py"

    # Create JavaScript symlinks
    ln -s "../$CC_SESSIONS_DIR/hooks" "$SESSIONS_DIR/hooks"
    ln -s "../$CC_SESSIONS_DIR/scripts" "$SESSIONS_DIR/scripts"
    ln -s "../$CC_SESSIONS_DIR/scripts/statusline.js" "$SESSIONS_DIR/statusline.js"
    echo "✓ Updated symlinks to JavaScript versions"

    echo ""
    echo "🟢 JavaScript implementation is now active"
    echo "Hooks will use: node"
    echo "API will use: node $SESSIONS_DIR/scripts/api/index.js"

elif [ -f "$CLAUDE_DIR/settings.json.py" ]; then
    # JavaScript is active, switch to Python
    echo "Switching from JavaScript to Python implementation..."

    # Switch settings files
    mv "$CLAUDE_DIR/settings.json" "$CLAUDE_DIR/settings.json.js"
    mv "$CLAUDE_DIR/settings.json.py" "$CLAUDE_DIR/settings.json"
    echo "✓ Switched settings.json to Python version"

    # Remove JavaScript symlinks
    if [ -d "$SESSIONS_DIR/hooks" ]; then
        # Remove all symlinks in hooks directory
        find "$SESSIONS_DIR/hooks" -type l -delete
        # Remove any __pycache__ directories
        rm -rf "$SESSIONS_DIR/hooks/__pycache__"
        # Remove the hooks directory if it's now empty
        rmdir "$SESSIONS_DIR/hooks" 2>/dev/null || true
    else
        rm -f "$SESSIONS_DIR/hooks"
    fi
    rm -f "$SESSIONS_DIR/scripts"
    rm -f "$SESSIONS_DIR/statusline.js"

    # Create Python symlinks
    ln -s "../$CC_SESSIONS_DIR/hooks" "$SESSIONS_DIR/hooks"
    ln -s "../$CC_SESSIONS_DIR/scripts" "$SESSIONS_DIR/scripts"
    ln -s "../$CC_SESSIONS_DIR/scripts/statusline.py" "$SESSIONS_DIR/statusline.py"
    echo "✓ Updated symlinks to Python versions"

    echo ""
    echo "🐍 Python implementation is now active"
    echo "Hooks will use: python"
    echo "API will use: python -m sessions.api"

else
    echo "Error: No alternate settings file found"
    echo "Expected either .claude/settings.json.js or .claude/settings.json.py"
    exit 1
fi

# Verify symlinks
echo ""
echo "Current symlinks in $SESSIONS_DIR:"
ls -la "$SESSIONS_DIR" | grep " -> "
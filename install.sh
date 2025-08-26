#!/bin/bash

# Claude Code Sessions - Installation Script
# This script sets up the sessions framework for task management

set -e  # Exit on error

echo "╔══════════════════════════════════════════╗"
echo "║    Claude Code Sessions Installer       ║"
echo "╚══════════════════════════════════════════╝"
echo

# Check for required dependencies
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(pwd)"

# Check for CLAUDE_PROJECT_DIR environment variable
if [ -z "$CLAUDE_PROJECT_DIR" ]; then
    echo "⚠️  CLAUDE_PROJECT_DIR not set. Setting it to current directory."
    export CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
    echo "   CLAUDE_PROJECT_DIR=$PROJECT_ROOT"
    echo
    echo "   To make this permanent, add to your shell profile:"
    echo "   export CLAUDE_PROJECT_DIR=\"$PROJECT_ROOT\""
    echo
fi

# Check if we're in a git repository (recommended)
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  Warning: Not in a git repository. Sessions works best with git."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo "Creating directory structure..."
mkdir -p "$PROJECT_ROOT/.claude/hooks"
mkdir -p "$PROJECT_ROOT/.claude/state"
mkdir -p "$PROJECT_ROOT/.claude/agents"
mkdir -p "$PROJECT_ROOT/sessions/tasks/done"
mkdir -p "$PROJECT_ROOT/sessions/protocols"
mkdir -p "$PROJECT_ROOT/sessions/agents"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install tiktoken --quiet || pip install tiktoken --quiet

# Copy hooks
echo "Installing hooks..."
cp "$SCRIPT_DIR/hooks/"*.py "$PROJECT_ROOT/.claude/hooks/"
chmod +x "$PROJECT_ROOT/.claude/hooks/"*.py

# Copy protocols
echo "Installing protocols..."
cp "$SCRIPT_DIR/protocols/"*.md "$PROJECT_ROOT/sessions/protocols/"

# Copy agents
echo "Installing agent definitions..."
cp "$SCRIPT_DIR/agents/"*.md "$PROJECT_ROOT/.claude/agents/"

# Copy templates
echo "Installing templates..."
cp "$SCRIPT_DIR/templates/TEMPLATE.md" "$PROJECT_ROOT/sessions/tasks/"

# Copy knowledge files
echo "Installing Claude Code knowledge base..."
mkdir -p "$PROJECT_ROOT/sessions/knowledge"
if [ -d "$SCRIPT_DIR/knowledge/claude-code" ]; then
    cp -r "$SCRIPT_DIR/knowledge/claude-code" "$PROJECT_ROOT/sessions/knowledge/"
fi

# Install daic command
echo "Installing daic command..."
if [ -w "/usr/local/bin" ]; then
    cp "$SCRIPT_DIR/scripts/daic" "/usr/local/bin/"
    chmod +x "/usr/local/bin/daic"
else
    echo "⚠️  Cannot write to /usr/local/bin. Trying with sudo..."
    sudo cp "$SCRIPT_DIR/scripts/daic" "/usr/local/bin/"
    sudo chmod +x "/usr/local/bin/daic"
fi

# Interactive configuration
echo
echo "═══════════════════════════════════════════"
echo "           Configuration Setup"
echo "═══════════════════════════════════════════"
echo

# Developer name
read -p "Your name (for session context): " developer_name
if [ -z "$developer_name" ]; then
    developer_name="the developer"
fi

# Optional statusline installation
echo
echo "Statusline Installation:"
echo "The sessions system includes a statusline script that shows:"
echo "- Current task and DAIC mode"
echo "- Token usage and warnings"
echo "- File change counts"
echo
read -p "Install sessions statusline? (y/n): " -n 1 -r
echo
install_statusline="n"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_statusline="y"
    if [ -f "$SCRIPT_DIR/scripts/statusline-script.sh" ]; then
        echo "Installing statusline script..."
        cp "$SCRIPT_DIR/scripts/statusline-script.sh" "$PROJECT_ROOT/.claude/"
        chmod +x "$PROJECT_ROOT/.claude/statusline-script.sh"
        
        # Create project-level settings.json with statusline config
        echo "Configuring statusline settings..."
        cat > "$PROJECT_ROOT/.claude/settings.json" << EOF
{
  "statusLine": {
    "type": "command",
    "command": "\$CLAUDE_PROJECT_DIR/.claude/statusline-script.sh",
    "padding": 0
  }
}
EOF
        echo "✅ Statusline installed and configured automatically"
        echo "   Configuration saved to .claude/settings.json"
    else
        echo "⚠️  Statusline script not found in package. Skipping."
    fi
fi

# DAIC trigger phrases
echo
echo "DAIC (Discussion, Alignment, Implementation, Check) System:"
echo "By default, Claude will discuss before implementing."
echo "Trigger phrases switch to implementation mode."
echo
echo "Default triggers: 'make it so', 'run that'"
read -p "Add custom trigger phrase (or press Enter to skip): " custom_trigger
triggers='["make it so", "run that"'
if [ -n "$custom_trigger" ]; then
    triggers="$triggers, \"$custom_trigger\""
fi
triggers="$triggers]"

# Advanced configuration prompt
echo
read -p "Configure advanced options? (y/n): " -n 1 -r
echo
advanced_config="n"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    advanced_config="y"
fi

# Tool blocking configuration (advanced)
blocked_tools='["Edit", "Write", "MultiEdit", "NotebookEdit"]'
if [ "$advanced_config" = "y" ]; then
    echo
    echo "Tool Blocking Configuration:"
    echo "Current blocked tools in discussion mode: Edit, Write, MultiEdit, NotebookEdit"
    echo "Available tools: Bash, Read, Grep, Glob, LS, WebSearch, WebFetch, Task"
    read -p "Modify blocked tools list? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter comma-separated list of tools to block: " custom_blocked
        if [ -n "$custom_blocked" ]; then
            # Convert to JSON array format
            blocked_tools="[$(echo "$custom_blocked" | sed 's/\([^,]*\)/"\1"/g')]"
        fi
    fi
fi

# Task prefixes (advanced)
task_prefixes_config=""
if [ "$advanced_config" = "y" ]; then
    echo
    echo "Task Prefix Configuration:"
    echo "Default: h- (high), m- (medium), l- (low), ?- (investigate)"
    read -p "Customize task prefixes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "High priority prefix [h-]: " high_prefix
        read -p "Medium priority prefix [m-]: " med_prefix
        read -p "Low priority prefix [l-]: " low_prefix
        read -p "Investigate prefix [?-]: " inv_prefix
        
        high_prefix="${high_prefix:-h-}"
        med_prefix="${med_prefix:-m-}"
        low_prefix="${low_prefix:-l-}"
        inv_prefix="${inv_prefix:-?-}"
        
        task_prefixes_config=',
  "task_prefixes": {
    "priority": ["'$high_prefix'", "'$med_prefix'", "'$low_prefix'", "'$inv_prefix'"]
  }'
    fi
fi

# Create configuration file
echo "Creating configuration..."
cat > "$PROJECT_ROOT/.claude/sessions-config.json" << EOF
{
  "developer_name": "$developer_name",
  "trigger_phrases": $triggers,
  "blocked_tools": $blocked_tools,
  "task_detection": {
    "enabled": true
  },
  "branch_enforcement": {
    "enabled": true
  }$task_prefixes_config
}
EOF

# Initialize DAIC state
echo '{"mode": "discussion"}' > "$PROJECT_ROOT/.claude/state/daic-mode.json"

# Create initial task state
cat > "$PROJECT_ROOT/.claude/state/current_task.json" << EOF
{
  "task": null,
  "branch": null,
  "services": [],
  "updated": "$(date +%Y-%m-%d)"
}
EOF

# CLAUDE.md Integration
echo
echo "═══════════════════════════════════════════"
echo "         CLAUDE.md Integration"
echo "═══════════════════════════════════════════"
echo
echo "The sessions system is designed to preserve context by loading only"
echo "what's needed for the current task. Keep your root CLAUDE.md minimal"
echo "with project overview and behavioral rules. Task-specific context is"
echo "loaded dynamically through the sessions system."
echo
echo "Your CLAUDE.md should be < 100 lines. Detailed documentation belongs"
echo "in task context manifests, not the root file."
echo

# Copy CLAUDE.sessions.md to project root
echo "Installing CLAUDE.sessions.md..."
cp "$SCRIPT_DIR/templates/CLAUDE.sessions.md" "$PROJECT_ROOT/"

# Create or update CLAUDE.md
if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    echo "Creating CLAUDE.md from template..."
    cp "$SCRIPT_DIR/templates/CLAUDE.example.md" "$PROJECT_ROOT/CLAUDE.md"
    echo "✅ CLAUDE.md created from best practice template"
    echo "   Please customize the project overview section"
else
    echo "CLAUDE.md already exists, checking for sessions include..."
    # Check if the include already exists
    if grep -q "@CLAUDE.sessions.md" "$PROJECT_ROOT/CLAUDE.md"; then
        echo "✅ CLAUDE.md already includes sessions behaviors"
    else
        echo "Adding sessions include to existing CLAUDE.md..."
        echo "" >> "$PROJECT_ROOT/CLAUDE.md"
        echo "## Sessions System Behaviors" >> "$PROJECT_ROOT/CLAUDE.md"
        echo "" >> "$PROJECT_ROOT/CLAUDE.md"
        echo "@CLAUDE.sessions.md" >> "$PROJECT_ROOT/CLAUDE.md"
        echo "✅ Added @CLAUDE.sessions.md include to your CLAUDE.md"
        echo
        echo "⚠️  Please review your CLAUDE.md and consider:"
        echo "   - Moving detailed documentation to task context manifests"
        echo "   - Keeping only project overview and core rules"
        echo "   - See CLAUDE.example.md for best practices"
    fi
fi

# Final checks
echo
echo "═══════════════════════════════════════════"
echo "          Installation Complete!"
echo "═══════════════════════════════════════════"
echo
echo "✅ Directory structure created"
echo "✅ Hooks installed"
echo "✅ Protocols and agents installed"
echo "✅ daic command available"
echo "✅ Configuration saved"
echo "✅ DAIC state initialized (Discussion mode)"
echo

# Test daic command
if command -v daic &> /dev/null; then
    echo "Testing daic command..."
    daic > /dev/null 2>&1
    echo "✅ daic command working"
else
    echo "⚠️  daic command not in PATH. Add /usr/local/bin to your PATH."
fi

echo
echo "Next steps:"
echo "1. Restart Claude Code to load the hooks"
echo "2. Create your first task: cp sessions/tasks/TEMPLATE.md sessions/tasks/m-my-first-task.md"
echo "3. Start working with DAIC workflow!"
echo
echo "Documentation: sessions/protocols/README.md"
echo "Developer: $developer_name"
echo
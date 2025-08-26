#!/bin/bash

# Claude Code Sessions - Installation Script
# This script sets up the sessions framework for task management

set -e  # Exit on error

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║            cc-sessions Installer           ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════╝${NC}"
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
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║                    CONFIGURATION SETUP                        ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo

# Developer name section
echo -e "${BOLD}${MAGENTA}★ DEVELOPER IDENTITY${NC}"
echo -e "${DIM}$(printf '─%.0s' {1..60})${NC}"
echo -e "${DIM}  Claude will use this name when addressing you in sessions${NC}"
echo

read -p "$(echo -e ${CYAN})  Your name: $(echo -e ${NC})" developer_name
if [ -z "$developer_name" ]; then
    developer_name="the developer"
fi
echo -e "${GREEN}  ✓ Hello, $developer_name!${NC}"

# Statusline installation section
echo
echo -e "${BOLD}${MAGENTA}★ STATUSLINE INSTALLATION${NC}"
echo -e "${DIM}$(printf '─%.0s' {1..60})${NC}"
echo -e "${WHITE}  Real-time status display in Claude Code showing:${NC}"
echo -e "${CYAN}    • Current task and DAIC mode${NC}"
echo -e "${CYAN}    • Token usage with visual progress bar${NC}"
echo -e "${CYAN}    • Modified file counts${NC}"
echo -e "${CYAN}    • Open task count${NC}"
echo

read -p "$(echo -e ${CYAN})  Install statusline? (y/n): $(echo -e ${NC})" -n 1 -r
echo
install_statusline="n"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_statusline="y"
    if [ -f "$SCRIPT_DIR/scripts/statusline-script.sh" ]; then
        echo -e "${DIM}  Installing statusline script...${NC}"
        cp "$SCRIPT_DIR/scripts/statusline-script.sh" "$PROJECT_ROOT/.claude/"
        chmod +x "$PROJECT_ROOT/.claude/statusline-script.sh"
        echo -e "${GREEN}  ✓ Statusline installed successfully${NC}"
    else
        echo -e "${YELLOW}  ⚠ Statusline script not found in package${NC}"
    fi
fi

# DAIC trigger phrases section
echo
echo -e "${BOLD}${MAGENTA}★ DAIC WORKFLOW CONFIGURATION${NC}"
echo -e "${DIM}$(printf '─%.0s' {1..60})${NC}"
echo -e "${WHITE}  The DAIC system enforces discussion before implementation.${NC}"
echo -e "${WHITE}  Trigger phrases tell Claude when you're ready to proceed.${NC}"
echo
echo -e "${CYAN}  Default triggers:${NC}"
echo -e "${GREEN}    → \"make it so\"${NC}"
echo -e "${GREEN}    → \"run that\"${NC}"
echo -e "${GREEN}    → \"go ahead\"${NC}"
echo -e "${GREEN}    → \"yert\"${NC}"
echo
echo -e "${DIM}  Hint: Common additions: \"implement it\", \"do it\", \"proceed\"${NC}"
echo

# Allow adding multiple custom trigger phrases
triggers='["make it so", "run that", "go ahead", "yert"'
while true; do
    read -p "$(echo -e ${CYAN})  Add custom trigger phrase (Enter to skip): $(echo -e ${NC})" custom_trigger
    if [ -z "$custom_trigger" ]; then
        break
    fi
    triggers="$triggers, \"$custom_trigger\""
    echo -e "${GREEN}  ✓ Added: \"$custom_trigger\"${NC}"
done
triggers="$triggers]"

# Advanced configuration
echo
echo -e "${BOLD}${MAGENTA}★ ADVANCED OPTIONS${NC}"
echo -e "${DIM}$(printf '─%.0s' {1..60})${NC}"
echo -e "${WHITE}  Configure tool blocking, task prefixes, and more${NC}"
echo

read -p "$(echo -e ${CYAN})  Configure advanced options? (y/n): $(echo -e ${NC})" -n 1 -r
echo
advanced_config="n"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    advanced_config="y"
fi

# Tool blocking configuration (advanced)
blocked_tools='["Edit", "Write", "MultiEdit", "NotebookEdit"]'
if [ "$advanced_config" = "y" ]; then
    echo
    echo -e "${CYAN}╭───────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│              Tool Blocking Configuration                      │${NC}"
    echo -e "${CYAN}├───────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${DIM}│   Tools can be blocked in discussion mode to enforce DAIC     │${NC}"
    echo -e "${DIM}│   Default: Edit, Write, MultiEdit, NotebookEdit are blocked   │${NC}"
    echo -e "${CYAN}╰───────────────────────────────────────────────────────────────╯${NC}"
    echo
    echo -e "${WHITE}  Available tools:${NC}"
    echo -e "    1. ${YELLOW}🔒${NC} Edit - Edit existing files"
    echo -e "    2. ${YELLOW}🔒${NC} Write - Create new files"
    echo -e "    3. ${YELLOW}🔒${NC} MultiEdit - Multiple edits in one operation"
    echo -e "    4. ${YELLOW}🔒${NC} NotebookEdit - Edit Jupyter notebooks"
    echo -e "    5. ${GREEN}🔓${NC} Bash - Run shell commands"
    echo -e "    6. ${GREEN}🔓${NC} Read - Read file contents"
    echo -e "    7. ${GREEN}🔓${NC} Grep - Search file contents"
    echo -e "    8. ${GREEN}🔓${NC} Glob - Find files by pattern"
    echo -e "    9. ${GREEN}🔓${NC} LS - List directory contents"
    echo -e "   10. ${GREEN}🔓${NC} WebSearch - Search the web"
    echo -e "   11. ${GREEN}🔓${NC} WebFetch - Fetch web content"
    echo -e "   12. ${GREEN}🔓${NC} Task - Launch specialized agents"
    echo
    echo -e "${DIM}  Hint: Edit tools are typically blocked to enforce discussion-first workflow${NC}"
    echo
    read -p "$(echo -e ${CYAN})  Modify blocked tools list? (y/n): $(echo -e ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "$(echo -e ${CYAN})  Enter comma-separated tool numbers to block: $(echo -e ${NC})" tool_numbers
        if [ -n "$tool_numbers" ]; then
            # Map numbers to tool names
            tools_array=("Edit" "Write" "MultiEdit" "NotebookEdit" "Bash" "Read" "Grep" "Glob" "LS" "WebSearch" "WebFetch" "Task")
            blocked_list=""
            IFS=',' read -ra NUMS <<< "$tool_numbers"
            for num in "${NUMS[@]}"; do
                num=$(echo $num | tr -d ' ')
                if [ "$num" -ge 1 ] && [ "$num" -le 12 ]; then
                    tool_idx=$((num - 1))
                    if [ -n "$blocked_list" ]; then
                        blocked_list="$blocked_list, \"${tools_array[$tool_idx]}\""
                    else
                        blocked_list="\"${tools_array[$tool_idx]}\""
                    fi
                fi
            done
            blocked_tools="[$blocked_list]"
            echo -e "${GREEN}  ✓ Tool blocking configuration saved${NC}"
        fi
    fi
fi

# Task prefixes (advanced)
task_prefixes_config=""
if [ "$advanced_config" = "y" ]; then
    echo
    echo -e "${BOLD}${MAGENTA}★ TASK PREFIX CONFIGURATION${NC}"
    echo -e "${DIM}$(printf '─%.0s' {1..60})${NC}"
    echo -e "${WHITE}  Task prefixes organize work by priority and type${NC}"
    echo
    echo -e "${CYAN}  Current prefixes:${NC}"
    echo -e "${WHITE}    → h- (high priority)${NC}"
    echo -e "${WHITE}    → m- (medium priority)${NC}"
    echo -e "${WHITE}    → l- (low priority)${NC}"
    echo -e "${WHITE}    → ?- (investigate/research)${NC}"
    echo
    
    read -p "$(echo -e ${CYAN})  Customize task prefixes? (y/n): $(echo -e ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "$(echo -e ${CYAN})  High priority prefix [h-]: $(echo -e ${NC})" high_prefix
        read -p "$(echo -e ${CYAN})  Medium priority prefix [m-]: $(echo -e ${NC})" med_prefix
        read -p "$(echo -e ${CYAN})  Low priority prefix [l-]: $(echo -e ${NC})" low_prefix
        read -p "$(echo -e ${CYAN})  Investigate prefix [?-]: $(echo -e ${NC})" inv_prefix
        
        high_prefix="${high_prefix:-h-}"
        med_prefix="${med_prefix:-m-}"
        low_prefix="${low_prefix:-l-}"
        inv_prefix="${inv_prefix:-?-}"
        
        task_prefixes_config=',
  "task_prefixes": {
    "priority": ["'$high_prefix'", "'$med_prefix'", "'$low_prefix'", "'$inv_prefix'"]
  }'
        echo -e "${GREEN}  ✓ Task prefixes updated${NC}"
    fi
fi

# Create configuration file
echo -e "${CYAN}Creating configuration...${NC}"
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

# Create or update .claude/settings.json with all hooks
echo -e "${CYAN}Configuring hooks in settings.json...${NC}"
if [ -f "$PROJECT_ROOT/.claude/settings.json" ]; then
    echo -e "${CYAN}Found existing settings.json, merging sessions hooks...${NC}"
    # Backup existing settings
    cp "$PROJECT_ROOT/.claude/settings.json" "$PROJECT_ROOT/.claude/settings.json.bak"
fi

# Create settings.json with all hooks
settings_content='{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/user-messages.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Task|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/sessions-enforce.py"
          }
        ]
      },
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/task-transcript-link.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use.py"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|clear",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.py"
          }
        ]
      }
    ]
  }'

# Add statusline if requested
if [ "$install_statusline" = "y" ]; then
    settings_content="${settings_content%\}},
  \"statusLine\": {
    \"type\": \"command\",
    \"command\": \"\$CLAUDE_PROJECT_DIR/.claude/statusline-script.sh\",
    \"padding\": 0
  }
}"
else
    settings_content="${settings_content%\}}
}"
fi

echo "$settings_content" > "$PROJECT_ROOT/.claude/settings.json"
echo -e "${GREEN}✓ Sessions hooks configured in settings.json${NC}"

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

# Final success message
echo
echo
echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║                 🎉 INSTALLATION COMPLETE! 🎉                  ║${NC}"
echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo

echo -e "${BOLD}${CYAN}  Installation Summary:${NC}"
echo -e "${DIM}  ─────────────────────${NC}"
echo -e "${GREEN}  ✓ Directory structure created${NC}"
echo -e "${GREEN}  ✓ Hooks installed and configured${NC}"
echo -e "${GREEN}  ✓ Protocols and agents deployed${NC}"
echo -e "${GREEN}  ✓ daic command available globally${NC}"
echo -e "${GREEN}  ✓ Configuration saved${NC}"
echo -e "${GREEN}  ✓ DAIC state initialized (Discussion mode)${NC}"

if [ "$install_statusline" = "y" ]; then
    echo -e "${GREEN}  ✓ Statusline configured${NC}"
fi

echo

# Test daic command
if command -v daic &> /dev/null; then
    echo -e "${GREEN}  ✓ daic command verified and working${NC}"
else
    echo -e "${YELLOW}  ⚠ daic command not in PATH${NC}"
    echo -e "${DIM}       Add /usr/local/bin to your PATH${NC}"
fi

echo
echo -e "${BOLD}${MAGENTA}  ★ NEXT STEPS${NC}"
echo -e "${DIM}  ─────────────${NC}"
echo
echo -e "${WHITE}  1. Restart Claude Code to activate the sessions hooks${NC}"
echo -e "${DIM}     → Close and reopen Claude Code${NC}"
echo
echo -e "${WHITE}  2. Create your first task:${NC}"
echo -e "${CYAN}     → Tell Claude: \"Create a new task\"${NC}"
echo -e "${CYAN}     → Or: \"Create a task for implementing feature X\"${NC}"
echo
echo -e "${WHITE}  3. Start working with the DAIC workflow:${NC}"
echo -e "${DIM}     → Discuss approach first${NC}"
echo -e "${DIM}     → Say \"make it so\" to implement${NC}"
echo -e "${DIM}     → Run \"daic\" to return to discussion${NC}"
echo
echo -e "${DIM}  ──────────────────────────────────────────────────────${NC}"
echo
echo -e "${BOLD}${CYAN}  Welcome aboard, $developer_name! 🚀${NC}"
echo
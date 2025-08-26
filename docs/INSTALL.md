# Installation Guide

Quick reference for installing the Claude Code Sessions framework.

## Prerequisites

- **Claude Code** with hooks enabled
- **Python 3** with pip
- **Git** (recommended)
- **Bash shell** environment
- **Write access** to `/usr/local/bin` (or sudo)

## Quick Install

```bash
# Clone the package
git clone https://github.com/yourusername/claude-sessions
cd claude-sessions

# Navigate to your project
cd /path/to/your/project

# Run installer
/path/to/claude-sessions/install.sh
```

## Installation Steps

### 1. Run Installer

The installer will guide you through:

1. **Dependency Check** - Verifies Python 3, pip, git
2. **Directory Creation** - Sets up `.claude/` and `sessions/`
3. **Developer Name** - For session context (e.g., "Alex")
4. **Statusline** - Optional (choose Y if you want task status display)
5. **Trigger Phrases** - Customize what switches to implementation mode
6. **Advanced Options** - Usually skip unless you need customization

### 2. Restart Claude Code

Close and reopen Claude Code to load the hooks.

### 3. Verify Installation

```bash
# Test DAIC command
daic
# Should output: "You are now in Discussion Mode..."

# Check state files
cat .claude/state/current_task.json
cat .claude/state/daic-mode.json

# Verify CLAUDE.sessions.md
ls CLAUDE.sessions.md
```

## What Gets Installed

```
your-project/
├── .claude/
│   ├── hooks/                 # Behavioral enforcement
│   │   ├── session-start.py   # Context loading
│   │   ├── sessions-enforce.py # DAIC enforcement
│   │   ├── user-messages.py   # Trigger detection
│   │   ├── post-tool-use.py   # Mode reminders
│   │   └── shared_state.py    # State management
│   ├── state/                 # Current state
│   │   ├── current_task.json  # Active task
│   │   └── daic-mode.json     # Discussion/Implementation
│   ├── agents/                # Agent definitions
│   ├── sessions-config.json   # Your configuration
│   └── statusline-script.sh   # Optional status display
├── sessions/
│   ├── tasks/                 # Your task files
│   │   ├── TEMPLATE.md        # Task template
│   │   └── done/              # Completed tasks
│   ├── protocols/             # Workflow guides
│   └── agents/                # Agent prompts
├── CLAUDE.sessions.md         # Core behaviors
└── CLAUDE.md                  # Your project + @include

/usr/local/bin/
└── daic                       # Global command
```

## Configuration Options

### Basic Configuration

During installation, you'll set:
- **Developer name**: How Claude addresses you
- **Statusline**: Whether to install (Y/n)
- **Custom triggers**: Additional phrases for implementation mode

### Advanced Configuration (Optional)

- **Tool blocking**: Which tools to block in discussion mode
- **Task prefixes**: Custom priority indicators
- **Branch enforcement**: Enable/disable git branch checking

### Manual Configuration

Edit `.claude/sessions-config.json`:

```json
{
  "developer_name": "Your Name",
  "trigger_phrases": ["make it so", "run that", "go ahead", "yert"],
  "blocked_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
  "branch_enforcement": {"enabled": true},
  "task_detection": {"enabled": true}
}
```

## Platform-Specific Notes

### macOS

```bash
# If /usr/local/bin doesn't exist
sudo mkdir -p /usr/local/bin
sudo chown $(whoami) /usr/local/bin

# Add to PATH in ~/.zshrc or ~/.bash_profile
export PATH="/usr/local/bin:$PATH"
```

### Linux

Should work out of the box. If not:

```bash
# Alternative install location
mkdir -p ~/.local/bin
cp scripts/daic ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
```

### Windows (WSL)

Use WSL (Windows Subsystem for Linux) and follow Linux instructions.

## Troubleshooting Installation

### "Permission denied" for /usr/local/bin

```bash
# The installer will prompt for sudo
# Or manually:
sudo cp /path/to/claude-sessions/scripts/daic /usr/local/bin/
sudo chmod +x /usr/local/bin/daic
```

### "daic: command not found"

```bash
# Check if installed
ls -la /usr/local/bin/daic

# Add to PATH
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "Module tiktoken not found"

```bash
# Install with pip3
pip3 install tiktoken

# Or with pip
pip install tiktoken

# Or with sudo
sudo pip3 install tiktoken
```

### Hooks not triggering

1. Restart Claude Code
2. Check hook permissions:
   ```bash
   ls -la .claude/hooks/*.py
   # All should be executable (-rwxr-xr-x)
   ```
3. Verify hooks are enabled in Claude Code settings

## Uninstallation

To remove the Sessions framework:

```bash
# Remove directories
rm -rf .claude/
rm -rf sessions/
rm -f CLAUDE.sessions.md

# Remove daic command
sudo rm /usr/local/bin/daic

# Remove from CLAUDE.md
# Manually edit and remove the @CLAUDE.sessions.md line

# Remove from settings.json
# Manually edit ~/.claude/settings.json to remove statusLine
```

## Updating

To update to a newer version:

```bash
# Pull latest version
cd /path/to/claude-sessions
git pull

# Re-run installer (preserves your config)
cd /path/to/your/project
/path/to/claude-sessions/install.sh
```

The installer is idempotent - safe to run multiple times.

## Getting Started After Installation

1. **Create your first task**:
   ```bash
   cp sessions/tasks/TEMPLATE.md sessions/tasks/m-my-first-task.md
   ```

2. **Edit the task file** with your requirements

3. **Start working with Claude**:
   ```
   You: Let's work on my-first-task
   Claude: [Loads task and begins discussion]
   ```

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed workflows.
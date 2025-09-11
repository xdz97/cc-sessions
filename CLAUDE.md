# cc-sessions CLAUDE.md

## Purpose
Complete Claude Code Sessions framework that enforces Discussion-Alignment-Implementation-Check (DAIC) methodology for AI pair programming workflows with comprehensive user configurability.

## Narrative Summary

The cc-sessions package transforms Claude Code from a basic AI coding assistant into a sophisticated workflow management system. It enforces structured collaboration patterns where Claude must discuss approaches before implementing code, maintains persistent task context across sessions, and provides specialized agents for complex operations.

The core innovation is the DAIC (Discussion-Alignment-Implementation-Check) enforcement through Python hooks that cannot be bypassed. When Claude attempts to edit code without explicit user approval ("go ahead", "make it so", etc.), the hooks block the tools and require discussion first. The system uses todo-based execution boundaries where approved TodoWrite lists define the exact scope of implementation work. This prevents both over-implementation and "execution anxiety" from per-tool reminders.

Recent architectural enhancement (v0.3.0) introduced comprehensive user configuration through the SessionsConfig system. Users can now customize trigger phrases, blocked tools, developer preferences, git workflows, and environment settings. This 320+ line configuration architecture provides type-safe, atomic configuration management with the same reliability as the core state system.

The framework includes persistent task management with git branch enforcement, context preservation through session restarts, specialized subagents for heavy operations, and automatic context compaction when approaching token limits.

## Key Files
- `cc_sessions/hooks/shared_state.py` - Core state and configuration management with SessionsConfig system
- `cc_sessions/hooks/sessions-enforce.py` - DAIC enforcement with user-configurable tool blocking
- `cc_sessions/hooks/session-start.py` - Session initialization with configuration integration
- `cc_sessions/hooks/user-messages.py` - Configurable trigger phrase detection and mode switching
- `cc_sessions/hooks/post-tool-use.py` - Todo completion detection and automated mode transitions
- `cc_sessions/hooks/subagent-hooks.py` - Subagent context management and flag handling
- `cc_sessions/scripts/api/__main__.py` - Sessions API entry point for programmatic access
- `cc_sessions/scripts/api/router.py` - Command routing and argument parsing
- `cc_sessions/scripts/api/state_commands.py` - State inspection and limited write operations
- `cc_sessions/scripts/api/config_commands.py` - Configuration management commands
- `cc_sessions/commands/` - User slash commands (mode, state, config, triggers)
- `cc_sessions/install.py` - Cross-platform installer with Windows compatibility and native shell support
- `install.js` - Node.js installer wrapper with Windows command detection and path handling
- `cc_sessions/scripts/daic.cmd` - Windows Command Prompt daic command
- `cc_sessions/scripts/daic.ps1` - Windows PowerShell daic command
- `cc_sessions/agents/service-documentation.md` - Service documentation maintenance agent
- `cc_sessions/protocols/task-creation.md` - Structured task creation workflow
- `pyproject.toml` - Package configuration with console script entry points

## Installation Methods
- `pipx install cc-sessions` - Isolated Python install (recommended)
- `npm install -g cc-sessions` - Global npm install
- `pip install cc-sessions` - Direct pip install
- Direct bash: `./install.sh` from repository

## Core Features

### DAIC Enforcement
- Blocks Edit/Write/MultiEdit tools in discussion mode
- Requires explicit trigger phrases to enter implementation mode
- Todo-based execution boundaries enforce exact scope matching
- Approved TodoWrite lists define implementation work scope
- Auto-return to discussion mode when all todos complete
- Clear active todos on mode switches
- Configurable trigger phrases via `/add-trigger` command
- Read-only Bash commands allowed in discussion mode
- Sessions API commands whitelisted in discussion mode

### Task Management
- Priority-prefixed tasks: h- (high), m- (medium), l- (low), ?- (investigate)
- Automatic git branch creation and enforcement
- Persistent context across session restarts
- Work log consolidation and cleanup

### Branch Enforcement
- Task-to-branch mapping: implement- → feature/, fix- → fix/, etc.
- Blocks code edits if current branch doesn't match task requirements
- Four failure modes: wrong branch, no branch, task missing, branch missing

### Context Preservation
- Automatic context compaction at 75%/90% token usage
- Session restart with full task context loading
- Specialized agents operate in separate contexts

### Sessions API
- **State Inspection** - View current task, mode, todos, flags, and metadata
- **Configuration Management** - Manage trigger phrases, git preferences, environment settings
- **Limited Write Operations** - One-way mode switching (implementation → discussion)
- **JSON Output Support** - Machine-readable format for programmatic use
- **Security Boundaries** - No access to safety-critical settings or todo manipulation
- **Dual Access** - Same functionality available via Python module and user slash commands

### Specialized Agents
- **context-gathering**: Creates comprehensive task context manifests
- **logging**: Consolidates work logs with cleanup and chronological ordering
- **code-review**: Reviews implementations for quality and patterns
- **context-refinement**: Updates context with session discoveries
- **service-documentation**: Maintains CLAUDE.md files for services

## Integration Points

### Consumes
- Claude Code hooks system for behavioral enforcement
- Git for branch management and enforcement
- Python 3.8+ with tiktoken for token counting
- Shell environment for command execution (Bash/PowerShell/Command Prompt)
- File system locks for atomic state/configuration operations

### Provides
- **Sessions API** - Programmatic access via `python -m sessions.api` or `python -m cc_sessions.scripts.api`
- **User Slash Commands** - `/mode`, `/state`, `/config`, `/add-trigger`, `/remove-trigger`
- `/add-trigger` - Dynamic trigger phrase configuration with persistent storage
- `daic` - Manual mode switching command
- Hook-based tool blocking with user-configurable patterns
- Task file templates and management protocols
- Agent-based specialized operations
- SessionsConfig API for runtime configuration management
- SessionsState API for unified state management

## Configuration

### SessionsConfig Architecture (v0.3.0+)
Primary configuration in `sessions/sessions-config.json` with comprehensive user customization:

**Environment Settings (`environment`):**
- `developer_name` - How Claude addresses the user (default: "developer")
- `os` - User operating system (linux, macos, windows)
- `shell` - User shell preference (bash, zsh, fish, powershell, cmd)

**Trigger Phrases (`trigger_phrases`):**
- `implementation_mode` - Phrases that switch to implementation mode (default: ["yert", "make it so", "run that"])
- `discussion_mode` - Phrases that return to discussion mode (default: ["stop", "silence"])
- `task_creation` - Phrases that trigger task creation (default: ["mek:", "mekdis"])
- `task_startup` - Phrases for task startup (default: ["start^", "begin task:"])
- `task_completion` - Phrases for task completion (default: ["finito"])
- `context_compaction` - Phrases for context compaction (default: ["lets compact", "squish"])

**Blocked Actions (`blocked_actions`):**
- `implementation_only_tools` - Tools blocked in discussion mode (default: Edit, Write, MultiEdit, NotebookEdit)
- `custom_blocked_patterns` - User-defined CLI patterns blocked in discussion mode
- `extrasafe` - Enhanced blocking mode

**Git Preferences (`git_preferences`):**
- `add_pattern` - Git add behavior (ask, all, modified)
- `default_branch` - Main branch name (default: "main")
- `commit_style` - Commit message style (conventional, simple, detailed)
- `auto_merge` - Automatic merge to main branch
- `auto_push` - Automatic push to remote
- `has_submodules` - Repository has submodules

**Feature Toggles (`features`):**
- `branch_enforcement` - Git branch validation
- `task_detection` - Task-based workflow automation
- `auto_ultrathink` - Enhanced AI reasoning
- `context_warnings` - Token usage warnings at 85%/90%

### State Management
Unified state in `sessions/sessions-state.json`:
- `current_task` - Active task metadata with frontmatter integration
- `mode` - Current DAIC mode (discussion/implementation)
- `todos` - Active and stashed todo lists with completion tracking
- `flags` - Context warnings, subagent status, session flags
- `metadata` - Freeform runtime state

### Windows Integration
Configuration in `.claude/settings.json`:
- Hook commands use Windows-style paths with `%CLAUDE_PROJECT_DIR%`
- Python interpreter explicitly specified for `.py` hook execution
- Native `.cmd` and `.ps1` script support for daic command

## Architecture Changes (v0.3.0)

### Unified State System
- **Migration from Multi-File to Single-File**: Replaced 6+ individual state files (`daic-mode.json`, `current-task.json`, `active-todos.json`, etc.) with unified `sessions/sessions-state.json`
- **Atomic Operations**: All state changes use file locking and atomic writes through `edit_state()` context manager
- **Type-Safe State Management**: SessionsState dataclass with comprehensive validation and enum-based modes
- **Backward Compatibility**: Seamless migration from old state file structure

### Comprehensive Configuration Architecture  
- **SessionsConfig System**: 320+ lines of type-safe configuration management with nested dataclasses
- **User Customization**: Complete customization of trigger phrases, blocked tools, git preferences, environment settings
- **Configuration Validation**: Automatic type coercion, error handling, and default fallbacks
- **Atomic Configuration Updates**: Same reliability guarantees as state management through `edit_config()` context manager

### Enhanced Hook Integration
- **Configuration-Driven Behavior**: All hooks now load user configuration and respect customized preferences
- **Unified Import Pattern**: Consistent `load_config()` and `load_state()` imports across all hook files
- **Improved Error Handling**: Comprehensive backup and recovery mechanisms for corrupted configuration/state files

## Key Patterns

### Hook Architecture
- **Unified State Management**: SessionsState class manages all runtime state in single JSON file with atomic operations
- **Configuration-Driven Enforcement**: SessionsConfig system provides type-safe user customization of all behavioral patterns
- **Pre-tool-use Validation**: sessions-enforce.py uses configurable patterns for tool blocking and branch validation
- **Post-tool-use Automation**: Automatic todo completion detection and mode transitions based on user preferences
- **Configurable Trigger Detection**: user-messages.py supports user-defined trigger phrases for all workflow transitions
- **Session Initialization**: session-start.py integrates configuration with task context loading
- **Subagent Protection**: Automatic subagent context detection and flag management with cleanup
- **Atomic File Operations**: File locking and atomic writes prevent state corruption across all operations
- **Cross-platform Compatibility**: pathlib.Path throughout with Windows-specific handling
- **API Command Integration**: Sessions API commands whitelisted in DAIC enforcement and bypass ultrathink detection

### Agent Delegation
- Heavy file operations delegated to specialized agents
- Agents receive full conversation transcript for context
- Agent results returned to main conversation thread
- Agent state isolated in separate context windows

### Configuration Management
- **Type-Safe Enums**: CCTools, TriggerCategory, GitCommitStyle, UserOS, UserShell for validation
- **Nested Dataclasses**: TriggerPhrases, BlockingPatterns, GitPreferences, SessionsEnv for organization
- **Runtime Configuration Methods**: Add/remove trigger phrases, manage blocked tools, update preferences programmatically
- **Atomic Configuration Updates**: edit_config() context manager with file locking prevents configuration corruption
- **Configuration Validation**: Automatic type coercion and error handling for user inputs
- **Default Fallbacks**: Comprehensive defaults ensure system functionality without configuration
- **User Preference Persistence**: All configuration changes automatically saved to sessions/sessions-config.json

### Task Structure
- Markdown files with frontmatter integration into TaskState class
- Directory-based tasks for complex multi-phase work
- File-based tasks for focused single objectives
- Automatic branch mapping from task naming conventions
- Git submodule awareness through task frontmatter

### Subagent Protection
- Detection mechanism prevents DAIC reminders in subagent contexts
- Subagents blocked from editing sessions/state files
- Todo completion checks bypass subagent contexts
- Automatic flag cleanup when Task tool completes
- Strict separation between main thread and agent operations

### Windows Compatibility
- Platform detection using `os.name == 'nt'` (Python) and `process.platform === 'win32'` (Node.js)
- File operations skip Unix permissions on Windows (no chmod calls)
- Command detection handles Windows executable extensions (.exe, .bat, .cmd)
- Global command installation to `%USERPROFILE%\AppData\Local\cc-sessions\bin`
- Hook commands use explicit `python` prefix and Windows environment variable format
- Native Windows scripts: daic.cmd (Command Prompt) and daic.ps1 (PowerShell)

## Package Structure

### Installation Variants
- Python package with pip/pipx/uv support
- NPM package wrapper for JavaScript environments
- Direct bash script for build-from-source installations
- Cross-platform compatibility (macOS, Linux, Windows 10/11)

### Template System
- Task templates for consistent structure
- CLAUDE.sessions.md behavioral template
- Protocol markdown files for complex workflows
- Agent prompt templates for specialized operations

## Quality Assurance Features

### Context Management
- Token counting and usage warnings at 75%/90% thresholds
- Automatic context compaction protocols
- State preservation across session boundaries
- Clean task file maintenance through logging agent

### Work Quality
- Mandatory discussion before implementation
- Code review agent for quality checks
- Pattern consistency through context gathering
- Branch enforcement prevents wrong-branch commits

### Process Integrity
- Hook-based enforcement cannot be bypassed
- Todo-based execution boundaries prevent scope creep
- Exact scope matching required for TodoWrite operations
- Auto-return to discussion when implementation complete
- **Atomic State Protection**: File locking prevents state corruption and race conditions
- **Configuration Validation**: Type-safe configuration prevents invalid behavioral patterns
- **Backup and Recovery**: Automatic backup of corrupted configuration/state files
- **API Security Boundaries**: Sessions API prevents access to safety-critical features
- Chronological work log maintenance
- Task scope enforcement through structured protocols

## Related Documentation

- docs/INSTALL.md - Detailed installation guide
- docs/USAGE_GUIDE.md - Workflow and feature documentation
- cc_sessions/knowledge/ - Internal architecture documentation
- README.md - Marketing-focused feature overview
- sessions/protocols/ - Workflow protocol specifications (in installed projects)

## Sessions API Usage

### User Slash Commands
- `/mode` - Toggle between discussion and implementation modes
- `/state [component]` - Show current state or specific component (todos, task, flags)
- `/config` - Show current configuration (read-only)
- `/add-trigger <category> <phrase>` - Add trigger phrase to specified category
- `/remove-trigger <category> <phrase>` - Remove trigger phrase from category

### Programmatic API

**State Operations:**
- `python -m sessions.api state [--json]` - Full state inspection
- `python -m sessions.api state <component> [--json]` - Specific component (mode/task/todos/flags)
- `python -m sessions.api mode discussion` - One-way switch to discussion mode
- `python -m sessions.api flags clear` - Reset behavioral flags
- `python -m sessions.api status` - Human-readable state summary
- `python -m sessions.api version` - Package version information

**Configuration Operations:**
- `python -m sessions.api config [--json]` - Full configuration inspection
- `python -m sessions.api config phrases list [category]` - View trigger phrases
- `python -m sessions.api config phrases add <category> "<phrase>"` - Add trigger phrase
- `python -m sessions.api config phrases remove <category> "<phrase>"` - Remove trigger phrase
- `python -m sessions.api config git show` - View git preferences
- `python -m sessions.api config git set <setting> <value>` - Update git preference
- `python -m sessions.api config env show` - View environment settings
- `python -m sessions.api config env set <setting> <value>` - Update environment setting

**Security Notes:**
- No access to blocked_actions configuration (prevents DAIC bypass)
- No two-way mode switching (prevents safety bypass)
- No todo manipulation (respects TodoWrite safety mechanisms)
- No access to branch_enforcement toggle (maintains git safety)

## Sessions System Behaviors

@CLAUDE.sessions.md

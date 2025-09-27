# cc-sessions CLAUDE.md

## Purpose
Complete Claude Code Sessions framework that enforces Discussion-Alignment-Implementation-Check (DAIC) methodology for AI pair programming workflows with comprehensive user configurability.

## Narrative Summary

The cc-sessions package transforms Claude Code from a basic AI coding assistant into a sophisticated workflow management system. It enforces structured collaboration patterns where Claude must discuss approaches before implementing code, maintains persistent task context across sessions, and provides specialized agents for complex operations.

The core innovation is the DAIC (Discussion-Alignment-Implementation-Check) enforcement through Python hooks that cannot be bypassed. When Claude attempts to edit code without explicit user approval ("go ahead", "make it so", etc.), the hooks block the tools and require discussion first. The system uses todo-based execution boundaries where approved TodoWrite lists define the exact scope of implementation work. This prevents both over-implementation and "execution anxiety" from per-tool reminders.

Recent architectural enhancement (v0.3.0) introduced comprehensive user configuration through the SessionsConfig system. Users can now customize trigger phrases, blocked tools, developer preferences, git workflows, and environment settings. This 320+ line configuration architecture provides type-safe, atomic configuration management with the same reliability as the core state system.

The v0.3.1+ enhancement introduces a templated protocol system where protocols auto-load content with configuration-based template variables, eliminating conditional instructions. Protocols adapt automatically based on user configuration (e.g., submodules support) without requiring manual decision-making. The `load_protocol_file()` helper function provides seamless protocol loading with template substitution.

The framework includes persistent task management with git branch enforcement, context preservation through session restarts, specialized subagents for heavy operations, and automatic context compaction when approaching token limits.

## Key Files
- `cc_sessions/hooks/shared_state.py:1-50` - Core state and configuration management with unified SessionsConfig system
- `cc_sessions/hooks/sessions_enforce.py:36-110` - Enhanced DAIC enforcement with comprehensive command categorization and argument analysis for write operation detection
- `cc_sessions/hooks/session_start.py` - Session initialization with configuration integration and dual-import pattern
- `cc_sessions/hooks/user_messages.py:72-84` - Protocol auto-loading with `load_protocol_file()` helper and centralized todo formatting with improved task startup notices
- `cc_sessions/hooks/user_messages.py:165-216` - Templated task creation protocol system with automatic todo loading
- `cc_sessions/hooks/user_messages.py:316-414` - Task startup protocol with conditional API startup-load command
- `cc_sessions/hooks/user_messages.py:218-314` - Task completion protocol with commit style templates and conditional todos
- `cc_sessions/hooks/post_tool_use.py` - Todo completion detection and automated mode transitions
- `cc_sessions/hooks/subagent_hooks.py` - Subagent context management and flag handling
- `cc_sessions/scripts/api/__main__.py` - Sessions API entry point for programmatic access
- `cc_sessions/scripts/api/router.py` - Command routing with protocol command support
- `cc_sessions/scripts/api/protocol_commands.py:59-172` - Protocol-specific API commands with startup-load returning full task content
- `cc_sessions/scripts/api/state_commands.py` - State inspection and limited write operations
- `cc_sessions/scripts/api/config_commands.py` - Configuration management commands
- `cc_sessions/commands/` - Thin wrapper slash commands following official Claude Code patterns
- `cc_sessions/install.py` - Cross-platform installer with Windows compatibility and native shell support
- `cc_sessions/kickstart/agent-customization-guide.md` - Complete guide for customizing agents during kickstart protocol
- `install.js` - Node.js installer wrapper with Windows command detection and path handling
- `cc_sessions/scripts/daic.cmd` - Windows Command Prompt daic command
- `cc_sessions/scripts/daic.ps1` - Windows PowerShell daic command
- `cc_sessions/agents/service-documentation.md` - Service documentation maintenance agent
- `cc_sessions/agents/context-gathering.md` - Enhanced context-gathering with better pattern examples and comprehensive research methodology
- `cc_sessions/agents/logging.md` - Improved logging agent with simplified transcript access and better cleanup patterns
- `cc_sessions/agents/context-refinement.md` - Context refinement with streamlined transcript reading
- `cc_sessions/protocols/task-creation/task-creation.md` - Main templated task creation protocol
- `cc_sessions/protocols/task-startup/task-startup.md` - Main templated task startup protocol with conditional sections
- `cc_sessions/protocols/task-completion/task-completion.md` - Main templated task completion protocol
- `cc_sessions/protocols/task-completion/commit-style-*.md` - Commit style templates (conventional, simple, detailed)
- `pyproject.toml` - Package configuration with console script entry points

## Installation Methods
- `pipx install cc-sessions` - Isolated Python install (recommended)
- `npm install -g cc-sessions` - Global npm install
- `pip install cc-sessions` - Direct pip install
- Direct bash: `./install.sh` from repository

## Core Features

### DAIC Enforcement
- Blocks Edit/Write/MultiEdit tools in discussion mode
- Enhanced command categorization with 70+ read-only commands recognized
- Intelligent argument analysis detects write operations (sed -i, awk output, find -delete, xargs with write commands)
- Improved redirection detection including stderr redirections (2>&1, &>, etc.)
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
- **State Inspection** - View current task, mode, todos, flags, metadata, and active protocol
- **Configuration Management** - Manage trigger phrases, git preferences, environment settings
- **Feature Toggle Operations** - Enhanced with `toggle` command for simple boolean value flipping
- **Limited Write Operations** - One-way mode switching (implementation → discussion)
- **Protocol Commands** - startup-load command for task loading during startup protocol
- **JSON Output Support** - Machine-readable format for programmatic use
- **Security Boundaries** - No access to safety-critical settings or todo manipulation
- **Thin Wrapper Command Architecture** - All slash commands delegate to API layer following Claude Code official patterns

### Specialized Agents
- **context-gathering**: Creates comprehensive task context manifests with enhanced pattern examples and architectural insights
- **logging**: Consolidates work logs with simplified transcript paths and improved chronological organization
- **code-review**: Reviews implementations for quality and patterns
- **context-refinement**: Updates context with session discoveries using simplified transcript access
- **service-documentation**: Maintains CLAUDE.md files for services

## Protocol Architecture (v0.3.1+)

### Templated Protocol System
The protocol system uses configuration-driven template substitution to eliminate conditional instructions. Instead of protocols containing "if you have submodules, do X, otherwise do Y" logic, protocol content adapts automatically based on user configuration.

#### Template Variables
- `{submodules_field}` - Conditional frontmatter field for submodules list
- `{submodules_instruction}` - Conditional instructions for submodule management
- `{default_branch}` - User's configured default branch name
- `{submodule_branch_todo}` - Conditional text for branch creation todos
- `{submodule_context}` - Conditional context references

#### Protocol Loading Helper
- `load_protocol_file(relative_path)` - Auto-loads and templates protocol content
- `format_todos_for_protocol(todos)` - Centralized formatting of CCTodo objects for protocol display
- Protocols reference `sessions/protocols/[protocol-name]/` directory structure
- Main protocol files include conditional chunks based on configuration
- Template substitution happens at runtime based on current user config

#### Configuration-Driven Conditional Sections
- **Submodules Support**: Entire sections appear/disappear based on `CONFIG.git_preferences.has_submodules`
- **Repository Type**: Protocols adapt for super-repo vs standard repo structures
- **User Preferences**: Branch naming, commit styles, and workflow preferences auto-populate

### Protocol Directory Structure
```
protocols/
├── task-creation/
│   └── task-creation.md                    # Main templated protocol
├── task-startup/
│   ├── task-startup.md                     # Main templated protocol  
│   ├── submodule-management.md             # Conditional chunk for submodules
│   ├── resume-notes-standard.md            # Conditional chunk for standard repos
│   └── resume-notes-superrepo.md           # Conditional chunk for super-repos
├── task-completion/
│   ├── task-completion.md                  # Main templated protocol
│   ├── commit-style-conventional.md        # Conventional commit style template
│   ├── commit-style-simple.md              # Simple commit style template
│   ├── commit-style-detailed.md            # Detailed commit style template
│   ├── commit-standard.md                  # Standard repo commit instructions
│   ├── commit-superrepo.md                 # Super-repo commit instructions
│   ├── staging-all.md                      # "Add all" staging instructions
│   ├── staging-ask.md                      # "Ask user" staging instructions
│   └── git-add-warning.md                  # Warning for "add all" pattern
└── context-compaction.md                   # Simple protocol (no templating)
```

## Integration Points

### Consumes
- Claude Code hooks system for behavioral enforcement
- Git for branch management and enforcement
- Python 3.8+ with tiktoken for token counting
- Shell environment for command execution (Bash/PowerShell/Command Prompt)
- File system locks for atomic state/configuration operations
- **CLAUDE_PROJECT_DIR environment variable** for symlinked development setup

### Provides
- **Sessions API** - Programmatic access via `python -m sessions.api` (unified module path)
- **Thin Wrapper Slash Commands** - `/mode`, `/state`, `/config`, `/add-trigger`, `/remove-trigger` following official Claude Code patterns
- **Protocol Commands** - `python -m sessions.api protocol startup-load <task-file>` returns full task file content for task loading
- **Enhanced Feature Management** - `config features toggle <key>` for simple boolean operations
- `daic` - Manual mode switching command
- Hook-based tool blocking with user-configurable patterns
- Templated protocol system with automatic content adaptation
- Task file templates and management protocols
- Agent-based specialized operations
- SessionsConfig API for runtime configuration management
- SessionsState API for unified state management with active protocol tracking

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
- `add_pattern` - Git add behavior (ask, all) - "modified" pattern removed as impractical
- `default_branch` - Main branch name (default: "main")
- `commit_style` - Commit message style with templates (conventional, simple, detailed)
- `auto_merge` - Automatic merge to main branch (controls commit/merge todos)
- `auto_push` - Automatic push to remote (controls push todos)
- `has_submodules` - Repository has submodules (drives protocol templating)

**Feature Toggles (`features`):**
- `branch_enforcement` - Git branch validation
- `task_detection` - Task-based workflow automation
- `auto_ultrathink` - Enhanced AI reasoning
- `context_warnings` - Token usage warnings at 85%/90%

### State Management
Unified state in `sessions/sessions-state.json`:
- `current_task` - Active task metadata with frontmatter integration and automatic status updates
- `mode` - Current DAIC mode (discussion/implementation)
- `active_protocol` - Currently active protocol (CREATE/START/COMPLETE/COMPACT/None)
- `api` - Protocol-specific API permissions (startup_load, completion)
- `todos` - Active and stashed todo lists with completion tracking  
- `flags` - Context warnings, subagent status, session flags
- `metadata` - Freeform runtime state

### Development Setup Integration
Configuration in `.claude/settings.json` supports both package and symlinked setups:
- **Package Installation**: Hook commands reference `cc_sessions.hooks.*`
- **Symlinked Development**: Hook commands reference `sessions/hooks/*` 
- **Dual-Context Import Pattern**: Code auto-detects CLAUDE_PROJECT_DIR for path resolution
- **Real-Time Development**: Changes to cc-sessions package immediately available without reinstall

### Windows Integration
Configuration in `.claude/settings.json`:
- Hook commands use Windows-style paths with `%CLAUDE_PROJECT_DIR%`
- Python interpreter explicitly specified for `.py` hook execution
- Native `.cmd` and `.ps1` script support for daic command

## Architecture Changes (v0.3.0+)

### Major System Modernization (v0.3.2+)
- **Git Workflow Simplification**: Removed impractical "modified" add pattern that forced manual file selection
- **Protocol Organization Cleanup**: Consolidated duplicate protocol files into organized subdirectory structure
- **State System Unification**: All protocols now reference unified `sessions/sessions-state.json` instead of deprecated separate files
- **Automatic Task Status Management**: Task status updates (in-progress, completion) now handled automatically by state system
- **Commit Style Templates**: Added templated commit message styles (conventional, simple, detailed) with branch-based selection
- **Protocol Command Integration**: Enhanced `startup-load` API command returns full task file content instead of just metadata
- **Conditional Todo System**: Todos automatically adapt based on user configuration (auto_merge, auto_push, etc.)
- **Discussion Mode Write Blocking Enhancements**: Comprehensive command categorization and intelligent argument analysis eliminates oversensitive blocking of legitimate read-only operations

### Protocol Automation Infrastructure (v0.3.2+)
- **SessionsProtocol Enum**: Tracks active protocols (`COMPACT`, `CREATE`, `START`, `COMPLETE`) for protocol state management
- **APIPerms Dataclass**: Protocol-specific command authorization with fields for `startup_load` and `completion` permissions
- **Active Protocol State Field**: New `active_protocol` field in SessionsState enables protocol-driven automation and command filtering
- **Protocol Command Infrastructure**: Enhanced Sessions API with protocol-specific command routing and permission validation
- **Protocol State Management**: Framework for protocols to manage their own execution state and permitted operations

### Unified State System
- **Migration from Multi-File to Single-File**: Replaced 6+ individual state files (`daic-mode.json`, `current-task.json`, `active-todos.json`, etc.) with unified `sessions/sessions-state.json`
- **Atomic Operations**: All state changes use file locking and atomic writes through `edit_state()` context manager
- **Type-Safe State Management**: SessionsState dataclass with comprehensive validation and enum-based modes
- **Backward Compatibility**: Seamless migration from old state file structure

### Templated Protocol System (v0.3.1+)
- **Configuration-Driven Protocol Loading**: `load_protocol_file()` helper function auto-loads protocol content with template substitution
- **Template Variables**: Protocols use format strings like `{submodules_field}` populated based on user configuration
- **Conditional Section Rendering**: Entire protocol sections appear/disappear based on configuration (e.g., submodules support)
- **Elimination of Manual Decisions**: Protocols adapt automatically without requiring conditional instructions
- **Modular Protocol Architecture**: Main protocol files reference conditional chunks based on user setup

### Comprehensive Configuration Architecture  
- **SessionsConfig System**: 320+ lines of type-safe configuration management with nested dataclasses
- **User Customization**: Complete customization of trigger phrases, blocked tools, git preferences, environment settings
- **Configuration Validation**: Automatic type coercion, error handling, and default fallbacks
- **Atomic Configuration Updates**: Same reliability guarantees as state management through `edit_config()` context manager

### Enhanced Hook Integration
- **Configuration-Driven Behavior**: All hooks now load user configuration and respect customized preferences
- **Unified Import Pattern**: Consistent `load_config()` and `load_state()` imports across all hook files
- **Improved Error Handling**: Comprehensive backup and recovery mechanisms for corrupted configuration/state files

## Recent Enhancements

### Discussion Mode Write Blocking (v0.3.2+)
Recent improvements to `sessions_enforce.py` address oversensitive blocking that prevented legitimate compound operations:

**Enhanced Command Classification:**
- `READONLY_FIRST`: Expanded from 20 to 70+ commands covering text processing, inspection, monitoring, and modern tools
- `WRITE_FIRST`: Comprehensive categorization of dangerous operations including system management and package managers
- **Intelligent Argument Analysis**: New `check_command_arguments()` function detects context-specific write operations

**Advanced Detection Patterns:**
- **sed -i Detection**: Identifies in-place editing operations that modify files
- **awk Output Analysis**: Recognizes file output within awk scripts using regex patterns
- **find Command Safety**: Detects `-delete` flag and dangerous `-exec` operations
- **xargs Validation**: Prevents write commands passed through xargs pipelines
- **Enhanced Redirection Detection**: Improved regex patterns catch stderr redirections (2>&1, &>) and complex file descriptor operations

**Improved Pipeline Handling:**
- **Proper Pipeline Splitting**: Enhanced regex prevents false positives on `||` logical operators
- **Per-Segment Analysis**: Each pipeline segment evaluated independently for safety
- **Context-Aware Validation**: Commands analyzed with their complete argument context

This eliminates false blocking of legitimate read-only compound operations while maintaining protection against actual write operations.

## Key Patterns

### Hook Architecture
- **Unified State Management**: SessionsState class manages all runtime state in single JSON file with atomic operations
- **Configuration-Driven Enforcement**: SessionsConfig system provides type-safe user customization of all behavioral patterns
- **Protocol State Management**: SessionsProtocol enum and active_protocol field enable protocol-driven automation
- **Protocol Command Authorization**: APIPerms dataclass provides protocol-specific command permission validation
- **Enhanced Pre-tool-use Validation**: sessions_enforce.py uses comprehensive command categorization with intelligent argument analysis for accurate write operation detection
- **Post-tool-use Automation**: Automatic todo completion detection and mode transitions based on user preferences
- **Configurable Trigger Detection**: user_messages.py supports user-defined trigger phrases for all workflow transitions
- **Protocol Auto-Loading**: `load_protocol_file()` helper eliminates manual "read this file" instructions
- **Centralized Protocol Todo System**: `format_todos_for_protocol()` provides consistent todo formatting across all protocols
- **Template-Based Protocol System**: Protocols auto-adapt based on configuration without conditional instructions
- **Automatic Task Status Updates**: Task lifecycle management through state system (status, started dates)
- **Commit Style Templating**: Dynamic commit message templates based on user preferences and branch patterns  
- **Conditional Todo Generation**: Protocol todos adapt automatically to user configuration (merge, push, submodules)
- **Session Initialization**: session_start.py integrates configuration with task context loading
- **Subagent Protection**: Automatic subagent context detection and flag management with cleanup
- **Atomic File Operations**: File locking and atomic writes prevent state corruption across all operations
- **Cross-platform Compatibility**: pathlib.Path throughout with Windows-specific handling
- **API Command Integration**: Sessions API commands whitelisted in DAIC enforcement and bypass ultrathink detection  
- **Dual-Context Import Pattern**: Supports both symlinked development and package installation through CLAUDE_PROJECT_DIR detection

### Agent Delegation
- Heavy file operations delegated to specialized agents with enhanced pattern recognition
- Agents access conversation transcripts through dedicated `sessions/transcripts/[agent-name]/` directories
- Agent results returned to main conversation thread with improved context preservation
- Agent state isolated in separate context windows
- Streamlined transcript access eliminates complex path management

### Configuration Management
- **Type-Safe Enums**: CCTools, TriggerCategory, GitCommitStyle, UserOS, UserShell for validation
- **Nested Dataclasses**: TriggerPhrases, BlockingPatterns, GitPreferences, SessionsEnv for organization
- **Runtime Configuration Methods**: Add/remove trigger phrases, manage blocked tools, update preferences programmatically
- **Atomic Configuration Updates**: edit_config() context manager with file locking prevents configuration corruption
- **Configuration Validation**: Automatic type coercion and error handling for user inputs
- **Default Fallbacks**: Comprehensive defaults ensure system functionality without configuration
- **User Preference Persistence**: All configuration changes automatically saved to sessions/sessions-config.json

### Protocol Loading & Templating
- **Auto-Loading Helper**: `load_protocol_file()` eliminates manual "read this file" instructions
- **Template Variable Substitution**: Format strings populated from user configuration at runtime
- **Conditional Content Rendering**: Entire protocol sections appear/disappear based on user setup
- **Modular Protocol Architecture**: Main protocols reference conditional chunks (submodule-management.md, resume-notes-*.md)
- **Configuration-Driven Adaptation**: Protocols automatically adapt without requiring conditional instructions
- **Development-Time Flexibility**: Protocol changes immediately available in symlinked setups

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
- **Symlinked Development Setup**: Use cc-sessions package locally without installation via symlinks
- Cross-platform compatibility (macOS, Linux, Windows 10/11)

### Development Setup
- **Symlink Structure**: `sessions/hooks/` → `cc-sessions/cc_sessions/hooks/` for real-time testing
- **Dual-Import Compatibility**: Code works in both symlinked and installed contexts
- **CLAUDE_PROJECT_DIR Detection**: Automatic path configuration for development environments

### Template System
- Task templates for consistent structure
- CLAUDE.sessions.md behavioral template
- **Templated Protocol Files**: Protocol content with format string variables
- **Configuration-Based Template Variables**: Auto-populated based on user preferences
- **Modular Protocol Architecture**: Main protocols reference conditional chunks
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

## Migration & Development Features

### Local Hook Migration
- **Configuration Extraction**: Automatic extraction of hardcoded values from local `.claude/hooks/` files
- **Symlinked Development Setup**: Use package functionality without installation via symlink structure
- **Dual-Context Compatibility**: Code works seamlessly in both development and production environments
- **Agent Preservation**: Local agent customizations maintained during migration
- **Protocol Reconciliation**: Intelligent merging of local and package protocol differences

### Development Workflow
- **Real-Time Testing**: Changes to cc-sessions package immediately available without reinstall cycles
- **CLAUDE_PROJECT_DIR Detection**: Automatic environment detection for path resolution
- **Import Pattern Flexibility**: Fallback import system supports both symlinked and installed contexts
- **Configuration-First Approach**: All customizations preserved through configuration rather than code changes

## Agent System Enhancements

### Enhanced Context-Gathering Agent
The context-gathering agent now provides comprehensive pattern recognition with detailed examples across multiple architecture types:
- **Architecture Patterns**: Identifies super-repo, mono-repo, microservices, and standard repository structures
- **Communication Patterns**: Recognizes REST, GraphQL, gRPC, WebSockets, message queues, and event-driven architectures
- **Data Access Patterns**: Detects ORM usage (SQLAlchemy, Prisma, TypeORM), caching strategies, and file system organization
- **Business Logic Recognition**: Captures validation patterns, authentication flows, data transformation pipelines, and workflow patterns
- **Improved Research Methodology**: More thorough component discovery with explicit guidance to trace call paths and understand full architecture

### Simplified Agent Transcript Access
All specialized agents now use streamlined transcript access through dedicated directories:
- **Logging Agent**: Reads from `sessions/transcripts/logging/` with improved chronological consolidation
- **Context-Refinement Agent**: Accesses `sessions/transcripts/context-refinement/` for discovery tracking
- **Consistent Pattern**: Eliminates complex path management across all agent operations

### Kickstart Agent Customization
New comprehensive guide at `cc_sessions/kickstart/agent-customization-guide.md` enables project-specific agent customization:
- **Technology Stack Adaptation**: Customize agents for specific languages, frameworks, and databases
- **Architectural Pattern Recognition**: Tailor pattern detection for microservices, serverless, monolithic, or frontend architectures
- **Domain-Specific Terminology**: Replace generic terms with project-specific vocabulary
- **Custom Skip Patterns**: Configure agents to skip generated files, vendor directories, or irrelevant paths
- **Compliance Integration**: Add security, accessibility, or regulatory requirements to code review patterns

### Agent Reliability Improvements
- **Task Startup Notice Fixes**: Resolved intermittent failures in task startup notifications through improved hook handling
- **Enhanced Error Handling**: Better transcript reading with fallback mechanisms
- **Atomic File Operations**: Consistent file locking patterns across all agent operations

## Related Documentation

- docs/INSTALL.md - Detailed installation guide
- docs/USAGE_GUIDE.md - Workflow and feature documentation
- cc_sessions/knowledge/ - Internal architecture documentation
- README.md - Marketing-focused feature overview
- sessions/protocols/ - Workflow protocol specifications (in installed projects)
- sessions/tasks/migration-audit.md - Documentation of local vs package differences
- cc_sessions/kickstart/agent-customization-guide.md - Complete agent customization guide

## Sessions API Usage

### User Slash Commands (Thin Wrappers)
- `/mode` - Toggle between discussion and implementation modes via API delegation
- `/state [component]` - Show current state or specific component via API delegation
- `/config` - Show current configuration via API delegation (read-only)
- `/add-trigger <category> <phrase>` - Add trigger phrase via API delegation (categories: implement, discuss, create, start, complete, compact)
- `/remove-trigger <category> <phrase>` - Remove trigger phrase via API delegation

### Programmatic API

**State Operations:**
- `python -m sessions.api state [--json]` - Full state inspection including active protocol
- `python -m sessions.api state <component> [--json]` - Specific component (mode/task/todos/flags/active_protocol/api)
- `python -m sessions.api state active_protocol [--json]` - View currently active protocol
- `python -m sessions.api state api [--json]` - View protocol-specific API permissions
- `python -m sessions.api mode discussion` - One-way switch to discussion mode
- `python -m sessions.api flags clear` - Reset behavioral flags
- `python -m sessions.api status` - Human-readable state summary
- `python -m sessions.api version` - Package version information

**Protocol Operations:**
- `python -m sessions.api protocol startup-load <task-file>` - Load task and return full file content during startup protocol
- Permission-based access controlled by active_protocol and api.startup_load states

**Configuration Operations:**
- `python -m sessions.api config [--json]` - Full configuration inspection
- `python -m sessions.api config phrases list [category]` - View trigger phrases
- `python -m sessions.api config phrases add <category> "<phrase>"` - Add trigger phrase
- `python -m sessions.api config phrases remove <category> "<phrase>"` - Remove trigger phrase
- `python -m sessions.api config features toggle <key>` - Toggle feature boolean values
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

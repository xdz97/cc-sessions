# cc-sessions CLAUDE.md

## Purpose
Complete Claude Code Sessions framework with dual-language implementation (Python/JavaScript) that enforces Discussion-Alignment-Implementation-Check (DAIC) methodology for AI pair programming workflows with comprehensive user configurability.

## Narrative Summary

The cc-sessions package transforms Claude Code from a basic AI coding assistant into a sophisticated workflow management system. It enforces structured collaboration patterns where Claude must discuss approaches before implementing code, maintains persistent task context across sessions, and provides specialized agents for complex operations.

The core innovation is the DAIC (Discussion-Alignment-Implementation-Check) enforcement through language-agnostic hooks that cannot be bypassed. Available in both Python and JavaScript implementations with complete feature parity, When Claude attempts to edit code without explicit user approval ("go ahead", "make it so", etc.), the hooks block the tools and require discussion first. The system uses todo-based execution boundaries where approved TodoWrite lists define the exact scope of implementation work. This prevents both over-implementation and "execution anxiety" from per-tool reminders.

Recent architectural enhancement (v0.3.0) introduced comprehensive user configuration through the SessionsConfig system. Users can now customize trigger phrases, blocked tools, developer preferences, git workflows, and environment settings. This 320+ line configuration architecture provides type-safe, atomic configuration management with the same reliability as the core state system.

The v0.3.1+ enhancement introduces a templated protocol system where protocols auto-load content with configuration-based template variables, eliminating conditional instructions. Protocols adapt automatically based on user configuration (e.g., submodules support) without requiring manual decision-making. The `load_protocol_file()` helper function provides seamless protocol loading with template substitution.

The v0.3.5+ enhancement adds first-class support for directory-based tasks with subtask workflows. Directory tasks provide structured multi-phase work where subtasks remain on a single feature branch until the entire effort completes. The system automatically detects directory tasks and adjusts protocol behavior - preventing auto-merge until all subtasks finish, loading planning-focused guidance during startup, and providing helper functions for consistent detection across the codebase.

The framework includes persistent task management with git branch enforcement, context preservation through session restarts, specialized subagents for heavy operations, and automatic context compaction when approaching token limits.

## Key Files
- `cc_sessions/hooks/shared_state.py|.js` - Core state and configuration management with unified SessionsConfig system, enhanced lock timeout behavior (1-second timeout with force-removal), fixed EnabledFeatures.from_dict() dataclass serialization, directory task helper functions `is_directory_task()` and `get_task_file_path()`, and simplified `find_git_repo()`/`findGitRepo()` functions that assume directory input (both Python and JavaScript implementations)
- `cc_sessions/hooks/sessions_enforce.py|.js` - Enhanced DAIC enforcement with comprehensive command categorization and argument analysis for write operation detection, calls `find_git_repo(file_path.parent)` for branch validation (both Python and JavaScript implementations)
- `cc_sessions/hooks/session_start.py|.js` - Session initialization with configuration integration, dual-import pattern, and kickstart protocol detection via `STATE.flags.noob` (both Python and JavaScript implementations)
- `cc_sessions/hooks/kickstart_session_start.py|.js` - Kickstart-only SessionStart hook that checks noob flag, handles reminder dates, loads entry/resume protocols, and short-circuits to let normal hooks run when noob=false (both Python and JavaScript implementations)
- `cc_sessions/hooks/user_messages.py|.js` - Protocol auto-loading with `load_protocol_file()` helper, centralized todo formatting, directory task detection for merge prevention, and improved task startup notices (both Python and JavaScript implementations)
- `cc_sessions/hooks/post_tool_use.py|.js` - Todo completion detection and automated mode transitions (both Python and JavaScript implementations)
- `cc_sessions/hooks/subagent_hooks.py|.js` - Subagent context management and flag handling (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/__main__.py` - Sessions API entry point with --from-slash flag support for contextual output (Python)
- `cc_sessions/scripts/api/index.js` - Sessions API entry point (JavaScript)
- `cc_sessions/scripts/api/router.py|.js` - Command routing with protocol command support, kickstart handler integration, and --from-slash flag handling (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/protocol_commands.py|.js` - Protocol-specific API commands with startup-load returning full task content (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/kickstart_commands.py|.js` - Kickstart-specific API commands for onboarding flow state management (next, mode, remind, complete) with hybrid self-cleanup system (both Python and JavaScript implementations)
- `cc_sessions/protocols/kickstart/01-entry.md` - Entry prompt with yes/later/never handling and natural language date parsing
- `cc_sessions/protocols/kickstart/02-mode-selection.md` - Mode selection protocol presenting full/api/seshxpert options
- `cc_sessions/protocols/kickstart/full/` - 12 protocol chunks for Full mode (30-45 min walkthrough)
- `cc_sessions/protocols/kickstart/api/` - 8 protocol chunks for API mode (10-15 min condensed version)
- `cc_sessions/protocols/kickstart/seshxpert/` - 1 protocol chunk for Seshxpert mode (5 min import/auto-generate)
- `cc_sessions/templates/h-kickstart-setup.md` - Dummy task template used for onboarding practice
- `cc_sessions/scripts/api/state_commands.py|.js` - State inspection and limited write operations (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/config_commands.py|.js` - Configuration management commands with --from-slash support for contextual output formatting, includes read/write/tools pattern management with CCTools enum validation (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/task_commands.py|.js` - Task management operations with index support and task startup protocols (both Python and JavaScript implementations)
- `cc_sessions/commands/` - Thin wrapper slash commands following official Claude Code patterns
- `cc_sessions/install.py` - Cross-platform installer with Windows compatibility and native shell support
- `cc_sessions/kickstart/agent-customization-guide.md` - Complete guide for customizing agents during kickstart protocol
- `cc_sessions/protocols/kickstart/` - Kickstart onboarding protocol directory with mode-specific chunks
- `cc_sessions/protocols/kickstart/01-entry.md` - Entry prompt with yes/later/never handling
- `cc_sessions/protocols/kickstart/02-mode-selection.md` - Mode selection (full/api/seshxpert)
- `cc_sessions/protocols/kickstart/full/03-core-workflow.md` - Interactive DAIC workflow demo
- `cc_sessions/protocols/kickstart/full/04-trigger-phrases.md` - Trigger phrase customization
- `cc_sessions/protocols/kickstart/full/05-orphaned-todos.md` - State system and todo management
- `cc_sessions/protocols/kickstart/full/06-tasks-and-branches.md` - Task and branch management workflows
- `cc_sessions/protocols/kickstart/full/07-task-startup-and-config.md` - Task startup protocol with dummy task
- `cc_sessions/protocols/kickstart/full/08-create-first-task.md` - Graduation and first real task
- `install.js` - Node.js installer wrapper with Windows command detection and path handling
- `cc_sessions/scripts/daic.cmd` - Windows Command Prompt daic command
- `cc_sessions/scripts/daic.ps1` - Windows PowerShell daic command
- `cc_sessions/agents/service-documentation.md` - Service documentation maintenance agent
- `cc_sessions/agents/context-gathering.md` - Enhanced context-gathering with better pattern examples and comprehensive research methodology
- `cc_sessions/agents/logging.md` - Improved logging agent with simplified transcript access and better cleanup patterns
- `cc_sessions/agents/context-refinement.md` - Context refinement with streamlined transcript reading
- `cc_sessions/protocols/task-creation/task-creation.md:37-74` - Main templated task creation protocol with directory task structure decision and user confirmation
- `cc_sessions/protocols/task-startup/task-startup.md` - Main templated task startup protocol with conditional sections
- `cc_sessions/protocols/task-startup/directory-task-startup.md` - Planning guidance for directory tasks emphasizing comprehensive subtask specification, comprehensive planning, and iterative same-branch workflow
- `cc_sessions/protocols/task-completion/task-completion.md` - Main templated task completion protocol with directory task detection and auto-merge prevention
- `cc_sessions/protocols/task-completion/commit-style-*.md` - Commit style templates (conventional, simple, detailed)
- `pyproject.toml` - Package configuration with console script entry points

## Installation Methods
**Python Variant:**
- `pipx install cc-sessions` - Isolated Python install (recommended)
- `pip install cc-sessions` - Direct pip install

**JavaScript Variant:**
- `npm install -g cc-sessions` - Global npm install
- `npx cc-sessions` - One-time execution

**Development:**
- Direct bash: `./install.sh` from repository
- **Symlinked Development Setup**: Use cc-sessions package locally without installation via symlinks

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
- File-based tasks for focused single objectives
- Directory-based tasks with subtask support for complex multi-phase work
- Automatic git branch creation and enforcement
- Persistent context across session restarts
- Work log consolidation and cleanup

### Directory Task Support
- **Helper Functions**: `is_directory_task()` detects directory tasks by checking for '/' in task path, `get_task_file_path()` resolves to README.md for directories or direct .md for files
- **Task Creation Integration**: Protocol explicitly asks users to confirm directory structure with clear explanation of workflow implications
- **Planning-Focused Startup**: Conditionally loads directory-task-startup.md guidance emphasizing comprehensive subtask specification before implementation
- **Merge Prevention**: Task completion protocol automatically detects directory tasks and prevents auto-merge until all subtasks complete, overriding user's auto_merge preference
- **Iterative Workflow**: All subtasks work on the same feature branch without merging until the entire multi-phase effort is done
- **Consistent Detection**: Helper functions used throughout hooks and API commands for reliable directory task identification

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
- **Configuration Management** - Manage trigger phrases, git preferences, environment settings, bash patterns, and tool blocking
- **Pattern Management** - Configure bash_read_patterns, bash_write_patterns, and implementation_only_tools via dedicated commands
- **Feature Toggle Operations** - Enhanced with `toggle` command for simple boolean value flipping
- **Limited Write Operations** - One-way mode switching (implementation → discussion)
- **Protocol Commands** - startup-load command for task loading during startup protocol
- **JSON Output Support** - Machine-readable format for programmatic use
- **Security Boundaries** - No access to safety-critical settings or todo manipulation
- **Slash Command Integration** - Consolidated sesh-* commands with API delegation pattern and --from-slash contextual output formatting

### Kickstart Onboarding Protocol
- **kickstart**: Interactive first-run onboarding system for new installations
- Three mode variants: Full (30-45 min), API (10-15 min), Seshxpert (5 min)
- Triggered automatically when `STATE.flags.noob` is `True`
- API-driven workflow with numbered protocol chunks per mode
- Configuration import support for experienced users setting up new repos
- Teaches DAIC workflow, trigger phrases, task management, agent customization
- Protocols located in `cc_sessions/protocols/kickstart/`
- Self-cleaning system: Deletes own files and returns manual cleanup instructions on completion

### Specialized Agents
- **context-gathering**: Creates comprehensive task context manifests with enhanced pattern examples and architectural insights
- **logging**: Consolidates work logs with simplified transcript paths and improved chronological organization
- **code-review**: Reviews implementations for quality and patterns
- **context-refinement**: Updates context with session discoveries using simplified transcript access
- **service-documentation**: Maintains CLAUDE.md files for services

## Protocol Architecture (v0.3.1+)

### Templated Protocol System with Structured Output
The protocol system uses configuration-driven template substitution to eliminate conditional instructions. Instead of protocols containing "if you have submodules, do X, otherwise do Y" logic, protocol content adapts automatically based on user configuration.

Enhanced with structured output formats, protocols now provide transparent communication at key decision points using standardized bracketed headers like `[PROPOSAL]`, `[STATUS]`, `[PLAN]`, `[FINDINGS]`, `[DECISION]`, `[QUESTION]`, `[RUNNING]`, and `[COMPLETE]` for improved user experience and predictable AI interactions.

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
│   └── task-creation.md                    # Main templated protocol with directory task confirmation
├── task-startup/
│   ├── task-startup.md                     # Main templated protocol
│   ├── submodule-management.md             # Conditional chunk for submodules
│   ├── directory-task-startup.md           # Conditional chunk for directory tasks
│   ├── resume-notes-standard.md            # Conditional chunk for standard repos
│   └── resume-notes-superrepo.md           # Conditional chunk for super-repos
├── task-completion/
│   ├── task-completion.md                  # Main templated protocol with directory task merge prevention
│   ├── commit-style-conventional.md        # Conventional commit style template
│   ├── commit-style-simple.md              # Simple commit style template
│   ├── commit-style-detailed.md            # Detailed commit style template
│   ├── commit-standard.md                  # Standard repo commit instructions
│   ├── commit-superrepo.md                 # Super-repo commit instructions
│   ├── staging-all.md                      # "Add all" staging instructions
│   ├── staging-ask.md                      # "Ask user" staging instructions
│   └── git-add-warning.md                  # Warning for "add all" pattern
├── context-compaction.md                   # Simple protocol (no templating)
└── kickstart/                              # First-run onboarding protocols (v0.3.6+)
    ├── 01-entry.md                         # Welcome prompt with yes/later/never
    ├── 02-mode-selection.md                # Three mode variants
    ├── full/                               # Full mode protocol chunks (30-45 min)
    │   ├── 03-core-workflow.md             # DAIC explanation with interactive demo
    │   ├── 04-trigger-phrases.md           # Trigger phrase configuration
    │   ├── 05-orphaned-todos.md            # State system and todo cleanup
    │   ├── 06-tasks-and-branches.md        # Task/branch workflows
    │   ├── 07-task-startup-and-config.md   # Task startup with dummy task practice
    │   ├── 08-create-first-task.md         # Create first real task
    │   ├── 09-always-available-protocols.md # Completion, compaction, helper protocols
    │   ├── 10-agent-customization.md       # Agent overview and customization intro
    │   ├── 11-code-review-customization.md # Code-review agent tech stack setup
    │   ├── 12-tool-configuration.md        # Custom readonly commands
    │   ├── 13-advanced-features.md         # Directory tasks, bypass mode, indexes
    │   └── 14-graduation.md                # Cleanup, summary, next steps
    ├── api/                                # API mode protocol chunks (10-15 min)
    │   ├── 03-core-workflow.md             # Condensed DAIC demo
    │   ├── 04-task-protocols.md            # Task workflows condensed
    │   ├── 05-context-management.md        # State system essentials
    │   ├── 06-configuration.md             # Quick config setup
    │   ├── 07-agent-customization.md       # Minimal agent setup
    │   ├── 08-advanced-concepts.md         # Brief advanced features
    │   ├── 09-create-first-task.md         # First real task
    │   └── 10-graduation.md                # Quick summary and next steps
    └── seshxpert/                          # Seshxpert mode protocol chunks (5 min)
        └── 03-quick-setup.md               # Import/auto-generate workflow
```

## Integration Points

### Consumes
- Claude Code hooks system for behavioral enforcement
- Git for branch management and enforcement
- **Python 3.8+** OR **Node.js 16+** (language-specific variants)
- Shell environment for command execution (Bash/PowerShell/Command Prompt)
- File system locks for atomic state/configuration operations
- **CLAUDE_PROJECT_DIR environment variable** for symlinked development setup
- **No external dependencies** - removed tiktoken and yaml dependencies from both languages

### Provides
- **Sessions API** - Programmatic access via `python -m sessions.api` (unified module path)
- **Consolidated Slash Commands** - `/sesh-config`, `/sesh-state`, `/sesh-tasks` with API delegation pattern and --from-slash contextual output
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
- `implementation_only_tools` - Tools blocked in discussion mode (default: Edit, Write, MultiEdit, NotebookEdit), managed via `config tools` commands with CCTools enum validation
- `bash_read_patterns` - Patterns considered "read only" in Bash tool inputs and allowed in discussion mode, managed via `config read` commands
- `bash_write_patterns` - Patterns considered "write-like" in Bash tool inputs and blocked in discussion mode, managed via `config write` commands
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

### Kickstart Onboarding Protocol System (v0.3.6+)

Comprehensive first-run onboarding system providing interactive guided setup and configuration for new cc-sessions installations:

**Three Mode Variants:**
- **Full Mode** (30-45 min): Complete walkthrough with 12 protocol chunks covering DAIC enforcement, trigger phrases, state management, task workflows, agent customization, tool configuration, and advanced features with interactive exercises and validation
- **API Mode** (10-15 min): Condensed 8 protocol chunks with same functionality but concise presentation for token budget consciousness
- **Seshxpert Mode** (5 min): Single protocol chunk with import/auto-generate support for experienced users setting up new repos

**Core Architecture:**
- **API-Driven Flow**: Protocols call `python -m sessions.api kickstart` commands for state management and progression
- **Numbered Protocol Chunks**: Discrete markdown files (01-14) per learning module, loaded sequentially via `next` command
- **Mode-Specific Directories**: `kickstart/full/` (12 chunks), `kickstart/api/` (8 chunks), `kickstart/seshxpert/` (1 chunk) with variant implementations
- **Interactive Learning**: Demonstrates concepts through practice with real commands and immediate feedback
- **Dummy Task Integration**: Uses `h-kickstart-setup.md` template as practice task throughout onboarding

**Session Start Integration:**
- Dedicated `kickstart_session_start.py|.js` hooks registered in settings.json for first-run detection
- Automatically triggered when `STATE.flags.noob` is `True` during session initialization
- Short-circuits immediately when noob=false to let normal session_start hooks run
- Loads `kickstart/01-entry.md` with yes/later/never options and natural language date parsing
- Resume support for multi-session onboarding with progress preserved in `STATE.metadata.kickstart_progress`
- Reminder system checks `kickstart_reminder_date` and re-presents entry prompt when time expires
- Config injection: Protocol chunks with `{config}` template variable receive formatted current configuration

**Full Mode Protocol Sequence:**
1. Core workflow and DAIC enforcement (03) - Interactive demonstration with trigger phrase practice
2. Trigger phrase customization (04) - Configuration of all six trigger categories
3. Orphaned todos management (05) - State system overview with practical examples
4. Task and branch workflows (06) - Task types, priorities, branch mapping, and enforcement
5. Task startup protocol (07) - Practice with dummy task and configuration of startup preferences
6. Create first task (08) - Guided creation of real task for current project work
7. Always-available protocols (09) - Completion, compaction, and helper protocols
8. Agent customization (10-11) - Context-gathering and code-review agent setup with tech stack assessment
9. Tool configuration (12) - Custom readonly commands and bash pattern management
10. Advanced features (13) - Directory tasks, bypass mode, task indexes, stashed todos
11. Graduation (14) - Cleanup, summary, quick reference card, and next steps

**API Mode Compression:**
- Same functionality as Full mode with condensed language and fewer examples
- Skips advanced features module (13) to reduce time investment
- Focus on essential configuration with minimal explanations
- 8 protocol chunks total covering core workflows through agent customization

**Seshxpert Mode Fast Path:**
- Single protocol chunk (03-quick-setup.md) with import/auto-generate workflow
- Copy sessions-config.json from existing repo (local or GitHub URL)
- Copy agent overrides from `.claude/agents/` directory
- Auto-generate configuration from repository detection
- Skip all explanatory content and move directly to graduation

**State Management:**
- Progress tracking in `STATE.metadata.kickstart_progress` with mode, started timestamp, last_active timestamp, current_module, completed_modules array
- Agent-specific progress tracking for customization workflow in kickstart_progress.agent_progress
- Reminder date storage in `STATE.metadata.kickstart_reminder_date` for "later" responses with dd:hh format parsing
- Graduation cleanup: Clears `noob` flag and kickstart metadata while preserving all configuration changes and agent overrides

**API Commands:**
- `python -m sessions.api kickstart next` - Load next protocol chunk based on mode and current progress with config template injection
- `python -m sessions.api kickstart mode <full|api|seshxpert>` - Initialize kickstart with selected mode and set initial progress state
- `python -m sessions.api kickstart remind <dd:hh>` - Set reminder for later onboarding (format: days:hours, e.g., "1:00" for tomorrow)
- `python -m sessions.api kickstart complete` - Exit kickstart with hybrid cleanup: automated file deletion + manual router/config cleanup instructions

**Self-Cleanup System:**
- Hybrid approach: Automated deletion of kickstart protocols, hooks, and setup task files
- Language detection: Determines Python vs JavaScript installation by checking which kickstart_session_start hook file exists (py vs js)
- Manual cleanup instructions for router imports, COMMAND_HANDLERS entries, settings.json hooks, and API command files
- Preserves `.claude/agents/` directory and all user customizations during cleanup
- Switches to implementation mode automatically before file deletion to bypass DAIC enforcement
- Returns formatted todo list for manual cleanup steps that can't be automated

**Protocol Files:**
- Base entry and mode selection: `cc_sessions/protocols/kickstart/01-entry.md`, `02-mode-selection.md`
- Full mode chunks (12): `cc_sessions/protocols/kickstart/full/03-core-workflow.md` through `14-graduation.md`
- API mode chunks (8): `cc_sessions/protocols/kickstart/api/03-core-workflow.md` through `10-graduation.md`
- Seshxpert mode chunk (1): `cc_sessions/protocols/kickstart/seshxpert/03-quick-setup.md`
- Dummy task template: `cc_sessions/templates/h-kickstart-setup.md` for onboarding practice

**Supporting Infrastructure:**
- Kickstart API module: `cc_sessions/scripts/api/kickstart_commands.py|.js` with next, mode, remind, complete commands
- Kickstart SessionStart hooks: `cc_sessions/hooks/kickstart_session_start.py|.js` with noob flag detection and reminder handling
- Module sequences: FULL_MODE_SEQUENCE (12 modules), API_MODE_SEQUENCE (8 modules), SESHXPERT_SEQUENCE (2 modules)
- Config formatting: `format_config_for_display()` helper generates readable markdown of current configuration
- Sessions API enhancements for bash pattern management: config read/write commands
- Agent customization guide: `cc_sessions/kickstart/agent-customization-guide.md` for tech stack-specific customization
- KICKSTART_APPROACH.md: Documents API-driven protocol pattern and implementation philosophy

### Directory Task Support (v0.3.5+)

Enhanced the task management system with first-class support for directory-based tasks with subtask workflows:

**Core Implementation:**
- **Helper Functions**: Added `is_directory_task(task_path)` and `get_task_file_path(task_path)` to shared_state.py:595-615 and shared_state.js for consistent directory task detection across all code
- **Detection Logic**: Simplified to check for '/' in task path (e.g., "h-implement-auth/01-setup.md") rather than filesystem verification for reliable subtask detection
- **Path Resolution**: `get_task_file_path()` automatically resolves directory tasks to README.md, file tasks to direct .md path
- **Type Safety**: Python implementation accepts Union[str, Path], normalizes to string for consistent '/' detection
- **Consistent Usage**: Updated 9 files across hooks and API commands to use new helper functions instead of manual detection

**Protocol Integration:**
- **Task Creation** (task-creation.md:57-74): Protocol explicitly asks users to confirm directory structure with clear explanation of implications:
  - Creating subtasks will be the first step after task creation
  - All work done iteratively on the same task branch
  - Plan and spec out subtasks comprehensively before implementation
  - Individual subtask commits won't merge to main until all subtasks complete
- **Task Startup**: Conditionally loads directory-task-startup.md guidance when `is_directory_task()` returns true, emphasizing:
  - Read entire task specification in README.md thoroughly
  - Analyze all success criteria to understand full scope
  - Plan comprehensive subtask breakdown with clear deliverables
  - Create well-defined subtask files with specific goals
- **Task Completion**: Automatically detects directory tasks using `is_directory_task(STATE.current_task.file)` and prevents auto-merge until all subtasks complete, overriding user's auto_merge preference

**Workflow Features:**
- Directory tasks work iteratively on the same feature branch without merging
- Subtask commits stay on the task branch until entire multi-phase effort completes
- Planning-first approach with comprehensive subtask breakdown requirements
- Manual merge control ensures quality review of complete work
- Each subtask has independent success criteria building toward overall task goals

**Implementation Approach:**
- Minimal, practical implementation over extensive automation (guidance-based rather than automated subtask management)
- Clean integration with existing protocol templating system using conditional section loading
- No breaking changes to existing task workflows (file-based tasks unaffected)
- Bug fixes included: Fixed incorrect `STATE.current_task.file_path` references, Path type handling, and template variable substitution

**Files Modified:**
- shared_state.py/js: Added helper functions
- user_messages.py/js: Integrated directory task detection in startup and completion protocols
- task-creation.md: Added directory structure decision point
- directory-task-startup.md: New planning guidance snippet

### Protocol Structured Output (v0.3.3+)
Enhanced all protocols with transparent structured output formats at key decision points:

**Structured Output Formats:**
- `[PROPOSAL]` - Task naming, success criteria, implementation plans
- `[STATUS]` - Pre-completion checks, context manifest status, git state
- `[PLAN]` - Implementation approaches with expandable explanations
- `[FINDINGS]` - Code review results with categorized issues
- `[DECISION]` - User choice points for context gathering, task indexing, file handling
- `[QUESTION]` - User input requests for task success definition
- `[RUNNING]`/`[COMPLETE]` - Agent execution tracking during context compaction

**Visual Indicators:**
- ✓ for completed items and successful states
- ✗ for failures or missing requirements
- □ for proposals, findings, and action items

This enhancement provides predictable AI communication patterns and improves transparency at protocol decision points, replacing informal communication with standardized formats that clearly indicate when user input or confirmation is required.

### JavaScript Implementation Complete (v0.3.4)

The cc-sessions package now provides complete feature parity between Python and JavaScript implementations, enabling users to choose their preferred runtime environment without functionality compromises.

**Complete JavaScript Port Achieved:**
- ✅ **6 Core Hook Files**: All hook files (`session_start.js`, `user_messages.js`, `post_tool_use.js`, `sessions_enforce.js`, `subagent_hooks.js`, `shared_state.js`) provide identical functionality to Python counterparts
- ✅ **6 API Module Files**: All API modules (`config_commands.js`, `index.js`, `protocol_commands.js`, `router.js`, `state_commands.js`, `task_commands.js`) completely rewritten to match Python functionality
- ✅ **Dependency Elimination**: Removed tiktoken and yaml dependencies from both language implementations
- ✅ **Architecture Simplification**: Both languages now use simple string parsing and character-based operations instead of external tokenization

**Technical Achievements:**
- **Stdin JSON Handling**: JavaScript hooks now properly read JSON input from stdin instead of command-line arguments, matching Claude Code's hook execution model
- **Atomic State Management**: Implemented Node.js equivalent patterns for Python's `edit_state()` context manager with proper file locking
- **Hook Output Compliance**: All JavaScript hooks output correct `hookSpecificOutput` JSON structure expected by Claude Code
- **Behavioral Equivalence**: Error handling, exit codes, and execution patterns match Python behavior exactly
- **File System Operations**: Proper async/await patterns for file operations with concurrent access protection

**Quality Assurance Process:**
Used systematic 5-step iterloop methodology for each file:
1. Read Python implementation completely
2. Read JavaScript implementation completely
3. Itemize functional differences
4. Apply fixes to achieve feature parity
5. Document changes made

**Status**: Both Python and JavaScript variants now provide identical DAIC enforcement, state management, task workflows, and API capabilities. Users can choose their preferred language without functional limitations.

**Architectural Cleanup During Port:**
- **Git Repository Detection Simplification**: Refactored `find_git_repo()`/`findGitRepo()` to assume directory input, eliminating file path existence checks and directory detection logic. Callers now pass `file_path.parent` (Python) or `path.dirname(filePath)` (JavaScript) when working with file paths, creating cleaner separation of concerns and more predictable behavior.

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

### System Reliability Improvements (2025-09-27)
Recent stability enhancements in `shared_state.py` address intermittent failures affecting statusline display and trigger phrase recognition:

**Lock Contention Resolution:**
- **Timeout Optimization**: Reduced lock acquisition timeout from 5 seconds to 1 second to eliminate user-visible delays
- **Force-Removal Mechanism**: Added aggressive lock cleanup after timeout instead of raising exceptions
- **Stale Lock Detection**: Enhanced process death detection with automatic cleanup of abandoned locks
- **Impact**: Eliminates intermittent failures when statusline and trigger phrase hooks compete for state file access

**Dataclass Serialization Fix:**
- **EnabledFeatures.from_dict()**: Fixed ContextWarnings instantiation to properly handle nested dictionary structures
- **Type Safety**: Enhanced validation prevents silent failures in feature flag handling
- **Configuration Reliability**: Ensures proper deserialization of complex configuration structures

These improvements maintain data integrity and atomic file operations while significantly improving system responsiveness and reliability during concurrent hook operations.

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
- **Atomic File Operations**: File locking and atomic writes prevent state corruption across all operations with optimized 1-second timeout and aggressive lock cleanup
- **Cross-platform Compatibility**: pathlib.Path throughout with Windows-specific handling
- **API Command Integration**: Sessions API commands whitelisted in DAIC enforcement and bypass ultrathink detection
- **Dual-Context Import Pattern**: Supports both symlinked development and package installation through CLAUDE_PROJECT_DIR detection
- **Reliable Lock Management**: Enhanced lock contention handling prevents intermittent failures in statusline and trigger phrase recognition
- **Simplified Git Repository Detection**: `find_git_repo()`/`findGitRepo()` functions assume directory input; callers responsible for passing `file_path.parent` or `path.dirname(filePath)` when working with file paths

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
- **Bash Pattern Management**: `config read` and `config write` commands for managing bash_read_patterns and bash_write_patterns
- **Tool Blocking Management**: `config tools` commands with CCTools enum validation for implementation_only_tools
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
- Directory-based tasks for complex multi-phase work with subtask support
- File-based tasks for focused single objectives
- Automatic branch mapping from task naming conventions
- Git submodule awareness through task frontmatter

**Directory Task Support:**
- **Helper Functions**: `is_directory_task(task_path)` in shared_state.py:595-607 and shared_state.js detects directory tasks by checking for '/' in path, with fallback to README.md existence check
- **Path Resolution**: `get_task_file_path(task_path)` in shared_state.py:609-615 and shared_state.js resolves to README.md for directory tasks or direct .md path for file tasks
- **Creation Protocol**: task-creation.md:57-74 asks users to confirm directory structure with explanation of subtask workflow, planning requirements, and same-branch iteration
- **Startup Protocol**: Conditionally loads directory-task-startup.md when `is_directory_task()` returns true, emphasizing comprehensive subtask specification before implementation
- **Completion Protocol**: Detects directory tasks and prevents auto-merge until all subtasks complete, overriding user's auto_merge preference to keep work on feature branch
- **Consistent Detection**: Both Python and JavaScript implementations use identical helper functions across all hooks and API commands for reliable identification

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
- **Python package** with pip/pipx/uv support (Python-only dependencies)
- **NPM package** for JavaScript environments (JavaScript-only dependencies)
- **Direct bash script** for build-from-source installations
- **Symlinked Development Setup**: Use cc-sessions package locally without installation via symlinks
- **Cross-platform compatibility** (macOS, Linux, Windows 10/11)
- **Complete feature parity** between Python and JavaScript implementations

### Language Implementation Status
- **Python Implementation**: Complete and fully functional (reference implementation)
- **JavaScript Implementation**: Complete with full feature parity (as of v0.3.4)
  - All 6 core hook files providing identical functionality
  - All 6 API module files with complete feature set
  - No external dependencies (tiktoken/yaml removed)
  - Proper stdin JSON handling and atomic state management
  - File locking patterns and async operations implemented

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
- **Atomic State Protection**: File locking prevents state corruption and race conditions with optimized 1-second timeout and force-removal after timeout
- **Configuration Validation**: Type-safe configuration prevents invalid behavioral patterns
- **Backup and Recovery**: Automatic backup of corrupted configuration/state files
- **API Security Boundaries**: Sessions API prevents access to safety-critical features
- **Enhanced Lock Reliability**: Improved lock contention handling eliminates user-visible delays from statusline and trigger phrase operations
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

### Consolidated Slash Commands
- `/sesh-config` - Comprehensive configuration management with API delegation pattern
- `/sesh-state` - State inspection and mode switching with enhanced output formatting
- `/sesh-tasks` - Task management operations (create, start, list, quick capture)

#### API Delegation Pattern
All slash commands use: `!python -m sessions.api <command> $ARGUMENTS --from-slash`

**Enhanced Features:**
- **Contextual Output**: `--from-slash` flag enables user-friendly responses optimized for slash command usage
- **Adaptive Error Messages**: Commands show valid options and contextual help when operations fail
- **Two-Level Help System**: Brief help at top level (`/sesh-config help`), verbose help for specific operations (`/sesh-config trigger help`)
- **Name Mapping**: Friendly aliases (go→implementation_mode, auto→true, etc.) for user convenience

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

**Kickstart Operations:**
- `python -m sessions.api kickstart next` - Load next module chunk in onboarding sequence
- `python -m sessions.api kickstart mode <full|api|seshxpert>` - Initialize kickstart with selected mode
- `python -m sessions.api kickstart remind <dd:hh>` - Schedule reminder for later onboarding (format: days:hours)
- `python -m sessions.api kickstart complete` - Exit kickstart, clear noob flag and progress metadata

**Configuration Operations:**
- `python -m sessions.api config [--json] [--from-slash]` - Full configuration inspection with optional contextual formatting
- `python -m sessions.api config phrases list [category] [--from-slash]` - View trigger phrases
- `python -m sessions.api config phrases add <category> "<phrase>" [--from-slash]` - Add trigger phrase
- `python -m sessions.api config phrases remove <category> "<phrase>" [--from-slash]` - Remove trigger phrase
- `python -m sessions.api config features toggle <key> [--from-slash]` - Toggle feature boolean values
- `python -m sessions.api config git show [--from-slash]` - View git preferences
- `python -m sessions.api config git set <setting> <value> [--from-slash]` - Update git preference
- `python -m sessions.api config env show [--from-slash]` - View environment settings
- `python -m sessions.api config env set <setting> <value> [--from-slash]` - Update environment setting
- `python -m sessions.api config read list [--from-slash]` - List bash read patterns
- `python -m sessions.api config read add <pattern> [--from-slash]` - Add bash read pattern
- `python -m sessions.api config read remove <pattern> [--from-slash]` - Remove bash read pattern
- `python -m sessions.api config write list [--from-slash]` - List bash write patterns
- `python -m sessions.api config write add <pattern> [--from-slash]` - Add bash write pattern
- `python -m sessions.api config write remove <pattern> [--from-slash]` - Remove bash write pattern
- `python -m sessions.api config tools list [--from-slash]` - List implementation-only tools
- `python -m sessions.api config tools block <ToolName> [--from-slash]` - Block tool in discussion mode
- `python -m sessions.api config tools unblock <ToolName> [--from-slash]` - Unblock tool

**Slash Command Integration:**
- All API commands support `--from-slash` flag for enhanced error messages and user-friendly output formatting
- Contextual help shows relevant options when commands fail
- Adaptive responses optimized for slash command user experience

**Security Notes:**
- No access to blocked_actions configuration (prevents DAIC bypass)
- No two-way mode switching (prevents safety bypass)
- No todo manipulation (respects TodoWrite safety mechanisms)
- No access to branch_enforcement toggle (maintains git safety)

## Sessions System Behaviors

@CLAUDE.sessions.md

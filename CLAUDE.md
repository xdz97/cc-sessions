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
- `cc_sessions/hooks/shared_state.py|.js` - Core state and configuration management with unified SessionsConfig system, enhanced lock timeout behavior (1-second timeout with force-removal), fixed EnabledFeatures.from_dict() dataclass serialization, directory task helper functions `is_directory_task()`, `get_task_file_path()`, subtask detection helpers `is_subtask()`, `is_parent_task()`, and path normalization `_normalize_task_path()` (lines 607-678 Python, 927-1023 JavaScript), simplified `find_git_repo()`/`findGitRepo()` functions that assume directory input, SessionsTodos.to_dict() serialization method for complete todos structure, EnabledFeatures.branch_enforcement configuration field (lines 299-314 Python, similar in JavaScript), and UTF-8 encoding enforcement for all file operations (both Python and JavaScript implementations)
- `cc_sessions/hooks/sessions_enforce.py|.js` - Enhanced DAIC enforcement with comprehensive command categorization and argument analysis for write operation detection, calls `find_git_repo(file_path.parent)` for branch validation with CONFIG.features.branch_enforcement guard (lines 351-352 Python, line 444 JavaScript) enabling alternative VCS support (both Python and JavaScript implementations)
- `cc_sessions/hooks/session_start.py|.js` - Session initialization with configuration integration, dual-import pattern, and kickstart protocol detection via `STATE.flags.noob` (both Python and JavaScript implementations)
- `cc_sessions/hooks/kickstart_session_start.py|.js` - Kickstart-only SessionStart hook that loads protocols based on sequence index in STATE.metadata['kickstart'], initializes sequence on first run, and displays current protocol with user instructions (both Python and JavaScript implementations)
- `cc_sessions/hooks/user_messages.py|.js` - Protocol auto-loading with `load_protocol_file()` helper, centralized todo formatting, directory task and subtask detection for context-aware protocol loading (lines 327-348 Python, 415-437 JavaScript), merge prevention for subtasks during completion, improved task startup notices, and UTF-8 encoding fixes for protocol file loading and transcript reading (both Python and JavaScript implementations)
- `cc_sessions/hooks/post_tool_use.py|.js` - Todo completion detection and automated mode transitions (both Python and JavaScript implementations)
- `cc_sessions/hooks/subagent_hooks.py|.js` - Subagent context management and flag handling with UTF-8 encoding for transcript reading (both Python and JavaScript implementations)
- `cc_sessions/python/statusline.py` / `cc_sessions/javascript/statusline.js` - Claude Code statusline integration with Nerd Fonts icon support, git branch display with upstream tracking indicators (↑/↓), detached HEAD detection, and UTF-8 encoding for transcript reading (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/__main__.py` - Sessions API entry point with --from-slash flag support for contextual output (Python)
- `cc_sessions/scripts/api/index.js` - Sessions API entry point (JavaScript)
- `cc_sessions/scripts/api/router.py|.js` - Command routing with protocol command support, kickstart handler integration, and --from-slash flag handling (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/protocol_commands.py|.js` - Protocol-specific API commands with startup-load returning full task content (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/kickstart_commands.py|.js` - Kickstart-specific API commands for onboarding flow state management (next, complete) with hybrid self-cleanup system (both Python and JavaScript implementations)
- `cc_sessions/python/protocols/kickstart/01-discussion.md` through `11-graduation.md` - Full mode protocol sequence (11 protocols total)
- `cc_sessions/python/protocols/kickstart/01-agents-only.md` - Subagents-only mode protocol
- `cc_sessions/templates/h-kickstart-setup.md` - Dummy task template used for onboarding practice
- `cc_sessions/scripts/api/state_commands.py|.js` - State inspection and limited write operations, uses SessionsTodos.to_dict() for simplified todo serialization in state component access and SessionsTodos.to_list('active') for todos command (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/config_commands.py|.js` - Configuration management commands with --from-slash support for contextual output formatting, includes read/write/tools pattern management with CCTools enum validation (both Python and JavaScript implementations)
- `cc_sessions/scripts/api/task_commands.py|.js` - Task management operations with index support and task startup protocols (both Python and JavaScript implementations)
- `cc_sessions/commands/` - Thin wrapper slash commands following official Claude Code patterns
- `cc_sessions/install.py` - Python-specific installer module with backup/restore functions: `create_backup()` creates timestamped backups, `restore_tasks()` restores task files after installation, content detection via task file counting, backup verification before proceeding, `configure_gitignore()` adds runtime file entries to project .gitignore (lines 324-346), automatic OS detection using platform.system() to configure sessions-config.json
- `install.js` - JavaScript-specific installer at package root with backup/restore functions: `createBackup()` creates timestamped backups, `restoreTasks()` restores task files after installation, content detection via recursive directory traversal, backup verification before proceeding, `configureGitignore()` adds runtime file entries to project .gitignore (lines 353-378), automatic OS detection using os.platform() to configure sessions-config.json
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
- `scripts/prepare-release.py` - Pre-flight validation with 7 automated checks (version sync, branch state, CHANGELOG format, git cleanliness, build tests, tool availability)
- `scripts/publish-release.py` - Atomic 15-step publishing workflow (merge next→main, tag, build, publish to PyPI/npm, GitHub release, CHANGELOG rotation)
- `scripts/check-version-sync.sh` - Standalone version consistency validator between package.json:3 and pyproject.toml:7
- `RELEASE.md` - Complete release workflow documentation for maintainers
- `cc_sessions/protocols/task-creation/task-creation.md:37-74` - Main templated task creation protocol with directory task structure decision and user confirmation
- `cc_sessions/protocols/task-startup/task-startup.md` - Main templated task startup protocol with conditional sections
- `cc_sessions/protocols/task-startup/directory-task-startup.md` - Planning guidance for parent README.md startup emphasizing comprehensive subtask specification, comprehensive planning, and task branch creation
- `cc_sessions/protocols/task-startup/subtask-startup.md` - Branch checkout guidance for subtask startup ensuring work continues on parent task branch
- `cc_sessions/protocols/task-completion/task-completion.md` - Main templated task completion protocol with directory task detection and auto-merge prevention
- `cc_sessions/protocols/task-completion/subtask-completion.md` - Subtask-specific completion guidance preventing individual subtask merges
- `cc_sessions/protocols/task-completion/commit-style-*.md` - Commit style templates (conventional, simple, detailed)
- `pyproject.toml` - Package configuration with console script entry points

## Installation Methods
**Python Variant (No Node.js required):**
- `pipx install cc-sessions` - Isolated Python install (recommended)
- `pip install cc-sessions` - Direct pip install
- `uv pip install cc-sessions` - UV package manager install
- Installer: `cc_sessions/install.py` module entry point
- Uses only: `cc_sessions/python/`, `cc_sessions/agents/`, `cc_sessions/knowledge/`

**JavaScript Variant (No Python required):**
- `npm install -g cc-sessions` - Global npm install
- `npx cc-sessions` - One-time execution
- Installer: `install.js` at package root
- Uses only: `cc_sessions/javascript/`, `cc_sessions/agents/`, `cc_sessions/knowledge/`

**Development:**
- Direct bash: `./install.sh` from repository
- **Symlinked Development Setup**: Use cc-sessions package locally without installation via symlinks

**Update/Reinstall Behavior:**
- Both installers detect existing installations and preserve user content automatically
- Timestamped backups created in `.claude/.backup-YYYYMMDD-HHMMSS/` before installation
- Task files and agent customizations restored after installation completes
- State and config files regenerate fresh (not backed up)
- Gitignore entries automatically added during first install to prevent tracking runtime files

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
- **Subtask Detection**: `is_subtask()` identifies individual subtask files (excludes README.md), `is_parent_task()` identifies parent README.md files within directory tasks
- **Path Normalization**: `_normalize_task_path()` handles absolute paths and strips sessions/tasks/ prefix for consistent detection across all code
- **Task Creation Integration**: Protocol explicitly asks users to confirm directory structure with clear explanation of workflow implications
- **Context-Aware Startup**: Protocols distinguish between parent task startup (planning guidance) and subtask startup (branch checkout guidance)
- **Parent Task Startup**: Loads directory-task-startup.md for README.md, emphasizes planning and subtask creation, creates task branch
- **Subtask Startup**: Loads subtask-startup.md for subtask files, checks for existing branch, focuses on subtask-specific implementation
- **Merge Prevention**: Task completion protocol automatically prevents merge for subtasks, only parent task completion merges to main branch
- **Iterative Workflow**: All subtasks work on the same feature branch without merging until the entire multi-phase effort is done
- **Consistent Detection**: Helper functions used throughout hooks and API commands for reliable directory task and subtask identification

### Branch Enforcement
- Task-to-branch mapping: implement- → feature/, fix- → fix/, etc.
- Blocks code edits if current branch doesn't match task requirements
- Four failure modes: wrong branch, no branch, task missing, branch missing
- **Configurable Toggle**: Users can disable branch enforcement via `CONFIG.features.branch_enforcement` for alternative VCS systems (Jujutsu, Mercurial, etc.)

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
- Two mode variants: Full (11 protocols, 15-30 min), Subagents-only (1 protocol, 5 min)
- Triggered automatically when `STATE.metadata['kickstart']` exists from installer choice
- Index-based progression system with sequence management in state
- Teaches DAIC enforcement, task management workflows, three core protocols, agents, and advanced features
- Protocols located in `cc_sessions/python/protocols/kickstart/` and `cc_sessions/javascript/protocols/kickstart/`
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
└── kickstart/                              # First-run onboarding protocols
    ├── 01-discussion.md                    # DAIC introduction with interactive demo
    ├── 02-implementation.md                # Implementation mode mechanics with TodoWrite
    ├── 03-tasks-overview.md                # Task management concepts and naming conventions
    ├── 04-task-creation.md                 # Task creation protocol with practice
    ├── 05-task-startup.md                  # Task startup protocol with practice
    ├── 06-task-completion.md               # Task completion protocol with practice
    ├── 07-compaction.md                    # Context compaction protocol
    ├── 08-agents.md                        # Five specialized agents overview
    ├── 09-api.md                           # Sessions API and slash commands
    ├── 10-advanced.md                      # Task indexes, iterloop, stashed todos
    ├── 11-graduation.md                    # Cleanup, summary, next steps
    └── 01-agents-only.md                   # Subagents-only mode (agent customization focus)
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
- **Sessions API** - Programmatic access via `sessions` (unified module path)
- **Consolidated Slash Commands** - `/sesh-config`, `/sesh-state`, `/sesh-tasks` with API delegation pattern and --from-slash contextual output
- **Protocol Commands** - `sessions protocol startup-load <task-file>` returns full task file content for task loading
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
- `branch_enforcement` - Git branch validation (default: true, can be disabled for alternative VCS systems like Jujutsu or Mercurial)
- `task_detection` - Task-based workflow automation
- `auto_ultrathink` - Enhanced AI reasoning
- `use_nerd_fonts` - Nerd Fonts icon display in statusline (default: true, shows icons when enabled, ASCII fallback when disabled)
- `auto_update` - Automatic package updates on session start (default: false, when enabled updates cc-sessions automatically when new version detected)
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

### Gitignore Configuration
Both Python and JavaScript installers automatically configure project `.gitignore` file:

**Automatic Entries Added:**
- `sessions/sessions-state.json` - Runtime session state (ephemeral, should never be tracked)
- `sessions/transcripts/` - Agent transcript files (runtime-generated, project-specific)

**Behavior:**
- Function location: `cc_sessions/install.py:324-346` (Python), `install.js:353-378` (JavaScript)
- Idempotent: Only adds entries if `sessions/sessions-state.json` not already present in file content
- Creates new `.gitignore` file if one doesn't exist
- Appends to existing `.gitignore` without overwriting
- Follows same pattern as existing `configure_claude_md()` function

**Rationale:**
- Prevents accidental commits of ephemeral state files
- Eliminates merge conflicts from runtime state changes
- Keeps agent transcripts out of repository (project-specific, not portable)
- Reduces repository clutter from runtime-generated files

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

### Release Management Workflow (v0.3.13+)

Complete release automation system for dual-package publishing to PyPI and npm with automatic update detection for users.

**Release Workflow Overview:**
- Simplified `next` → `main` branching strategy for solo development
- Development accumulates on `next` with continuous CHANGELOG maintenance
- Manual version bumping and CHANGELOG finalization on `next` branch
- Automated validation ensures consistency before publishing
- Atomic publishing sequence merges, tags, builds, and publishes to both registries
- Complete workflow documented in `RELEASE.md` for maintainers

**Pre-Flight Validation (prepare-release.py):**
- 7 automated checks: version sync (package.json:3 and pyproject.toml:7), branch state (on `next`), CHANGELOG format (version with date, no "Unreleased"), git cleanliness (no uncommitted files), Python build (`python -m build`), npm validation (`npm pack --dry-run`), tool availability (python, npm, twine, git)
- Interactive mode with detailed actionable guidance for each failure
- `--auto` flag for CI integration with simple checklist output
- Offers to launch publish script on successful validation

**Atomic Publishing (publish-release.py):**
- 15-step sequence with comprehensive pre-flight checks before point of no return
- Extracts version from package.json automatically
- Validates credentials for PyPI (twine) and npm (npm whoami)
- Merges `next` → `main`, creates git tag `vX.Y.Z` on main
- Builds Python artifacts and publishes to PyPI via twine
- Publishes to npm registry simultaneously
- Pushes commits and tags to GitHub
- Extracts CHANGELOG section and creates GitHub Release with notes
- Returns to `next` branch and creates new "Unreleased" section for next cycle
- Interactive rollback support with manual recovery instructions on failure

**Version Consistency (check-version-sync.sh):**
- Standalone bash utility for version validation across package managers
- Reads package.json line 3 and pyproject.toml line 7
- Exits 0 if versions match, exits 1 if mismatched
- Used by release scripts, CI workflows, and manual validation

**Update Detection for Users:**
- Flag-based caching in `STATE.metadata` prevents redundant PyPI/npm checks on every session start
- Update status tracked: `update_available` (true/false/undefined), `latest_version`, `current_version`
- Check logic: if flag doesn't exist, query PyPI (Python) or npm registry (JavaScript), set flag based on result
- CHANGELOG excerpt extraction shows first 3 changes from new version in notification
- Notification appears on session start with upgrade instructions for both package managers

**Auto-Update Feature (Opt-In):**
- Configurable via `CONFIG.features.auto_update` (default: false, users must enable)
- When enabled, automatically runs pip/npm upgrade on session start when update detected
- Blocking operation with 60-second timeout and graceful fallback to manual message
- Clears update flag on successful upgrade, shows confirmation message
- Maintains user control over when package updates occur

**Update Management API:**
- `sessions state update suppress` - Sets flag to false, suppresses notifications until next actual update (user remains on current version but stops seeing warnings)
- `sessions state update check` - Clears cached flags, forces fresh PyPI/npm check on next session start
- `sessions state update status` - Shows current version, latest version, and update availability with flag state

**Implementation Files:**
- scripts/prepare-release.py (404 lines) - Pre-flight validation with 7 checks, interactive/auto modes, actionable error guidance
- scripts/publish-release.py (418 lines) - Atomic 15-step publishing with rollback support and manual recovery instructions
- scripts/check-version-sync.sh (38 lines) - Bash version consistency validator
- RELEASE.md - Complete release workflow documentation for maintainers
- session_start.py lines 352-434 (Python) - Update detection with PyPI checks, CHANGELOG parsing, auto-update support
- session_start.js lines 111-226 (JavaScript) - Update detection with npm registry checks, CHANGELOG parsing, auto-update support
- shared_state.py line 304 - auto_update feature flag in EnabledFeatures dataclass
- state_commands.py lines 513-579 (Python) - Update management commands (suppress, check, status)
- state_commands.js - JavaScript parity for update management commands

### Statusline Nerd Fonts and Git Branch Display (v0.3.12+)

Enhanced Claude Code statusline with visual improvements and git branch information:

**Nerd Fonts Icon Support:**
- Context icon (󱃖) for context usage display
- Task icon (󰒓) for current task display
- Mode icons (󰭹 for Discussion, 󰷫 for Implementation)
- Tasks icon (󰈙) for open task count
- Git branch icon (󰘬) for branch display
- Detached HEAD icon (󰌺) for detached state
- ASCII fallback when use_nerd_fonts disabled

**Git Branch Display:**
- Branch name appears at end of line 2 with automatic `-C` command pattern
- Uses `git branch --show-current` for reliable branch detection
- Detached HEAD detection shows commit hash with broken link icon (󰌺 @abc1234)
- ASCII fallback shows `@abc1234 [detached]` when Nerd Fonts disabled

**Upstream Tracking Indicators:**
- Shows commits ahead of remote with ↑N (e.g., ↑3)
- Shows commits behind remote with ↓N (e.g., ↓2)
- Combined display when both ahead and behind (e.g., ↑3↓2)
- Appears in uncommitted section between edited files and open tasks
- Uses `git rev-list --count @{u}..HEAD` and `HEAD..@{u}` for tracking status
- Gracefully handles missing upstream with silent failure

**Configuration Toggle:**
- Feature flag: `CONFIG.features.use_nerd_fonts` (default: true)
- Toggle via API: `sessions config features toggle use_nerd_fonts`
- Toggle via slash command: `/sessions config features toggle use_nerd_fonts`
- View current state: `sessions config features show`

**Implementation:**
- Python: Lines 62-68, 159-213, 222-225, 260, 265, 277-278 in statusline.py
- JavaScript: Lines 76-77, 154, 164-207, 214-216, 260, 267, 280-281 in statusline.js
- Configuration: Lines 303, 315 in shared_state.py (EnabledFeatures dataclass)
- API toggle: Lines 619-631 in config_commands.py

**Space Optimization:**
- Removed "files" text from uncommitted section to accommodate upstream indicators
- Now shows `✎ 5 ↑3` instead of `✎ 5 files`
- Line 2 format: `Mode | Edited & Uncommitted with upstream | Open Tasks | Git branch`

**Files Modified:**
- statusline.py: Lines 62-68, 159-213, 222-225, 260-278
- statusline.js: Lines 76-77, 154-207, 214-216, 260-283
- shared_state.py: Lines 303, 315 (EnabledFeatures)
- shared_state.js: Mirror implementation
- config_commands.py: Lines 619-631 (toggle support)
- config_commands.js: Mirror implementation

### Branch Enforcement Configuration Toggle (v0.3.11+)

Enhanced branch enforcement system with user-configurable toggle to support alternative version control systems beyond Git:

**Problem Solved:**
Users working with alternative VCS systems (Jujutsu, Mercurial, Fossil, etc.) experienced friction with Git-specific branch enforcement. The system assumed Git branches and would block operations when branch expectations didn't match, requiring manual workarounds like emptying task branch fields.

**Implementation:**
- Added `CONFIG.features.branch_enforcement` toggle with default value of `true` (preserves existing Git workflow safety)
- Both Python and JavaScript enforcement hooks check feature flag before validating branches
- Early exit with code 0 (allow) when branch_enforcement is disabled at shared_state.py:351-352 and shared_state.js:444
- Configuration API provides `features toggle branch_enforcement` command for simple boolean flipping
- Feature documented in kickstart onboarding protocols for discoverability

**User Control:**
- Toggle via Sessions API: `sessions config features toggle branch_enforcement`
- Toggle via slash command: `/sessions config features toggle branch_enforcement`
- View current state: `sessions config features show`
- Compatible with configuration import/export during kickstart seshxpert mode

**Integration Points:**
- Enforcement hooks: `sessions_enforce.py:351-352` (Python), `sessions_enforce.js:444` (JavaScript)
- Configuration system: `shared_state.py:299-314` (EnabledFeatures dataclass with branch_enforcement field)
- API commands: `config_commands.py:619-631` (toggle operation), `config_commands.js` (JavaScript parity)
- Kickstart protocols: `kickstart/api/06-configuration.md:57` and `kickstart/seshxpert/03-quick-setup.md:57` document toggle availability

**Design Rationale:**
- Opt-out rather than opt-in preserves Git workflow safety for majority of users
- Simple boolean toggle avoids complex VCS abstraction layer
- Configuration-based approach enables per-repository customization
- Complete feature parity between Python and JavaScript implementations
- Hooks continue to respect all other DAIC enforcement patterns when branch_enforcement is disabled

**Use Cases:**
- Jujutsu (JJ) users who prefer working without traditional branches
- Mercurial repositories with different branch semantics
- Fossil or other distributed VCS systems
- Experimentation with alternative Git workflows
- Teams using trunk-based development without feature branches

**Related GitHub Issue:**
- Issue #43: "What is the most elegant way to stop the branch checking when working" - Closed with this implementation

### CI Environment Detection for GitHub Actions (v0.3.0+)

All hooks now automatically detect CI environments and bypass DAIC enforcement to enable automated Claude Code agents in GitHub Actions:

**Problem Solved:**
When running Claude Code agents in GitHub Actions (e.g., documentation maintenance bots, automated code review), DAIC mode enforcement would block the agent from making changes. The agent would get stuck in discussion mode and couldn't complete automated tasks.

**Implementation:**
- Added `is_ci_environment()` function to GLOBALS section of all 12 hooks (6 Python + 6 JavaScript)
- Detection checks for environment variables: `GITHUB_ACTIONS`, `GITHUB_WORKFLOW`, `CI`, `CONTINUOUS_INTEGRATION`
- Early exit with code 0 (bypass) when any CI indicator is detected
- Prevents all DAIC enforcement in CI contexts while preserving full functionality in local development

**Hook Coverage:**
All hooks include CI detection with early exit pattern:
- `sessions_enforce.py|.js` - Lines 115-126 (Python), bypasses DAIC mode enforcement at line 270-272
- `session_start.py|.js` - Lines 35-45, skips session initialization messages at line 366-368
- `user_messages.py|.js` - Lines 33-46, bypasses trigger phrase detection at line 44-46
- `post_tool_use.py|.js` - Lines 33-46, skips todo completion checks at line 44-46
- `subagent_hooks.py|.js` - Lines 21-34, bypasses subagent protection at line 32-34
- `kickstart_session_start.py|.js` - Lines 27-40, skips onboarding prompts at line 38-40

**Use Cases:**
- Documentation maintenance bots that automatically update CLAUDE.md files
- Automated code review agents that create pull requests
- CI/CD workflows that need to make commits without user interaction
- Any GitHub Actions workflow using Claude Code agents

**Security Considerations:**
- Environment variables are platform-controlled (GitHub Actions sets them automatically)
- No user configuration required - works automatically in CI environments
- Local development unaffected - all DAIC enforcement remains active
- Focused on GitHub Actions (Claude Code's only CI integration) with generic CI fallback

**Files Modified:**
- Python hooks: `cc_sessions/python/hooks/sessions_enforce.py`, `session_start.py`, `user_messages.py`, `post_tool_use.py`, `subagent_hooks.py`, `kickstart_session_start.py`
- JavaScript hooks: `cc_sessions/javascript/hooks/sessions_enforce.js`, `session_start.js`, `user_messages.js`, `post_tool_use.js`, `subagent_hooks.js`, `kickstart_session_start.js`

### Backup and Restore During Reinstall (v0.3.9+)

Both Python and JavaScript installers now automatically preserve user content during updates and reinstalls:

**Detection and Verification:**
- Installers detect existing `sessions/` directory and check for actual user content
- Content verification ensures only meaningful installations are backed up (not just empty directories)
- Recursive scanning of `sessions/tasks/` directory looks for any `.md` files to determine if backup is needed

**Backup Process:**
- Creates timestamped backup directory: `.claude/.backup-YYYYMMDD-HHMMSS/`
- Backs up all task files from `sessions/tasks/` (includes `done/`, `indexes/`, and all subdirectories)
- Backs up agent customizations from `.claude/agents/` directory
- Verifies backup integrity by comparing file counts before proceeding with installation
- Aborts installation if backup verification fails to prevent data loss

**Restoration Process:**
- After installation completes, automatically restores task files to `sessions/tasks/`
- Preserves all directory structure and subdirectories during restoration
- Graceful error handling with fallback to manual recovery if restoration fails
- Agent files preserved in backup for manual restoration if needed

**User Experience:**
- Clear color-coded messaging throughout backup/restore process
- Displays backup location with relative paths for easy access
- Provides file counts for verification (e.g., "Backed up 12 task files")
- Fresh install vs update detection with appropriate messaging

**What Gets Preserved:**
- All task files in `sessions/tasks/` (including `done/`, `indexes/`, subdirectories)
- Agent customizations in `.claude/agents/` (backed up for manual restoration)

**What Gets Updated:**
- All hook files (`sessions/hooks/`) - Always updated for bug fixes and new features
- All API files (`sessions/api/`) - Always updated for command improvements
- All protocol files (`sessions/protocols/`) - Always updated for protocol enhancements
- All knowledge files (`sessions/knowledge/`) - Always updated for documentation
- State and config files (`sessions-state.json`, `sessions-config.json`) - Regenerate fresh via kickstart

**Implementation Details:**
- Python: Lines 380-443 in `cc_sessions/install.py` (create_backup, restore_tasks functions)
- JavaScript: Lines 423-524 in `install.js` (createBackup, restoreTasks functions)
- Both implementations use identical logic with language-specific file operations
- Backup directories remain in `.claude/` directory for safety and manual recovery

### Installer Refactoring for Language Separation (v0.3.8+)

Complete separation of Python and JavaScript installation paths eliminates cross-language dependencies:

**Architecture Changes:**
- **Separate Installers**: `install.js` (root) for npm, `cc_sessions/install.py` (module) for pip
- **Language-Specific File Trees**: All runtime files organized under `cc_sessions/javascript/` or `cc_sessions/python/`
- **No Cross-Language Dependencies**: npm installation works without Python runtime, pip installation works without Node.js runtime
- **Shared Resources**: Agents and knowledge base included in both packages for identical functionality

**File Organization:**
- JavaScript variant: Uses only `cc_sessions/javascript/` (hooks, api, statusline, protocols, commands, templates)
- Python variant: Uses only `cc_sessions/python/` (hooks, api, statusline, protocols, commands, templates)
- Both variants: Include `cc_sessions/agents/` and `cc_sessions/knowledge/`

**Package Configuration Updates:**
- **package.json**: Files list now only includes `javascript/`, `agents/`, `knowledge/` (removed Python files)
- **pyproject.toml**: Package-data now only includes `python/**/*` (removed JavaScript files)
- **Dependency Cleanup**: Removed tiktoken dependency from both variants (dead code eliminated)

**State Initialization Enhancement:**
- Both installers now call `loadState()`/`load_state()` and `loadConfig()`/`load_config()` during installation
- State files (`sessions-state.json`, `sessions-config.json`) created early rather than lazy initialization on first hook run
- Ensures state infrastructure exists before first session starts

**Installation Commands:**
- npm/npx: `npx cc-sessions` or `npm install -g cc-sessions && cc-sessions` (Node.js only)
- pip/pipx: `cc-sessions` command after install (Python only)
- Both variants provide identical DAIC enforcement, task management, and protocol functionality

**Automatic Gitignore Configuration:**
- Both installers automatically add entries to project `.gitignore` file
- Entries added: `sessions/sessions-state.json` (runtime state) and `sessions/transcripts/` (agent transcripts)
- Idempotent behavior: Entries only added if not already present in existing `.gitignore`
- Creates new `.gitignore` file if one doesn't exist
- Follows same pattern as `configure_claude_md()` function

**Benefits:**
- Simplified installation process with no mixed-language complexity
- Smaller package sizes (each variant only ships its language-specific files)
- No Python availability checks in JavaScript installer
- No Node.js dependency handling in Python installer
- Cleaner separation of concerns for future maintenance

### Kickstart Onboarding Protocol System

Comprehensive first-run onboarding system providing interactive guided setup and configuration for new cc-sessions installations:

**Two Mode Variants:**
- **Full Mode** (15-30 min): Complete walkthrough with 11 protocol chunks covering DAIC enforcement, task workflows (creation, startup, completion), compaction, agents, API, and advanced features with interactive exercises and validation
- **Subagents Mode** (5 min): Single protocol chunk focused on agent customization for experienced users

**Core Architecture:**
- **Index-Based Progression**: Protocols loaded sequentially from `FULL_MODE_SEQUENCE` or `SUBAGENTS_MODE_SEQUENCE` arrays
- **State-Driven Flow**: Progress tracked in `STATE.metadata['kickstart']` with sequence, current_index, and completed array
- **Installer Integration**: Automatically triggered when `STATE.metadata['kickstart']` exists from installer choice
- **Interactive Learning**: Demonstrates concepts through practice with real commands and immediate feedback
- **Dummy Task Integration**: Uses `h-kickstart-setup.md` template as practice task throughout onboarding

**Session Start Integration:**
- Dedicated `kickstart_session_start.py|.js` hooks registered in settings.json for onboarding detection
- Automatically triggered when `STATE.metadata['kickstart']` exists during session initialization
- Initializes sequence on first run, resumes from current_index on subsequent runs
- Loads protocol content from `sessions/protocols/kickstart/{protocol-file}` based on mode sequence
- Displays user instructions: "Just say 'kickstart' and press enter to begin"

**Full Mode Protocol Sequence (11 protocols):**
1. Discussion mode (01-discussion.md) - DAIC introduction with interactive blocking demo
2. Implementation mode (02-implementation.md) - TodoWrite mechanics and mode switching
3. Tasks overview (03-tasks-overview.md) - Task management concepts and naming conventions
4. Task creation (04-task-creation.md) - Task creation protocol with hands-on practice
5. Task startup (05-task-startup.md) - Task startup protocol with dummy task
6. Task completion (06-task-completion.md) - Task completion protocol with git workflow
7. Context compaction (07-compaction.md) - Compaction protocol for mid-task context management
8. Agents (08-agents.md) - Five specialized agents overview and capabilities
9. Sessions API (09-api.md) - Sessions API commands and slash command integration
10. Advanced features (10-advanced.md) - Task indexes, iterloop pattern, stashed todos with concrete examples
11. Graduation (11-graduation.md) - Cleanup, summary, philosophy, next steps

**Subagents Mode Sequence (1 protocol):**
1. Agents-only (01-agents-only.md) - Fast-track agent customization without tutorial

**State Management:**
- Progress tracking in `STATE.metadata['kickstart']` with mode, sequence, current_index, completed array, last_active timestamp
- Sequence initialization on first run sets sequence array and current_index to 0
- Resume support preserves progress across session restarts
- Graduation cleanup: Removes entire `metadata['kickstart']` entry while preserving all configuration changes

**API Commands:**
- `sessions kickstart next` - Load next protocol chunk, auto-increments current_index, marks previous as completed
- `sessions kickstart complete` - Exit kickstart with hybrid cleanup: automated file deletion + manual router/config cleanup instructions

**Self-Cleanup System:**
- Hybrid approach: Automated deletion of kickstart protocols, hooks, and setup task files
- Language detection: Determines Python vs JavaScript installation by checking which kickstart_session_start hook file exists (py vs js)
- Manual cleanup instructions for router imports, COMMAND_HANDLERS entries, settings.json hooks, and API command files
- Preserves `.claude/agents/` directory and all user customizations during cleanup
- Switches to implementation mode automatically before file deletion to bypass DAIC enforcement
- Returns formatted todo list for manual cleanup steps that can't be automated

**Protocol Content Highlights:**
- **Concrete Examples**: Iterloop demonstrates user-provided lists vs Claude-identified lists (10-advanced.md:46-70)
- **Practical Scenarios**: Stashed todos example shows debugging workflow with task discovery (10-advanced.md:84-92)
- **Index Usage**: Real-world index examples for feature work, performance tasks, refactoring (10-advanced.md:15-24)
- **Interactive Demonstrations**: Discussion mode shows blocking behavior with actual tool attempts (01-discussion.md:56-78)

**Supporting Infrastructure:**
- Kickstart API module: `cc_sessions/scripts/api/kickstart_commands.py|.js` with next, complete commands
- Kickstart SessionStart hooks: `cc_sessions/hooks/kickstart_session_start.py|.js` with metadata detection and sequence initialization
- Module sequences: FULL_MODE_SEQUENCE (11 protocols), SUBAGENTS_MODE_SEQUENCE (1 protocol)
- Protocol loading: `load_protocol_file()` helper reads from `sessions/protocols/kickstart/` directory

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

### Todo Serialization Refactoring (2025-10-06)
Code organization improvements in todo serialization eliminate duplication and establish single source of truth:

**New SessionsTodos Method:**
- **to_dict() Implementation**: Added serialization method to SessionsTodos class in shared_state.py:504-509 and shared_state.js:547-554
- **Complete Structure Output**: Returns `{"active": [...], "stashed": [...]}` format with stashed only included if present
- **Leverages Existing Methods**: Uses existing to_list(which) method for individual bucket serialization

**API Command Refactoring:**
- **state_commands.py Cleanup**: Replaced duplicated serialization code at lines 99-108 and 353-357 with single to_dict() call
- **state_commands.js Cleanup**: Replaced duplicated serialization code at lines 125-138 and 461-474 with single toDict() call
- **Differential Command Scoping**: state todos command shows complete structure via to_dict(), todos command shows only active via to_list('active')
- **Identical Output Verification**: Tested both Python and JavaScript implementations produce byte-for-byte identical JSON output

**Code Quality Benefits:**
- Eliminates 30+ lines of duplicated serialization logic across 4 locations
- Provides single source of truth for todos structure format
- Simplifies future maintenance by centralizing serialization patterns
- Maintains complete feature parity between Python and JavaScript implementations

## Key Patterns

### Hook Architecture
- **Unified State Management**: SessionsState class manages all runtime state in single JSON file with atomic operations
- **Configuration-Driven Enforcement**: SessionsConfig system provides type-safe user customization of all behavioral patterns
- **Branch Enforcement Toggle**: CONFIG.features.branch_enforcement enables users to disable Git branch validation for alternative VCS systems (Jujutsu, Mercurial, etc.) while preserving all other DAIC enforcement patterns
- **CI Environment Detection**: All 12 hooks (6 Python + 6 JavaScript) automatically detect CI environments and bypass DAIC enforcement via `is_ci_environment()` function checking `GITHUB_ACTIONS`, `GITHUB_WORKFLOW`, `CI`, and `CONTINUOUS_INTEGRATION` environment variables, enabling Claude Code agents in GitHub Actions to complete automated tasks without discussion mode blocking
- **Protocol State Management**: SessionsProtocol enum and active_protocol field enable protocol-driven automation
- **Protocol Command Authorization**: APIPerms dataclass provides protocol-specific command permission validation
- **Enhanced Pre-tool-use Validation**: sessions_enforce.py uses comprehensive command categorization with intelligent argument analysis for accurate write operation detection
- **Post-tool-use Automation**: Automatic todo completion detection and mode transitions based on user preferences
- **Configurable Trigger Detection**: user_messages.py supports user-defined trigger phrases for all workflow transitions
- **Protocol Auto-Loading**: `load_protocol_file()` helper eliminates manual "read this file" instructions
- **Centralized Protocol Todo System**: `format_todos_for_protocol()` provides consistent todo formatting across all protocols
- **Centralized Todo Serialization**: SessionsTodos.to_dict() method eliminates duplicated serialization code across API commands, providing single source of truth for todos structure
- **Template-Based Protocol System**: Protocols auto-adapt based on configuration without conditional instructions
- **Automatic Task Status Updates**: Task lifecycle management through state system (status, started dates)
- **Commit Style Templating**: Dynamic commit message templates based on user preferences and branch patterns
- **Conditional Todo Generation**: Protocol todos adapt automatically to user configuration (merge, push, submodules)
- **Session Initialization**: session_start.py integrates configuration with task context loading
- **Subagent Protection**: Automatic subagent context detection and flag management with cleanup
- **Atomic File Operations**: File locking and atomic writes prevent state corruption across all operations with optimized 1-second timeout and aggressive lock cleanup
- **Cross-platform Compatibility**: pathlib.Path throughout with Windows-specific handling
- **UTF-8 Encoding Enforcement**: All file I/O operations explicitly specify UTF-8 encoding (Python: `encoding='utf-8', errors='backslashreplace'`, JavaScript: `'utf-8'`) to prevent platform-specific encoding issues on Windows (cp1252) and ensure consistent behavior across all platforms
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
- **UTF-8 Encoding Fix**: All file I/O operations explicitly specify UTF-8 encoding to prevent Windows cp1252 encoding issues (Python uses `encoding='utf-8', errors='backslashreplace'`, JavaScript uses `'utf-8'`)
- **Automatic OS Detection**: Both Python and JavaScript installers detect operating system using platform.system()/os.platform() and configure sessions-config.json appropriately

## Package Structure

### Installation Variants
- **Python package** with pip/pipx/uv support (Python-only dependencies)
- **NPM package** for JavaScript environments (JavaScript-only dependencies)
- **Direct bash script** for build-from-source installations
- **Symlinked Development Setup**: Use cc-sessions package locally without installation via symlinks
- **Cross-platform compatibility** (macOS, Linux, Windows 10/11)
- **Complete feature parity** between Python and JavaScript implementations

### Installer Architecture (v0.3.8+)

The cc-sessions package provides separate language-specific installers with no cross-language dependencies:

**Language-Specific Installers:**
- **JavaScript Installer**: `install.js` at package root - only uses `cc_sessions/javascript/` files
- **Python Installer**: `cc_sessions/install.py` as module entry point - only uses `cc_sessions/python/` files
- **No Cross-Language Dependencies**: Each installer operates entirely within its language ecosystem
- **Gitignore Configuration**: Both installers include `configure_gitignore()` / `configureGitignore()` functions that automatically add runtime file entries to project `.gitignore`

**File Structure Organization:**
- `cc_sessions/javascript/` - JavaScript-specific files (hooks, api, statusline, protocols, commands, templates)
- `cc_sessions/python/` - Python-specific files (hooks, api, statusline, protocols, commands, templates)
- `cc_sessions/agents/` - Shared agent definitions (included in both packages)
- `cc_sessions/knowledge/` - Shared knowledge base (included in both packages)

**Package Configuration:**
- **package.json**: Only includes `javascript/`, `agents/`, `knowledge/` (no Python files)
- **pyproject.toml**: Only includes `python/**/*` via package-data (no JavaScript files)
- **State Initialization**: Both installers call `loadState()`/`load_state()` and `loadConfig()`/`load_config()` during installation to create `sessions-state.json` and `sessions-config.json` early

**Installation Commands:**
- JavaScript: `npx cc-sessions` or `npm install -g cc-sessions && cc-sessions`
- Python: `cc-sessions` command (after pip/pipx install)
- Both: Require only their respective runtime (Node.js OR Python, not both)

**Backup and Restore System:**
- **Existing Installation Detection**: Installers check for `sessions/` directory with actual user content (not just empty directories)
- **Automatic Backup**: Creates timestamped backup directory `.claude/.backup-YYYYMMDD-HHMMSS/` before updating installation
- **Content Verification**: Validates backup integrity by comparing file counts before proceeding with installation
- **Selective Preservation**: Backs up `sessions/tasks/` (all subdirectories) and user-customized agents from `.claude/agents/`
- **Automatic Restoration**: Restores task files after installation completes, with graceful error handling and fallback to manual recovery
- **Clear User Messaging**: Displays backup location and restoration status with color-coded feedback
- **State File Regeneration**: State and config files (`sessions-state.json`, `sessions-config.json`) intentionally regenerate fresh via kickstart onboarding

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

- **RELEASE.md** - Complete release workflow guide for maintainers (version bumping, validation, publishing to PyPI/npm, GitHub releases)
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
All slash commands use: `!sessions <command> $ARGUMENTS --from-slash`

**Enhanced Features:**
- **Contextual Output**: `--from-slash` flag enables user-friendly responses optimized for slash command usage
- **Adaptive Error Messages**: Commands show valid options and contextual help when operations fail
- **Two-Level Help System**: Brief help at top level (`/sesh-config help`), verbose help for specific operations (`/sesh-config trigger help`)
- **Name Mapping**: Friendly aliases (go→implementation_mode, auto→true, etc.) for user convenience

### Programmatic API

**State Operations:**
- `sessions state [--json]` - Full state inspection including active protocol
- `sessions state <component> [--json]` - Specific component (mode/task/todos/flags/active_protocol/api)
- `sessions state active_protocol [--json]` - View currently active protocol
- `sessions state api [--json]` - View protocol-specific API permissions
- `sessions state update suppress` - Suppress update notifications
- `sessions state update check` - Force re-check for updates
- `sessions state update status` - Show current update status and version information
- `sessions mode discussion` - One-way switch to discussion mode
- `sessions flags clear` - Reset behavioral flags
- `sessions status` - Human-readable state summary
- `sessions version` - Package version information

**Protocol Operations:**
- `sessions protocol startup-load <task-file>` - Load task and return full file content during startup protocol
- Permission-based access controlled by active_protocol and api.startup_load states

**Kickstart Operations:**
- `sessions kickstart next` - Load next protocol chunk in sequence, increment current_index
- `sessions kickstart complete` - Exit kickstart, clear metadata, delete files

**Configuration Operations:**
- `sessions config [--json] [--from-slash]` - Full configuration inspection with optional contextual formatting
- `sessions config phrases list [category] [--from-slash]` - View trigger phrases
- `sessions config phrases add <category> "<phrase>" [--from-slash]` - Add trigger phrase
- `sessions config phrases remove <category> "<phrase>" [--from-slash]` - Remove trigger phrase
- `sessions config features toggle <key> [--from-slash]` - Toggle feature boolean values (supports branch_enforcement, task_detection, auto_ultrathink, use_nerd_fonts, auto_update, warn_85, warn_90)
- `sessions config git show [--from-slash]` - View git preferences
- `sessions config git set <setting> <value> [--from-slash]` - Update git preference
- `sessions config env show [--from-slash]` - View environment settings
- `sessions config env set <setting> <value> [--from-slash]` - Update environment setting
- `sessions config read list [--from-slash]` - List bash read patterns
- `sessions config read add <pattern> [--from-slash]` - Add bash read pattern
- `sessions config read remove <pattern> [--from-slash]` - Remove bash read pattern
- `sessions config write list [--from-slash]` - List bash write patterns
- `sessions config write add <pattern> [--from-slash]` - Add bash write pattern
- `sessions config write remove <pattern> [--from-slash]` - Remove bash write pattern
- `sessions config tools list [--from-slash]` - List implementation-only tools
- `sessions config tools block <ToolName> [--from-slash]` - Block tool in discussion mode
- `sessions config tools unblock <ToolName> [--from-slash]` - Unblock tool

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

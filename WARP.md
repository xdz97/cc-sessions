# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

- Install cc-sessions into a target repo (recommended paths from README):
  - Python: pipx run cc-sessions
  - Node: npx cc-sessions
- Run Sessions API locally (after installing into a repo) without slash commands:
  - Python: python -m cc_sessions.python.api state
  - Python (JSON): python -m cc_sessions.python.api state --json
  - JS: node cc_sessions/javascript/api/index.js state
- Try core subsystems via API (examples):
  - State: sessions state | python -m cc_sessions.python.api state
  - Config: sessions config show | python -m cc_sessions.python.api config show
  - Tasks: sessions tasks idx list | python -m cc_sessions.python.api tasks idx list
  - Mode: sessions mode discussion | python -m cc_sessions.python.api mode no

Notes
- This repo ships both Python (PyPI) and Node (npm) packages with feature parity; there is no test or lint setup in package.json/pyproject.toml.
- For local installer testing from this repo, invoke the installers from a target project directory:
  - Python: python /absolute/path/to/this/repo/cc_sessions/install.py
  - Node: node /absolute/path/to/this/repo/cc_sessions/install.js

## High-level architecture

- Dual-language package with mirrored functionality
  - Python under cc_sessions/python/**
  - JavaScript under cc_sessions/javascript/**
- Installers
  - cc_sessions/install.py and cc_sessions/install.js copy hooks, API, protocols, agents, commands, and templates into the target repo; perform backups and initialize config/state.
- Hooks (DAIC enforcement and lifecycle)
  - cc_sessions/{python|javascript}/hooks/
    - sessions_enforce.*: pre-tool enforcement and write blocking in discussion mode
    - session_start.* and kickstart_session_start.*: session initialization and onboarding
    - post_tool_use.*: transitions after tool use; todo completion checks
    - user_messages.*: trigger phrase detection and protocol loading
    - subagent_hooks.*: isolate specialized agent behavior
    - shared_state.*: config/state models, enums, file locking, helpers
- Sessions API (router + subsystems)
  - Router: cc_sessions/{python|javascript}/api/router.*
  - Entry points: python -m cc_sessions.python.api and node cc_sessions/javascript/api/index.js
  - Handlers: state_commands.*, config_commands.*, task_commands.*, protocol_commands.*, uninstall_commands.*
- Protocols (natural language workflow templates)
  - cc_sessions/protocols/{task-creation,task-startup,task-completion,context-compaction}/
  - cc_sessions/protocols/kickstart/: 11-step interactive onboarding
- Specialized agents (run in separate contexts)
  - cc_sessions/agents/: context-gathering, logging, code-review, context-refinement, service-documentation
- Knowledge and templates
  - cc_sessions/knowledge/claude-code/: internal docs (hooks reference, subagents, tool permissions)
  - cc_sessions/templates/: task and documentation templates
- Distribution metadata
  - pyproject.toml exposes cc-sessions (Python) console script
  - package.json exposes cc-sessions (Node) bin and publishes mirrored resources

## Key rules from CLAUDE.md (important behavior)

- DAIC methodology is enforced by default: write/edit tools are blocked until the user explicitly approves a plan via trigger phrases.
- Trigger phrases (configurable via Sessions Config) control mode transitions and workflows:
  - implementation (e.g., "yert"), discussion (e.g., "SILENCE"), creation (e.g., "mek:"), startup (e.g., "start^"), completion (e.g., "finito"), compaction (e.g., "squish").
- Unified Sessions command and API
  - /sessions ... in Claude Code; sessions ... in shell; python -m cc_sessions.python.api ... for direct API
  - Core subsystems: state, config, tasks, protocol, uninstall (kickstart if present)
- Known compatibility note (from CLAUDE.md): Claude Code v2.0.9+ has an upstream stderr aggregation bug affecting parallel tool execution; use v2.0.8 until fixed if you encounter 400 API errors during parallel operations.

# Quick Setup for Experienced Users

## Import from Existing Repo?

Have another repo with cc-sessions already configured?

You can copy:
- Configuration (trigger phrases, git preferences, features)
- Agent customizations

**Path to existing repo** (local path or github URL):

[Wait for response]

---

**If they provide a path:**

1. Copy `sessions/sessions-config.json` from source to `sessions/sessions-config.json` here
2. Copy `.claude/agents/*` from source to `.claude/agents/*` here

**If they skip:**

Continue to manual config.

---

## Current Configuration

Run: `node sessions/scripts/api/index.js config`

[Show full config]

**What do you want to change?**

[Wait for response]

---

**Available config commands:**

```bash
# Trigger Phrases
node sessions/scripts/api/index.js config triggers add <category> "<phrase>"
node sessions/scripts/api/index.js config triggers remove <category> "<phrase>"
# Categories: go, no, create, start, complete, compact

# Git Preferences
node sessions/scripts/api/index.js config git set <setting> <value>
# Settings: default_branch, commit_style, auto_merge, auto_push, has_submodules

# Environment Settings
node sessions/scripts/api/index.js config env set <setting> <value>
# Settings: os, shell, developer_name

# Feature Toggles
node sessions/scripts/api/index.js config features toggle <key>
# Keys: branch_enforcement, task_detection, auto_ultrathink, context_warnings, extrasafe

# Tool Blocking
node sessions/scripts/api/index.js config tools block <ToolName>
node sessions/scripts/api/index.js config tools unblock <ToolName>

# Bash Patterns
node sessions/scripts/api/index.js config read add "<pattern>"
node sessions/scripts/api/index.js config read remove "<pattern>"
node sessions/scripts/api/index.js config write add "<pattern>"
node sessions/scripts/api/index.js config write remove "<pattern>"
```

Work through their requested changes.

---

## Agent Customization

**Want to customize agents?**

Available agents:
- context-gathering (most commonly customized - benefits from knowing your patterns)
- code-review (most commonly customized - benefits from knowing your threat model and performance standards)
- logging
- context-refinement
- service-documentation

Which ones?

[Wait for response]

**For each agent they choose:**

Brief tech stack discussion, update `.claude/agents/[agent-name].md`

---

## Complete

Run: `node sessions/scripts/api/index.js kickstart complete`

You're ready. Run `/clear` and start working.

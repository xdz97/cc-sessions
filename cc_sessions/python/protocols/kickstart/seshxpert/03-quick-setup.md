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

Run: `sessions config`

[Show full config]

**What do you want to change?**

[Wait for response]

---

**Available config commands:**

```bash
# Trigger Phrases
sessions config triggers add <category> "<phrase>"
sessions config triggers remove <category> "<phrase>"
# Categories: go, no, create, start, complete, compact

# Git Preferences
sessions config git set <setting> <value>
# Settings: default_branch, commit_style, auto_merge, auto_push, has_submodules

# Environment Settings
sessions config env set <setting> <value>
# Settings: os, shell, developer_name

# Feature Toggles
sessions config features toggle <key>
# Keys: branch_enforcement, task_detection, auto_ultrathink, context_warnings, extrasafe

# Tool Blocking
sessions config tools block <ToolName>
sessions config tools unblock <ToolName>

# Bash Patterns
sessions config read add "<pattern>"
sessions config read remove "<pattern>"
sessions config write add "<pattern>"
sessions config write remove "<pattern>"
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

Run: `sessions kickstart complete`

You're ready. Run `/clear` and start working.

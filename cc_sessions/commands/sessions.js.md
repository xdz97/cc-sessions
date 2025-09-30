---
allowed-tools: Bash(node:*)
argument-hint: "Use '/sessions help' for all commands"
description: "Unified sessions management (tasks, state, config) - JavaScript version"
disable-model-invocation: true
---
!`node ${CLAUDE_PROJECT_DIR}/sessions/scripts/api/index.js $ARGUMENTS --from-slash`

Present the output to the user.
---
allowed-tools: Bash(python:*)
argument-hint: "Use '/sessions help' for all commands"
description: "Unified sessions management (tasks, state, config)"
disable-model-invocation: true
---
!`python -m sessions.api slash $ARGUMENTS --from-slash`

Present the output to the user.

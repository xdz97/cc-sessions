---
allowed-tools: [Bash]
argument-hint: "(implementation_mode|discussion_mode|task_creation|task_startup|task_completion|context_compaction) <phrase>"
description: Remove a trigger phrase from specified category
---

Remove the trigger phrase:
!`python -m cc_sessions.scripts.api config phrases remove "$1" "$2"`

Tell the user the result in a single line.
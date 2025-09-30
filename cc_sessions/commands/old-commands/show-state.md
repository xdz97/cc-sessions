---
description: Show current session state or specific component
allowed-tools: [Bash]
argument-hint: "[todos|task|flags]"
---
!`if [ -z "$ARGUMENTS" ]; then python -m sessions.api state; else python -m sessions.api state $ARGUMENTS; fi`

Present the output concisely without additional commentary.

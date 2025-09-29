---
allowed-tools: [Bash]
argument-hint: "clear"
description: "(clear) -> [todos|task|flags] | (set) -> [mode -> [api|bypass|implementation]"
disable-model-invocation: true
---
!`python -m sessions.api todos $ARGUMENTS --from-slash`

Tell the user the result in a single line.

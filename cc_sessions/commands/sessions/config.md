---
allowed-tools: [Bash]
argument-hint: "Use '/config help' for settings, use '/config show' to inspect"
description: "Modify or inspect the sessions config"
disable-model-invocation: true
---

TODO: Create this slash command such that it will instruct you to return the output based on the input according to the following schema (dont copy description text verbatim, I'm not being exhaustive im just showing you how it should work):

$1 argument:
- "help": Give the user an exact concise help snippet showing clearly how to use all of the other commands under this slash command - also available after every $1 argument to explain all of the subcommands for that command
- "show": Give the user a neat easy to read list of their current configuration settings and what it means for their experience per setting
- "trigger" (trigger phrases):
  $2 argument "add|remove|list":
    $3 argument
    - "go": implementation_mode trigger phrases
    - "no": discussion_mode trigger phrases
    - "create": task_creation trigger phrases
    - "start": task_startup trigger phrases
    - "complete": task_completion trigger phrases
    - "compact": context_compaction trigger phrases
    if add or remove, $4+ argument will be the phrase they want to add/remove (accounting for spaces in the bash argument syntax) 
- "git" (git preferences):
  $2 argument:
  - "add <ask|all>" (whether to add all during git staging or ask what to stage)
  - "branch <default branch name>" (change the default branch that Claude merges task branches into on completion)
  - "commit <reg|simp|op>" (change the default commit style that Claude uses - reg = conventional, simp = simple, op = detailed)
  - "merge <auto|ask>" (automatically merge task branches into default branch on task completion or ask first)
  - "push <auto|ask>"
  - "repo <super|mono>" (determine has_submodules flag to condition protocol instructions accordingly)
- "env"
  $2 argument
  - "os <linux|mac|windows>"
  - "shell <bash|zsh|fish|pwr|cmd>"
  - "name <what you want Claude to call you"
- "perms" (things the user wants blocked/allowed)
  $2 argument
  - "bash"
    $3+ arguments
    - "read <add|remove|list> <cli command for add/remove>" (add, remove, or list bash command patterns that are allowed in discussion mode)
    - "write <add|remove|list> <cli command for add/remove>" (add, remove, or list bash command patterns that are blocked in discussion mode"
    - "safe <extra|off>" (extrasafe mode means that all cli commands that arent in our read or write list are blocked automatically,  means that if we didnt explicitly exclude/include it its not blocked)
  - "tools"
    $3 argument
    - "list" (output a list of all tools currently blocked in discussion mode and all tools claude code can use that arent blocked in discussion mode)
    - "block <valid tool name>" (add any valid claude code tool name to the list of implementation_only_tools)
    - "allow <valid tool name>" (remove any valid tool name from the list of blocked tools)
- "features"

...I feel like you can figure out how to do this last one based on the config schema we have and the patterns I laid down here.

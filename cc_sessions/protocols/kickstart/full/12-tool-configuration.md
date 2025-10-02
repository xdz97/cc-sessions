# Tool Configuration

Let's talk about how cc-sessions controls what I can do in discussion mode versus implementation mode.

## DAIC Tool Blocking

By default, cc-sessions blocks Edit, Write, MultiEdit, NotebookEdit, and TodoWrite in discussion mode. But you might want to block other tools too:

- **Task** - Prevents me from launching agents without approval
- **SlashCommand** - Blocks slash command execution
- Any other Claude Code tool you want restricted: Read, Glob, Grep, Bash, WebFetch, WebSearch, BashOutput, KillShell, ExitPlanMode

**Do you want to block any additional tools in discussion mode?**

[Wait for user's response]

---

**If they want to block additional tools:**

For each tool they mention, add it using:

```bash
/sessions config tools block <ToolName>
```

Example: `/sessions config tools block Task`

If the user wants to add Bash, strongly advise against it. If they insist, skip the next section and call `python -m sessions.kickstart next`

---

## Bash Read/Write for DAIC

cc-sessions is smart about Bash. It knows the difference between:
- **Read commands**: ls, cat, grep, git status, docker ps, etc.
- **Write commands**: rm, sed -i, git commit, docker run, etc.

In discussion mode, I can run read commands but not write commands. This lets me inspect your system without changing anything.

## Custom Read Patterns

Sometimes you have tools that cc-sessions doesn't recognize as safe. Like:
- `docker` - You might want me to run `docker ps` or `docker logs` to see what's running
- `kubectl` - Inspect Kubernetes resources without changing them
- Custom scripts or tooling specific to your workflow

You can add these to your bash_read_patterns so they're allowed in discussion mode.

## Do You Need Custom Read Patterns?

Think about tools you use regularly to inspect your system:
- Container tools (docker, podman)
- Orchestration tools (kubectl, helm)
- Cloud CLIs (aws, gcloud, azure)
- Database inspection tools
- Custom monitoring or status scripts

**What tools do you regularly use to check status or inspect things?**

[Wait for user's response]

---

**If they have tools to add:**

For each tool they mention, think about which specific subcommands are truly read-only with no destructive variants.

For example, if they say "docker":
- Truly read-only: `docker ps`, `docker inspect`, `docker logs`, `docker version`
- Has destructive variants: `docker images` (has `docker image prune`, `docker image rm`)
- Clearly write-like: `docker run`, `docker rm`, `docker stop`, `docker build`

Be conservative - only add commands that can't possibly modify state:

```bash
/sessions config read add "docker ps"
/sessions config read add "docker inspect"
/sessions config read add "docker logs"
/sessions config read add "docker version"
```

Ask: "Should I also add the write-like docker commands to the blocked list to be extra safe?"

If yes, add them to the write patterns:
```bash
/sessions config write add "docker run"
/sessions config write add "docker rm"
/sessions config write add "docker stop"
/sessions config write add "docker image"
```

Do this for each tool they mentioned - be conservative and only add truly safe read-only commands.

[Wait for them to finish adding tools]

---

**After they add tools (or if they have none to add):**

## Extrasafe Mode

One more thing about bash command handling.

When I try to run a bash command in discussion mode, cc-sessions checks:
1. Is it in your bash_read_patterns? → Allow it
2. Is it in your bash_write_patterns? → Block it
3. Is it a known safe command (ls, cat, git status, etc.)? → Allow it
4. Is it a known write command (rm, git commit, etc.)? → Block it

But what about commands that don't match any of these lists?

**Extrasafe mode** (recommended, enabled by default):
- Unrecognized commands are treated as **write-like** and blocked
- Safer default - I can't run random commands without you explicitly allowing them

**Extrasafe disabled**:
- Unrecognized commands are treated as **read-only** and allowed
- More permissive - assumes commands are safe unless proven otherwise

Most users keep extrasafe enabled. It's the safer choice and the recommended default.

Do you want to keep extrasafe on or disable it?

[Wait for user's response]

---

**If they want to change it:**

To toggle extrasafe:
```bash
/sessions config features toggle extrasafe
```

Then, run: `python -m sessions.kickstart next`

This will move to the next module.

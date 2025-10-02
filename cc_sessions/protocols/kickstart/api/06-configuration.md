# Configuration

cc-sessions is highly customizable. Let's set up key preferences.

## Git Workflow Preferences

Configure how cc-sessions handles git operations.

### Auto-merge

After completing a task, auto-merge to main branch?

Options: `true` (auto-merge) or `false` (ask first)

Run: `/sessions config git set auto_merge <true|false>`

### Auto-push

After merging to main, auto-push to remote?

Options: `true` (auto-push) or `false` (ask first)

Run: `/sessions config git set auto_push <true|false>`

### Commit Style

How should commit messages be formatted?

Options:
- `conventional` - type(scope): description format
- `simple` - brief description only
- `detailed` - comprehensive multi-line commits

Run: `/sessions config git set commit_style <style>`

## Feature Toggles

Enable/disable system features.

### Branch Enforcement

Prevent code edits if current branch doesn't match task?

Default: `true` (recommended)

Toggle: `/sessions config features toggle branch_enforcement`

### Extrasafe Mode

Block unrecognized bash commands in discussion mode?

Default: `true` (recommended - safer)

Toggle: `/sessions config features toggle extrasafe`

## Tool Blocking

By default, Edit/Write/MultiEdit/NotebookEdit/TodoWrite are blocked in discussion mode.

Want to block additional tools? (Task, SlashCommand, Bash, etc.)

[Wait for response]

If yes, for each tool:

Run: `/sessions config tools block <ToolName>`

Example: `/sessions config tools block Task`

## Bash Command Patterns

cc-sessions distinguishes between:
- **Read commands**: ls, cat, grep, git status, docker ps (allowed in discussion mode)
- **Write commands**: rm, sed -i, git commit, docker run (blocked in discussion mode)

### Custom Read Patterns

Have tools you use to inspect your system? (docker, kubectl, cloud CLIs, custom scripts)

What tools do you regularly use to check status or inspect things?

[Wait for response]

---

**For each tool they mention:**

Analyze which subcommands are truly safe:

Example for docker:
- Truly safe: `docker ps`, `docker inspect`, `docker logs`, `docker version`
- Has destructive variants: `docker images` (→ `docker image prune`, `docker image rm`)
- Clearly write-like: `docker run`, `docker rm`, `docker stop`

Show them your analysis, then add only the safe ones:

Run: `/sessions config read add "docker ps"`
Run: `/sessions config read add "docker inspect"`
Run: `/sessions config read add "docker logs"`
Run: `/sessions config read add "docker version"`

Ask: "Should I also add the write-like docker commands to the blocked list for extra safety?"

If yes:
Run: `/sessions config write add "docker run"`
Run: `/sessions config write add "docker rm"`
Run: `/sessions config write add "docker stop"`
Run: `/sessions config write add "docker image"`

Be conservative - only add commands with no possible destructive variants.

---

## View Current Config

See all your settings:

Run: `/sessions config`

---

Run: `python -m sessions.kickstart next`

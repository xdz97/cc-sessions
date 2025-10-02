# Sessions State and Todo Tracking

Quick note about how cc-sessions keeps you in control during implementation.

## Why Todo Tracking Exists

When you approve implementation, I create a todo list of exactly what I'll do. That list is loaded into **sessions state** - a file that tracks the current task, mode, and what work is approved.

**The point**: I can only work within approved todos. If I try to add new work or change the plan mid-implementation, the system blocks me. This prevents me from going rogue while in implementation mode.

## You Just Created an Orphaned Todo

Remember when you used your stop phrase to switch back to discussion mode? That happened *before* I checked off my last todo.

The system marked all my todos as complete and returned me to discussion mode... but there's still one orphaned todo sitting in state from our trigger phrase exercise.

## Cleaning Up Orphaned Todos

Normally I can (and will) clear up orphaned todos, but you can also do it. Try this:

```
/sessions state todos clear
```

[Wait for user to run the command]

---

**After they run the command:**

Confirm the orphaned todo has been cleared.

## The Sessions API is Discoverable

We'll get more into the slash command API in the advanced section. For now, we're just focusing on the main stuff.

But if you ever want to explore: `/sessions` or `/sessions help` shows you top-level command categories. Then using any command category without valid commands returns help for that category. It's highly discoverable that way.

---

## Statusline Setup

Do you already have a statusline setup that you like, or would you like to use the cc-sessions statusline?

The cc-sessions statusline shows:
- Context window progress bar
- Current task
- Current mode (discussion/implementation)
- Uncommitted files in the current branch
- Open tasks

[Wait for user's response]

---

**Instructions based on user's response:**

### If they want the cc-sessions statusline:

Detect their installation type (check if they have node or python version):
- Check for `$CLAUDE_PROJECT_DIR/sessions/scripts/statusline.js` → use Node version
- Check for `$CLAUDE_PROJECT_DIR/sessions/scripts/statusline.py` → use Python version

Update their `.claude/settings.json`:

For Node version:
```json
"statusline": {
  "type": "command",
  "command": "node $CLAUDE_PROJECT_DIR/sessions/scripts/statusline.js",
  "padding": 0
}
```

For Python version:
```json
"statusline": {
  "type": "command",
  "command": "python $CLAUDE_PROJECT_DIR/sessions/scripts/statusline.py",
  "padding": 0
}
```

Tell them the statusline has been configured.

### If they already have their own statusline:

Ask: "Would you like to run the Claude Code statusline-setup agent to add Mode: [mode] and Task: [task] from sessions/sessions-state.json to your existing statusline?"

If yes:
- Use the statusline-setup agent
- Provide instructions: "Add session mode and current task info from sessions/sessions-state.json to the existing statusline. Read the current statusline configuration, enhance it to display the mode (discussion/implementation) and active task name, preserving all existing statusline elements."

If no:
- Acknowledge and continue

---

Run: `python -m sessions.kickstart next`

This will load the next module.

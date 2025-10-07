SAY TO THE USER>>>
Now lets recap:

- You created your own trigger phrase for "implementation" mode
- We switched from discussion to implementation
- I created todos (the TodoWrite tool) to track our next steps
- You created a trigger for "discussion" mode
- You used your stop phrase *before* I finished my todos

## You Just Created an Orphaned Todo

We use these todos to ensure I don't go off the rails. I'm trained to use todos on every turn. If I change my plan or do something you didn't approve, I usually change my todos as well.

I can't learn my around this, it's how I'm trained. So, it's a good way to prevent me from drifting from your approved plan.

## Cleaning Up Orphaned Todos

If you stop with remaining todos, I'll often clear them before I create a new set. Normally I can (and will) clear up orphaned todos, but you can also do it. Try this:

```
/sessions state todos clear
```
<<<

**After they run the command:**

>>>Thanks for that! 

You just used the cc-sessions API. 

But, you don't need me to tell you how to use it...

## The Sessions API is Discoverable

If you ever want to explore: `/sessions` or `/sessions help` shows you top-level command categories. 

Then using any command category without valid commands returns help for that category. It's highly discoverable that way.

Go ahead and check it out. When you're ready to continue, just say "next"!
<<<

After they signal continue:

>>> Okay, next...

Do you already have a statusline setup that you like, or would you like to use the cc-sessions statusline?

The cc-sessions statusline shows:
- Context window progress bar
- Current task
- Current mode (discussion/implementation)
- Uncommitted files in the current branch
- Open tasks
<<<

**Instructions based on user's response:**

### If they want the cc-sessions statusline:

`sessions state flags

Update their `.claude/settings.json`:

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

Run: `sessions kickstart next`

This will load the next module.

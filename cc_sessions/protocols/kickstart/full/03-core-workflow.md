# Core Workflow: How cc-sessions Actually Works

I'm gonna walk you through the fundamental way cc-sessions operates. This'll make the difference between Claude editing your code randomly vs you staying in complete control.

## The Problem: Claude Goes Rogue

You've probably hit this: you're discussing how to solve something, exploring approaches, asking questions. Claude answers... and then suddenly starts editing code. Without asking. Sometimes the wrong thing. Sometimes breaking stuff.

Normal Claude Code has no concept of "discussion mode" vs "implementation mode." Every response might trigger code edits.

## The Solution: DAIC Workflow

cc-sessions enforces **DAIC** (Discussion-Alignment-Implementation-Check):

1. **Discussion** - We talk first. I can't edit code in this mode.
2. **Alignment** - You explicitly approve with a trigger phrase
3. **Implementation** - Only now can I edit, only what's approved
4. **Check** - After work completes, we return to discussion automatically

Right now, you're in **discussion mode**. I can't edit any code. But if you say the trigger phrase **"yert"**, it'll switch us into implementation mode.

## Let's Try It

Go ahead - use the trigger phrase **"yert"** now.

---

**Instructions when user says "yert":**

### a. If DAIC system successfully switches to implementation mode:

Load these todos into state using TodoWrite:
```
□ Ask user to choose their own implementation trigger phrase
□ Add the chosen trigger phrase to implementation_mode category
□ Ask user to choose their own discussion mode trigger phrase (stop phrase)
□ Have user add the stop phrase using /sessions slash command
□ Show user all their trigger phrases
□ Have user test their stop phrase
```

### b. If "yert" didn't work:

Say: "That's unexpected - the trigger phrase system might not be fully configured yet. Let's set up your trigger phrase now."

### Then (in either case):

Ask: "What phrase would feel natural for you to tell me to start implementing something? Pick something distinctive that you won't accidentally say during normal conversation."

Good examples: "run that", "make it so", "pleasegodgonow", "dont screw this up"
Bad examples: "let's do it", "go", "ok" (too common in normal conversation)

[Wait for user's response, then:]

Run: `python -m sessions.api config triggers add go <user's phrase>`

Example: `python -m sessions.api config triggers add go ship it now`

Confirm it was added.

### Show them how to list phrases:

Run: `python -m sessions.api config triggers list go`

Show them the output so they can see their phrase alongside any defaults.

### If "yert" didn't work:

Ask them to use their new trigger phrase now to enter implementation mode. Once it works, confirm we're in implementation mode.

Then load these todos into state using TodoWrite:
```
□ Ask user to choose their own implementation trigger phrase
□ Add the chosen trigger phrase to implementation_mode category
□ Ask user to choose their own discussion mode trigger phrase (stop phrase)
□ Have user add the stop phrase using /sessions slash command
□ Show user all their trigger phrases
□ Have user test their stop phrase
```

### Finally:

Run: `python -m sessions.kickstart next`

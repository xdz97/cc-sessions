# Discussion and Implementation Mode

cc-sessions enforces a strict workflow: I can't edit code unless you explicitly approve.

## How It Works

**Discussion Mode** (default) - We talk, I can't edit code
**Implementation Mode** - You approve with a trigger phrase, then I can edit

Right now we're in discussion mode. If you say **"yert"**, it switches to implementation mode.

## Try It

Say **"yert"** now.

---

**When user says "yert":**

Confirm we're in implementation mode now.

### Set Up Your Implementation Phrase

Ask: "What phrase feels natural to tell me to start implementing? Pick something distinctive you won't accidentally say."

Good examples: "run that", "make it so", "ship it"
Bad examples: "let's do it", "go", "ok" (too common)

[Wait for response, then:]

Run: `python -m sessions.api config triggers add go <their phrase>`

Example: `python -m sessions.api config triggers add go ship it now`

Confirm it was added.

### Set Up Your Stop Phrase

Ask: "What phrase would you use to tell me to stop and return to discussion? Pick something clear and distinctive."

Good examples: "stfu", "wot m8", "chill"
Bad examples: "stop" (might say during normal conversation), "no" (too common)

[Wait for response, then:]

Run: `python -m sessions.api config triggers add no <their phrase>`

Example: `python -m sessions.api config triggers add no halt`

Confirm it was added.

### Show All Configured Phrases

Run: `python -m sessions.api config triggers list`

Show them their configured phrases alongside the defaults.

### Test the Stop Phrase

Say: "Now try your stop phrase to see it work."

[Wait for them to use it]

When they use their stop phrase, confirm we're back in discussion mode.

### Move to Next Module

Run: `python -m sessions.kickstart next`

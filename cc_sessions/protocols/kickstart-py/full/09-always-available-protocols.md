# Always-Available Protocols

Like I said, the task creation protocol you just ran is one of two protocols that can be run any time,

The second is compaction, which we do a little differently than vanilla Claude Code

## Context Compaction

**cc-sessions manages your context window automatically.**

You're using a model with either 200K tokens or 1M tokens. cc-sessions knows which one and tracks your usage:

- **85% full** - Warning appears, you can keep going
- **90% full** - Hard recommendation to compact

**cc-sessions avoids compaction by design**. If tasks and subtasks are written properly, it should rarely take you more than a context window to complete a task. **You only need compaction if you're in the middle of a task and are out of context.**

But, sometimes, tasks run long and you gotta preserve what you've done to pick up where you left off.

Compaction runs three maintenance agents to preserve your work, then starts a fresh window. Your task state, todos, and progress all carry forward seamlessly.

## Setting Up Compaction Trigger Phrase

The default compaction trigger phrase is **squish**.

But like everything else, you can customize it. Pick something that feels natural when you're running out of space.

Good examples: "lets compact", "squish", "compress"
Bad examples: "save" (too vague), "clear" (confusing with other operations)

What phrase would you like to use for context compaction?

[Wait for user's response]

---

**Instructions after user provides their phrase:**

Tell them to add it using the `/sessions` command:

```
/sessions config triggers add compact <user's phrase>
```

Example: `/sessions config triggers add compact squish`

Tell them to run it now.

[Wait for them to run the command]

---

**After they run the command:**

Confirm their phrase has been added.

Now say:

"Let's demonstrate compaction right now. This will show you exactly what happens when you approach token limits.

Use your compaction trigger phrase now."

[Wait for them to trigger compaction]

---

**When they trigger compaction:**

You'll enter the context compaction protocol. Follow it completely:

1. Run logging agent to update work logs
2. Run context-refinement agent to check for discoveries
3. Run service-documentation agent if service interfaces changed (they haven't, so it'll skip)

Right before you announce "Ready to continue with fresh context window":

Update the kickstart setup task file to include "Run `python -m sessions.kickstart next` **immediately** after starting the new context window"

Then announce ready to clear and tell the user "Run the /clear default slash command, then say "lets continue" after we clear and we'll pick right back up.

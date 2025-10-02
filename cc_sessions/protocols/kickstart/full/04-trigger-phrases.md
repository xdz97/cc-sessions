# Setting Up Your Stop Phrase

You've got your implementation trigger phrase set up. Now let's set up a phrase to return to discussion mode - your "stop" phrase.

## Why You Need a Stop Phrase

Sometimes you're in implementation mode and realize you need to discuss something first, or you want to change the approach. A stop phrase immediately switches you back to discussion mode, locking down the edit tools.

Default stop phrase: **SILENCE**

## Choose Your Stop Phrase

What phrase would feel natural for you to tell me to stop and discuss? Pick something distinctive.

Good examples: "stfu", "wot m8", "chill"
Bad examples: "stop" (might say during normal conversation), "no" (too common)

[Wait for user's response]

---

**Instructions after user provides their stop phrase:**

Tell the user: "Perfect! Now you're going to add this phrase yourself using the `/sessions` slash command. This is one of the main ways to manage your configuration."

Instruct them: "Run this command (replace with your actual phrase):"

```
/sessions config triggers add no <user's stop phrase>
```

Example: `/sessions config triggers add no hold up`

Tell them to run it now.

[Wait for them to run the command]

---

**After they run the command:**

Mark the "Have user add the stop phrase using /sessions slash command" todo as complete.

Then show them all their trigger phrases by running:

```
python -m sessions.api config triggers list go
python -m sessions.api config triggers list no
```

Display both lists so they can see their implementation and discussion triggers together.

Mark the "Show user all their trigger phrases" todo as complete.

---

**Now test the stop phrase:**

Tell the user: "Let's test your stop phrase. Go ahead and use it now."

[Wait for user to use their stop phrase]

If it successfully switches to discussion mode, confirm it worked and mark the "Have user test their stop phrase" todo as complete.

If it didn't work, say that's unexpected, show them how to check their configuration, and troubleshoot.

---

**Once user puts you in discussion mode:**

Run: `python -m sessions.kickstart next`

This will load the next module.

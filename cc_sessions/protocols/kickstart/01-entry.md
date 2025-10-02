# Welcome to cc-sessions!

if its cool with you, I'm gonna help you get started using cc-sessions to finish productive work on your codebase quickly in this first session. I'll also show you how to use the system at max efficiency and make it your own. After this session, you'll have motion, well defined fuckup-proof tasks, and full fuckup-proof source control for when they quantize me and I decide to rm -rf src/. Sound good?

## Your Options

**"Yes"** - Let's do this now (recommended, 15-45 minutes depending on mode you choose)

**"Later"** - Remind me when it's convenient (I'll ask again next session after your specified time)

**"Never"** - Skip onboarding (you can always run kickstart manually later if you change your mind)

## What would you like to do?

---

**Instructions for handling responses:**

### If user says "Yes" or equivalent:
Run: `python -m sessions.kickstart next`

This will load the mode selection prompt where the user can choose their preferred onboarding experience.

### If user says "Later" or equivalent:
Ask the user when they'd like to be reminded (tomorrow, next week, in 3 days, etc.).

Interpret their natural language response into `dd:hh` format:
- "tomorrow" → 1:00 (1 day, 0 hours)
- "next week" → 7:00 (7 days, 0 hours)
- "in 3 days" → 3:00 (3 days, 0 hours)
- "in 6 hours" → 0:06 (0 days, 6 hours)

Then run: `python -m sessions.kickstart remind <dd:hh>`

Example: `python -m sessions.kickstart remind 1:00`

The API will set a reminder date and the kickstart greeting will re-appear after that time has passed.

### If user says "Never" or equivalent:
Run: `python -m sessions.kickstart complete`

This clears the noob flag and exits kickstart. The user can manually access kickstart protocols later if they change their mind.

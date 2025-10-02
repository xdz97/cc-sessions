# Choose Your Onboarding Mode

cc-sessions kickstart supports three different onboarding experiences. Choose the one that fits your situation:

---

## Full Mode

**Who it's for**: You've never used this before

**Time**: 30-45 minutes

**What you get**:
- Learn how to use this to actually finish work faster
- Stop Claude from randomly editing code without permission
- Get Claude to understand your project's patterns and tech stack
- Set up foolproof git workflows so nothing breaks
- Configure shortcuts that match how you talk
- Learn the power features that make your life way easier
- Interactive walkthrough with examples

**Choose this if**: "I have time to learn this properly" or "Show me everything"

---

## API Mode

**Who it's for**: You're using the API and watching your token budget

**Time**: 10-15 minutes

**What you get**:
- Same setup as Full mode
- Same features and configuration
- Just way more concise - no fluff, straight to the point
- We respect your wallet

**Choose this if**: "I'm paying per token, be efficient" or "Time is money"

---

## Seshxpert Mode

**Who it's for**: You already know this system, setting up a new repo

**Time**: 5 minutes

**What you get**:
- Copy your sessions-config.json from another repo (local or github)
- Copy your agent definitions from another repo
- Only configure what needs configuring for this specific repo
- Skip any step you want
- Done

**Choose this if**: "I know what I'm doing, just let me configure this repo"

---

## Which mode would you like?

---

**Instructions for handling user's mode selection:**

Determine which mode the user chose based on their response (they might say "full", "Full Mode", "I want the complete walkthrough", "api", "API mode", "seshxpert", "expert mode", etc.).

Normalize to one of: `full`, `api`, or `seshxpert`

Then run: `python -m sessions.kickstart mode <selected-mode>`

Examples:
- `python -m sessions.kickstart mode full`
- `python -m sessions.kickstart mode api`
- `python -m sessions.kickstart mode seshxpert`

The API will:
- Initialize kickstart_progress metadata with the selected mode
- Set started timestamp
- Set current_module to the first module
- Determine which mode-specific directory to use
- Return the path to the first module chunk (e.g., `kickstart/full/03-core-workflow.md`)

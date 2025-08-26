<center>## SHOCKING REPORT REVEALS:</center>
## Vibe coding is shitty and confusing and produces garbage software that sucks to work on.

**Claude Code makes it less shitty, but not by enough.**

## The Problem

I'm going to guess how you got here and you can tell me if I get it right:

- The LLM programmer hype gave you a nerd boner
- The people hyping LLM programming made your boner crawl back into your body (are you ready to 'scale your impact', dog?)
- You held your nose and downloaded Cursor/added Cline or Roo Code/npm installed Claude Code *(after regretfully installing Node.js jk typescripters don't cry is just joke)*

At first this was obviously novel and interesting. Some things were shitty but mostly you were enjoying not having to write a context manager or even recognize that you needed one for your dumb client wrapper.

You were scaling your impact (whew).

But then Claude started doing Claude things. You asked it to add error handling to one function. It added error handling to every function in the file. And changed your error types. And your logging format. And somehow your indentation is different now?

You learned to be more specific. 'ONLY change lines 45-52.' Claude changes lines 45-52. Also lines 1-44. Also creates a new file you didn't ask for. Also helpful reminder that you should add TypeScript types (you're writing Python).

The context window thing started getting annoying. You're explaining the same architecture for the fifth time today. Claude's like 'what database?' Brother. We've been using Postgres for six hours. You were just in there.

Your CLAUDE.md is now longer than your actual code. 'NEVER use class components.' 'ALWAYS use the existing auth middleware.' 'DO NOT refactor unrelated code.' 'REMEMBER we use PostgreSQL.' Claude reads the first line and freestyle raps the rest.

You tried the subagents. 'Use the code review agent.' Cool, it's reviewing code with zero context about your application. 'Use the research agent.' It's researching the wrong library. You can't even talk to these things. They're like contractors who don't speak your language and you communicate through Google Translate and prayer.

Now you're here. Your codebase is 'done' but it's held together with string and vibes. There's three different state management patterns. Your auth flow would make a security researcher weep. You've got utility functions that are duplicated in four files because Claude kept forgetting they exist.

The real kicker? You know exactly what's wrong but fixing it means understanding code you didn't write in patterns you don't recognize using approaches you wouldn't choose.

You're not a programmer anymore. You're a prompt engineer with a production system.

## The Solution

So, now you're here. Since this is exclusively about Claude Code I'm going to assume that you are a CC user and you are looking to make that better. Lit.

So let's talk about Claude Code.

Of the major AI programming IDEs/scaffolds, Claude Code is probably the best and Claude models are probably the best (though Google is kinda coming for that ass).

But, Claude Code is not without its major faults and boner-killing frustrations.

For instance, it would be nice if Claude had to talk to you before writing code so you didn't end up with 500 lines of implementation for a one-line change.

It would be nice if you didn't lose everything when the context window died and Claude actually remembered what you were working on tomorrow.

It would be nice if your rules actually worked instead of being suggestions that Claude ignores after the first 1000 tokens.

It would be nice if you didn't have to explain your entire architecture every. single. session. and Claude actually inherited understanding from previous work.

It would be nice if Claude couldn't randomly refactor working code while you're trying to add a button.

It would be nice if you didn't have to manually check which branch you're on in five different repos and Claude actually stopped you before you edited the wrong one.

It would be nice if subagents weren't completely blind to what you're working on so they didn't gather wrong context and waste everyone's time.

It would be nice if you could see your context filling up before it exploded in your face.

It would be nice if you didn't have to copy-paste the same context between sessions like it's 1995 and Claude actually maintained state like a real application.

It would be nice if Claude followed the patterns in your codebase instead of inventing new ones every time it touches a file.

It would be nice if you didn't have to write increasingly desperate rules in CLAUDE.md and Claude was actually forced to follow consistent behavior.

It would be nice if your todo lists didn't vanish into the ether and you actually had persistent task management with real context.

It would be nice if Claude couldn't blow past your 'please stop and discuss' and actually had to get permission before implementing.

It would be nice if you didn't discover three duplicate implementations of the same function and Claude actually knew what code already exists.

This is what Sessions does. It makes all of these nice things happen. Not through more rules or documentation or prompting techniques. Through enforcement that Claude can't ignore, state that persists, and workflows that actually work.

## How It Works

Here's how it works:

You install Sessions. Five minutes, one script. It sets up hooks that Claude can't bypass, state management that persists, and a task system that actually remembers things.

Now when you start working, Claude is in Discussion Mode by default. It can read files, search code, analyze patterns. But it can't edit anything. Can't write. Can't even create a file. It HAS to talk to you first.

You: 'Add error handling to the auth flow'
Claude: *reads the auth code, understands the patterns, explains what it found and what it plans to do*
You: 'go ahead'
Claude: *NOW it can edit*

That's it. That's the whole DAIC thing. Discussion, Alignment, Implementation, Check. Claude can't skip ahead. The hooks literally block the tools.

<details>
<summary>See it in action</summary>

```
You: add user search to the dashboard

Claude: I'll help add user search to the dashboard. Let me first examine the current implementation.

[reads dashboard components, existing search patterns, API structure]

Looking at your codebase:
- Dashboard uses /components/Dashboard/index.tsx
- You have a SearchBar component already in /components/common/
- API has a users.search endpoint that's not being used
- Your other searches use debouncing with 300ms delay

I can add user search by:
1. Importing the existing SearchBar component
2. Adding state management with your existing useQueryState hook
3. Connecting to the users.search endpoint
4. Following your debounce pattern from products search

Should I implement this?

You: yep go ahead

Claude: [NOW Claude can edit - implements exactly what was discussed]
```

Without Sessions? Claude would've created a new search component, ignored your API endpoint, and used a different state pattern.

</details>

When your context window hits 75%, you get a warning. Not after it dies. Before. You wrap up clean, save your work, start fresh. The task file has everything - what you're building, what you've done, what's next. Claude reads it and continues exactly where you left off.

<details>
<summary>Context persistence demo</summary>

```
[Friday, 4pm - deep in implementing a payment system]

Claude: ⚠️ Context at 75% - Consider wrapping up soon

You: use the logging agent to save our work

Claude: [Saves detailed work log with all changes]

You: [Close laptop, weekend happens]

[Monday, 9am]

You: lets continue

Claude: Welcome back! Resuming work on m-payment-integration.
Last session we:
- Integrated Stripe checkout flow
- Added webhook handlers for payment events  
- Created payment status tracking

Current state: Testing webhook signatures
Next: Add retry logic for failed webhooks

Let's continue with the retry logic implementation.
```

Zero context rebuilding. Claude knows exactly where you left off.

</details>

Those subagents that were useless? Now they get context manifests. The code review agent knows your patterns. The research agent knows your stack. They run in separate threads so your main context stays clean. They come back with actual useful information instead of random shit they guessed.

<details>
<summary>Agents that actually work</summary>

```
You: use the context-gathering agent to understand how our caching system works

Claude: I'll use the context-gathering agent to analyze your caching system.

[Agent runs in separate context - doesn't pollute your main thread]

Agent results: I've created a comprehensive context manifest:

CACHING ARCHITECTURE:
- Redis for session cache (30min TTL)
- PostgreSQL materialized views for reports  
- React Query for client-side caching (5min stale time)
- CDN caching for static assets

KEY PATTERNS:
- Cache keys use format: {service}:{entity}:{id}:{version}
- Invalidation happens through CacheManager.invalidate()
- All cache operations logged to cache_operations table

IMPLEMENTATION LOCATIONS:
- Server cache: /lib/cache/redis-cache.ts
- Client cache: /hooks/useQueryWithCache.ts
- Cache invalidation: /api/middleware/cache-invalidator.ts

[Full context manifest saved to task file - available forever]
```

The agent understood your patterns because it could analyze everything without token limits.

</details>

Your tasks aren't todos that disappear. They're persistent files with context manifests that explain how everything works, work logs that track what's been done, and success criteria that define done. Forever. You can leave for a month and come back to perfect context.

Branch enforcement means Claude checks what branch you're on before every edit. Wrong branch? Blocked. Here's the command to fix it. No more accidentally editing main. No more git archaeology.

<details>
<summary>Branch enforcement in action</summary>

```
[Working on task m-fix-auth, supposed to be on feature/fix-auth branch]

You: update the login validation

Claude: I'll update the login validation. Let me look at the current implementation.

[Claude tries to edit src/auth/login.ts]

❌ BLOCKED: Branch mismatch!
- Task requires: feature/fix-auth  
- You're on: main

Run this command:
git checkout feature/fix-auth

You: git checkout feature/fix-auth

You: okay now update it

Claude: [NOW can edit the file safely on the correct branch]
```

No more "oh fuck I edited main" at 11pm.

</details>

Your CLAUDE.md stays under 100 lines because the behavioral rules are in CLAUDE.sessions.md and enforced by hooks. Not suggestions Claude might follow. Actual enforcement that can't be ignored.

The statusline shows you everything in real-time. Current task. DAIC mode. Token usage. What files have been edited. You always know what's happening.

<details>
<summary>Statusline keeping you informed</summary>

```
[Bottom of your Claude Code window - two lines]

██████░░░░ 45.2% (72k/160k) | Task: m-payment-integration
DAIC: Discussion | ✎ 3 files | [4 open]

[After you say "go ahead"]

██████░░░░ 47.1% (75k/160k) | Task: m-payment-integration  
DAIC: Implementation | ✎ 5 files | [4 open]

[When approaching context limit - bar turns red]

████████░░ 78.3% (125k/160k) | Task: m-payment-integration
DAIC: Discussion | ✎ 12 files | [4 open]

[When no task is active]

██░░░░░░░░ 12.1% (19k/160k) | Task: None
DAIC: Discussion | ✎ 0 files | [4 open]
```

Progress bar changes color: green < 50%, orange < 80%, red >= 80%.

</details>

When Claude is done implementing, it's reminded to run 'daic' to return to discussion mode. Can't edit anything until you explicitly allow it again. No more runaway implementations. No more surprise refactors.

This isn't complex. It's not heavy process. It's invisible rails that keep Claude from going off the cliff. You still describe what you want in natural language. Claude still writes code. But now it happens in a way that doesn't produce garbage.

You code at the same speed. You just don't spend the next three hours unfucking what Claude just did.

## Installation

Alright, you're convinced. Let's unfuck your workflow.

### Requirements

You need:
- Claude Code (you have this or you wouldn't be here)
- Python 3 + pip (for the hooks)
- Git (probably)
- 5 minutes

### Install

Pick your poison:

**NPM/NPX** (Node.js users):
```bash
cd your-broken-project
npx cc-sessions                  # One-time install
# or
npm install -g cc-sessions       # Global install
cc-sessions                      # Run in your project
```

**Pip/Pipx/UV** (Python users):
```bash
pipx install cc-sessions         # Isolated install (recommended)
cd your-broken-project
cc-sessions                      # Run the installer
# or
pip install cc-sessions          # Regular pip
# or  
uv pip install cc-sessions       # UV package manager
```

**Direct Bash** (Old school):
```bash
git clone https://github.com/GWUDCAP/cc-sessions
cd your-broken-project
/path/to/cc-sessions/install.sh
```

The installer asks you:
- Your name (so Claude knows who it's disappointing)
- If you want the statusline (you do)
- What triggers implementation mode ('go ahead', 'ship it', whatever)
- Some other config shit (just hit enter)

That's it. Restart Claude Code. You're done.

### What Just Happened

You now have:
- Hooks that enforce discussion before implementation
- State that persists between sessions
- Task management that actually works
- Agents that aren't completely useless
- Git branch enforcement
- Token warnings before death
- A chance at maintaining this code in 6 months

### Your First Task

Tell Claude:
```
Create a task using @sessions/protocols/task-creation.md for: 
[EXPLAIN THE TASK]
```

Claude will:
- Create the task file with proper structure
- Use the context-gathering agent to gather everything they need to know to complete the task based on your existing codebase
- Build a context manifest so it never forgets what it learned
- Set up the task as your current focus

Then just say 'let's work on [task-name]' and watch Claude actually discuss before implementing.

Welcome to software development with guardrails.

## Customizing Sessions

Sessions is built to be modified. You can use Claude Code itself to improve Sessions or adapt it to your workflow.

<details>
<summary>How to customize Sessions</summary>

### Understanding the Structure

Sessions comes with knowledge files that explain its own architecture:
```
sessions/knowledge/claude-code/
├── hooks-reference.md     # How hooks work and can be modified
├── subagents.md          # Agent capabilities and customization
├── tool-permissions.md   # Tool blocking configuration
└── slash-commands.md     # Command system reference
```

### Modifying Behaviors

Tell Claude:
```
Using the hooks reference at @sessions/knowledge/claude-code/hooks-reference.md, 
modify the DAIC enforcement to allow Bash commands in discussion mode
```

Claude can:
- Adjust trigger phrases in `.claude/sessions-config.json`
- Modify hook behaviors in `.claude/hooks/`
- Update protocols in `sessions/protocols/`
- Create new agents in `.claude/agents/`
- Customize task templates

### Common Customizations

**Change what tools are blocked:**
```json
// .claude/sessions-config.json
"blocked_tools": ["Edit", "Write"]  // Remove MultiEdit to allow it
```

**Add your own trigger phrases:**
```json
"trigger_phrases": ["make it so", "ship it", "do the thing"]
```

**Modify agent prompts:**
Edit files in `.claude/agents/` to change how agents behave.

**Update workflows:**
Protocols in `sessions/protocols/` are just markdown - edit them to match your process.

### Pro Tips

1. Sessions has its own CLAUDE.md at `sessions/CLAUDE.md` for meta work
2. Use the knowledge files to understand the system deeply
3. Test changes in a separate branch first
4. The hooks are just Python - add logging if needed
5. Keep your customizations documented

Remember: You're not just using Sessions, you're evolving it. Make it yours.

</details>

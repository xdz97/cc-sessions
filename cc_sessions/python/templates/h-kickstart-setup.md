---
name: kickstart-setup
branch: feature/kickstart-setup
status: pending
created: 2025-10-02
submodules: []
---

# Configure cc-sessions for Your Repository

## Problem/Goal
Configure cc-sessions based on your repository structure and preferences. Use the context-gathering agent to analyze your codebase and provide recommendations for optimal settings. Complete remaining cc-session setup and walkthrough.

## Success Criteria
- [ ] Repository structure analyzed by context-gathering agent
- [ ] Git preferences configured (has_submodules, default_branch)
- [ ] Workflow preferences set (commit_style, auto_merge, auto_push)
- [ ] Feature toggles configured (auto_ultrathink, context_warnings)
- [ ] Task completion trigger phrases configured
- [ ] Context compaction run once
- [ ] Subagents customized
- [ ] Advanced settings and concepts covered
- [ ] Bash read/write tools and agent tools configured
- [ ] Configuration verified and saved

## Context Manifest
<!-- Run context-gathering agent with special instructions:
"Analyze this repository to provide configuration recommendations for cc-sessions. Focus on:
1. Repository structure (super-repo with submodules, mono-repo, or standard)
2. Default git branch
3. Common patterns and conventions
4. Tech stack for later agent customization

Provide specific recommendations for has_submodules, default_branch, and other git preferences." -->

## User Notes

This is a kickstart configuration task. After context-gathering analyzes the repository, work through each setting:

### 1. Repository Structure
Present agent findings about submodules.
Ask: "Does this look correct?"
Update: `python -m sessions.api config git set has_submodules <true|false>`

### 2. Default Branch
Present agent findings about default branch.
Ask: "Is <branch> your default branch?"
Update: `python -m sessions.api config git set default_branch <branch>`

### 3. Commit Style
Explain options:
- **conventional**: `feat: add user authentication` (structured, semantic)
- **simple**: `add user authentication` (brief, direct)
- **detailed**: Multi-line with context (verbose)

Ask preference.
Update: `python -m sessions.api config git set commit_style <choice>`

### 4. Auto Merge
Explain: When task completes, automatically merge to default branch?
- Yes: Fast workflow, assumes you trust the work
- No: Manual merge, more control

Ask preference.
Update: `python -m sessions.api config git set auto_merge <true|false>`

### 5. Auto Push
Explain: Automatically push commits to remote?
- Yes: Changes immediately backed up
- No: Manual push, more control

Ask preference.
Update: `python -m sessions.api config git set auto_push <true|false>`

### 6. Auto Ultrathink
Tell the user: 

Claude just performs better with a larger thinking budget, but more thinking tokens means more tokens. For Claude Max x20 subscribers, this hasn't been a concern (until very recently), but for API and Pro users this means either more cost or more waiting around for limits to free back up.

cc-sessions defaults have the Max x20 user in mind - every user message you send, by default, is followed up by an "ultrathink" tag to trigger the maximum thinking budget. This makes interactions with Claude in cc-sessions as intelligent as possible. But it also costs a lot if you're footing the bill (and not Anthropic).

**auto_ultrathink** (default: enabled)
- Automatically adds `[[ ultrathink ]]` to your messages
- Makes me use extended thinking for better responses

If you want to disable auto-ultrathink, you can run `/sessions config features toggle auto_ultrathink`.

### 7. Continue with kickstart chunks
The kickstart API will guide you through the remaining work for this task.

Use: `python -m sessions.kickstart next`

## Work Log
<!-- Updated during kickstart -->

---
task: h-manage-github-prs
priority: high
status: active
branch: feature/manage-github-prs
started: 2025-10-07
---

# Task: Manage Open GitHub Pull Requests for v0.3.0 Release

## Context

With v0.3.0 release approaching, the cc-sessions repository has 6 open pull requests from external contributors. The repository is currently 81 commits ahead of origin/main with significant architectural changes.

## Objective

Review all open PRs, extract valuable contributions, inline changes with proper attribution, and manage contributor relations appropriately for v0.3.0 release.

## Success Criteria

- [ ] All 6 open PRs documented as individual subtask files
- [ ] Each PR evaluated for compatibility with v0.3.0
- [ ] Valuable changes inlined with proper attribution
- [ ] Contributors credited in GitHub comments and CHANGELOG
- [ ] PRs declined with clear explanation where appropriate
- [ ] Release notes document all contributor credits

## Open Pull Requests

1. PR #47 - @gabelul - README TL;DR documentation
2. PR #45 - @gabelul - Safe uninstaller implementation
3. PR #40 - @gabelul - Context window detection (70+ files)
4. PR #28 - @bl4ckh4nd - Task creation in discussion mode
5. PR #27 - @bl4ckh4nd - Transcript encoding and Windows support
6. PR #21 - @dnviti - Statusline enhancements

## Context Manifest

### How GitHub PR Management Works in Open Source Projects

When maintaining an open source project that receives external contributions, PR management involves several interconnected workflows that balance contributor relations, code quality, and architectural integrity.

**The Standard GitHub PR Flow:**
When a contributor forks a repository and opens a pull request, GitHub creates a reference to their branch that can be fetched and reviewed locally. The maintainer can use `gh pr list` to see all open PRs, `gh pr view <number>` to inspect details including the diff, commits, and file changes, and `gh pr checkout <number>` to test the changes locally on a branch named pr-<number>. If the changes look good and pass CI, the maintainer merges via `gh pr merge <number>` or the GitHub web interface, which automatically credits the contributor in the merge commit.

**Why This Standard Flow Won't Work Here:**
Our situation is unique because we're 81 commits ahead of origin/main with v0.3.0 containing massive architectural refactoring. The open PRs target code that has been:
- Moved from cc_sessions/hooks/ to cc_sessions/python/hooks/ and cc_sessions/javascript/hooks/
- Completely rewritten with unified state management
- Refactored with new configuration architecture
- Enhanced with features that supersede some PR functionality

If we attempt to merge these PRs directly, Git will encounter conflicts in files that no longer exist at their original paths, or worse, will silently merge changes into legacy code patterns that we've intentionally replaced.

**The Inline Strategy:**
Instead of merging PRs directly, we inline valuable changes by:
1. Reviewing the PR's intent and implementation locally
2. Manually applying the good ideas to our current v0.3.0 codebase
3. Adapting changes to fit the new architecture
4. Committing with proper attribution using Git's Co-Authored-By trailer format
5. Commenting on the PR to explain what was inlined
6. Closing the PR with gratitude and links to commits

**Attribution and Credit:**
Proper attribution is ethically important and legally required. Git supports multi-author commits through trailer lines in commit messages. The Co-Authored-By trailer makes GitHub automatically link the contributor's profile to the commit.

**Release Notes and CHANGELOG:**
We document contributor credits in:
1. CHANGELOG.md - Under each version's sections with contributor links
2. GitHub Release Notes - Contributors section with profile links

**Communication Pattern:**
When inlining changes, comments should be grateful, transparent about why direct merge isn't possible, specific about what was inlined, and link to commits.

**When to Decline:**
Some PRs won't align with the project's direction or may be superseded by completed work. Be respectful, explain clearly why it doesn't fit, suggest alternatives if applicable.

### Current Repository State (v0.3.0)

The cc-sessions repository has undergone massive architectural evolution for v0.3.0:

**File Organization Changes:**
Originally, all hooks and scripts lived in cc_sessions/hooks/ and cc_sessions/scripts/. This created cross-language dependency issues. The v0.3.0 refactoring completely separated the languages:
- Python: cc_sessions/python/hooks/, cc_sessions/python/api/, cc_sessions/python/statusline.py
- JavaScript: cc_sessions/javascript/hooks/, cc_sessions/javascript/api/, cc_sessions/javascript/statusline.js
- Shared: cc_sessions/agents/, cc_sessions/knowledge/

Any PR targeting files in old cc_sessions/hooks/ will need changes applied to BOTH Python and JavaScript to maintain feature parity.

**State Management Unification:**
Previously used 6+ separate JSON files (daic-mode.json, current_task.json, active-todos.json, etc.). In v0.3.0, consolidated into single sessions/sessions-state.json managed through SessionsState dataclass with atomic file locking. Any PR modifying state handling needs adaptation to unified state system using load_state() and edit_state() context manager.

**Configuration Architecture:**
v0.3.0 introduced comprehensive SessionsConfig system with 320+ lines of type-safe configuration. Replaced scattered patterns with dataclasses: TriggerPhrases, BlockingPatterns, GitPreferences, SessionsEnv, EnabledFeatures. Configuration in sessions/sessions-config.json accessed via load_config() and edit_config().

**UTF-8 Encoding Enforcement:**
Critical v0.3.0 fix addresses Windows compatibility by explicitly specifying UTF-8 encoding on ALL file I/O. Prevents Windows cp1252 default causing crashes. Both languages use encoding='utf-8' consistently.

**CI Environment Detection:**
All 12 hooks include is_ci_environment() function detecting GitHub Actions via GITHUB_ACTIONS, GITHUB_WORKFLOW, CI environment variables. When in CI, DAIC enforcement bypasses to allow automated agents.

**Branch Enforcement Toggle:**
v0.3.0 added CONFIG.features.branch_enforcement toggle (default: true) supporting alternative VCS systems like Jujutsu, Mercurial, Fossil. When disabled, sessions_enforce skips Git branch validation while maintaining other DAIC enforcement.

**Directory Task Support:**
Task system supports file-based (h-task.md) and directory-based (h-task/README.md with subtasks). Helper functions is_directory_task() and get_task_file_path() provide consistent detection. Directory tasks work iteratively on same branch without merging until all subtasks complete.

### Technical Reference Details

**GitHub CLI Commands:**
- gh pr list --limit 50 --json number,title,author,state,url,createdAt,headRefName,body
- gh pr view <number> --json title,body,author,files,commits
- gh pr checkout <number>
- gh pr diff <number>
- gh pr comment <number> --body "message"
- gh pr close <number>

**Git Attribution Format:**
Use heredoc for multi-line commit messages with Co-Authored-By trailer:
```
Co-Authored-By: Gabi Florea <hola@booplex.com>
```

**File Locations:**

Subtask Files:
- Create in: sessions/tasks/h-manage-github-prs/
- Format: 01-pr<number>-<short-name>.md
- Include: Technical analysis, compatibility assessment, inline strategy, attribution

CHANGELOG Updates:
- File: CHANGELOG.md
- Format: - Thanks to @username for [contribution] (#PR-number)

Code Files Requiring Dual-Language Updates:
- Python: cc_sessions/python/hooks/*.py, cc_sessions/python/api/*.py
- JavaScript: cc_sessions/javascript/hooks/*.js, cc_sessions/javascript/api/*.js

**Key Architecture Files:**

State Management:
- cc_sessions/python/hooks/shared_state.py - SessionsState, load_state(), edit_state()
- cc_sessions/javascript/hooks/shared_state.js - JavaScript equivalent

Configuration:
- cc_sessions/python/hooks/shared_state.py (lines 77-314) - Enums and SessionsConfig
- cc_sessions/python/api/config_commands.py - Configuration API

DAIC Enforcement:
- cc_sessions/python/hooks/sessions_enforce.py - Tool blocking, bash patterns, CI bypass
- cc_sessions/javascript/hooks/sessions_enforce.js - JavaScript equivalent

Installers:
- cc_sessions/install.py - Python installer with backup/restore
- install.js - JavaScript installer with backup/restore

Task Protocols:
- cc_sessions/python/protocols/task-creation/task-creation.md
- cc_sessions/python/protocols/task-completion/task-completion.md

**PR Author Emails:**
- @gabelul (Gabi Florea): hola@booplex.com
- @bl4ckh4nd: Use GitHub noreply
- @dnviti: Use GitHub noreply

For no public email, use: username@users.noreply.github.com

### Process Workflow

**Phase 1: Documentation (Create Subtasks)**
For each PR:
1. gh pr view <number> --json title,body,author,files,commits
2. Create subtask: sessions/tasks/h-manage-github-prs/0X-pr<number>-<name>.md
3. Document: PR summary, technical analysis, v0.3.0 compatibility, value assessment, inline strategy, attribution plan

**Phase 2: Inline Implementation**
For PRs with valuable changes:
1. Study PR diff (gh pr diff or gh pr checkout)
2. Identify equivalent v0.3.0 location
3. Apply to BOTH Python and JavaScript for core functionality
4. Test changes
5. Commit with attribution
6. Comment on PR with commit links

**Phase 3: Communication**
For each PR:
1. Post comment explaining outcome
2. Thank contributor
3. Be transparent about constraints
4. Link to commits/issues
5. Close PR if appropriate

**Phase 4: Documentation**
1. Update CHANGELOG.md with credits
2. Prepare release notes Contributors section
3. Verify all commits have Co-Authored-By

### Success Validation

**Completion Checklist:**
- [ ] All 6 PRs have subtask files with complete analysis
- [ ] All valuable changes inlined to v0.3.0
- [ ] All inline commits include Co-Authored-By
- [ ] All PRs have respectful comments
- [ ] CHANGELOG.md updated
- [ ] Release notes drafted
- [ ] All PRs closed
- [ ] No open PRs remain

**Quality Standards:**
- Complete and accurate attribution
- Warm, respectful, appreciative comments
- v0.3.0 architectural consistency maintained
- Both Python and JavaScript updated for core changes
- All tests pass
- CHANGELOG and release notes properly formatted

## Work Log

### Planning Phase
- Analyzed all 6 open PRs
- Documented v0.3.0 architectural state
- Created comprehensive context manifest

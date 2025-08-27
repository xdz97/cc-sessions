# Task Startup Protocol

When starting work on a task (new or existing):

## 0. Git Setup

Check task frontmatter for branch name and modules list, then create/checkout branches.

**For main tasks** (no letter suffix):
1. Start from main branch (safe to pull since we don't commit to main)
2. Pull latest changes from origin/main
3. Create the new task branch

**For subtasks** (branch contains letter suffix like tt1a-*):
1. First check current status to ensure no uncommitted changes
   - Run `git status` and address EVERY file shown
   - Check inside each submodule for uncommitted changes if applicable
   - Either commit or stash ALL changes, never leave files behind
2. Ensure the parent branch exists and checkout from it
3. If the parent branch has a remote, check if it needs updating:
   - Fetch the remote version
   - Compare local and remote to determine if pulling is needed
   - Alert if branches have diverged
4. Create the subtask branch from the parent branch

**For multi-repo projects:**
If your project uses submodules or multiple repos, create matching branches in ALL affected modules listed in the task frontmatter.

Example: If working on tt1-login-ux-flow affecting web_app and auth_service, create tt1-login-ux-flow branches in both.

> Note: If resuming work on an existing branch:
> - Check git status first for uncommitted work
> - Address EVERY file shown in `git status`
> - Checkout the branch
> - Only pull from remote if the remote branch exists

## 1. Update Task State

After creating/checking out branches, update the .claude/state/current_task.json file.

**CORRECT FORMAT (use these exact field names):**
```json
{
  "task": "task-name",        // Just the task name, NO path, NO .md extension
  "branch": "feature/branch", // The Git branch name (NOT "branch_name")
  "services": ["service1"],   // Array of affected services/modules
  "updated": "2025-08-27"     // Current date in YYYY-MM-DD format
}
```

**COMMON MISTAKES TO AVOID:**
- ❌ Using `"task_file"` instead of `"task"`
- ❌ Using `"branch_name"` instead of `"branch"`
- ❌ Including path like `"tasks/m-task.md"` instead of just `"m-task"`
- ❌ Including `.md` file extension

## 2. Load Task Context Manifest

Read the Context Manifest section from the task file.

If the Context Manifest is missing:
- For new tasks: Run context-gathering agent (should have been done during creation)
- For old tasks: Consider running context-gathering agent to create one

## 3. Load Context

Based on the manifest:
- Read the narrative explanation to understand how everything works
- Note technical reference details for implementation
- Check environmental requirements
- Note file locations for where changes will be made
- Change the frontmatter status to "in-progress"
- Add "started: YYYY-MM-DD" to the front matter

## 4. Verify Understanding

Before diving in:
- Understand the success criteria
- Review the work log for previous progress
- Check for blockers or gotchas
- Confirm approach with user if needed

## 5. Work Mode

Remember:
- Follow DAIC protocol (Discussion before Implementation)
- Use code-review agent after significant changes
- Update work log as you go
- Delegate heavy analysis to agents

## Example First Message

"I've loaded the context for [task]. Based on the manifest, I understand we're working on [summary]. The last work log entry shows [status]. Should I continue with [next step] or would you like to discuss the approach?"
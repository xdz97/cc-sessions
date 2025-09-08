# Task Completion Protocol

When a task meets its success criteria:

## Protocol Todos
<!-- Use TodoWrite to add these todos exactly as written -->
□ Verify all success criteria are checked off
□ Run code-review agent and address any critical issues
□ Run logging agent to consolidate work logs
□ Run service-documentation agent to update CLAUDE.md files and other documentation
□ Commit all changes with comprehensive message
□ OPTIONAL: Merge task branch to main and push
□ Archive completed task and select next task

## 1. Pre-Completion Checks

Verify before proceeding:
- [ ] All success criteria checked off in task file
- [ ] No unaddressed work remaining

**NOTE**: Do NOT commit yet - agents will modify files

## 2. Run Completion Agents

Delegate to specialized agents in this order:
```
1. code-review agent - Review all implemented code for security/quality
   Include: Changed files, task context, implementation approach
   **IMPORTANT**: After code-review completes, report findings to user:
   - Summarize any critical issues or warnings
   - Ask if they want to address issues before completion
   - Wait for user confirmation before proceeding
   
2. service-documentation agent - Update CLAUDE.md files 
   Include: List of services modified during task
   
3. logging agent - Finalize task documentation
   Include: Task completion summary, final status
```

## 3. Task Archival

After agents complete:
```bash
# Update task file status to 'completed'
# Move to done/ directory
mv sessions/tasks/[priority]-[task-name].md sessions/tasks/done/
# or for directories:
mv sessions/tasks/[priority]-[task-name]/ sessions/tasks/done/
```

## 4. Clear Task State

```bash
# Clear task state (but keep file)
cat > sessions/state/current-task.json << 'EOF'
{
  "task": null
}
EOF
```

## 5. Git Operations (Commit & Merge)

**NOTE**: DO NOT perform **ANY** git operations until you have cleared task state and archived the task file. This ensures your final commit and merge is complete with no unstaged/uncommitted changes.

### Step 1: Check for Super-repo Structure
To be sure, determine if you're in a regular git repo or a super-repo with submodules (sessions/ and .claude/ will be in the same directory as .gitmodules):
```bash
# Check if we're in a super-repo with submodules from the sessions/ parent directory
if [ -f .gitmodules ]; then
  echo "Super-repo detected with submodules"
  # Follow submodule commit ordering below
else
  echo "Standard repository"
  # Skip to step 4
fi
```

### Step 2: Review Unstaged Changes
If in a regular repo, check for unstaged changes. If in a super-repo, check each submodule listed in the task frontmatter *and* the super-repo itself.
```bash
# Check for any unstaged changes
git status

# If changes exist, present them to user:
# "I found the following unstaged changes: [list]
# Would you like to:
# 1. Commit all changes (git add -A)
# 2. Select specific changes to commit
# 3. Review changes first"
```

### Step 3: Commit and Merge (Conditional on Structure and Preference)
First, ask the user if they would like to simply commit all changes, commit *and* merge, or commit, merge, *and* push. Based on their preference and repo type, follow the appropriate steps below.

**IF SUPER-REPO**: Process from deepest submodules to super-repo

### A. Deepest Submodules First (Depth 2+)
For any submodules within submodules:
1. Navigate to each modified deep submodule
2. Stage changes based on user preference from Step 2
3. Commit all changes with descriptive message
4. If user opted to merge, merge into main or desired branch
5. If user opted to push, push the merged branch

### B. Direct Submodules (Depth 1)
For all modified direct submodules:
1. Navigate to each modified submodule
2. Stage changes based on user preference
3. Commit all changes with descriptive message
4. If user opted to merge, merge into main or desired branch
5. If user opted to push, push the merged branch

### C. Super-repo (Root)
After ALL submodules are committed and merged:
1. Return to super-repo root
2. Stage changes based on user preference
3. Commit all changes with descriptive message
4. If user opted to merge, merge into main or desired branch
5. If user opted to push, push the merged branch

**IF STANDARD REPO**: 
1. Stage changes based on user preference
2. Commit with descriptive message
3. If user opted to merge, merge into main or desired branch
4. If user opted to push, push the merged branch

## 6. Select Next Task

Immediately after archival:
```bash
# List all tasks (simple and reliable)
ls -la sessions/tasks/

# Present the list to user
echo "Task complete! Here are the remaining tasks:"
# User can see which are .md files vs directories vs symlinks
```

User selects next task:
- Switch to task branch: `git checkout [branch-name]`
- Update task state: Edit `sessions/state/current-task.json` with new task
- Follow task-startup.md protocol

If no tasks remain:
- Celebrate completion!
- Ask user what they want to tackle next
- Create new task following task-creation.md

## Important Notes

- NEVER skip the agent steps - they maintain system integrity
- Task files in done/ serve as historical record
- Completed experiments should document learnings even if code is discarded
- If task is abandoned incomplete, document why in task file before archiving

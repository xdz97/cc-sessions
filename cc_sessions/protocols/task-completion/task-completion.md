# Task Completion Protocol

When a task meets its success criteria:

{todos}

{git_add_warning}

## 1. Pre-Completion Checks

Verify before proceeding:

```markdown
[STATUS: Pre-Completion Checks]
✓ All success criteria checked off in task file
✓ No unaddressed work remaining

Ready to proceed with task completion.
```

If any checks fail, stop and address the remaining work first.

## 2-4. Run Completion Agents

Delegate to specialized agents in this order:
```
1. code-review agent - Review all implemented code for security/quality
   Include: Changed files, task context, implementation approach
   **IMPORTANT**: After code-review completes, report findings using this format:

```markdown
[FINDINGS: Code Review]
The code review agent has completed its analysis:

Critical Issues:
□ [None found / Description of critical issues]

Warnings:
□ [Description of any warnings]

Suggestions:
□ [Optional improvements identified]

Would you like to address any of these findings before completing the task?
- YES: We'll fix the issues first
- NO: Proceed with task completion

Your choice:
```

   - Wait for user confirmation before proceeding
   
2. service-documentation agent - Update CLAUDE.md files 
   Include: List of services modified during task
   
3. logging agent - Finalize task documentation
   Include: Task completion summary, final status
```

## 5. Task Archival

After agents complete:
```bash
# Update task file status to 'completed'
# Move to done/ directory
mv sessions/tasks/[priority]-[task-name].md sessions/tasks/done/
# or for directories:
mv sessions/tasks/[priority]-[task-name]/ sessions/tasks/done/
```

## 4. Git Operations (Commit & Merge)

**NOTE**: DO NOT perform **ANY** git operations until you have cleared task state and archived the task file. This ensures your final commit and merge is complete with no unstaged/uncommitted changes.

{staging_instructions}

{commit_instructions}

## Important Notes

- NEVER skip the agent steps - they maintain system integrity
- Task files in done/ serve as historical record
- Completed experiments should document learnings even if code is discarded
- If task is abandoned incomplete, document why in task file before archiving

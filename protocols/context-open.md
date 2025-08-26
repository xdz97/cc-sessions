# Context Open Protocol

Triggered automatically by SessionStart hook when resuming work.

## 1. Task Detection

SessionStart hook checks:
- Is there an active task in .claude/state/current_task.json?
- If yes → Load task context (sessions/tasks/{task_name}.md)
- If no → Present task list for selection

## 2. Context Loading

For active task:
- Read task file
- If task status is "pending", change it to "in-progress" and run task-startup protocol
- Read context manifest in full
- Review work log to understand position

## 3. Work Resumption

Present to user:
- Current task summary
- Last work log entry
- Immediate next steps from task

## 4. DAIC State

SessionStart hook ensures:
- Discussion mode is active by default
- User knows about 'daic' command

## Integration with Hooks

This protocol is primarily executed by the SessionStart hook, not manually. The hook:
1. Detects new session
2. Checks for active task
3. Guides context loading
4. Sets appropriate DAIC mode

## Manual Fallback

If hooks fail or need manual override:
```bash
# Check active task
cat .claude/state/current_task.json

# Load task file (if task is set)
TASK=$(jq -r .task .claude/state/current_task.json)
if [ "$TASK" != "null" ]; then
  cat sessions/tasks/$TASK.md
fi

# Follow task's context manifest
```
---
allowed-tools: Bash, Read
argument-hint: [task-name]
description: Start working on a task (create branch and set active)
---

Start working on task: $ARGUMENTS

1. Check if sessions/tasks/$ARGUMENTS.md or sessions/tasks/$ARGUMENTS/ exists
2. Read the task file to get the branch name from frontmatter
3. Create the git branch if it doesn't exist
4. Switch to that branch
5. Create/update the active symlink to point to this task
6. Update the task status to 'in-progress'
7. Show the task details and success criteria

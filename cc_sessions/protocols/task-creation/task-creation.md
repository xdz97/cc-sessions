# Task Creation Protocol

{todos}

## Creating a Task
Follow these numbered steps to complete each todo above:

### 1: Create task file from template with appropriate priority, type, and structure

#### First, determine task priority
All task files MUST include a priority prefix before the task type:

- `h-` → High priority
- `m-` → Medium priority  
- `l-` → Low priority
- `?-` → Investigate (task may be obsolete, speculative priority)

Examples:
- `h-fix-auth-redirect.md`
- `m-implement-oauth.md`
- `l-docs-api-reference.md`
- `?-research-old-feature.md`

#### Then, choose task type prefix based on the primary goal (comes after priority):

- `implement-` → New functionality (creates feature/ branch)
- `fix-` → Bug fixes, corrections (creates fix/ branch)  
- `refactor-` → Code improvements (creates feature/ branch)
- `research-` → Investigation only (no branch needed)
- `experiment-` → Proof of concepts (creates experiment/ branch)
- `migrate-` → Moving/updating systems (creates feature/ branch)
- `test-` → Adding tests (creates feature/ branch)
- `docs-` → Documentation (creates feature/ branch)

Combine: `[priority]-[type]-[descriptive-name]`

#### Next, decide if task needs file or directory structure

**Use a FILE when**:
- Single focused goal
- Estimated < 3 days work
- No obvious subtasks at creation time
- Examples:
  - `h-fix-auth-redirect.md`
  - `m-research-mcp-features.md`
  - `l-refactor-redis-client.md`

**Use a DIRECTORY when**:
- Multiple distinct phases
- Needs clear subtasks from the start
- Estimated > 3 days work
- Examples:
  - `h-implement-auth/` (magic links + OAuth + sessions)
  - `m-migrate-to-postgres/` (schema + data + cutover)
  - `l-test-all-services/` (per-service test files)

#### Finally, create the task file
For file:
```bash
cp sessions/tasks/TEMPLATE.md sessions/tasks/[priority]-[task-name].md
```
For directory:
```bash
mkdir sessions/tasks/[priority]-[task-name]
cp sessions/tasks/TEMPLATE.md sessions/tasks/[priority]-[task-name]/README.md
```

Then fill out task frontmatter
  - task: Must match filename (including priority prefix)
  - branch: Based on task type (or 'none' for research)
  - status: Start as 'pending'
  - created: Today's date{submodules_field}

### 2: Write problem statement and success criteria
First, clarify your understanding of the task with the user as needed. Then, write a clear description of what we're solving/building in Problem/Goal section.

Propose specific, measurable success criteria to the user that unambiguously define "done" and adjust as needed based on user feedback. Once approved, record the success criteria with checkboxes in the text file.

### 3: Run context-gathering agent or mark complete
  - Ask user: "Would you like to run the context-gathering agent now?"
  - If yes: Use context-gathering agent on sessions/tasks/[priority]-[task-name].md
  - If no: Mark this step complete and continue
  - Context manifest MUST be complete before work begins (if not now, during task startup)

### 4: Update service index files if applicable
  - Check if task relates to any task indexes (sessions/tasks/indexes)
  - If not, ask user if they would like to create a new index for any affected features, code paths, or services
  - Add task to relevant index files under appropriate priority section
  - Skip if no relevant index exists

### 5: Commit the new task file
- Stage the task file and any updated index files
- Commit with descriptive message about the new task


## Task Evolution

If a file task needs subtasks during work:
1. Create directory with same name
2. Move original file to directory as README.md
3. Add subtask files
4. Update active task reference if needed
  - ex:
  ```json
  {{ "task": "some-task-dir/README.md" }}
  ```
  - ex:
  ```json
  {{ "task": "some-task-dir/some-subtask.md" }}
  ```

## Important Note on Context

The context-gathering agent is responsible for creating a complete, self-contained context manifest. This replaces the deprecated patterns system. If the context proves insufficient during implementation, the agent's prompt should be improved rather than adding workarounds or modifying the context manifest manually.

## Protocol Completion

Once the task file has been created and the context-gathering agent has populated the context manifest:

1. Inform the user that the task has been successfully created
2. Show the task file path: `sessions/tasks/[priority]-[task-name].md`
3. **DO NOT start working on the task** - The task has been created but will remain in 'pending' status
4. The task will not be started now unless the user explicitly asks to begin work on it
5. If the user wants to start the task, they should use the task startup protocol

This completes the task creation protocol. The task is now ready to be started at a future time.

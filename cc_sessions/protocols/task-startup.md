# Task Startup Protocol

When starting work on a task (new or existing):

## Protocol Todos
<!-- Use TodoWrite to add these todos exactly as written -->
□ Check git status and handle any uncommitted changes
□ Create/checkout task branch and matching submodule branches
□ Update sessions/state/current-task.json with task name
□ Load task context manifest and verify understanding
□ Update task status to in-progress and add started date

## 1. Git Setup

Check task frontmatter for branch name and modules list, then create/checkout branches.

### Check for Super-repo Structure

```bash
# Check if we're in a super-repo with submodules
if [ -f .gitmodules ]; then
  echo "Super-repo detected - will need to manage submodule branches"
else
  echo "Standard repository - simple branch management"
fi
```

### Branch Creation/Checkout

1. Start from main branch
2. Reconcile any divergences - ensure that any unstaged changes to main are committed or stashed based on user preferences and any unpulled changes are pulled from origin/main
3. Once origin/main contains all local change the user wants and local main contains all remote change, create the new task branch


### Super-repo Submodule Management (IF .gitmodules exists)

**CRITICAL: Create matching branches in ALL affected submodules**
- Check the task frontmatter for the modules list
- For each module listed:
  - Navigate to that module directory
  - Check for uncommitted changes first
  - If not on main, checkout main and pull latest
  - Create a branch with the same name as the task branch
  - Return to the parent directory

Example: If working on tt1-login-ux-flow affecting io_web and io_user_model, create tt1-login-ux-flow branches in both submodules.

**Branch Discipline Rules:**
- Task frontmatter must list ALL modules that might be edited
- All listed modules MUST have matching task branches
- Before editing any file, verify the submodule is on the correct branch
- If a module needs to be added mid-task, create its branch immediately

> Note: If resuming work on an existing branch:
> - Check git status first for uncommitted work in super-repo AND all submodules
>   - Address EVERY file shown in `git status`, not just expected files
>   - Common missed files: CLAUDE.md, sessions/state files, test outputs
>   - Either commit ALL changes or explicitly discuss with user
> - Checkout the branch in the super-repo
> - For each affected submodule, navigate to it and checkout the matching branch
> - Only pull from remote if the remote branch exists

## 2. Update Task State

After creating/checking out branches, update the sessions/state/current-task.json file.

```json
{
  "task": "task-name"  // Just the task name, NO path, NO .md extension
}
```

The full task state (branch, modules, status) is read from the task file frontmatter.

**COMMON MISTAKES TO AVOID:**
- ❌ Including path like `"tasks/m-task.md"` instead of just `"m-task"`
- ❌ Including `.md` file extension
- ❌ Adding branch or services fields (these come from frontmatter now)

## 3. Load Task Context Manifest

Read the Context Manifest section from the task file.

If the Context Manifest is missing, you **must** use the context-gathering agent to analyze this task and create a context manifest.

## 4. Load Context & Verify Branch State

Based on the manifest:
- Read the narrative explanation to understand how everything works
- Note technical reference details for implementation
- Check environmental requirements
- Note file locations for where changes will be made
- Read prescribed file segments (if any)
- Change the frontmatter status to "in-progress"
- Add "started: MM/DD/YYYY" to the front matter


## 5. Verify Understanding

Before diving in:
- Understand the success criteria
- Review the work log for previous progress
- Check for blockers or gotchas

## 6. Initial Discussion & Planning

After loading task context:
1. Analyze the task requirements thoroughly
2. Propose implementation plan with specific todo list:
   ```
   I propose to implement the following:
   □ [Specific action 1]: [Expanded explanation of the todo item]
   □ [Specific action 2]: [Expanded explanation of the todo item]
   □ [Specific action 3]: [Expanded explanation of the todo item]
   
   Shall I proceed with this implementation?
   ```
3. Iterate based on user feedback until approved
4. Upon approval, convert proposed todos to TodoWrite exactly as written

**IMPORTANT**: Until your todos are approved, you are seeking the user's approval of an explicitly proposed and properly explained list of execution todos. Besides answering user questions during discussion, your messages should end with an expanded explanation of each todo, the clean list of todos, and **no further messages**.

## 7. Work Mode
For the duration of the task:
- Discuss before implementing
- Constantly seek user input and approval

Once approved, remember:
- *Immediately* load your proposed todo items *exactly* as you proposed them using ToDoWrite
- Work logs are maintained by the logging agent (not manually)

After completion of the last task in any todo list:
- *Do not* try to run any write-based tools (you will be automatically put into discussion mode)
- Repeat todo proposal and approval workflow for any additional write/edit-based work

## Example First Message

"I've loaded the context for [task]. Based on the manifest, I understand we're working on [summary]. The last work log entry shows [status]. 

Here is the work I think we should accomplish:
- [todo item]: [full explanation]
- [todo item]: [full explanation]
- ...

Use any disccusion mode trigger phrase if you approve the proposal *or* tell me how I should adjust the proposal."

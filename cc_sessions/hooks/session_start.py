#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from importlib.metadata import version, PackageNotFoundError
import requests, json, sys, shutil
from typing import Dict, List, Optional, Tuple
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import edit_state, PROJECT_ROOT, load_config, SessionsProtocol, get_task_file_path, is_directory_task
##-##

#-#

# ===== GLOBALS ===== #
sessions_dir = PROJECT_ROOT / 'sessions'

STATE = None
CONFIG = load_config()

developer_name = CONFIG.environment.developer_name

# Initialize context
context = f"You are beginning a new context window with the developer, {developer_name}.\n\n"

# Quick configuration checks
needs_setup = False
quick_checks = []
#-#

# ===== FUNCTIONS ===== #

def parse_index_file(index_path) -> Optional[Tuple[Dict, List[str]]]:
    """Parse an index file and extract metadata and task lines."""
    if not index_path.exists():
        return None

    try:
        content = index_path.read_text()
        lines = content.split('\n')
    except (IOError, UnicodeDecodeError):
        return None

    # Extract frontmatter using simple string parsing (like task files)
    metadata = {}
    if lines and lines[0] == '---':
        for i, line in enumerate(lines[1:], 1):
            if line == '---':
                break
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    # Extract task lines (those starting with - `)
    task_lines = []
    for line in lines:
        if line.strip().startswith('- `'):
            task_lines.append(line.strip())

    return metadata, task_lines

def list_open_tasks_grouped() -> str:
    """List open tasks grouped by their indexes."""
    tasks_dir = PROJECT_ROOT / 'sessions' / 'tasks'
    indexes_dir = tasks_dir / 'indexes'

    # First collect all tasks as before
    task_files = []
    if tasks_dir.exists():
        task_files = sorted([f for f in tasks_dir.glob('*.md') if f.name != 'TEMPLATE.md'])
    for task_dir in sorted([d for d in tasks_dir.iterdir() if d.is_dir() and d.name not in ['done', 'indexes']]):
        readme_file = task_dir / 'README.md'
        if readme_file.exists():
            task_files.append(task_dir)
        subtask_files = sorted([f for f in task_dir.glob('*.md') if f.name not in ['TEMPLATE.md', 'README.md']])
        task_files.extend(subtask_files)

    # Build task status map
    task_status = {}
    for task_file in task_files:
        fpath = get_task_file_path(task_file)
        if not fpath.exists():
            continue
        try:
            with fpath.open('r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
        except (IOError, UnicodeDecodeError):
            continue
        task_name = f"{task_file.name}/" if is_directory_task(task_file) else task_file.name
        status = None
        for line in lines:
            if line.startswith('status:'):
                status = line.split(':')[1].strip()
                break
        if status:
            task_status[task_name] = status

    # Parse all index files
    indexed_tasks = {}
    index_info = {}
    if indexes_dir.exists():
        for index_file in sorted(indexes_dir.glob('*.md')):
            result = parse_index_file(index_file)
            if result:
                metadata, task_lines = result
                if metadata and 'index' in metadata:
                    index_id = metadata['index']
                    index_info[index_id] = {
                        'name': metadata.get('name', index_id),
                        'description': metadata.get('description', ''),
                        'tasks': []
                    }
                    # Extract task names from the lines
                    for line in task_lines:
                        # Extract task name from format: - `task-name.md` - description
                        if '`' in line:
                            try:
                                start = line.index('`') + 1
                                end = line.index('`', start)
                                task = line[start:end]
                                if task in task_status:
                                    indexed_tasks[task] = index_id
                                    index_info[index_id]['tasks'].append(task)
                            except ValueError:
                                # Malformed line, skip it
                                continue

    # Build output
    output = "No active task set. Available tasks:\n\n"

    # Display tasks grouped by index
    for index_id, info in sorted(index_info.items()):
        if info['tasks']:  # Only show indexes with tasks
            output += f"## {info['name']}\n"
            if info['description']:
                output += f"{info['description']}\n"
            for task in info['tasks']:
                if task in task_status:
                    output += f"  • {task} ({task_status[task]})\n"
            output += "\n"

    # Show unindexed tasks
    unindexed = [task for task in task_status if task not in indexed_tasks]
    if unindexed:
        output += "## Uncategorized\n"
        for task in sorted(unindexed):
            output += f"  • {task} ({task_status[task]})\n"
        output += "\n"

    # Add startup instructions
    output += f"""To select a task:
- Type in one of your startup commands: {CONFIG.trigger_phrases.task_startup}
- Include the task file you would like to start using `@`
- Hit Enter to activate task startup
"""
    return output

#-#

"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║ ██████╗██████╗██████╗██████╗██████╗ █████╗ ██╗  ██╗      ██████╗██████╗ █████╗ █████╗ ██████╗ ║
║ ██╔═══╝██╔═══╝██╔═══╝██╔═══╝╚═██╔═╝██╔══██╗███╗ ██║      ██╔═══╝╚═██╔═╝██╔══██╗██╔═██╗╚═██╔═╝ ║
║ ██████╗█████╗ ██████╗██████╗  ██║  ██║  ██║████╗██║      ██████╗  ██║  ███████║█████╔╝  ██║   ║
║ ╚═══██║██╔══╝ ╚═══██║╚═══██║  ██║  ██║  ██║██╔████║      ╚═══██║  ██║  ██╔══██║██╔═██╗  ██║   ║
║ ██████║██████╗██████║██████║██████╗╚█████╔╝██║╚███║      ██████║  ██║  ██║  ██║██║ ██║  ██║   ║
║ ╚═════╝╚═════╝╚═════╝╚═════╝╚═════╝ ╚════╝ ╚═╝ ╚══╝      ╚═════╝  ╚═╝  ╚═╝  ╚═╝╚═╝ ╚═╝  ╚═╝   ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
SessionStart Hook

Initializes session state and loads task context:
- Checks for required components (daic command, tiktoken)  
- Clears session warning flags and stale state
- Loads current task or lists available tasks
- Updates task status from pending to in-progress
"""

# ===== EXECUTION ===== #

#!> 1. Clear flags and todos for new session
with edit_state() as s: 
    s.flags.clear_flags()
    s.todos.clear_active()
    restored = s.todos.restore_stashed()
    STATE = s
context += "Cleared session flags and active todos for new session.\n\n"

if restored:
    context += f"""Restored {restored} stashed todos from previous session:\n\n{STATE.todos.active}\n\nTo clear, use `cd .claude/hooks && python -c \"from shared_state import edit_state; with edit_state() as s: s.todos.clear_stashed()\"`\n\n"""
#!<

#!> 2. Nuke transcripts dir
transcripts_dir = sessions_dir / 'transcripts'
if transcripts_dir.exists(): shutil.rmtree(transcripts_dir, ignore_errors=True)
#!<

#!> 3. Load current task or list available tasks
# Check for active task
if (task_file := STATE.current_task.file_path) and task_file.exists():
    # Check if task status is pending and update to in-progress
    task_content = task_file.read_text()
    task_updated = False

    # Parse task frontmatter to check status
    if task_content.startswith('---'):
        lines = task_content.split('\n')
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('---'):
                break
            if line.startswith('status: pending'):
                lines[i] = 'status: in-progress'
                task_updated = True
                # Write back the updated content
                task_file.write_text('\n'.join(lines))
                task_content = '\n'.join(lines)
                break

        # Output the full task state
        context += f"""Current task state:
```json
{json.dumps(STATE.current_task.task_state, indent=2)}
```

Loading task file: {STATE.current_task.file}
{"=" * 60}
{task_content}
{"=" * 60}

"""

    context += f"""Since you are resuming an in-progress task, follow these instructions:

    1. Analyze the task requirements and work completed thoroughly
    2. Analyze any next steps itemized in the task file and, if necessary, ask any questions from the user for clarification.
    3. Propose implementation plan with structured format:

```markdown
[PLAN: Implementation Approach]
Based on the task requirements, I propose the following implementation:

□ [Specific action 1]
  → [Expanded explanation of what this involves]

□ [Specific action 2]
  → [Expanded explanation of what this involves]

□ [Specific action 3]
  → [Expanded explanation of what this involves]

To approve these todos, you may use any of your implementation mode trigger phrases: 
{CONFIG.trigger_phrases.implementation_mode}
```

3. Iterate based on user feedback until approved
4. Upon approval, convert proposed todos to TodoWrite exactly as written

**IMPORTANT**: Until your todos are approved, you are seeking the user's approval of an explicitly proposed and properly explained list of execution todos. Besides answering user questions during discussion, your messages should end with an expanded explanation of each todo, the clean list of todos, and **no further messages**.

**For the duration of the task**:
- Discuss before implementing
- Constantly seek user input and approval

Once approved, remember:
- *Immediately* load your proposed todo items *exactly* as you proposed them using ToDoWrite
- Work logs are maintained by the logging agent (not manually)

After completion of the last task in any todo list:
- *Do not* try to run any write-based tools (you will be automatically put into discussion mode)
- Repeat todo proposal and approval workflow for any additional write/edit-based work"""

else:
    context += list_open_tasks_grouped()
#!<

#!> 4. Check cc-sessions version
try: current_version = version('cc-sessions')
except PackageNotFoundError: current_version = None
try:
    resp = requests.get("https://pypi.org/pypi/cc-sessions/json", timeout=2)
    if resp.ok:
        latest_version = resp.json().get("info", {}).get("version")
        if current_version and current_version != latest_version:
            context += f"Update available for cc-sessions: {current_version} → {latest_version}. Run `pip install --upgrade cc-sessions` to update."
except requests.RequestException: pass
#!<

#-#

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(output))

sys.exit(0)

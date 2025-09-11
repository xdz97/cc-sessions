#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from importlib.metadata import version, PackageNotFoundError
import requests, json, sys, shutil
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import edit_state, PROJECT_ROOT, load_config
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

        if task_updated: context += "[Note: Task status updated from 'pending' to 'in-progress']\n\nFollow the task-startup protocol to create branches and set up the work environment.\n\n"
        else: context += "Review the Work Log at the end of the task file above and continue the task.\n\n"
else:
    # No active task - list available tasks
    tasks_dir = sessions_dir / 'tasks'
    task_files = []

    if tasks_dir.exists(): task_files = sorted([f for f in tasks_dir.glob('*.md') if f.name != 'TEMPLATE.md'])
    for task_dir in sorted([d for d in tasks_dir.iterdir() if d.is_dir() and d.name != 'done']):
        readme_file = task_dir / 'README.md'
        if readme_file.exists(): task_files.append(task_dir)
        subtask_files = sorted([f for f in task_dir.glob('*.md') if f.name not in ['TEMPLATE.md', 'README.md']])
        task_files.extend(subtask_files)

    if task_files:
        context += "No active task set. Available tasks:\n"
        for task_file in task_files:
            fpath = task_file / 'README.md' if task_file.is_dir() else task_file
            if not fpath.exists(): continue
            # Read first few lines to get task info
            with fpath.open('r', encoding='utf-8') as f: lines = f.readlines()[:10]
            task_name = f"{task_file.name}/" if task_file.is_dir() else task_file.name
            status = 'unknown'
            for line in lines:
                if line.startswith('status:'): status = line.split(':')[1].strip(); break
            context += f"  • {task_name} ({status})\n"

        context += """
To select a task:
1. Update sessions/state/current-task.json with the task name
2. Or create a new task following sessions/protocols/task-creation.md
"""
    else: context += """No tasks found. 

To create your first task:
1. Copy the template: cp sessions/tasks/TEMPLATE.md sessions/tasks/[priority]-[task-name].md
Priority prefixes: h- (high), m- (medium), l- (low), ?- (investigate)
2. Fill in the task details
3. Update sessions/state/current-task.json
4. Follow sessions/protocols/task-startup.md
"""
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

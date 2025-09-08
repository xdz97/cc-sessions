#!/usr/bin/env python3
# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import json
import sys
import os
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import (  check_daic_mode_bool, set_daic_mode, store_active_todos, 
                            get_current_model, clear_active_todos, PROJECT_ROOT,
                            stash_active_todos )
##-##

#-#

# ===== GLOBALS ===== #
input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")

# Check if this is any /add-*-trigger command
prompt_stripped = prompt.strip()
is_add_trigger_command = (prompt_stripped.startswith('/add-') and '-trigger' in prompt_stripped.split()[0] if prompt_stripped else False)

# Check current DAIC mode
current_mode = check_daic_mode_bool()

CURRENT_MODEL = get_current_model()

# Only add ultrathink if not /add-trigger command
context = "" if is_add_trigger_command else "[[ ultrathink ]]\n"
transcript_path = input_data.get("transcript_path", "")

active_todos_file = PROJECT_ROOT / 'sessions' / 'state' / 'active-todos.json'

#!> Trigger phrase detection
daic_phrases = ["run that", "yert", "make it so"]
task_creation_phrases = []
task_completion_phrases = []
task_start_phrases = []
compaction_phrases = ["lets compact"]

try:
    if USER_CONFIG:
        daic_phrases += USER_CONFIG.get('trigger_phrases', [])
        task_creation_phrases += USER_CONFIG.get('task_creation_phrases', [])
        task_completion_phrases += USER_CONFIG.get('task_completion_phrases', [])
        task_start_phrases += USER_CONFIG.get('task_start_phrases', [])
        compaction_phrases += USER_CONFIG.get('compaction_phrases', [])
except Exception as e: print(f"[DEBUG] Error loading trigger phrases: {e}", file=sys.stderr)

daic_toggle_detected = any(phrase.lower() in prompt.lower() for phrase in daic_phrases)
task_creation_detected = any(phrase.lower() in prompt.lower() for phrase in task_creation_phrases)
task_completion_detected = any(phrase.lower() in prompt.lower() for phrase in task_completion_phrases)
task_start_detected = any(phrase.lower() in prompt.lower() for phrase in task_start_phrases)
compaction_detected = any(phrase.lower() in prompt.lower() for phrase in compaction_phrases)

if any([daic_toggle_detected, task_creation_detected, task_completion_detected, task_start_detected, compaction_detected]):
    clear_active_todos()
#!<

#-#

"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║ ██╗   ██╗ ██████╗██████╗██████╗   ███╗   ███╗██████╗ ██████╗ ██████╗ █████╗  ██████╗██████╗ ║
║ ██║   ██║██╔════╝██╔═══╝██╔══██╗  ████╗ ████║██╔═══╝██╔════╝██╔════╝██╔══██╗██╔════╝██╔═══╝ ║
║ ██║   ██║███████╗█████╗ ██████╔╝  ██╔████╔██║█████╗ ███████╗███████╗███████║██║  ██╗█████╗  ║
║ ██║   ██║╚════██║██╔══╝ ██╔══██╗  ██║╚██╔╝██║██╔══╝ ╚════██║╚════██║██╔══██║██║  ██║██╔══╝  ║
║ ╚██████╔╝██████╔╝██████╗██║  ██║  ██║ ╚═╝ ██║██████╗██████╔╝██████╔╝██║  ██║╚██████╔╝██████╗ ║
║  ╚═════╝ ╚═════╝ ╚═════╝╚═╝  ╚═╝  ╚═╝     ╚═╝╚═════╝╚═════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
UserPromptSubmit Hook

Manages DAIC mode transitions and protocol triggers:
- Detects trigger phrases for mode switching and protocol activation  
- Monitors context window usage and provides warnings
- Auto-loads protocol todos when protocols are triggered
- Clears active todos when switching contexts
"""

# ===== FUNCTIONS ===== #
def get_context_length_from_transcript(transcript_path):
    """Get current context length from the most recent main-chain message in transcript"""
    try:
        with open(transcript_path, 'r') as f: lines = f.readlines()

        most_recent_usage = None
        most_recent_timestamp = None
        # Parse each JSONL entry
        for line in lines:
            try:
                data = json.loads(line.strip())
                # Skip sidechain entries (subagent calls)
                if data.get('isSidechain', False): continue

                # Check if this entry has usage data
                if data.get('message', {}).get('usage'):
                    entry_time = data.get('timestamp')
                    # Track the most recent main-chain entry with usage
                    if entry_time and (not most_recent_timestamp or entry_time > most_recent_timestamp):
                        most_recent_timestamp = entry_time
                        most_recent_usage = data['message']['usage']
            except json.JSONDecodeError: continue

        # Calculate context length from most recent usage
        if most_recent_usage:
            context_length = (
                most_recent_usage.get('input_tokens', 0) +
                most_recent_usage.get('cache_read_input_tokens', 0) +
                most_recent_usage.get('cache_creation_input_tokens', 0)
            )
            return context_length
    except Exception: pass
    return 0
#-#

# ===== EXECUTION ===== #

## ===== TOKEN MONITORING ===== ##
# Check context usage and warn if needed
if transcript_path and os.path.exists(transcript_path):
    context_length = get_context_length_from_transcript(transcript_path)

    if context_length > 0:
        # Calculate percentage of usable context (opus 160k/sonnet 800k practical limit before auto-compact)
        usable_tokens = 160000
        if CURRENT_MODEL == "sonnet": usable_tokens = 800000
        usable_percentage = (context_length / usable_tokens) * 100

        # Check for warning flag files to avoid repeating warnings
        warning_85_flag = PROJECT_ROOT / "sessions" / "state" / "context-warning-85.flag"
        warning_90_flag = PROJECT_ROOT / "sessions" / "state" / "context-warning-90.flag"

        # Token warnings (only show once per session)
        if usable_percentage >= 90 and not warning_90_flag.exists():
            context += f"\n[90% WARNING] {context_length:,}/{usable_tokens:,} tokens used ({usable_percentage:.1f}%). CRITICAL: Run sessions/protocols/task-completion.md to wrap up this task cleanly!\n"
            warning_90_flag.parent.mkdir(parents=True, exist_ok=True)
            warning_90_flag.touch()
        elif usable_percentage >= 85 and not warning_85_flag.exists():
            context += f"\n[Warning] Context window is {usable_percentage:.1f}% full ({context_length:,}/{usable_tokens:,} tokens). The danger zone is >90%. You will receive another warning when you reach 90% - don't panic but gently guide towards context compaction or task completion (if task is nearly complete). Task completion often satisfies compaction requirements and should allow the user to clear context safely, so you do not need to worry about fitting in both processes.\n"
            warning_85_flag.parent.mkdir(parents=True, exist_ok=True)
            warning_85_flag.touch()
##-##

## ===== CONTEXT MUTATIONS ===== ##

#!> DAIC mode toggling
# Implementation triggers (only work in discussion mode, skip for /add-trigger)
if not is_add_trigger_command and current_mode and daic_toggle_detected:
    set_daic_mode(False)  # Switch to implementation
    context += """[DAIC: Implementation Mode Activated]
CRITICAL RULES:
- Convert your proposed todos to TodoWrite EXACTLY as written
- Do NOT add new todos - only implement approved items
- Do NOT remove todos - complete them or return to discussion
- Check off each todo as you complete it
- If you discover you need to change your approach, return to discussion mode (Bash, 'daic') and explain
- Todo list defines your execution boundary
- When all todos are complete, you'll auto-return to discussion (no daic command needed)
"""

# Emergency stop (works in any mode)
if any(word in prompt for word in ["SILENCE", "STOP"]):  # Case sensitive
    set_daic_mode(True)  # Force discussion mode
    clear_active_todos()  # Clear any active todo list
    context += "[DAIC: EMERGENCY STOP] All tools locked. You are now in discussion mode. Re-align with your pair programmer.\n"
#!<

#!> Task creation
if not is_add_trigger_command and task_creation_detected:
    task_creation_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-creation.md'
    set_daic_mode(False)
    had_active_todos = False
    if active_todos_file.exists(): had_active_todos = True; stash_active_todos()

    # Auto-load protocol todos
    protocol_todos = [
        {'content': 'Determine task priority and type prefix', 'status': 'pending', 'activeForm': 'Determining task priority and type prefix'},
        {'content': 'Decide if task needs file or directory structure', 'status': 'pending', 'activeForm': 'Deciding if task needs file or directory structure'},
        {'content': 'Create task file with proper frontmatter', 'status': 'pending', 'activeForm': 'Creating task file with proper frontmatter'},
        {'content': 'Write clear problem statement and success criteria', 'status': 'pending', 'activeForm': 'Writing clear problem statement and success criteria'},
        {'content': 'Run context-gathering agent to create context manifest', 'status': 'pending', 'activeForm': 'Running context-gathering agent to create context manifest'},
        {'content': 'Update appropriate service index files', 'status': 'pending', 'activeForm': 'Updating appropriate service index files'},
        {'content': 'Commit the new task file', 'status': 'pending', 'activeForm': 'Committing the new task file'}
    ]
    store_active_todos(protocol_todos)

    # Add task detection note
    context += f"""[Task Detection Notice]
Language in the user prompt indicates that the user may want to create a task or the message may reference something that could be a task.

Assess whether the user has explicitly asked to create a task, often evidenced by the use of one of the following trigger phrases:
{task_creation_phrases if task_creation_phrases else 'No custom trigger phrases defined.'}

**If and only if appropriate**, lightly attempt to dissuade the user from tasks that would be more like a major version than a line item of one or a minor patch.

If its an explicit task creation request, immediately read {task_creation_protocol_path} and follow the instructions therein to create the task.

If you can't be sure, read the protocol after confirmation from the user.

"""

    if had_active_todos:
        context += """Your previous todos have been stashed and task creation protocol todos have been made active. Your previous todos will be restored after the task creation todos are complete. Do not attempt to update or complete them until after the task creation protocol todos have been completed.

"""
#!<

#!> Task completion
if not is_add_trigger_command and task_completion_detected:
    task_completion_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-completion.md'
    set_daic_mode(False)
 
    # Auto-load protocol todos
    protocol_todos = [
        {'content': 'Verify all success criteria are checked off', 'status': 'pending', 'activeForm': 'Verifying all success criteria are checked off'},
        {'content': 'Run code-review agent and address any critical issues', 'status': 'pending', 'activeForm': 'Running code-review agent and addressing critical issues'},
        {'content': 'Run logging agent to consolidate work logs', 'status': 'pending', 'activeForm': 'Running logging agent to consolidate work logs'},
        {'content': 'Run context-refinement agent to update task context', 'status': 'pending', 'activeForm': 'Running context-refinement agent to update task context'},
        {'content': 'Commit all changes with comprehensive message', 'status': 'pending', 'activeForm': 'Committing all changes with comprehensive message'},
        {'content': 'Merge task branch to main and push', 'status': 'pending', 'activeForm': 'Merging task branch to main and pushing'},
        {'content': 'Archive completed task and select next task', 'status': 'pending', 'activeForm': 'Archiving completed task and selecting next task'}
    ]
    store_active_todos(protocol_todos)

    # Add task completion note
    context += f"""[Task Completion Notice]
Language in the user prompt indicates that the user may want to complete the current task.
IF you or the user believe that the current task is complete, or IF the user has explicitly asked to complete the task, check the current task file and report back on its completion status.

If you are ready to complete the task, you *MUST* read {task_completion_protocol_path} and follow the instructions therein to complete the task.

"""
#!<

#!> Task startup
if not is_add_trigger_command and task_start_detected:
    task_start_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-startup.md'

    set_daic_mode(False)

    # Auto-load protocol todos
    protocol_todos = [
        {'content': 'Check git status and handle any uncommitted changes', 'status': 'pending', 'activeForm': 'Checking git status and handling uncommitted changes'},
        {'content': 'Create/checkout task branch and matching submodule branches', 'status': 'pending', 'activeForm': 'Creating/checking out task branch and matching submodule branches'},
        {'content': 'Update sessions/state/current-task.json with task name', 'status': 'pending', 'activeForm': 'Updating sessions/state/current-task.json with task name'},
        {'content': 'Load task context manifest and verify understanding', 'status': 'pending', 'activeForm': 'Loading task context manifest and verifying understanding'},
        {'content': 'Update task status to in-progress and add started date', 'status': 'pending', 'activeForm': 'Updating task status to in-progress and adding started date'},
    ]
    store_active_todos(protocol_todos)

    protocol_file = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-startup.md'

    with open(protocol_file, 'r') as f:
        protocol_content = f.read()

    context += f"""[Task Startup Notice]
Language in the user prompt indicates that the user may want to start a new task. If the user wants to begin a new task, you *MUST* follow the task startup protocol: at {protocol_content} to begin the task properly.

"""
#!<

#!> Context compaction
if not is_add_trigger_command and compaction_detected:
    compaction_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'context-compaction.md'
    had_active_todos = False
    if active_todos_file.exists(): had_active_todos = True; stash_active_todos()
    set_daic_mode(False)
    # Auto-load protocol todos
    protocol_todos = [
        {'content': 'Run logging agent to update work logs', 'status': 'pending', 'activeForm': 'Running logging agent to update work logs'},
        {'content': 'Run context-refinement agent to check for discoveries', 'status': 'pending', 'activeForm': 'Running context-refinement agent to check for discoveries'},
        {'content': 'Run service-documentation agent if service interfaces changed', 'status': 'pending', 'activeForm': 'Running service-documentation agent if service interfaces changed'},
        {'content': 'Verify/update sessions/state/current-task.json', 'status': 'pending', 'activeForm': 'Verifying/updating sessions/state/current-task.json'},
        {'content': 'Announce readiness for context clear', 'status': 'pending', 'activeForm': 'Announcing readiness for context clear'}
    ]
    store_active_todos(protocol_todos)

    # Add context compaction note
    context += f"""[Context Compaction Notice]
Language in the user prompt indicates that the user may want to compact context. You *MUST* read {compaction_protocol_path} and follow the instructions therein to compact context properly.

"""
    if had_active_todos: context += """Your todos have been stashed and will be restored in the next session after the user clears context. Do not attempt to update or complete your previous todo list (context compaction todos are now active).

"""
#!<

#!> Iterloop detection
if "iterloop" in prompt.lower():
    context += "ITERLOOP DETECTED:\nYou have been instructed to iteratively loop over a list. Identify what list the user is referring to, then follow this loop: present one item, wait for the user to respond with questions and discussion points, only continue to the next item when the user explicitly says 'continue' or something similar\n"
#!<

##-##

#-#

# Output the context additions
output = { "hookSpecificOutput": { "hookEventName": "UserPromptSubmit", "additionalContext": context } }
print(json.dumps(output))

sys.exit(0)

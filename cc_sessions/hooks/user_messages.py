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
from shared_state import load_state, edit_state, Mode, PROJECT_ROOT, CCTodo, TaskState, edit_config, load_config
##-##

#-#

# ===== GLOBALS ===== #
input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")
transcript_path = input_data.get("transcript_path", "")

STATE = load_state()
CONFIG = load_config()

# Check if this is any /add-*-trigger command
prompt_stripped = prompt.strip()
is_add_trigger_command = (prompt_stripped.startswith('/add-trigger') if prompt_stripped else False)

# Only add ultrathink if not /add-trigger command
if CONFIG.features.auto_ultrathink and not is_add_trigger_command: context = "[[ ultrathink ]]\n\n"
else: context = ""

#!> Trigger phrase detection
implementation_phrase_detected = any(phrase.lower() in prompt.lower() for phrase in CONFIG.trigger_phrases.implementation_mode)
discussion_phrase_detected = any(phrase.lower() in prompt.lower() for phrase in CONFIG.trigger_phrases.discussion_mode)
task_creation_detected = any(phrase.lower() in prompt.lower() for phrase in CONFIG.trigger_phrases.task_creation)
task_completion_detected = any(phrase.lower() in prompt.lower() for phrase in CONFIG.trigger_phrases.task_completion)
task_start_detected = any(phrase.lower() in prompt.lower() for phrase in CONFIG.trigger_phrases.task_startup)
compaction_detected = any(phrase.lower() in prompt.lower() for phrase in CONFIG.trigger_phrases.context_compaction)
#!<

#!> Flags
had_active_todos = False
#!<

#-#

"""
╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║ ██████╗ █████╗  █████╗ ███╗  ███╗██████╗ ██████╗  ██╗  ██╗ █████╗  █████╗ ██╗  ██╗██████╗ ║
║ ██╔══██╗██╔═██╗██╔══██╗████╗████║██╔══██╗╚═██╔═╝  ██║  ██║██╔══██╗██╔══██╗██║ ██╔╝██╔═══╝ ║
║ ██████╔╝█████╔╝██║  ██║██╔███║██║██████╔╝  ██║    ███████║██║  ██║██║  ██║█████╔╝ ██████╗ ║
║ ██╔═══╝ ██╔═██╗██║  ██║██║╚══╝██║██╔═══╝   ██║    ██╔══██║██║  ██║██║  ██║██╔═██╗ ╚═══██║ ║
║ ██║     ██║ ██║╚█████╔╝██║    ██║██║       ██║    ██║  ██║╚█████╔╝╚█████╔╝██║  ██╗██████║ ║
║ ╚═╝     ╚═╝ ╚═╝ ╚════╝ ╚═╝    ╚═╝╚═╝       ╚═╝    ╚═╝  ╚═╝ ╚════╝  ╚════╝ ╚═╝  ╚═╝╚═════╝ ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝
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
        if STATE.model == "sonnet": usable_tokens = 800000
        usable_percentage = (context_length / usable_tokens) * 100

        # Token warnings (only show once per session)
        if usable_percentage >= 90 and not STATE.flags.context_90 and CONFIG.features.context_warnings.warn_90:
            context += f"\n[90% WARNING] {context_length:,}/{usable_tokens:,} tokens used ({usable_percentage:.1f}%). CRITICAL: Run sessions/protocols/task-completion.md to wrap up this task cleanly!\n"
            with edit_state() as s: s.flags.context_90 = True; STATE = s
        elif usable_percentage >= 85 and not STATE.flags.context_85 and CONFIG.features.context_warnings.warn_85:
            context += f"\n[Warning] Context window is {usable_percentage:.1f}% full ({context_length:,}/{usable_tokens:,} tokens). The danger zone is >90%. You will receive another warning when you reach 90% - don't panic but gently guide towards context compaction or task completion (if task is nearly complete). Task completion often satisfies compaction requirements and should allow the user to clear context safely, so you do not need to worry about fitting in both processes.\n"
            with edit_state() as s: s.flags.context_85 = True; STATE = s
##-##

## ===== CONTEXT MUTATIONS ===== ##

#!> DAIC mode toggling
# Implementation triggers (only work in discussion mode, skip for /add-trigger)
if not is_add_trigger_command and STATE.mode is Mode.NO and implementation_phrase_detected:
    with edit_state() as s: s.mode = Mode.GO; STATE = s
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
if discussion_phrase_detected:  # Case sensitive
    with edit_state() as s: s.mode = Mode.NO; s.todos.clear_active(); STATE = s
    context += "[DAIC: EMERGENCY STOP] All tools locked. You are now in discussion mode. Re-align with your pair programmer.\n"
#!<

#!> Task creation
if not is_add_trigger_command and task_creation_detected:
    task_creation_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-creation.md'
    with edit_state() as s: 
        s.mode = Mode.GO
        if s.todos.active: had_active_todos = True; s.todos.stash_active()
        # Auto-load protocol todos
        s.todos.active = [
            CCTodo(
                content='Determine task priority and type prefix',
                activeForm='Determining task priority and type prefix'),
            CCTodo(
                content='Decide if task needs file or directory structure',
                activeForm='Deciding if task needs file or directory structure'),
            CCTodo(
                content='Create task file from template',
                activeForm='Creating task file'),
            CCTodo(
                content='Write clear problem statement and success criteria',
                activeForm='Writing clear problem statement and success criteria'),
            CCTodo(
                content='Run context-gathering agent to create context manifest',
                activeForm='Running context-gathering agent to create context manifest'),
            CCTodo(
                content='Update appropriate service index files',
                activeForm='Updating appropriate service index files'),
            CCTodo(
                content='Commit the new task file',
                activeForm='Committing the new task file')]
        STATE = s

    # Add task detection note
    context += f"""[Task Detection Notice]
Language in the user prompt indicates that the user may want to create a task or the message may reference something that could be a task.

Assess whether the user has explicitly asked to create a task, often evidenced by the use of one of the following trigger phrases:
{CONFIG.trigger_phrases.task_creation if CONFIG.trigger_phrases.task_creation else 'No custom trigger phrases defined.'}

**If and only if appropriate**, lightly attempt to dissuade the user from tasks that would be more like a major version than a line item of one or a minor patch.

If its an explicit task creation request, immediately read {task_creation_protocol_path} and follow the instructions therein to create the task.

If you can't be sure, read the protocol after confirmation from the user.

"""

    if had_active_todos:
        context += "Your previous todos have been stashed and task creation protocol todos have been made active. Your previous todos will be restored after the task creation todos are complete. Do not attempt to update or complete them until after the task creation protocol todos have been completed.\n\n"
#!<

#!> Task completion
if not is_add_trigger_command and task_completion_detected:
    task_completion_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-completion.md'
    with edit_state() as s:
        s.mode = Mode.GO
 
        # Auto-load protocol todos
        s.todos.active = [
            CCTodo(
                content='Verify all success criteria are checked off',
                activeForm='Verifying status of success criteria'),
            CCTodo(
                content='Run code-review agent and address any critical issues',
                activeForm='Running code-review agent'),
            CCTodo(
                content='Run logging agent to consolidate work logs',
                activeForm='Running logging agent to consolidate work logs'),
            CCTodo(
                content='Run service-documentation agent to update CLAUDE.md files and other documentation',
                activeForm='Running service-documentation agent to update documentation'),
            CCTodo(
                content='Mark task file complete and move to tasks/done/',
                activeForm='Archiving task file'),
            CCTodo(
                content='Commit all changes with comprehensive message and (USER OPTION: merge to main)',
                activeForm='Committing and merging'),
            CCTodo(
                content='USER OPTION: Push changes to remote',
                activeForm='Asking user about pushing changes')
        ]
        STATE = s

    # Add task completion note
    context += f"[Task Completion Notice]\nLanguage in the user prompt indicates that the user may want to complete the current task.\n\nIF you or the user believe that the current task is complete, or IF the user has explicitly asked to complete the task, check the current task file and report back on its completion status.\n\n If you are ready to complete the task, you *MUST* read {task_completion_protocol_path} and follow the instructions therein to complete the task.\n\n"
#!<

#!> Task startup
if not is_add_trigger_command and task_start_detected:
    task_reference = None
    words = prompt.split()
    for word in words:
        if word.startswith("@") and ("sessions/tasks/" in word) and word.endswith(".md"):
            task_reference = word.split('sessions/tasks/')[-1]
            break
    task_start_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-startup.md'
    with edit_state() as s: 
        s.mode = Mode.GO
        s.todos.clear_active()
        s.todos.active = [
            CCTodo(
                content='Check git status and handle any uncommitted changes',
                activeForm='Checking git status and handling uncommitted changes'),
            CCTodo(
                content='Create/checkout task branch and matching submodule branches',
                activeForm='Creating/checking out task branch(es)'),
            CCTodo(
                content='Update current-task.json with new task',
                activeForm='Updating current-task.json'),
            CCTodo(
                content='Load task context manifest and verify understanding',
                activeForm='Loading task context manifest and verifying understanding'),
            CCTodo(
                content='Update task status to in-progress and add started date',
                activeForm='Updating task status to in-progress and adding started date')]
        STATE = s

    protocol_content = None
    if task_start_protocol_path.exists():
        with open(task_start_protocol_path, 'r') as f: protocol_content = f.read()

    context += f"[Task Startup Notice]\nLanguage in the user prompt indicates that the user may want to start a new task. "

    if task_reference: 
        task_data = TaskState.load_task(file=task_reference)
        with edit_state() as s: s.current_task = task_data; STATE = s
        context += f"A potential task reference was detected in the user prompt: {task_reference}. This task has been set as the current task."

    context += "If the user wants to begin a new task, you *MUST* follow the task startup protocol:\n"

    if protocol_content: context += f"{protocol_content}\n"
    else: context += f"sessions/protocols/task-startup.md\n"
#!<

#!> Context compaction
if not is_add_trigger_command and compaction_detected:
    compaction_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'context-compaction.md'
    if STATE.todos.active: 
        had_active_todos = True
        with edit_state() as s: s.mode = Mode.GO; s.todos.stash_active(); STATE = s
    # Auto-load protocol todos
    with edit_state() as s: s.todos.active = [
        CCTodo(
            content='Run logging agent to update work logs',
            activeForm='Running logging agent to update work logs'),
        CCTodo(
            content='Run context-refinement agent to check for discoveries',
            activeForm='Running context-refinement agent to check for discoveries'),
        CCTodo(
            content='Run service-documentation agent (if service interfaces changed)',
            activeForm='Running service-documentation agent if service interfaces changed'),
        CCTodo(
            content='Verify/update current task state',
            activeForm='Verifying/updating current task'),
        CCTodo(
            content='Announce readiness for context clear',
            activeForm='Announcing readiness for context clear')]
    STATE = s

    # Add context compaction note
    context += f"[Context Compaction Notice]\nLanguage in the user prompt indicates that the user may want to compact context. You *MUST* read {compaction_protocol_path} and follow the instructions therein to compact context properly.\n"

    if had_active_todos: context += "Your todos have been stashed and will be restored in the next session after the user clears context. Do not attempt to update or complete your previous todo list (context compaction todos are now active).\n"
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

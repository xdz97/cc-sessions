#!/usr/bin/env python3
"""User message hook to detect DAIC trigger phrases and special patterns."""
import json
import sys
import re
import os
try:
    import tiktoken
except ImportError:
    tiktoken = None
from shared_state import check_daic_mode_bool, set_daic_mode, store_active_todos

# Load input
input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")
transcript_path = input_data.get("transcript_path", "")
context = ""

# Get configuration (if exists)
try:
    from pathlib import Path
    from shared_state import get_project_root
    PROJECT_ROOT = get_project_root()
    CONFIG_FILE = PROJECT_ROOT / "sessions" / "sessions-config.json"
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        config = {}
except:
    config = {}

# Default trigger phrases if not configured
DEFAULT_TRIGGER_PHRASES = ["make it so", "run that", "yert"]
trigger_phrases = config.get("trigger_phrases", DEFAULT_TRIGGER_PHRASES)

# Load all trigger categories from config
task_creation_phrases = config.get("task_creation_phrases", ["create a task", "create a new task", "write a task"])
task_completion_phrases = config.get("task_completion_phrases", ["complete the task", "are we done here", "is the task complete"])
task_start_phrases = config.get("task_start_phrases", ["start the task", "begin the task", "let's start the task"])
compaction_phrases = config.get("compaction_phrases", ["let's compact", "compact context", "run compaction"])

# Check if this is any /add-*-trigger command
prompt_stripped = prompt.strip()
is_add_trigger_command = (prompt_stripped.startswith('/add-') and '-trigger' in prompt_stripped.split()[0] if prompt_stripped else False)

# Detect all trigger types
prompt_lower = prompt.lower()
daic_toggle_detected = any(phrase.lower() in prompt_lower for phrase in trigger_phrases)
task_creation_detected = any(phrase.lower() in prompt_lower for phrase in task_creation_phrases)
task_completion_detected = any(phrase.lower() in prompt_lower for phrase in task_completion_phrases)
task_start_detected = any(phrase.lower() in prompt_lower for phrase in task_start_phrases)
compaction_detected = any(phrase.lower() in prompt_lower for phrase in compaction_phrases)

# Check API mode and add ultrathink if not in API mode (skip for /add-trigger)
if not config.get("api_mode", False) and not is_add_trigger_command:
    context = "[[ ultrathink ]]\n"

# Token monitoring
def get_context_length_from_transcript(transcript_path):
    """Get current context length from the most recent main-chain message in transcript"""
    try:
        import os
        if not os.path.exists(transcript_path):
            return 0
            
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        
        most_recent_usage = None
        most_recent_timestamp = None
        
        # Parse each JSONL entry
        for line in lines:
            try:
                data = json.loads(line.strip())
                # Skip sidechain entries (subagent calls)
                if data.get('isSidechain', False):
                    continue
                    
                # Check if this entry has usage data
                if data.get('message', {}).get('usage'):
                    entry_time = data.get('timestamp')
                    # Track the most recent main-chain entry with usage
                    if entry_time and (not most_recent_timestamp or entry_time > most_recent_timestamp):
                        most_recent_timestamp = entry_time
                        most_recent_usage = data['message']['usage']
            except json.JSONDecodeError:
                continue
        
        # Calculate context length from most recent usage
        if most_recent_usage:
            context_length = (
                most_recent_usage.get('input_tokens', 0) +
                most_recent_usage.get('cache_read_input_tokens', 0) +
                most_recent_usage.get('cache_creation_input_tokens', 0)
            )
            return context_length
    except Exception:
        pass
    return 0

# Check context usage and warn if needed (only if tiktoken is available)
if transcript_path and tiktoken and os.path.exists(transcript_path):
    context_length = get_context_length_from_transcript(transcript_path)
    
    if context_length > 0:
        # Calculate percentage of usable context (160k practical limit before auto-compact)
        usable_percentage = (context_length / 160000) * 100
        
        # Check for warning flag files to avoid repeating warnings
        from pathlib import Path
        PROJECT_ROOT = get_project_root()
        warning_75_flag = PROJECT_ROOT / ".claude" / "state" / "context-warning-75.flag"
        warning_90_flag = PROJECT_ROOT / ".claude" / "state" / "context-warning-90.flag"
        
        # Token warnings (only show once per session)
        if usable_percentage >= 90 and not warning_90_flag.exists():
            context += f"\n[90% WARNING] {context_length:,}/160,000 tokens used ({usable_percentage:.1f}%). CRITICAL: Run sessions/protocols/task-completion.md to wrap up this task cleanly!\n"
            warning_90_flag.parent.mkdir(parents=True, exist_ok=True)
            warning_90_flag.touch()
        elif usable_percentage >= 75 and not warning_75_flag.exists():
            context += f"\n[75% WARNING] {context_length:,}/160,000 tokens used ({usable_percentage:.1f}%). Context is getting low. Be aware of coming context compaction trigger.\n"
            warning_75_flag.parent.mkdir(parents=True, exist_ok=True)
            warning_75_flag.touch()

# DAIC keyword detection
current_mode = check_daic_mode_bool()

# Implementation triggers (only work in discussion mode, skip for /add-trigger)
if not is_add_trigger_command and current_mode and daic_toggle_detected:
    set_daic_mode(False)  # Switch to implementation
    context += """[DAIC: Implementation Mode Activated]
CRITICAL RULES:
- Convert your proposed todos to TodoWrite EXACTLY as written
- Do NOT add new todos - only implement approved items
- Do NOT remove todos - complete them or return to discussion
- Check off each todo as you complete it
- If you need to change approach: run 'daic' immediately
- Todo list defines your execution boundary
- When all todos are complete, you'll auto-return to discussion
"""

# Emergency stop (works in any mode)
if any(word in prompt for word in ["SILENCE", "STOP"]):  # Case sensitive
    set_daic_mode(True)  # Force discussion mode
    from shared_state import clear_active_todos
    clear_active_todos()  # Clear any active todo list
    context += "[DAIC: EMERGENCY STOP] All tools locked. You are now in discussion mode. Re-align with your pair programmer.\n"

# Iterloop detection
if "iterloop" in prompt.lower():
    context += "You have been instructed to iteratively loop over a list. Identify what list the user is referring to, then follow this loop: present one item, wait for the user to respond with questions and discussion points, only continue to the next item when the user explicitly says 'continue' or something similar\n"

# Protocol detection - explicit phrases that trigger protocol reading

# Task creation detection
if not is_add_trigger_command and task_creation_detected:
    task_creation_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-creation.md'
    set_daic_mode(False)
    
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
    
    context += f"""[Task Creation Notice]
Language in the user prompt indicates that the user may want to create a task. Tasks are for:
• Work that needs to be done later
• Work that needs separate context  
• Work that needs its own git branch
• NOT subtasks of current work (those go in the current task file/directory)

If the user *is* asking to create a task, you *MUST* read {task_creation_protocol_path} and follow the instructions therein to create the task.

"""

# Task completion detection
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
    
    context += f"""[Task Completion Notice]
Language in the user prompt indicates that the user may want to complete the current task. 

IF you or the user believe that the current task is complete, or IF the user has explicitly asked to complete the task, check the current task file and report back on its completion status.

If you are ready to complete the task, you *MUST* read {task_completion_protocol_path} and follow the instructions therein to complete the task.

"""

# Task startup detection
if not is_add_trigger_command and task_start_detected:
    task_start_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'task-startup.md'
    set_daic_mode(False)
    
    # Auto-load protocol todos
    protocol_todos = [
        {'content': 'Check git status and handle any uncommitted changes', 'status': 'pending', 'activeForm': 'Checking git status and handling uncommitted changes'},
        {'content': 'Create/checkout task branch and matching submodule branches', 'status': 'pending', 'activeForm': 'Creating/checking out task branch and matching submodule branches'},
        {'content': 'Update .claude/state/current_task.json with task name', 'status': 'pending', 'activeForm': 'Updating .claude/state/current_task.json with task name'},
        {'content': 'Load task context manifest and verify understanding', 'status': 'pending', 'activeForm': 'Loading task context manifest and verifying understanding'},
        {'content': 'Update task status to in-progress and add started date', 'status': 'pending', 'activeForm': 'Updating task status to in-progress and adding started date'},
        {'content': 'Enter discussion mode and propose implementation todos', 'status': 'pending', 'activeForm': 'Entering discussion mode and proposing implementation todos'}
    ]
    store_active_todos(protocol_todos)
    
    context += f"""[Task Startup Notice]
Language in the user prompt indicates that the user may want to start a new task. If the user wants to begin a new task, you *MUST* follow the task startup protocol at {task_start_protocol_path} to begin the task properly.

"""

# Context compaction detection
if not is_add_trigger_command and compaction_detected:
    compaction_protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / 'context-compaction.md'
    set_daic_mode(False)
    
    # Auto-load protocol todos
    protocol_todos = [
        {'content': 'Run logging agent to update work logs', 'status': 'pending', 'activeForm': 'Running logging agent to update work logs'},
        {'content': 'Run context-refinement agent to check for discoveries', 'status': 'pending', 'activeForm': 'Running context-refinement agent to check for discoveries'},
        {'content': 'Run service-documentation agent if service interfaces changed', 'status': 'pending', 'activeForm': 'Running service-documentation agent if service interfaces changed'},
        {'content': 'Verify/update .claude/state/current_task.json', 'status': 'pending', 'activeForm': 'Verifying/updating .claude/state/current_task.json'},
        {'content': 'Announce readiness for context clear', 'status': 'pending', 'activeForm': 'Announcing readiness for context clear'}
    ]
    store_active_todos(protocol_todos)
    
    context += f"""[Context Compaction Notice]
Language in the user prompt indicates that the user may want to compact context. You *MUST* read {compaction_protocol_path} and follow the instructions therein to compact context properly.
"""


# Task detection patterns (optional feature)
if config.get("task_detection", {}).get("enabled", True):
    task_patterns = [
        r"(?i)we (should|need to|have to) (implement|fix|refactor|migrate|test|research)",
        r"(?i)create a task for",
        r"(?i)add this to the (task list|todo|backlog)",
        r"(?i)we'll (need to|have to) (do|handle|address) (this|that) later",
        r"(?i)that's a separate (task|issue|problem)",
        r"(?i)file this as a (bug|task|issue)"
    ]
    
    task_mentioned = any(re.search(pattern, prompt) for pattern in task_patterns)
    
    if task_mentioned:
        # Add task detection note
        context += """
[Task Detection Notice]
The message may reference something that could be a task.

IF you or the user have discovered a potential task that is sufficiently unrelated to the current task, ask if they'd like to create a task file.

Tasks are:
• More than a couple commands to complete
• Semantically distinct units of work
• Work that takes meaningful context
• Single focused goals (not bundled multiple goals)
• Things that would take multiple days should be broken down
• NOT subtasks of current work (those go in the current task file/directory)

If they want to create a task, follow the task creation protocol.
"""

# Output the context additions
if context:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context
        }
    }
    print(json.dumps(output))

sys.exit(0)

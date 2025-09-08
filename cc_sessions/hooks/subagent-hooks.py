#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from collections import deque
import tiktoken
import json
import sys
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import PROJECT_ROOT
##-##

#-#

# ===== GLOBALS ===== #
# Load input from stdin
try: input_data = json.load(sys.stdin)
except json.JSONDecodeError as e: print(f"Error: Invalid JSON input: {e}", file=sys.stderr); sys.exit(1)

# Check if this is a Task tool call
tool_name = input_data.get("tool_name", "")
if tool_name != "Task": sys.exit(0)

# Get the transcript path from the input data
transcript_path = input_data.get("transcript_path", "")
if not transcript_path: sys.exit(0)

# Get the transcript into memory
with open(transcript_path, 'r') as f: transcript = [json.loads(line) for line in f]
transcript = deque(transcript)
#-#

"""
╔═══════════════════════════════════════════════════════════════════╗
║ ██████╗██╗ ██╗█████╗  █████╗  █████╗██████╗██╗  ██╗██████╗██████╗ ║
║ ██╔═══╝██║ ██║██╔═██╗██╔══██╗██╔═══╝██╔═══╝███╗ ██║╚═██╔═╝██╔═══╝ ║
║ ██████╗██║ ██║█████╔╝███████║██║    █████╗ ████╗██║  ██║  ██████╗ ║
║ ╚═══██║██║ ██║██╔═██╗██╔══██║██║ ██╗██╔══╝ ██╔████║  ██║  ╚═══██║ ║
║ ██████║╚████╔╝█████╔╝██║  ██║╚█████║██████╗██║╚███║  ██║  ██████║ ║
║ ╚═════╝ ╚═══╝ ╚════╝ ╚═╝  ╚═╝ ╚════╝╚═════╝╚═╝ ╚══╝  ╚═╝  ╚═════╝ ║
╚═══════════════════════════════════════════════════════════════════╝
PreToolUse:Task:subagent_type hooks

This module handles PreToolUse processing for the Task tool:
    - Chunks the transcript for subagents based on token limits
    - Saves transcript chunks to designated directories
    - Sets flags to manage subagent context
"""

# ===== EXECUTION ===== #

#!> Trunc + clean transcript
# Remove any pre-work transcript entries
start_found = False
while not start_found and transcript:
    # OPTIMIZE: Use deque for efficient pops from the front
    entry = transcript.popleft()
    message = entry.get('message')
    if message:
        content = message.get('content')
        if isinstance(content, list):
            for block in content:
                if block.get('type') == 'tool_use' and block.get('name') in ['Edit', 'MultiEdit', 'Write']: start_found = True

# Clean the transcript
clean_transcript = deque()
for entry in transcript:
    message = entry.get('message')
    message_type = entry.get('type')

    if message and message_type in ['user', 'assistant']:
        content = message.get('content')
        role = message.get('role')
        clean_entry = { 'role': role, 'content': content }
        clean_transcript.append(clean_entry)
#!<

#!> Prepare subagent dir for transcript files
subagent_type = 'shared'
task_call = clean_transcript[-1]
for block in task_call.get('content'):
    if block.get('type') == 'tool_use' and block.get('name') == 'Task':
        task_input = block.get('input')
        subagent_type = task_input.get('subagent_type')

# Clear the current transcript directory
BATCH_DIR = PROJECT_ROOT / 'sessions' / 'state' / subagent_type
BATCH_DIR.mkdir(parents=True, exist_ok=True)
target_dir = BATCH_DIR
for item in target_dir.iterdir():
    if item.is_file(): item.unlink()
#!<

#!> Set subagent flag
subagent_flag = PROJECT_ROOT / 'sessions' / 'state' / 'in_subagent_context.flag'
subagent_flag.touch()
#!<

#!> Prepare tiktoken
enc = tiktoken.get_encoding('cl100k_base')
def n_tokens(s: str) -> int:
    return len(enc.encode(s))
#!<

#!> Chunk and save transcript batches
MAX_TOKENS_PER_BATCH = 18_000
transcript_batch, batch_tokens, file_index = [], 0, 1             

while clean_transcript:
    entry = clean_transcript.popleft()
    entry_tokens = n_tokens(json.dumps(entry, ensure_ascii=False))

    if batch_tokens + entry_tokens > MAX_TOKENS_PER_BATCH and transcript_batch:
        file_path = BATCH_DIR / f"current_transcript_{file_index:03}.json"
        with file_path.open('w') as f:
            json.dump(transcript_batch, f, indent=2, ensure_ascii=False)
        file_index += 1
        transcript_batch, batch_tokens = [], 0

    transcript_batch.append(entry)
    batch_tokens += entry_tokens

if transcript_batch:
    file_path = BATCH_DIR / f'current_transcript_{file_index:03}.json'
    with file_path.open('w') as f:
        json.dump(transcript_batch, f, indent=2, ensure_ascii=False)
#!<

#-#

# Allow the tool call to proceed
sys.exit(0)

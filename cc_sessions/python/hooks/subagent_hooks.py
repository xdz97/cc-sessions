#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import json, sys, math, bisect
from collections import deque
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import edit_state, PROJECT_ROOT
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

#!> Set subagent flag
with edit_state() as s: s.flags.subagent = True; STATE = s
#!<

#!> Trunc + clean transcript
# Remove any pre-work transcript entries
start_found = False
while not start_found and transcript:
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
if not clean_transcript: print("[Subagent] No relevant transcript entries found, skipping snapshot."); sys.exit(0)
task_call = clean_transcript[-1]
content = task_call.get('content')
if isinstance(content, list):
    for block in content:
        if block.get('type') == 'tool_use' and block.get('name') == 'Task':
            task_input = block.get('input') or {}
            subagent_type = task_input.get('subagent_type', subagent_type)

# Clear the current transcript directory
BATCH_DIR = PROJECT_ROOT / 'sessions' / 'transcripts' / subagent_type
BATCH_DIR.mkdir(parents=True, exist_ok=True)
for item in BATCH_DIR.iterdir():
    if item.is_file(): item.unlink()
#!<

#!> Chunk and save transcript batches
MAX_BYTES = 24000
usable_context = 160000
if STATE.model == "sonnet": usable_context = 800000
clean_transcript_text = json.dumps(list(clean_transcript), indent=2, ensure_ascii=False)

chunks = []
buf_chars = []
buf_bytes = 0
last_newline_idx = None
last_space_idx = None

for ch in clean_transcript_text:
    ch_b = len(ch.encode("utf-8"))

    # If overflowing, flush a chunk
    if buf_bytes + ch_b > MAX_BYTES:
        cut_idx = None
        if last_newline_idx is not None: cut_idx = last_newline_idx
        elif last_space_idx is not None: cut_idx = last_space_idx
        if cut_idx is not None and cut_idx > 0:
            # Emit chunk up to the breakpoint
            chunks.append("".join(buf_chars[:cut_idx]))
            remainder = buf_chars[cut_idx:]
            buf_chars = remainder
            buf_bytes = sum(len(c.encode("utf-8")) for c in buf_chars)
        else:
            # No breakpoints, hard cut what we got
            if buf_chars: chunks.append("".join(buf_chars))
            buf_chars = []
            buf_bytes = 0

        last_newline_idx = None
        last_space_idx = None

    buf_chars.append(ch)
    buf_bytes += ch_b

    if ch == "\n": last_newline_idx = len(buf_chars); last_space_idx = None
    elif ch == " " and last_newline_idx is None: last_space_idx = len(buf_chars)

# Flush any remaining buffer
if buf_chars: chunks.append("".join(buf_chars))

assert all(len(c.encode("utf-8")) <= MAX_BYTES for c in chunks), "Chunking failed to enforce byte limit"

for idx, chunk in enumerate(chunks, start=1):
    part_name = f"current_transcript_{idx:03d}.txt"
    part_path = BATCH_DIR / part_name
    with part_path.open('w', encoding='utf-8', newline="\n") as f: f.write(chunk)
#!<

#-#

# Allow the tool call to proceed
sys.exit(0)

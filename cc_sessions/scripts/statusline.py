# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import json, sys, subprocess, os
from pathlib import Path
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
if 'CLAUDE_PROJECT_DIR' in os.environ:
    PROJECT_ROOT = Path(os.environ['CLAUDE_PROJECT_DIR']).resolve()
    sys.path.insert(0, str(PROJECT_ROOT))
    # Use local symlinked sessions package when in development mode
    from sessions.hooks.shared_state import edit_state, Model, Mode, find_git_repo, load_state
else:
    # Use installed cc-sessions package in production
    from cc_sessions.hooks.shared_state import edit_state, Model, Mode, find_git_repo, load_state
##-##

#-#

# ===== GLOBALS ===== #

#!> Parse input + set constants
# read json input from stdin
data = json.load(sys.stdin)

cwd = data.get("cwd", ".")
model_name = data.get("model", {}).get("display_name", "unknown")
session_id = data.get("session_id", "unknown")

task_dir = PROJECT_ROOT / "sessions" / "tasks"
#!<

#!> Colors/styles
green = "\033[38;5;114m"
orange = "\033[38;5;215m"
red = "\033[38;5;203m"
gray = "\033[38;5;242m"
l_gray = "\033[38;5;250m"
cyan = "\033[38;5;111m"
purple = "\033[38;5;183m"
reset = "\033[0m"
#!<

#!> Determine model and context limit
curr_model = None
context_limit = 160000
if "[1m]" in model_name.lower(): context_limit = 800000
if "sonnet" in model_name.lower(): curr_model = Model.SONNET
elif "opus" in model_name.lower(): curr_model = Model.OPUS
else: curr_model = Model.UNKNOWN
#!<

#!> Update model in shared state
STATE = load_state()
if not STATE or STATE.model != curr_model:
    with edit_state() as s: s.model = curr_model; STATE = s
#!<

#-#

"""
╔═══════════════════════════════════════════════════════════════════════════╗
║ ██████╗██████╗ █████╗ ██████╗██╗ ██╗██████╗██╗     ██████╗██╗  ██╗██████╗ ║
║ ██╔═══╝╚═██╔═╝██╔══██╗╚═██╔═╝██║ ██║██╔═══╝██║     ╚═██╔═╝███╗ ██║██╔═══╝ ║
║ ██████╗  ██║  ███████║  ██║  ██║ ██║██████╗██║       ██║  ████╗██║█████╗  ║
║ ╚═══██║  ██║  ██╔══██║  ██║  ██║ ██║╚═══██║██║       ██║  ██╔████║██╔══╝  ║
║ ██████║  ██║  ██║  ██║  ██║  ╚████╔╝██████║███████╗██████╗██║╚███║██████╗ ║
║ ╚═════╝  ╚═╝  ╚═╝  ╚═╝  ╚═╝   ╚═══╝ ╚═════╝╚══════╝╚═════╝╚═╝ ╚══╝╚═════╝ ║
╚═══════════════════════════════════════════════════════════════════════════╝
Sessions default status line script
Shows:
- Context usage progress bar (with Ayu Dark colors)
- Current task name
- Current mode (Discussion or Implementation)
- Count of edited & uncommitted files in the current git repo
- Count of open tasks in sessions/tasks (files + dirs)
"""

# ===== EXECUTION ===== #

## ===== PROGRESS BAR ===== ##

#!> Pull context length from transcript
context_length = None
transcript_path = data.get('transcript_path', None)

if transcript_path:
    try:
        with open(transcript_path, 'r') as f: lines = f.readlines()
        most_recent_usage = None
        most_recent_timestamp = None

        for line in lines:
            try:
                data = json.loads(line.strip())
                # Skip sidechain entries (subagent calls)
                if data.get('isSidechain', False): continue

                # Check for usage data in main-chain messages
                if data.get('message', {}).get('usage'):
                    timestamp = data.get('timestamp')
                    if timestamp and (not most_recent_timestamp or timestamp > most_recent_timestamp):
                        most_recent_timestamp = timestamp
                        most_recent_usage = data['message']['usage']
            except: continue

        # Calculate context length (input + cache tokens only, NOT output)
        if most_recent_usage:
            context_length = (most_recent_usage.get('input_tokens', 0) + most_recent_usage.get('cache_read_input_tokens', 0) + most_recent_usage.get('cache_creation_input_tokens', 0))
    except Exception as e:
        pass
#!<

#!> Use context_length and context_limit to calculate context percentage
if context_length and context_length < 17000: context_length = 17000
if context_length and context_limit:
    pct = (context_length * 100) / context_limit
    progress_pct = f"{pct:.1f}"
    progress_pct_int = int(pct)
    if progress_pct_int > 100: progress_pct = "100.0"; progress_pct_int = 100
else:
    progress_pct = "0.0"
    progress_pct_int = 0
#!<

#!> Formatting and styling
# Format token counts in 'k'
formatted_tokens = f"{context_length // 1000}k" if context_length else "17k"
formatted_limit = f"{context_limit // 1000}k" if context_limit else "160k"

# Progress bar blocks (0-10)
filled_blocks = min(progress_pct_int // 10, 10)
empty_blocks = 10 - filled_blocks

# Ayu Dark colors (referencing from memory)
# TODO: Verify Ayu Dark code conversions
if progress_pct_int < 50: bar_color =  green
elif progress_pct_int < 80: bar_color = orange
else: bar_color = red
#!<

#!> Construct progress bar string
# Build progress bar string
progress_bar = []
progress_bar.append(bar_color + ("█" * filled_blocks))
progress_bar.append(gray + ("░" * empty_blocks))
progress_bar.append(reset + f" {l_gray}{progress_pct}% ({formatted_tokens}/{formatted_limit}){reset}")

progress_bar_str = "".join(progress_bar)
#!<
##-##

## ===== CURRENT TASK ===== ##
curr_task = STATE.current_task.name if STATE else None
##-##

## ===== CURRENT MODE ===== ##
curr_mode = "Implementation" if STATE.mode == Mode.GO else "Discussion"
##-##

## ===== COUNT EDITED & UNCOMMITTED ===== ##
# Use subprocess to count edited and uncommitted files (unstaged or staged)
if cwd == str(PROJECT_ROOT): git_path = PROJECT_ROOT / ".git"
else: git_path = find_git_repo(Path(cwd))
total_edited = 0
if git_path and git_path.exists():
    try:
        # Count unstaged changes
        unstaged_cmd = ["git", "--git-dir", str(git_path), "--work-tree", str(cwd), "diff", "--name-only"]
        unstaged_files = subprocess.check_output(unstaged_cmd).decode().strip().split('\n')
        unstaged_count = len([f for f in unstaged_files if f])  # Filter out empty strings

        # Count staged changes
        staged_cmd = ["git", "--git-dir", str(git_path), "--work-tree", str(cwd), "diff", "--cached", "--name-only"]
        staged_files = subprocess.check_output(staged_cmd).decode().strip().split('\n')
        staged_count = len([f for f in staged_files if f])  # Filter out empty strings

        total_edited = unstaged_count + staged_count
    except: total_edited = 0
##-##

## ===== COUNT OPEN TASKS ===== ##
open_task_count = 0
open_task_dir_count = 0

if task_dir.exists() and task_dir.is_dir():
    for file in task_dir.iterdir():
        if file.is_file() and file.name != "TEMPLATE.md" and file.suffix == ".md": open_task_count += 1
        if file.is_dir() and file.name != "done": open_task_dir_count += 1
##-##

## ===== FINAL OUTPUT ===== ##
# Line 1
context_part = progress_bar_str if progress_bar_str else f"{gray}No context usage data{reset}"
task_part = f"{cyan}Task: {curr_task}{reset}" if curr_task else f"{cyan}Task: {gray}None loaded{reset}"
print(context_part + " | " + task_part)

# Line 2 - Mode | Edited & Uncommitted (trunc) | Open Tasks
print(f"{purple}Mode: {curr_mode}{reset}" + " | " + f"{orange}✎ {total_edited} files to commit{reset}" + " | " + f"{cyan}Open Tasks: {open_task_count + open_task_dir_count}{reset}")
##-##

#-#

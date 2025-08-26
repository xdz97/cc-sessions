#!/usr/bin/env python3
"""Post-tool-use hook to remind about DAIC command in implementation mode."""
import json
import sys
from shared_state import check_daic_mode_bool

# Load input
input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
cwd = input_data.get("cwd", "")

# Check current mode
discussion_mode = check_daic_mode_bool()

# Only remind if in implementation mode
implementation_tools = ["Bash", "Write", "Edit", "MultiEdit"]
if not discussion_mode and tool_name in implementation_tools:
    # Output reminder
    print("[DAIC Reminder] When you're done implementing, run: daic", file=sys.stderr)

# Check for cd command in Bash operations
if tool_name == "Bash":
    command = tool_input.get("command", "")
    if "cd " in command:
        print(f"[CWD: {cwd}]", file=sys.stderr)

sys.exit(2)  # Exit code 2 feeds stderr back to Claude
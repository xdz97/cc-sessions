#!/usr/bin/env python3
"""Pre-tool-use hook to enforce DAIC (Discussion, Alignment, Implementation, Check) workflow and branch consistency."""
import json
import sys
import subprocess
from pathlib import Path
from shared_state import check_daic_mode_bool, get_task_state, get_project_root

# Load configuration from project's .claude directory
PROJECT_ROOT = get_project_root()
CONFIG_FILE = PROJECT_ROOT / "sessions" / "sessions-config.json"

# Default configuration (used if config file doesn't exist)
DEFAULT_CONFIG = {
    "trigger_phrases": ["make it so", "run that"],
    "blocked_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
    "branch_enforcement": {
        "enabled": True,
        "task_prefixes": ["implement-", "fix-", "refactor-", "migrate-", "test-", "docs-"],
        "branch_prefixes": {
            "implement-": "feature/",
            "fix-": "fix/",
            "refactor-": "feature/",
            "migrate-": "feature/",
            "test-": "feature/",
            "docs-": "feature/"
        }
    },
    "read_only_bash_commands": [
        "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
        "grep", "rg", "find", "which", "whereis", "type", "file", "stat",
        "du", "df", "tree", "basename", "dirname", "realpath", "readlink",
        "whoami", "env", "printenv", "date", "cal", "uptime", "ps", "top",
        "wc", "cut", "sort", "uniq", "comm", "diff", "cmp", "md5sum", "sha256sum",
        "git status", "git log", "git diff", "git show", "git branch", 
        "git remote", "git fetch", "git describe", "git rev-parse", "git blame",
        "docker ps", "docker images", "docker logs", "npm list", "npm ls",
        "pip list", "pip show", "yarn list", "curl", "wget", "jq", "awk",
        "sed -n", "tar -t", "unzip -l"
    ]
}

def load_config():
    """Load configuration from file or use defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG

def find_git_repo(path: Path) -> Path:
    """Walk up directory tree to find .git directory."""
    current = path if path.is_dir() else path.parent
    
    while current.parent != current:  # Stop at filesystem root
        if (current / ".git").exists():
            return current
        current = current.parent
    return None

# Load input
input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

# Load configuration
config = load_config()

# For Bash commands, check if it's a read-only operation
if tool_name == "Bash":
    command = tool_input.get("command", "").strip()
    
    # Check for write patterns
    import re
    write_patterns = [
        r'>\s*[^>]',  # Output redirection
        r'>>',         # Append redirection
        r'\btee\b',    # tee command
        r'\bmv\b',     # move/rename
        r'\bcp\b',     # copy
        r'\brm\b',     # remove
        r'\bmkdir\b',  # make directory
        r'\btouch\b',  # create/update file
        r'\bsed\s+(?!-n)',  # sed without -n flag
        r'\bnpm\s+install',  # npm install
        r'\bpip\s+install',  # pip install
        r'\bapt\s+install',  # apt install
        r'\byum\s+install',  # yum install
        r'\bbrew\s+install',  # brew install
    ]
    
    has_write_pattern = any(re.search(pattern, command) for pattern in write_patterns)
    
    if not has_write_pattern:
        # Check if ALL commands in chain are read-only
        command_parts = re.split(r'(?:&&|\|\||;|\|)', command)
        all_read_only = True
        
        for part in command_parts:
            part = part.strip()
            if not part:
                continue
            
            # Check against configured read-only commands
            is_part_read_only = any(
                part.startswith(prefix) 
                for prefix in config.get("read_only_bash_commands", DEFAULT_CONFIG["read_only_bash_commands"])
            )
            
            if not is_part_read_only:
                all_read_only = False
                break
        
        if all_read_only:
            # Allow read-only commands without checks
            sys.exit(0)

# Check current mode
discussion_mode = check_daic_mode_bool()

# Block configured tools in discussion mode
if discussion_mode and tool_name in config.get("blocked_tools", DEFAULT_CONFIG["blocked_tools"]):
    print(f"[DAIC: Tool Blocked] You're in discussion mode. The {tool_name} tool is not allowed. You need to seek alignment first.", file=sys.stderr)
    sys.exit(2)  # Block with feedback

# Branch enforcement for Write/Edit/MultiEdit tools (if enabled)
branch_config = config.get("branch_enforcement", DEFAULT_CONFIG["branch_enforcement"])
if branch_config.get("enabled", True) and tool_name in ["Write", "Edit", "MultiEdit"]:
    # Get the file path being edited
    file_path = tool_input.get("file_path", "")
    if file_path:
        file_path = Path(file_path)
        
        # Get current task state
        task_state = get_task_state()
        expected_branch = task_state.get("branch")
        affected_services = task_state.get("services", [])
        
        if expected_branch:
            # Find the git repo for this file
            repo_path = find_git_repo(file_path)
            
            if repo_path:
                try:
                    # Get current branch
                    result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    current_branch = result.stdout.strip()
                    
                    # Get project root (parent of .claude directory)
                    project_root = Path.cwd()
                    while project_root.parent != project_root:
                        if (project_root / ".claude").exists():
                            break
                        project_root = project_root.parent
                    
                    # Check if we're in a submodule
                    if repo_path != project_root and repo_path.is_relative_to(project_root):
                        # We're in a submodule
                        service_name = repo_path.name
                        
                        if current_branch != expected_branch:
                            if service_name in affected_services:
                                print(f"[Branch Mismatch] Service '{service_name}' is on branch '{current_branch}' but should be on '{expected_branch}'. Please checkout the correct branch.", file=sys.stderr)
                                sys.exit(2)
                            else:
                                print(f"[New Service Detected] Service '{service_name}' isn't in the task's affected services. Please update the task file if this service should be included.", file=sys.stderr)
                                sys.exit(2)
                    else:
                        # Single repo or main repo
                        if current_branch != expected_branch:
                            print(f"[Branch Mismatch] Repository is on branch '{current_branch}' but task expects '{expected_branch}'. Please checkout the correct branch.", file=sys.stderr)
                            sys.exit(2)
                            
                except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                    # Can't check branch, allow to proceed but warn
                    print(f"Warning: Could not verify branch: {e}", file=sys.stderr)

# Allow tool to proceed
sys.exit(0)
#!/usr/bin/env python3
"""
Learning Commands

API commands for managing the learning system:
- List topics
- Show topic details
- Add new topics
- Manually trigger learning recording
- Show relevant topics for current context
"""

# ===== IMPORTS ===== #
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add hooks to path for imports
import os
if 'CLAUDE_PROJECT_DIR' in os.environ:
    sessions_path = os.path.join(os.environ['CLAUDE_PROJECT_DIR'], 'sessions')
    hooks_path = os.path.join(sessions_path, 'hooks')
    if hooks_path not in sys.path:
        sys.path.insert(0, hooks_path)

try:
    from shared_state import load_state, edit_state, PROJECT_ROOT
    from learnings_helpers import (
        ensure_learnings_structure,
        list_all_topics,
        get_topic_info,
        add_topic,
        detect_relevant_topics,
        load_topic_patterns,
        load_topic_gotchas,
        load_topic_history,
        format_learnings_for_protocol,
        LEARNINGS_DIR
    )
    from codebase_scanner import (
        scan_codebase,
        convert_scan_to_learnings,
        format_scan_report
    )
except ImportError:
    # Fallback to package imports
    from cc_sessions.python.hooks.shared_state import load_state, edit_state, PROJECT_ROOT
    from cc_sessions.python.hooks.learnings_helpers import (
        ensure_learnings_structure,
        list_all_topics,
        get_topic_info,
        add_topic,
        detect_relevant_topics,
        load_topic_patterns,
        load_topic_gotchas,
        load_topic_history,
        format_learnings_for_protocol,
        LEARNINGS_DIR
    )
    from cc_sessions.python.hooks.codebase_scanner import (
        scan_codebase,
        convert_scan_to_learnings,
        format_scan_report
    )

# ===== COMMANDS ===== #

def cmd_list_topics(args: List[str], json_output: bool = False) -> None:
    """List all available learning topics"""
    ensure_learnings_structure()
    topics = list_all_topics()

    if json_output:
        output = {"topics": []}
        for topic in topics:
            info = get_topic_info(topic)
            if info:
                output["topics"].append({
                    "name": topic,
                    "description": info.get("description", ""),
                    "keywords": info.get("keywords", []),
                    "last_updated": info.get("last_updated")
                })
        print(json.dumps(output, indent=2))
    else:
        if not topics:
            print("No learning topics found. Run 'sessions learnings init' to create default topics.")
            return

        print("📚 Available Learning Topics:\n")
        for topic in topics:
            info = get_topic_info(topic)
            if info:
                print(f"  • {topic}")
                print(f"    {info.get('description', 'No description')}")
                if info.get('keywords'):
                    keywords = ', '.join(info['keywords'][:5])
                    print(f"    Keywords: {keywords}")
                print()

def cmd_show_topic(args: List[str], json_output: bool = False) -> None:
    """Show detailed information about a specific topic"""
    if not args:
        print("Error: Topic name required", file=sys.stderr)
        print("Usage: sessions learnings show <topic>", file=sys.stderr)
        sys.exit(1)

    topic = args[0]
    info = get_topic_info(topic)

    if not info:
        print(f"Error: Topic '{topic}' not found", file=sys.stderr)
        print("Run 'sessions learnings list' to see available topics", file=sys.stderr)
        sys.exit(1)

    patterns = load_topic_patterns(topic)
    gotchas = load_topic_gotchas(topic)
    history = load_topic_history(topic)

    if json_output:
        output = {
            "topic": topic,
            "info": info,
            "patterns": patterns,
            "gotchas": gotchas,
            "history": history
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"📚 Learning Topic: {topic}\n")
        print(f"Description: {info.get('description', 'No description')}\n")

        if info.get('keywords'):
            print(f"Keywords: {', '.join(info['keywords'])}\n")

        if info.get('file_patterns'):
            print(f"File Patterns: {', '.join(info['file_patterns'])}\n")

        if info.get('related_topics'):
            print(f"Related Topics: {', '.join(info['related_topics'])}\n")

        # Patterns
        successful = patterns.get("successful_patterns", [])
        if successful:
            print(f"\n✓ Successful Patterns ({len(successful)}):")
            for p in successful[:5]:  # Show top 5
                print(f"  • {p.get('name', 'Unnamed')}: {p.get('description', 'No description')}")
                if p.get('use_count'):
                    print(f"    Used {p['use_count']} times, success rate: {p.get('success_rate', 1.0):.0%}")

        anti = patterns.get("anti_patterns", [])
        if anti:
            print(f"\n✗ Anti-Patterns ({len(anti)}):")
            for p in anti[:5]:
                print(f"  • {p.get('name', 'Unnamed')}: {p.get('problem', 'No description')}")

        # Gotchas
        file_gotchas = gotchas.get("file_specific", {})
        general_gotchas = gotchas.get("general_gotchas", [])

        if file_gotchas or general_gotchas:
            print(f"\n⚠️  Known Gotchas:")
            for file_path, issues in list(file_gotchas.items())[:3]:
                for issue in issues:
                    print(f"  • {file_path}:{issue.get('line_range', '??')}: {issue['issue']}")
            for gotcha in general_gotchas[:3]:
                print(f"  • {gotcha.get('issue', 'No description')}")

        # History
        tasks = history.get("tasks_completed", [])
        errors = history.get("common_errors", {})

        if tasks:
            print(f"\n📊 History: {len(tasks)} tasks completed")
            if errors:
                print(f"Common errors: {', '.join(list(errors.keys())[:3])}")

        print(f"\nLast updated: {info.get('last_updated', 'Never')}")

def cmd_add_topic(args: List[str], json_output: bool = False) -> None:
    """Add a new learning topic"""
    if len(args) < 2:
        print("Error: Topic name and description required", file=sys.stderr)
        print("Usage: sessions learnings add <topic> <description> [keywords...]", file=sys.stderr)
        sys.exit(1)

    topic_name = args[0]
    description = args[1]
    keywords = args[2:] if len(args) > 2 else []

    # Generate default file patterns based on topic name
    file_patterns = [f"**/{topic_name}/*", f"**/*_{topic_name}.py", f"**/*{topic_name.capitalize()}*.ts"]

    success = add_topic(topic_name, description, keywords, file_patterns)

    if json_output:
        print(json.dumps({"success": success, "topic": topic_name}))
    else:
        if success:
            print(f"✓ Added new learning topic: {topic_name}")
            print(f"  Description: {description}")
            if keywords:
                print(f"  Keywords: {', '.join(keywords)}")
            print(f"\nTopic directory created at: sessions/learnings/{topic_name}/")
        else:
            print(f"Error: Topic '{topic_name}' already exists", file=sys.stderr)
            sys.exit(1)

def cmd_relevant_topics(args: List[str], json_output: bool = False) -> None:
    """Show topics relevant to current task or context"""
    ensure_learnings_structure()
    state = load_state()

    task_content = ""
    file_paths = []

    # Get task content if there's an active task
    if state.current_task.file:
        task_file = state.current_task.file_path
        if task_file and task_file.exists():
            task_content = task_file.read_text(encoding="utf-8")

    # Detect relevant topics
    topics = detect_relevant_topics(task_content, file_paths)

    if json_output:
        print(json.dumps({"relevant_topics": topics}))
    else:
        if not topics:
            print("No relevant topics detected for current context.")
            print("Topics are detected based on task content and file patterns.")
            return

        print("📚 Relevant Learning Topics:\n")
        for i, topic in enumerate(topics, 1):
            info = get_topic_info(topic)
            print(f"{i}. {topic}")
            if info:
                print(f"   {info.get('description', '')}")
        print(f"\nUse 'sessions learnings show <topic>' to see detailed learnings.")

def cmd_record_learnings(args: List[str], json_output: bool = False) -> None:
    """Manually trigger learning recording for current task"""
    state = load_state()

    if not state.current_task.file:
        print("Error: No active task", file=sys.stderr)
        print("Start a task with 'sessions tasks start' first", file=sys.stderr)
        sys.exit(1)

    # This would typically be called by the task-completion protocol
    # For manual invocation, we'll provide instructions

    if json_output:
        print(json.dumps({"status": "not_implemented", "message": "Manual learning recording not yet implemented"}))
    else:
        print("Manual learning recording is typically triggered automatically during task completion.")
        print("\nTo record learnings manually:")
        print("1. Ensure your task is complete and committed")
        print("2. Use the Task tool to invoke the learning-recorder agent:")
        print(f"   Task(subagent_type='learning-recorder', prompt='Record learnings for {state.current_task.file}')")
        print("\nThe agent will analyze your changes and update the learning database.")

def cmd_init_learnings(args: List[str], json_output: bool = False) -> None:
    """Initialize the learning system with default topics"""
    from datetime import datetime, timezone

    # Check for --scan flag
    scan_codebase_flag = "--scan" in args
    if scan_codebase_flag:
        args.remove("--scan")

    ensure_learnings_structure()

    # If scan flag, analyze codebase and populate learnings
    if scan_codebase_flag:
        if not json_output:
            print("🔍 Scanning codebase...")
            print("This may take a moment for large projects...\n")

        # Scan the codebase
        scan_results = scan_codebase(max_files=500)

        # Convert to learnings format
        learnings_data = convert_scan_to_learnings(scan_results)

        # Save learnings to files
        timestamp = datetime.now(timezone.utc).isoformat()
        patterns_added = 0
        gotchas_added = 0

        for topic, data in learnings_data.items():
            topic_dir = LEARNINGS_DIR / topic
            if not topic_dir.exists():
                continue

            # Update patterns file
            patterns_file = topic_dir / "patterns.json"
            if patterns_file.exists():
                patterns_json = json.loads(patterns_file.read_text(encoding="utf-8"))

                # Add discovered patterns
                for pattern in data["patterns"]:
                    pattern["discovered_at"] = timestamp
                    patterns_json["successful_patterns"].append(pattern)
                    patterns_added += 1

                patterns_file.write_text(json.dumps(patterns_json, indent=2), encoding="utf-8")

            # Update gotchas file
            gotchas_file = topic_dir / "gotchas.json"
            if gotchas_file.exists() and data["gotchas"]:
                gotchas_json = json.loads(gotchas_file.read_text(encoding="utf-8"))

                # Add discovered gotchas
                for gotcha in data["gotchas"]:
                    gotcha["discovered"] = timestamp
                    gotchas_json["general_gotchas"].append(gotcha)
                    gotchas_added += 1

                gotchas_file.write_text(json.dumps(gotchas_json, indent=2), encoding="utf-8")

        if json_output:
            print(json.dumps({
                "status": "initialized_with_scan",
                "topics": list_all_topics(),
                "scan_results": scan_results,
                "patterns_added": patterns_added,
                "gotchas_added": gotchas_added
            }, indent=2))
        else:
            # Print scan report
            print(format_scan_report(scan_results))
            print(f"\n{'='*60}")
            print("✓ Learning system initialized with codebase scan")
            print(f"\n📚 Pre-populated learnings:")
            print(f"  • {patterns_added} patterns discovered")
            print(f"  • {gotchas_added} potential gotchas identified")
            print(f"\nLearning directory: sessions/learnings/")
            print("Run 'sessions learnings list' to see all topics.")
            print("Run 'sessions learnings show <topic>' to see discovered patterns.")
    else:
        # Standard init without scan
        if json_output:
            print(json.dumps({"status": "initialized", "topics": list_all_topics()}))
        else:
            topics = list_all_topics()
            print("✓ Learning system initialized")
            print(f"\nCreated {len(topics)} default topics:")
            for topic in topics:
                print(f"  • {topic}")
            print(f"\nLearning directory: sessions/learnings/")
            print("\n💡 Tip: Use 'sessions learnings init --scan' to analyze your codebase")
            print("   and pre-populate learnings with discovered patterns.")
            print("\nRun 'sessions learnings list' to see all topics.")

def cmd_enable_learnings(args: List[str], json_output: bool = False) -> None:
    """Enable the learning system"""
    with edit_state() as state:
        state.learnings.enabled = True

    if json_output:
        print(json.dumps({"status": "enabled"}))
    else:
        print("✓ Learning system enabled")
        print("Learnings will be automatically loaded during task startup.")

def cmd_disable_learnings(args: List[str], json_output: bool = False) -> None:
    """Disable the learning system"""
    with edit_state() as state:
        state.learnings.enabled = False

    if json_output:
        print(json.dumps({"status": "disabled"}))
    else:
        print("✓ Learning system disabled")
        print("Learnings will not be loaded during task startup.")

def cmd_status(args: List[str], json_output: bool = False) -> None:
    """Show learning system status"""
    ensure_learnings_structure()
    state = load_state()
    topics = list_all_topics()

    if json_output:
        output = {
            "enabled": state.learnings.enabled,
            "auto_load": state.learnings.auto_load,
            "total_topics": len(topics),
            "active_topics": state.learnings.active_topics,
            "loaded_patterns": len(state.learnings.loaded_patterns)
        }
        print(json.dumps(output, indent=2))
    else:
        status = "enabled" if state.learnings.enabled else "disabled"
        print(f"Learning System: {status}")
        print(f"Auto-load: {'enabled' if state.learnings.auto_load else 'disabled'}")
        print(f"\nTotal topics: {len(topics)}")

        if state.learnings.active_topics:
            print(f"Active topics: {', '.join(state.learnings.active_topics)}")
            print(f"Loaded patterns: {len(state.learnings.loaded_patterns)}")
        else:
            print("No active topics (none loaded yet)")

        print(f"\nLearning directory: {LEARNINGS_DIR}")

# ===== ROUTER ===== #

LEARNING_COMMANDS = {
    "list": cmd_list_topics,
    "show": cmd_show_topic,
    "add": cmd_add_topic,
    "relevant": cmd_relevant_topics,
    "record": cmd_record_learnings,
    "init": cmd_init_learnings,
    "enable": cmd_enable_learnings,
    "disable": cmd_disable_learnings,
    "status": cmd_status,
}

def route_learning_command(subcmd: str, args: List[str], json_output: bool = False) -> None:
    """Route learning subcommands"""
    if subcmd not in LEARNING_COMMANDS:
        print(f"Error: Unknown learnings subcommand: {subcmd}", file=sys.stderr)
        print(f"Available commands: {', '.join(LEARNING_COMMANDS.keys())}", file=sys.stderr)
        sys.exit(1)

    LEARNING_COMMANDS[subcmd](args, json_output)

if __name__ == "__main__":
    # Allow direct invocation for testing
    if len(sys.argv) < 2:
        print("Usage: learning_commands.py <subcommand> [args...]", file=sys.stderr)
        sys.exit(1)

    subcmd = sys.argv[1]
    args = sys.argv[2:]
    json_flag = "--json" in args
    if json_flag:
        args.remove("--json")

    route_learning_command(subcmd, args, json_flag)

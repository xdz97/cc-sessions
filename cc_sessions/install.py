#!/usr/bin/env python3
"""
Claude Code Sessions Framework - Python Installer
Cross-platform installation script for the Sessions framework
"""

import os
import sys
import json
import shutil
import stat
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Colors for terminal output
class Colors:
    RESET = '\033[0m'
    BRIGHT = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'

def color(text: str, color_code: str) -> str:
    """Colorize text for terminal output"""
    return f"{color_code}{text}{Colors.RESET}"

def command_exists(command: str) -> bool:
    """Check if a command exists in the system"""
    return shutil.which(command) is not None

def get_package_dir() -> Path:
    """Get the directory where the package is installed"""
    import cc_sessions
    return Path(cc_sessions.__file__).parent

class SessionsInstaller:
    def __init__(self):
        self.package_dir = get_package_dir()
        self.project_root = Path.cwd()
        self.config = {
            "developer_name": "the developer",
            "trigger_phrases": ["make it so", "run that", "go ahead", "yert"],
            "blocked_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
            "task_detection": {"enabled": True},
            "branch_enforcement": {"enabled": True}
        }
    
    def check_dependencies(self) -> None:
        """Check for required dependencies"""
        print(color("Checking dependencies...", Colors.CYAN))
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(color("❌ Python 3.8+ is required.", Colors.RED))
            sys.exit(1)
        
        # Check pip
        if not command_exists("pip3") and not command_exists("pip"):
            print(color("❌ pip is required but not installed.", Colors.RED))
            sys.exit(1)
        
        # Check Git (warning only)
        if not command_exists("git"):
            print(color("⚠️  Warning: Git not found. Sessions works best with git.", Colors.YELLOW))
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    def create_directories(self) -> None:
        """Create necessary directory structure"""
        print(color("Creating directory structure...", Colors.CYAN))
        
        dirs = [
            ".claude/hooks",
            ".claude/state", 
            ".claude/agents",
            "sessions/tasks/done",
            "sessions/protocols",
            "sessions/agents",
            "sessions/knowledge"
        ]
        
        for dir_path in dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)
    
    def install_python_deps(self) -> None:
        """Install Python dependencies"""
        print(color("Installing Python dependencies...", Colors.CYAN))
        try:
            pip_cmd = "pip3" if command_exists("pip3") else "pip"
            subprocess.run([pip_cmd, "install", "tiktoken", "--quiet"], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            print(color("⚠️  Could not install tiktoken. You may need to install it manually.", Colors.YELLOW))
    
    def copy_files(self) -> None:
        """Copy all necessary files to the project"""
        # Copy hooks
        print(color("Installing hooks...", Colors.CYAN))
        hooks_dir = self.package_dir / "hooks"
        if hooks_dir.exists():
            for hook_file in hooks_dir.glob("*.py"):
                dest = self.project_root / ".claude/hooks" / hook_file.name
                shutil.copy2(hook_file, dest)
                dest.chmod(0o755)
        
        # Copy protocols
        print(color("Installing protocols...", Colors.CYAN))
        protocols_dir = self.package_dir / "protocols"
        if protocols_dir.exists():
            for protocol_file in protocols_dir.glob("*.md"):
                dest = self.project_root / "sessions/protocols" / protocol_file.name
                shutil.copy2(protocol_file, dest)
        
        # Copy agents
        print(color("Installing agent definitions...", Colors.CYAN))
        agents_dir = self.package_dir / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                dest = self.project_root / ".claude/agents" / agent_file.name
                shutil.copy2(agent_file, dest)
        
        # Copy templates
        print(color("Installing templates...", Colors.CYAN))
        template_file = self.package_dir / "templates/TEMPLATE.md"
        if template_file.exists():
            dest = self.project_root / "sessions/tasks/TEMPLATE.md"
            shutil.copy2(template_file, dest)
        
        # Copy knowledge files
        knowledge_dir = self.package_dir / "knowledge/claude-code"
        if knowledge_dir.exists():
            print(color("Installing Claude Code knowledge base...", Colors.CYAN))
            dest_dir = self.project_root / "sessions/knowledge/claude-code"
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(knowledge_dir, dest_dir)
    
    def install_daic_command(self) -> None:
        """Install the daic command globally"""
        print(color("Installing daic command...", Colors.CYAN))
        
        daic_source = self.package_dir / "scripts/daic"
        if not daic_source.exists():
            print(color("⚠️  daic script not found in package.", Colors.YELLOW))
            return
        
        daic_dest = Path("/usr/local/bin/daic")
        
        try:
            shutil.copy2(daic_source, daic_dest)
            daic_dest.chmod(0o755)
        except PermissionError:
            print(color("⚠️  Cannot write to /usr/local/bin. Trying with sudo...", Colors.YELLOW))
            try:
                subprocess.run(["sudo", "cp", str(daic_source), str(daic_dest)], check=True)
                subprocess.run(["sudo", "chmod", "+x", str(daic_dest)], check=True)
            except subprocess.CalledProcessError:
                print(color("⚠️  Could not install daic command globally.", Colors.YELLOW))
    
    def configure(self) -> None:
        """Interactive configuration"""
        print()
        print(color("═══════════════════════════════════════════", Colors.BRIGHT))
        print(color("           Configuration Setup", Colors.BRIGHT))
        print(color("═══════════════════════════════════════════", Colors.BRIGHT))
        print()
        
        # Developer name
        name = input("Your name (for session context): ")
        if name:
            self.config["developer_name"] = name
        
        # Statusline installation
        print()
        print(color("Statusline Installation:", Colors.CYAN))
        print("The sessions system includes a statusline script that shows:")
        print("- Current task and DAIC mode")
        print("- Token usage and warnings")
        print("- File change counts")
        print()
        
        install_statusline = input("Install sessions statusline? (y/n): ")
        
        if install_statusline.lower() == 'y':
            statusline_source = self.package_dir / "scripts/statusline-script.sh"
            if statusline_source.exists():
                print(color("Installing statusline script...", Colors.CYAN))
                statusline_dest = self.project_root / ".claude/statusline-script.sh"
                shutil.copy2(statusline_source, statusline_dest)
                statusline_dest.chmod(0o755)
                
                # Create project-level settings.json
                settings = {
                    "statusLine": {
                        "type": "command",
                        "command": "$CLAUDE_PROJECT_DIR/.claude/statusline-script.sh",
                        "padding": 0
                    }
                }
                
                settings_file = self.project_root / ".claude/settings.json"
                settings_file.write_text(json.dumps(settings, indent=2))
                
                print(color("✅ Statusline installed and configured automatically", Colors.GREEN))
            else:
                print(color("⚠️  Statusline script not found in package.", Colors.YELLOW))
        
        # DAIC trigger phrases
        print()
        print(color("DAIC (Discussion, Alignment, Implementation, Check) System:", Colors.CYAN))
        print("By default, Claude will discuss before implementing.")
        print("Trigger phrases switch to implementation mode.")
        print()
        print(f"Default triggers: {', '.join(self.config['trigger_phrases'])}")
        
        custom_trigger = input("Add custom trigger phrase (or press Enter to skip): ")
        if custom_trigger:
            self.config["trigger_phrases"].append(custom_trigger)
        
        # Advanced configuration
        print()
        advanced = input("Configure advanced options? (y/n): ")
        
        if advanced.lower() == 'y':
            # Tool blocking
            print()
            print(color("Tool Blocking Configuration:", Colors.CYAN))
            print(f"Current blocked tools: {', '.join(self.config['blocked_tools'])}")
            modify_tools = input("Modify blocked tools list? (y/n): ")
            
            if modify_tools.lower() == 'y':
                custom_blocked = input("Enter comma-separated list of tools to block: ")
                if custom_blocked:
                    self.config["blocked_tools"] = [t.strip() for t in custom_blocked.split(',')]
    
    def save_config(self) -> None:
        """Save configuration files"""
        print(color("Creating configuration...", Colors.CYAN))
        
        # Save sessions config
        config_file = self.project_root / ".claude/sessions-config.json"
        config_file.write_text(json.dumps(self.config, indent=2))
        
        # Initialize DAIC state
        daic_state = self.project_root / ".claude/state/daic-mode.json"
        daic_state.write_text(json.dumps({"mode": "discussion"}, indent=2))
        
        # Create initial task state
        current_date = datetime.now().strftime("%Y-%m-%d")
        task_state = self.project_root / ".claude/state/current_task.json"
        task_state.write_text(json.dumps({
            "task": None,
            "branch": None,
            "services": [],
            "updated": current_date
        }, indent=2))
    
    def setup_claude_md(self) -> None:
        """Set up CLAUDE.md integration"""
        print()
        print(color("═══════════════════════════════════════════", Colors.BRIGHT))
        print(color("         CLAUDE.md Integration", Colors.BRIGHT))
        print(color("═══════════════════════════════════════════", Colors.BRIGHT))
        print()
        
        print("The sessions system is designed to preserve context by loading only")
        print("what's needed for the current task. Keep your root CLAUDE.md minimal")
        print("with project overview and behavioral rules. Task-specific context is")
        print("loaded dynamically through the sessions system.")
        print()
        print("Your CLAUDE.md should be < 100 lines. Detailed documentation belongs")
        print("in task context manifests, not the root file.")
        print()
        
        # Copy CLAUDE.sessions.md to project root
        print(color("Installing CLAUDE.sessions.md...", Colors.CYAN))
        sessions_md = self.package_dir / "templates/CLAUDE.sessions.md"
        if sessions_md.exists():
            dest = self.project_root / "CLAUDE.sessions.md"
            shutil.copy2(sessions_md, dest)
        
        # Check for existing CLAUDE.md
        claude_md = self.project_root / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            if "@CLAUDE.sessions.md" not in content:
                print(color("Adding sessions include to existing CLAUDE.md...", Colors.CYAN))
                
                addition = "\n## Sessions System Behaviors\n\n@CLAUDE.sessions.md\n"
                with claude_md.open("a") as f:
                    f.write(addition)
                
                print(color("✅ Added @CLAUDE.sessions.md include to your CLAUDE.md", Colors.GREEN))
                print()
                print(color("⚠️  Please review your CLAUDE.md and consider:", Colors.YELLOW))
                print("   - Moving detailed documentation to task context manifests")
                print("   - Keeping only project overview and core rules")
                print("   - See CLAUDE.example.md for best practices")
            else:
                print(color("✅ CLAUDE.md already includes sessions behaviors", Colors.GREEN))
        else:
            # Create from template
            print(color("Creating CLAUDE.md from template...", Colors.CYAN))
            example_md = self.package_dir / "templates/CLAUDE.example.md"
            if example_md.exists():
                shutil.copy2(example_md, claude_md)
                print(color("✅ CLAUDE.md created from best practice template", Colors.GREEN))
                print("   Please customize the project overview section")
    
    def run(self) -> None:
        """Run the full installation process"""
        print(color("╔══════════════════════════════════════════╗", Colors.BRIGHT))
        print(color("║    Claude Code Sessions Installer       ║", Colors.BRIGHT))
        print(color("╚══════════════════════════════════════════╝", Colors.BRIGHT))
        print()
        
        # Check CLAUDE_PROJECT_DIR
        if not os.environ.get("CLAUDE_PROJECT_DIR"):
            print(color(f"⚠️  CLAUDE_PROJECT_DIR not set. Setting it to {self.project_root}", Colors.YELLOW))
            print("   To make this permanent, add to your shell profile:")
            print(f'   export CLAUDE_PROJECT_DIR="{self.project_root}"')
            print()
        
        try:
            self.check_dependencies()
            self.create_directories()
            self.install_python_deps()
            self.copy_files()
            self.install_daic_command()
            self.configure()
            self.save_config()
            self.setup_claude_md()
            
            # Success message
            print()
            print(color("═══════════════════════════════════════════", Colors.BRIGHT))
            print(color("          Installation Complete!", Colors.BRIGHT))
            print(color("═══════════════════════════════════════════", Colors.BRIGHT))
            print()
            
            print(color("✅ Directory structure created", Colors.GREEN))
            print(color("✅ Hooks installed", Colors.GREEN))
            print(color("✅ Protocols and agents installed", Colors.GREEN))
            print(color("✅ daic command available", Colors.GREEN))
            print(color("✅ Configuration saved", Colors.GREEN))
            print(color("✅ DAIC state initialized (Discussion mode)", Colors.GREEN))
            print()
            
            # Test daic command
            if command_exists("daic"):
                print(color("Testing daic command...", Colors.CYAN))
                print(color("✅ daic command working", Colors.GREEN))
            else:
                print(color("⚠️  daic command not in PATH. Add /usr/local/bin to your PATH.", Colors.YELLOW))
            
            print()
            print(color("Next steps:", Colors.CYAN))
            print("1. Restart Claude Code to load the hooks")
            print("2. Create your first task:")
            print('   Tell Claude: "Create a task using @sessions/protocols/task-creation.md"')
            print("3. Start working with DAIC workflow!")
            print()
            print(f"Developer: {self.config['developer_name']}")
            
        except Exception as e:
            print(color(f"❌ Installation failed: {e}", Colors.RED))
            sys.exit(1)

def main():
    """Main entry point for the installer"""
    installer = SessionsInstaller()
    installer.run()

def install():
    """Alias for main() for compatibility"""
    main()

if __name__ == "__main__":
    main()
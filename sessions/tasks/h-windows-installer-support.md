---
task: h-windows-installer-support
branch: fix/windows-installer-support
status: in-progress
created: 2025-08-28
started: 2025-08-28
modules: [cc_sessions/install.py, cc_sessions/hooks, package.json, pyproject.toml, npm-installer.js]
---

# Windows Installer Support

## Problem/Goal
The Python (pip/pipx) and Node.js (npm) installers for cc-sessions currently don't work on Windows. Need to add proper Windows platform detection, path handling, and shell command compatibility.

## Success Criteria
- [ ] Python installer detects and handles Windows correctly
- [ ] Node.js npm installer works on Windows
- [ ] Installation scripts use proper path separators
- [ ] Shell commands use appropriate Windows alternatives
- [ ] Hooks work correctly on Windows systems
- [ ] Tested on Windows 10/11 with both PowerShell and Command Prompt

## Context Manifest

### How Windows Installation Currently Fails

When users attempt to install cc-sessions on Windows, multiple fundamental compatibility issues cause complete installation failure across all three installation methods (Python, Node.js, and Bash). The root problem stems from the fact that all installers were designed with Unix/POSIX assumptions and contain hard-coded Unix-specific behaviors.

**Python Installer (install.py) Failures:**

The main Python installer at `cc_sessions/install.py` fails on Windows due to several critical issues. The file copy operations use Unix permissions via `shutil.copy2()` followed by `dest.chmod(0o755)` which fails on Windows NTFS filesystems that don't support Unix octal permissions. The global `daic` command installation attempts to copy to `/usr/local/bin/daic` which doesn't exist on Windows - it should use system PATH locations like `%PROGRAMDATA%` or user-specific locations.

Path handling throughout the installer uses forward slashes and Unix conventions. For example, the hook configuration in `save_config()` uses hardcoded paths like `$CLAUDE_PROJECT_DIR/.claude/hooks/user-messages.py` which fails on Windows where environment variable expansion and path separators work differently.

The `command_exists()` function uses `shutil.which()` but doesn't account for Windows executable extensions (.exe, .bat, .cmd). Shell command execution assumes Unix commands - the git operations and pip installation calls may fail due to different command names or path resolution on Windows.

**Node.js Installer (install.js) Failures:**

The Node.js installer has similar path and permission issues. The `commandExists()` function at line 88 uses Unix `which` command via `execSync('which ${command}')` which doesn't exist on Windows - it should use `where` command instead.

File permission setting via `fs.chmod(path, 0o755)` fails on Windows. The installer attempts to copy the daic script to `/usr/local/bin/` which is Unix-specific. The interactive menu system uses terminal escape codes that may not work correctly in Windows Command Prompt (though they work in PowerShell).

Directory detection logic assumes Unix paths and may not handle Windows drive letters or UNC paths correctly. The `PROJECT_ROOT` detection could fail if running from network drives or unusual Windows filesystem layouts.

**Package Configuration Issues:**

The `package.json` explicitly excludes Windows with `"os": ["darwin", "linux", "!win32"]` at line 40, which means npm will refuse to install the package on Windows systems. The `pyproject.toml` classifiers only list "Operating System :: MacOS" and "Operating System :: POSIX :: Linux" but not Windows.

**Bash Script (install.sh) Fundamental Incompatibility:**

The bash installation script is completely incompatible with Windows unless users have WSL (Windows Subsystem for Linux) installed. Even with WSL, path translation between Windows and Linux filesystem spaces creates additional complexity.

**Hook System Windows Issues:**

The Python hooks in `cc_sessions/hooks/` contain several Windows incompatibilities. In `sessions-enforce.py`, the path checking logic at line 133 attempts to handle both forward and backslashes with `('.claude/state' in str(file_path) or '.claude\\state' in str(file_path))` but this is incomplete.

The `shared_state.py` file uses `Path.cwd()` and assumes Unix-style directory traversal. Git command execution in `sessions-enforce.py` uses subprocess with Unix assumptions about command availability and output format.

The global `daic` command script is a bash script that won't work on Windows without bash environment. It uses Unix path traversal and Python execution assumptions.

### For Windows Support Implementation

To implement proper Windows support, we need to address platform detection, path handling, permission management, command installation, and shell compatibility across all three installation methods.

**Platform Detection Strategy:**
The installers need robust platform detection using `sys.platform` (Python) and `process.platform` (Node.js). Windows-specific logic should handle different Windows versions (10, 11), different shells (PowerShell, Command Prompt), and different installation contexts (user vs system-wide).

**Path Handling Universalization:**
All path operations need to use `pathlib.Path` (Python) or `path` module (Node.js) instead of hardcoded separators. Environment variable expansion needs Windows-specific handling (`%VAR%` vs `$VAR`). UNC paths, drive letters, and Windows filesystem quirks need accommodation.

**Permission and File Operations:**
Windows doesn't use Unix octal permissions. File operations should use `os.stat` and Windows ACL when needed, or skip permission setting entirely since Windows executability is determined by file extension. The `.cmd` and `.bat` extensions should be added to scripts for Windows.

**Global Command Installation:**
Instead of `/usr/local/bin`, Windows installation should:
- Use `%PROGRAMDATA%\cc-sessions\bin` for system-wide installation
- Use `%USERPROFILE%\AppData\Local\cc-sessions\bin` for user installation  
- Add to PATH during installation
- Create both `daic.cmd` batch file and `daic.ps1` PowerShell script wrappers

**Shell Command Compatibility:**
The `daic` global command needs Windows implementations:
- `daic.cmd` batch file for Command Prompt
- `daic.ps1` PowerShell script
- Both should locate project root and execute Python appropriately

**Dependency Management:**
Windows Python may be installed as `python` rather than `python3`. Pip may be `pip` rather than `pip3`. The installers need to detect available commands and use appropriate versions.

### Technical Reference Details

#### Critical Files Requiring Windows Updates

**Primary Installers:**
- `cc_sessions/install.py` - Lines 41-42 (command detection), 186-199 (global command install), 431-451 (hook configuration), entire path handling
- `install.js` - Lines 88-95 (command detection), 241-257 (global command install), 88-95 permission setting
- `package.json` - Line 40 (OS restriction removal)

**Hook System Files:**  
- `cc_sessions/hooks/sessions-enforce.py` - Lines 133, 158-214 (subprocess calls), path handling throughout
- `cc_sessions/hooks/shared_state.py` - Path operations, directory traversal logic
- `cc_sessions/scripts/daic` - Entire file needs Windows equivalents (.cmd, .ps1)

#### Windows-Specific Implementation Requirements

**File Permission Handling:**
```python
# Instead of: dest.chmod(0o755)
if os.name != 'nt':
    dest.chmod(0o755)
# Windows executability is handled by file extension
```

**Command Detection:**
```python
def command_exists(command: str) -> bool:
    if os.name == 'nt':
        # Windows - try with common extensions
        for ext in ['', '.exe', '.bat', '.cmd']:
            if shutil.which(command + ext):
                return True
        return False
    return shutil.which(command) is not None
```

**Global Command Installation Paths:**
- Windows System: `%PROGRAMDATA%\cc-sessions\bin`  
- Windows User: `%USERPROFILE%\AppData\Local\cc-sessions\bin`
- Unix: `/usr/local/bin` (existing behavior)

**Hook Configuration Environment Variables:**
- Windows: `%CLAUDE_PROJECT_DIR%\.claude\hooks\script.py`
- Unix: `$CLAUDE_PROJECT_DIR/.claude/hooks/script.py` (existing)

#### Required New Files

**Windows daic Command Implementations:**
- `cc_sessions/scripts/daic.cmd` - Batch file for Command Prompt
- `cc_sessions/scripts/daic.ps1` - PowerShell script for PowerShell
- Both should replicate the functionality of the existing bash `daic` script

**Installation Method Verification:**
All three installation methods (pip/pipx, npm, bash) need Windows testing and verification. The npm package.json needs OS restriction removal and Windows-specific documentation.

## Context Files
<!-- Added by context-gathering agent or manually -->
- @cc_sessions/install.py  # Main Python installer - comprehensive Windows compatibility needed
- @install.js         # Node.js installer wrapper - command detection and permissions fixes needed  
- @package.json             # NPM package config - OS restriction removal needed
- @pyproject.toml           # Python package config - Windows OS classifier needed
- @cc_sessions/hooks/sessions-enforce.py # Core enforcement hook - subprocess and path fixes needed
- @cc_sessions/hooks/shared_state.py # State management - path handling fixes needed
- @cc_sessions/scripts/daic # Bash global command - Windows equivalents needed (.cmd, .ps1)
- @install.sh # Bash installer - Windows compatibility notes needed

## User Notes
<!-- Any specific notes or requirements from the developer -->
Current installers fail on Windows due to Unix-specific assumptions in paths, permissions, command detection, and global command installation. Need comprehensive cross-platform compatibility while maintaining existing Unix/Mac functionality.

## Work Log
<!-- Updated as work progresses -->
- [2025-08-28] Created task for Windows installer support
- [2025-08-28] Added comprehensive context manifest covering all Windows compatibility issues
- [2025-08-28] Fixed Python installer (install.py) with Windows path handling and daic script installation
- [2025-08-28] Fixed Node.js installer (install.js) with cross-platform command detection
- [2025-08-28] Removed Windows exclusion from package.json and added Windows OS classifier to pyproject.toml
- [2025-08-28] Created Windows-specific daic.cmd and daic.ps1 scripts for native Windows shells
- [2025-08-28] Fixed hook path handling using pathlib.Path for cross-platform compatibility
- [2025-08-28] Updated session-start.py to use shutil.which() instead of Unix 'which' command
- [2025-08-28] Added Windows commands to read-only list in sessions-enforce.py
- [2025-08-28] Removed "bash" reference from user-messages.py to be platform-agnostic
- [2025-08-28] Verified command files work with Git Bash (Claude Code's Windows shell environment)
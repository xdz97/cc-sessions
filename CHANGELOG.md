# Changelog

## [Unreleased - v0.3.0]

### Added
- **CI Environment Detection**: All hooks now automatically detect CI environments (GitHub Actions, etc.) and bypass DAIC enforcement to enable automated Claude Code agents
  - Thanks to @oppianmatt (matt@oppian.com) for the implementation guidance (#14)
- **Nerd Fonts Icons and Git Branch Display**: Enhanced statusline with Nerd Fonts icons and git branch information
  - Nerd Fonts icons for context, task, mode, open tasks, and git branch
  - Git branch display at end of line 2
  - Configurable toggle with ASCII fallback for users without Nerd Fonts
  - Thanks to @dnviti (dnviti@gmail.com) for the ideas (#21)
- **Safe Uninstaller**: Interactive uninstaller with automatic backups, dry-run mode, and user data preservation
  - Thanks to @gabelul for the uninstaller concept (#45)

## [0.2.8] - 2025-09-04

### Changed
- **No More Sudo Required**: The `daic` command no longer requires sudo for installation
- **Package Manager Integration**: `daic` is now installed as a package command:
  - Python: Automatically available when installed via pip/pipx
  - Node.js: Automatically available when installed via npm  
- **Fallback Location**: Local fallback moved from `.claude/bin` to `sessions/bin`
- **Cleaner Directory Structure**: cc-sessions specific files moved out of `.claude/` to keep it clean for Claude Code

### Added
- `cc_sessions/daic.py` - Python entry point for pip installations
- `daic.js` - Node.js entry point for npm installations
- Console scripts entry in `pyproject.toml`
- Bin entry in `package.json`

### Removed
- Sudo fallback logic from all installers
- Global `/usr/local/bin` installation attempt

## [0.2.7] - Previous Release
- Initial public release
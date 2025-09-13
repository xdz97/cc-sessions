#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from typing import Any, List, Optional, Dict
import json
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from hooks.shared_state import load_config, edit_config, TriggerCategory, GitAddPattern, GitCommitStyle, UserOS, UserShell
##-##

#-#

# ===== GLOBALS ===== #
#-#

# ===== DECLARATIONS ===== #
#-#

# ===== CLASSES ===== #
#-#

# ===== FUNCTIONS ===== #

#!> Main config handler
def handle_config_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle configuration commands.
    
    Usage:
        config                          - Show full config
        config phrases <operation>      - Manage trigger phrases
        config git <operation>          - Manage git preferences
        config env <operation>          - Manage environment settings
        config features <operation>     - Manage feature toggles
        config validate                 - Validate configuration
    """
    if not args:
        # Show full config
        config = load_config()
        if json_output:
            return config.to_dict()
        return format_config_human(config)
    
    section = args[0].lower()
    section_args = args[1:] if len(args) > 1 else []
    
    if section == 'phrases':
        return handle_phrases_command(section_args, json_output)
    elif section == 'git':
        return handle_git_command(section_args, json_output)
    elif section == 'env':
        return handle_env_command(section_args, json_output)
    elif section == 'features':
        return handle_features_command(section_args, json_output)
    elif section == 'validate':
        return validate_config(json_output)
    else:
        raise ValueError(f"Unknown config section: {section}. Valid sections: phrases, git, env, features, validate")

def format_config_human(config) -> str:
    """Format full config for human reading."""
    lines = [
        "=== Sessions Configuration ===",
        "",
        "Trigger Phrases:",
    ]
    
    for category in TriggerCategory:
        phrases = getattr(config.trigger_phrases, category.value, [])
        if phrases:
            lines.append(f"  {category.value}: {', '.join(phrases)}")
    
    lines.extend([
        "",
        "Git Preferences:",
        f"  Add Pattern: {config.git_preferences.add_pattern.value}",
        f"  Default Branch: {config.git_preferences.default_branch}",
        f"  Commit Style: {config.git_preferences.commit_style.value}",
        f"  Auto Merge: {config.git_preferences.auto_merge}",
        f"  Auto Push: {config.git_preferences.auto_push}",
        f"  Has Submodules: {config.git_preferences.has_submodules}",
        "",
        "Environment:",
        f"  OS: {config.environment.os.value}",
        f"  Shell: {config.environment.shell.value}",
        f"  Developer Name: {config.environment.developer_name}",
        "",
        "Features:",
        f"  Branch Enforcement: {config.features.branch_enforcement}",
        f"  Task Detection: {config.features.task_detection}",
        f"  Auto Ultrathink: {config.features.auto_ultrathink}",
        f"  Context Warnings (85%): {config.features.context_warnings.warn_85}",
        f"  Context Warnings (90%): {config.features.context_warnings.warn_90}",
    ])
    
    return "\n".join(lines)
#!<

#!> Trigger phrases handlers
def handle_phrases_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle trigger phrase commands.
    
    Usage:
        config phrases list [category]
        config phrases add <category> "<phrase>"
        config phrases remove <category> "<phrase>"
        config phrases clear <category>
    """
    if not args:
        # List all phrases
        config = load_config()
        phrases = config.trigger_phrases.list_phrases()
        if json_output:
            return {"phrases": phrases}
        return format_phrases_human(phrases)
    
    action = args[0].lower()
    
    if action == 'list':
        config = load_config()
        if len(args) > 1:
            # List specific category
            category = args[1]
            phrases = config.trigger_phrases.list_phrases(category)
        else:
            # List all
            phrases = config.trigger_phrases.list_phrases()
        
        if json_output:
            return {"phrases": phrases}
        return format_phrases_human(phrases)
    
    elif action == 'add':
        if len(args) < 3:
            raise ValueError("Usage: config phrases add <category> \"<phrase>\"")
        
        category = args[1]
        phrase = args[2]
        
        with edit_config() as config:
            added = config.trigger_phrases.add_phrase(category, phrase)
        
        if json_output:
            return {"added": added, "category": category, "phrase": phrase}
        if added:
            return f"Added '{phrase}' to {category}"
        else:
            return f"'{phrase}' already exists in {category}"
    
    elif action == 'remove':
        if len(args) < 3:
            raise ValueError("Usage: config phrases remove <category> \"<phrase>\"")
        
        category = args[1]
        phrase = args[2]
        
        with edit_config() as config:
            removed = config.trigger_phrases.remove_phrase(category, phrase)
        
        if json_output:
            return {"removed": removed, "category": category, "phrase": phrase}
        if removed:
            return f"Removed '{phrase}' from {category}"
        else:
            return f"'{phrase}' not found in {category}"
    
    elif action == 'clear':
        if len(args) < 2:
            raise ValueError("Usage: config phrases clear <category>")
        
        category = args[1]
        
        with edit_config() as config:
            # Clear the category by setting it to empty list
            category_enum = config.trigger_phrases._coax_phrase_type(category)
            setattr(config.trigger_phrases, category_enum.value, [])
        
        if json_output:
            return {"cleared": category}
        return f"Cleared all phrases in {category}"
    
    elif action == 'show':
        # Show specific category
        if len(args) < 2:
            raise ValueError("Usage: config phrases show <category>")
        
        category = args[1]
        config = load_config()
        phrases = config.trigger_phrases.list_phrases(category)
        
        if json_output:
            return {"phrases": phrases}
        return format_phrases_human(phrases)
    
    else:
        raise ValueError(f"Unknown phrases action: {action}. Valid actions: list, add, remove, clear, show")

def format_phrases_human(phrases: Dict[str, List[str]]) -> str:
    """Format phrases for human reading."""
    lines = ["Trigger Phrases:"]
    for category, phrase_list in phrases.items():
        if phrase_list:
            lines.append(f"  {category}:")
            for phrase in phrase_list:
                lines.append(f"    - {phrase}")
        else:
            lines.append(f"  {category}: (none)")
    return "\n".join(lines)
#!<

#!> Git preferences handlers
def handle_git_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle git preference commands.
    
    Usage:
        config git show
        config git set <key> <value>
    """
    if not args or args[0] == 'show':
        # Show git preferences
        config = load_config()
        git_prefs = config.git_preferences
        
        if json_output:
            return {
                "git_preferences": {
                    "add_pattern": git_prefs.add_pattern.value,
                    "default_branch": git_prefs.default_branch,
                    "commit_style": git_prefs.commit_style.value,
                    "auto_merge": git_prefs.auto_merge,
                    "auto_push": git_prefs.auto_push,
                    "has_submodules": git_prefs.has_submodules,
                }
            }
        
        lines = [
            "Git Preferences:",
            f"  add_pattern: {git_prefs.add_pattern.value}",
            f"  default_branch: {git_prefs.default_branch}",
            f"  commit_style: {git_prefs.commit_style.value}",
            f"  auto_merge: {git_prefs.auto_merge}",
            f"  auto_push: {git_prefs.auto_push}",
            f"  has_submodules: {git_prefs.has_submodules}",
        ]
        return "\n".join(lines)
    
    action = args[0].lower()
    
    if action == 'set':
        if len(args) < 3:
            raise ValueError("Usage: config git set <key> <value>")
        
        key = args[1].lower()
        value = args[2]
        
        with edit_config() as config:
            if key == 'add_pattern':
                try:
                    config.git_preferences.add_pattern = GitAddPattern(value)
                except ValueError:
                    raise ValueError(f"Invalid add_pattern: {value}. Valid values: ask, all")
            
            elif key == 'default_branch':
                config.git_preferences.default_branch = value
            
            elif key == 'commit_style':
                try:
                    config.git_preferences.commit_style = GitCommitStyle(value)
                except ValueError:
                    raise ValueError(f"Invalid commit_style: {value}. Valid values: conventional, simple, detailed")
            
            elif key in ['auto_merge', 'auto_push', 'has_submodules']:
                bool_value = value.lower() in ['true', '1', 'yes', 'on']
                setattr(config.git_preferences, key, bool_value)
            
            else:
                raise ValueError(f"Unknown git preference: {key}")
        
        if json_output:
            return {"updated": key, "value": value}
        return f"Updated git.{key} to {value}"
    
    else:
        raise ValueError(f"Unknown git action: {action}. Valid actions: show, set")
#!<

#!> Environment settings handlers
def handle_env_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle environment setting commands.
    
    Usage:
        config env show
        config env set <key> <value>
    """
    if not args or args[0] == 'show':
        # Show environment settings
        config = load_config()
        env = config.environment
        
        if json_output:
            return {
                "environment": {
                    "os": env.os.value,
                    "shell": env.shell.value,
                    "developer_name": env.developer_name,
                }
            }
        
        lines = [
            "Environment Settings:",
            f"  os: {env.os.value}",
            f"  shell: {env.shell.value}",
            f"  developer_name: {env.developer_name}",
        ]
        return "\n".join(lines)
    
    action = args[0].lower()
    
    if action == 'set':
        if len(args) < 3:
            raise ValueError("Usage: config env set <key> <value>")
        
        key = args[1].lower()
        value = args[2]
        
        with edit_config() as config:
            if key == 'os':
                try:
                    config.environment.os = UserOS(value)
                except ValueError:
                    raise ValueError(f"Invalid os: {value}. Valid values: linux, macos, windows")
            
            elif key == 'shell':
                try:
                    config.environment.shell = UserShell(value)
                except ValueError:
                    raise ValueError(f"Invalid shell: {value}. Valid values: bash, zsh, fish, powershell, cmd")
            
            elif key == 'developer_name':
                config.environment.developer_name = value
            
            else:
                raise ValueError(f"Unknown environment setting: {key}")
        
        if json_output:
            return {"updated": key, "value": value}
        return f"Updated env.{key} to {value}"
    
    else:
        raise ValueError(f"Unknown env action: {action}. Valid actions: show, set")
#!<

#!> Feature toggles handlers
def handle_features_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle feature toggle commands.
    
    Usage:
        config features show
        config features set <key> <value>
    """
    if not args or args[0] == 'show':
        # Show feature toggles
        config = load_config()
        features = config.features
        
        if json_output:
            return {
                "features": {
                    "branch_enforcement": features.branch_enforcement,
                    "task_detection": features.task_detection,
                    "auto_ultrathink": features.auto_ultrathink,
                    "warn_85": features.context_warnings.warn_85,
                    "warn_90": features.context_warnings.warn_90,
                }
            }
        
        lines = [
            "Feature Toggles:",
            f"  branch_enforcement: {features.branch_enforcement}",
            f"  task_detection: {features.task_detection}",
            f"  auto_ultrathink: {features.auto_ultrathink}",
            f"  warn_85: {features.context_warnings.warn_85}",
            f"  warn_90: {features.context_warnings.warn_90}",
        ]
        return "\n".join(lines)
    
    action = args[0].lower()
    
    if action == 'set':
        if len(args) < 3:
            raise ValueError("Usage: config features set <key> <value>")
        
        key = args[1].lower()
        value = args[2]
        bool_value = value.lower() in ['true', '1', 'yes', 'on']
        
        with edit_config() as config:
            if key in ['task_detection', 'auto_ultrathink']:
                # Safe features
                setattr(config.features, key, bool_value)
            
            elif key in ['warn_85', 'warn_90']:
                # Context warning features
                setattr(config.features.context_warnings, key, bool_value)
            
            elif key == 'branch_enforcement':
                # Not exposed to prevent safety bypass
                raise ValueError("Cannot modify branch_enforcement via API")
            
            else:
                raise ValueError(f"Unknown feature: {key}")
        
        if json_output:
            return {"updated": key, "value": bool_value}
        return f"Updated features.{key} to {bool_value}"
    
    else:
        raise ValueError(f"Unknown features action: {action}. Valid actions: show, set")
#!<

#!> Config validation
def validate_config(json_output: bool = False) -> Any:
    """
    Validate the current configuration.
    """
    try:
        config = load_config()
        # The load itself validates the structure
        
        # Additional validation checks
        issues = []
        
        # Check for empty required fields
        if not config.git_preferences.default_branch:
            issues.append("Git default_branch is empty")
        
        if not config.environment.developer_name:
            issues.append("Developer name is empty")
        
        # Check for at least one implementation trigger phrase
        if not config.trigger_phrases.implementation_mode:
            issues.append("No implementation mode trigger phrases defined")
        
        if issues:
            if json_output:
                return {"valid": False, "issues": issues}
            return "Configuration issues found:\n" + "\n".join(f"  - {issue}" for issue in issues)
        
        if json_output:
            return {"valid": True}
        return "Configuration is valid"
        
    except Exception as e:
        if json_output:
            return {"valid": False, "error": str(e)}
        return f"Configuration error: {e}"
#!<

#-#
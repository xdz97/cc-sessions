# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from pathlib import Path
import json
import sys
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
##-##

#-#

def add_phrase(phrase_type: str, phrase: str):
    # For cc-sessions, we use sessions-config.json in the sessions directory
    config_file_path = Path('sessions') / 'sessions-config.json'
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if config_file_path.exists():
        with open(config_file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {
            "trigger_phrases": [],
            "daic_phrases": [],
            "task_creation_phrases": [],
            "task_completion_phrases": [],
            "task_start_phrases": [],
            "compaction_phrases": []
        }
    
    # Map phrase types to keys in the config
    key_map = {
        "daic": "daic_phrases",
        "create": "task_creation_phrases",
        "complete": "task_completion_phrases",
        "start": "task_start_phrases",
        "compact": "compaction_phrases"
    }
    
    if phrase_type in key_map:
        key = key_map[phrase_type]
        # Ensure the key exists
        if key not in data:
            data[key] = []
        
        if phrase not in data[key]:
            data[key].append(phrase)
            
            # Also add to the main trigger_phrases list for DAIC triggers
            if phrase_type == "daic" and "trigger_phrases" in data:
                if phrase not in data["trigger_phrases"]:
                    data["trigger_phrases"].append(phrase)
            
            with open(config_file_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Added phrase '{phrase}' to {key}.")
        else:
            print(f"Phrase '{phrase}' already exists in {key}.")
    else:
        print(f"Invalid phrase type: {phrase_type}")

if __name__ == "__main__":
    phrase_type = sys.argv[1] if len(sys.argv) > 1 else ""
    phrase = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    if phrase_type not in ["daic", "create", "start", "complete", "compact"] or not phrase:
        print("Usage: add_phrases.py <phrase_type> <phrase>")
        print("phrase_type must be one of: daic, create, start, complete, compact")
        sys.exit(1)
    add_phrase(phrase_type, phrase)
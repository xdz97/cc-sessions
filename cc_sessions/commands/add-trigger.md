---
allowed-tools: Bash(python3:*), Bash(python:*), Bash(echo:*)
argument-hint: "(daic|create|start|complete|compact) <phrase>"
description: Add a trigger phrase for various actions (daic, create, start, complete, compact)
---

Validate the trigger type and phrase:
!`TYPE=$(echo "$ARGUMENTS" | cut -d' ' -f1)
PHRASE=$(echo "$ARGUMENTS" | cut -d' ' -f2-)
if [ -z "$TYPE" ] || [ -z "$PHRASE" ]; then
    echo "Error: Usage: /add-trigger <type> <phrase>"
    echo "Types: daic, create, start, complete, compact"
    exit 1
fi
case "$TYPE" in
    daic|create|start|complete|compact)
        # Valid type, proceed
        ;;
    *)
        echo "Error: Invalid trigger type '$TYPE'"
        echo "Valid types: daic, create, start, complete, compact"
        exit 1
        ;;
esac
python3 sessions/scripts/add_phrases.py "$TYPE" "$PHRASE" || python sessions/scripts/add_phrases.py "$TYPE" "$PHRASE"`

Tell the user: "Successfully added `$2` as a $1 trigger phrase."

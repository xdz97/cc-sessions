# Context Compaction Protocol

Use when context window is ~75% full or when switching to a new major section of work.

## 1. Complete Current Work

Before compacting:
- Finish any in-progress implementation
- Ensure all tests pass
- Commit any uncommitted changes

## 2. Run Logging Agent

Use the logging agent to consolidate work logs:
```
Use logging agent to organize and consolidate the work log for [task]
```

## 3. Run Context Refinement Agent  

Update the context manifest with discoveries:
```
Use context-refinement agent to update the context manifest with discoveries from this session
```

## 4. Run Code Review Agent (if applicable)

If significant code was written:
```
Use code-review agent to review changes made in this session for [task]
```

## 5. Create Checkpoint

Document the current state:
- What was accomplished
- What remains to be done
- Any blockers or considerations
- Next concrete steps

## 6. Start Fresh Context

Begin new context window with:
- Updated task file (with refined context and logs)
- Clear starting point
- Specific next steps

## When to Compact

Compact context when:
- Token usage exceeds 75%
- Switching between major sections of work
- Before starting complex new features
- After completing significant milestones
- When conversation becomes sluggish

## Benefits

- Maintains performance
- Preserves important discoveries
- Keeps clean work logs
- Ensures knowledge transfer between contexts
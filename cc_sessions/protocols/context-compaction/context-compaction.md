# Context Compaction Protocol

When context window reaches ~90%, you will be instructed to perform these steps:

{todos}

## 1. Run Maintenance Agents

Before compacting, delegate to agents:

1. **logging agent** - Update work logs in task file
   - Automatically receives full conversation context
   - Logs work progress and updates task status

2. **context-refinement agent** - Check for discoveries/drift
   - Reads transcript files automatically  
   - Will update context ONLY if changes found
   - Skip if task is complete

3. **service-documentation agent** - Update CLAUDE.md files
   - Only if service interfaces changed significantly
   - Include list of modified services

## Note on Context Refinement

The context-refinement agent is speculative - it will only update the context manifest if genuine drift or new discoveries occurred. This prevents unnecessary updates while ensuring important findings are captured.

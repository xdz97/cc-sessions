---
allowed-tools: Bash, Write, Read
argument-hint: [prefix]-[name] 
description: Create a new task in sessions
---
Create a new task file for: $ARGUMENTS

Based on our current conversation context:
1. Copy the template from sessions/tasks/TEMPLATE.md to sessions/tasks/$ARGUMENTS.md
2. Fill in the frontmatter:
   - task: $ARGUMENTS
   - branch: (determine from prefix)
   - status: pending
   - created: today's date
   - modules: (infer from context or ask if unclear)
3. Write the Problem/Goal section based on what we've been discussing
4. Define Success Criteria based on the context
5. Add any Context Files I think are relevant
6. Include any User Notes from our discussion

If I need clarification on:
- Which modules/services are involved
- Specific success criteria
- Priority or complexity

Ask those questions first, then create the complete task file.

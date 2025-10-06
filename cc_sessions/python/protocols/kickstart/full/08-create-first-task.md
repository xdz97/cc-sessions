# Creating Your First Real Task

Okay, now that you know how the task startup protocol works, lets learn about task creation.

Task creation is one of two protocols that can be run any time you need to run them...

Even if there's an active task, active todos being tracked, or you're in the middle of something - when you activate task creation, your state will be saved and resumed after the task has been made.

## File vs Directory Tasks

Tasks come in two forms:

**File Tasks** (simple, focused):
- Single markdown file
- One clear goal
- Estimated < 3 days work
- Example: `h-fix-auth-redirect.md`, `m-refactor-redis-client.md`

**Directory Tasks** (complex, multi-phase):
- Directory with README.md and subtask files
- Multiple distinct phases
- Needs clear subtasks from the start
- Example: `h-implement-auth/`, `m-migrate-to-postgres/`

For your first real task, we're going to start small with a **file task**.

## Pick Something Real But Small

Think of something you know needs to be done in your codebase:
- A bug that needs fixing
- A small feature to add
- Something to refactor
- A piece of code to double-check

Start small - pick something you can describe in a sentence or two.

What task comes to mind?

[Wait for user's response]

---

**Instructions after user describes their task:**

Tell them: "Perfect! Now just use your task creation trigger phrase with that description."

Example: If their phrase is "new task:" and they want to fix a bug, they'd say:
`new task: fix the login redirect loop when session expires`

Wait for them to use their trigger phrase.

---

**When they trigger task creation:**

You'll enter the task creation protocol. Follow it completely:

1. Propose task naming (priority, type, descriptive name)
2. Ask about success criteria
3. **Context gathering step** - Here's what to explain when you reach this step:

"The context-gathering agent is a major part of the performance boost cc-sessions offers. Instead of me randomly learning about your task as I go, the agent dedicates an entire run to tearing apart your codebase and finding everything the task needs to know:
- Patterns and conventions I should follow
- Variables, imports, and signatures I'll interact with
- Sources and dependencies I need to be aware of
- Existing code I should match or extend

All that context gets put front and center in your task file. I won't have to dig around - I'll only need to look at the source code we're working with. I never have to regain this context through brute force search if the task spans multiple context windows, either.

I strongly recommend using the context-gathering agent on this task to see it in action."

Then follow their choice (yes/no for running the agent).

4. Update task indexes (if applicable)
5. Commit the task file

---

**After task creation protocol completes:**

Run: `python -m sessions.kickstart next`

This will move to the next module.

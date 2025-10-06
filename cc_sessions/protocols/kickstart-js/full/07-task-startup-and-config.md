# Task Startup and Configuration

Now let's learn about the **task startup protocol** - how you begin work on a task with full context loaded.

## How Task Startup Works

The task startup protocol:
- Loads the task file into context
- Creates/checks out the git branch for the task
- Loads the context manifest (all the patterns and code you need to know)
- Sets up task tracking in session state
- Puts you in discussion mode to plan the work

Default startup phrase: **start^:**

## The @ Syntax

You use **@ syntax** to reference task files. This conveniently loads the task file into context and sets up tracking:

Example: `start^: @h-fix-auth-redirect.md`

The @ tells me exactly which task to load.

## Add Your Startup Phrase

Pick a phrase that feels natural for starting work.

Good examples: "begin task:", "work on:", "lets start:", "start working on:"
Bad examples: "start" (too common), "begin" (might conflict)

What phrase would you like to use for starting tasks?

[Wait for user's response]

---

**Instructions after user provides their phrase:**

Tell them to add it using the `/sessions` command:

```
/sessions config triggers add start <user's phrase>
```

Example: `/sessions config triggers add start begin task:`

Tell them to run it now.

[Wait for them to run the command]

---

**After they run the command:**

Confirm their phrase has been added.

## Let's Configure Your Repository

We've created a special task to guide you through the rest of kickstart: `h-kickstart-setup.md`

This task will:
- Create a git branch (`feature/kickstart-setup`) to demonstrate the full workflow
- Run context-gathering agent to analyze your repository
- Walk you through all important configuration settings
- Finish out the rest of the tutorial with an active task (for demonstration purposes)

Now use your startup phrase with this task:

```
<your phrase>: @sessions/tasks/kickstart-config.md
```

Example: `begin task: @sessions/tasks/kickstart-config.md`

[Wait for them to use startup phrase]

---

**When they trigger startup:**

Follow the task startup protocol completely. The task file contains all the instructions for what to do during this task.

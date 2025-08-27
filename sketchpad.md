## Why We're Here 
For the last year, I've been working on an AI agent scaffolding framework called ByteBot, and now we're getting very close to beginning a public release schedule. But, in preparation for that public release, we're going to release our dev tooling that has made our lives easier as a public good.

## How You Got Here

- If you're watching this, you're likely using AI programming tools like Claude Code or Cursor

- You likely got sold on the dream that people who largely do not write or engineer production software are selling you - the Matt Bermans of the world told you you could "scale your impact", they talk about "agentic programming" and "vibe coding", and you rushed in headlong

## My Frustrations

- Agent programmers do too much without talking to me first
- Agent programmers dont understand my codebase and the patterns/conventions relavant to the current task 
- Agent programmers dont remember rules (the more rules, the worse the adherence)
- Agent programmers recommend goofy shit that is unimportant 
- Agent programmers need to be explicitly told how to manage their own agent loop and context or have it manually managed for them 
- Agent programmers need to be explicitly told to keep good repo hygeine 
- Current solutions smuggle the "natural" out of "natural language programming"

## What It Feels Like
- Your codebase is a messy behemoth you dont understand
- You wouldn't even know where to start fixing it 
- The only way to identify all the problems with it is to read it line by line and address issues as you find them (no faster than if you programmed it yourself, probably slower)
- Your comfort with your language atrophies (or never develops in the first place)
- You are using third party dependencies or externally-defined patterns that you arent familiar with (have to go learn before you can even identify whats wrong before you can even attempt to fix it)

## Claude Code Strengths
- Uses Claude models by default
- No more API budgeting - use with a Claude Max subscription pretty much infinitely
- Hooks, subagents, and dynamic context loading (programmatic control over the agentic loop)
- Very simple and barebones - doesn't get cute with trying to solve common frustrations (leaves that up to you explicitly) 

## Installing cc-sessions


- Lets fix *all* (see: many) of your problems
- Prereqs: Python 3.something w/ pip, git, and Claude Code

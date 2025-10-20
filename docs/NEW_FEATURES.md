# New Features Guide

This guide covers the new features added to your custom cc-sessions fork.

## Table of Contents
- [Learning System](#learning-system)
- [Specialized Modes](#specialized-modes)
- [Model Cost Optimization](#model-cost-optimization)

---

## Learning System

The learning system captures patterns, gotchas, and insights from your work to make you smarter over time.

### Quick Start

**Initialize the learning system:**
```bash
sessions learnings init --scan
```

This scans your codebase and pre-populates learnings with detected tech stack, patterns, and potential issues.

### How It Works

**During Task Creation** (`mek:`):
- System detects relevant learning topics based on task description
- You choose to include learnings in task file or load at startup

**During Task Startup** (`start^:`):
- Automatically loads relevant learnings for your task
- Shows patterns, gotchas, and anti-patterns from previous work

**During Task Completion** (`finito`):
- Learning-recorder agent extracts new patterns and gotchas
- Updates learning database for future tasks

### Learning Topics

Default topics include:
- **infrastructure** - DevOps, CI/CD, Docker, K8s
- **sso** - Authentication, OAuth, JWT, sessions
- **security** - Input validation, encryption, permissions
- **api** - REST, GraphQL, endpoints, rate limiting
- **database** - SQL, ORMs, migrations, schemas
- **frontend** - React, Vue, UI components
- **testing** - Unit tests, integration tests, test patterns

### Commands

```bash
# List all learning topics
sessions learnings list

# Show detailed info about a topic
sessions learnings show sso

# Add a new custom topic
sessions learnings add devops "CI/CD and deployment" docker kubernetes github-actions

# Detect relevant topics for current task
sessions learnings relevant

# Enable/disable automatic learning loading
sessions learnings enable
sessions learnings disable

# Check learning system status
sessions learnings status
```

### Example Workflow

**1. Create a task with learning detection:**
```
You: mek: implement OAuth authentication

Claude: [Detects relevant topics: sso, security, api]

How would you like to handle learnings for this task?

Option A - Include Now: Add learnings directly to task file
Option B - Load at Startup (Recommended): Load when you start^: the task
Option C - Skip: Don't include learnings

You: B

Claude: ✓ Task created with relevant_topics: [sso, security, api]
```

**2. Start the task:**
```
You: start^: implement-oauth

Claude: [Loads learnings automatically]

[LEARNINGS: Relevant Knowledge Loaded]

📚 Active Topics: sso, security, api

### SSO - Known Patterns
- Token Refresh Pattern (used 12 times, 100% success)
  Always refresh OAuth tokens 5 minutes before expiry
  Example: services/auth.py:45-60

### SSO - Known Gotchas
⚠️ services/auth.py:67 - Missing await causes silent failures
   Severity: critical
   → Solution: Always use async/await for database operations

[Proceeds with task implementation]
```

**3. Complete the task:**
```
You: finito

Claude: [Runs learning-recorder agent]
        [Extracts new patterns from your implementation]
        [Updates learning database]

Recorded 3 new patterns and 2 gotchas to sso topic.
```

### Learning File Structure

```
sessions/learnings/
├── index.json              # Topic index
└── topics/
    ├── sso/
    │   ├── patterns.json   # Successful patterns
    │   ├── gotchas.json    # Issues encountered
    │   └── history.json    # Usage history
    ├── security/
    │   ├── patterns.json
    │   ├── gotchas.json
    │   └── history.json
    └── ...
```

---

## Specialized Modes

Specialized modes restrict available tools to focus Claude on specific tasks.

### Available Modes

#### 1. Code Review Mode
**Purpose**: Analyze code quality, security, and best practices (read-only)

**Allowed Tools**: Read, Grep, Glob, Bash (read-only), Task
**Blocked Tools**: Write, Edit, MultiEdit, NotebookEdit

**Enter the mode:**
```bash
sessions smode enter code_review src/auth/
```

**Example session:**
```
You: sessions smode enter code_review src/

Claude: [Entered code_review mode]

        I'll perform a systematic code review of src/

        [Reviews all files in src/]

        ## Code Review Summary

        **Scope**: src/ (45 files)
        **Lines of Code**: ~3,200
        **Languages**: Python, JavaScript

        ### Critical Issues
        □ src/auth.py:67 - SQL injection vulnerability in login endpoint
        □ src/api.py:123 - Missing authentication check on admin route

        ### High Priority Issues
        □ src/utils.py:45 - Hardcoded API keys
        □ src/database.py:89 - Connection pool not properly closed

        [... more findings ...]

You: review complete

Claude: [Exited code_review mode]
        Returned to normal operation.
```

#### 2. Refactor Mode
**Purpose**: Improve code structure without changing functionality

**Allowed Tools**: Read, Edit, Grep, Glob, Bash, Task
**Blocked Tools**: Write (focus on refactoring, not creating)

**Enter the mode:**
```bash
sessions smode enter refactor src/payment_processor.py
```

**Example workflow:**
```
You: sessions smode enter refactor src/messy_code.py

Claude: [Entered refactor mode]

        I've analyzed src/messy_code.py. Here's my refactoring plan:

        ## Refactoring Plan

        **Target**: src/messy_code.py
        **Goal**: Extract methods, reduce complexity

        ### Proposed Changes
        1. Extract 3 methods from 150-line process_order() function
        2. Consolidate duplicate validation code
        3. Simplify nested conditionals using guard clauses

        Approve? [You approve]

        [Makes incremental changes with tests between each]

        ✓ Extracted calculate_total() method
        ✓ Extracted apply_discount() method
        ✓ Tests pass

        [Continues refactoring...]

You: refactoring complete
```

#### 3. Debug Mode
**Purpose**: Investigate and fix bugs systematically

**Allowed Tools**: All tools (debugging needs full access)
**Blocked Tools**: None

**Enter the mode:**
```bash
sessions smode enter debug
```

**Example workflow:**
```
You: sessions smode enter debug

You: Users are getting 500 errors when trying to checkout

Claude: [Entered debug mode]

        Let me investigate systematically:

        1. Checking error logs...
        2. Found stack trace showing NoneType error in payment.py:45
        3. Creating reproduction script...
        4. Root cause: payment_method can be None when user profile incomplete

        ## Root Cause Analysis

        **Location**: payment.py:45
        **Problem**: Missing null check for payment_method
        **Why it happens**: New users without completed profile

        ### Proposed Fix
        Add null check and return meaningful error

        [Implements fix with tests]

        ✓ Bug fixed - Checkout now handles incomplete profiles gracefully

You: bug fixed
```

#### 4. Optimize Mode
**Purpose**: Improve performance through measurement and optimization

**Allowed Tools**: Read, Edit, Grep, Glob, Bash, Task
**Blocked Tools**: Write (focus on optimizing existing code)

**Enter the mode:**
```bash
sessions smode enter optimize src/data_processor.py
```

**Example workflow:**
```
You: sessions smode enter optimize src/slow_endpoint.py

Claude: [Entered optimize mode]

        First, let me profile the code...

        ## Performance Baseline
        **Target**: /api/users endpoint
        **Current**: 2.3s average response time

        ### Profiling Results
        Bottleneck: N+1 query problem (line 45)
        - 500ms per user lookup (×100 users = 50 seconds!)

        ## Optimization Plan
        1. Batch database queries using JOIN
        2. Add Redis caching for user profiles

        Expected improvement: 50x faster

        [Implements optimizations]

        ## Results
        **Before**: 2.3s average
        **After**: 45ms average
        **Improvement**: 51x faster! ✓

You: optimization complete
```

#### 5. Document Mode
**Purpose**: Create and maintain project documentation

**Allowed Tools**: All tools (documentation often needs creating new files)
**Blocked Tools**: None

**Enter the mode:**
```bash
sessions smode enter document
```

### Specialized Mode Commands

```bash
# List all available modes
sessions smode list

# Enter a mode
sessions smode enter <mode> [args...]

# Check current mode
sessions smode current

# Exit current mode
sessions smode exit
```

### Exit Phrases

Each mode has natural language exit phrases:
- **Code Review**: "review complete", "done reviewing", "exit review"
- **Refactor**: "refactoring complete", "done refactoring", "exit refactor"
- **Debug**: "bug fixed", "debugging complete", "exit debug"
- **Optimize**: "optimization complete", "done optimizing", "exit optimize"
- **Document**: "documentation complete", "done documenting", "exit document"

Or use the command: `sessions smode exit`

---

## Model Cost Optimization

Your fork is optimized to use cost-effective models by default.

### Model Pricing

| Model | Context | Input Cost | Output Cost | Default Use |
|-------|---------|-----------|-------------|-------------|
| **Haiku 4.5** | 200k | $1/M tokens | $5/M tokens | Heavy read operations |
| **Sonnet 4.5** | 200k-800k | $3/M tokens | $15/M tokens | **✓ Main session (default)** |
| Opus 3.5 | 200k | $15/M tokens | $75/M tokens | Not recommended (5x more expensive) |

### Cost Savings

**Before (Opus default)**: ~$15/$75 per million tokens
**After (Sonnet default)**: ~$3/$15 per million tokens
**Savings**: **~80% cost reduction** 💰

### How It Works

1. **Auto-Detection**: System detects which model you're using
2. **Context Tracking**: Adjusts context limits based on detected model
3. **Smart Warnings**: Triggers 85% and 90% context warnings to prevent overruns
4. **Compaction**: Helps you compact context before hitting limits

### Context Limits

The system automatically adjusts based on your model:

- **Haiku 4.5**: 200k tokens
- **Sonnet 4.5**: 200k base (800k with extended context)
- **Opus 3.5**: 200k tokens

### Cost Strategy

**Main Session (Sonnet)**:
- Complex reasoning and code generation
- Context-aware planning and implementation
- Best balance of intelligence and cost

**Future Enhancement (Haiku via Agents)**:
- Heavy read operations (codebase scanning)
- Log analysis and search
- Routine tasks and simple operations

The parallel agent system (currently skipped) would enable delegating heavy read operations to cheaper Haiku instances while keeping the main session on Sonnet.

### Example Cost Calculation

**Typical Task Session**:
- Input: ~50k tokens (reading code, context)
- Output: ~10k tokens (code generation, responses)

**With Sonnet (default)**:
- Input cost: 50k × ($3/1M) = $0.15
- Output cost: 10k × ($15/1M) = $0.15
- **Total: $0.30 per task**

**If using Opus (not recommended)**:
- Input cost: 50k × ($15/1M) = $0.75
- Output cost: 10k × ($75/1M) = $0.75
- **Total: $1.50 per task** (5x more!)

### Smart Context Management

The system warns you before you hit context limits:

**85% Warning**:
```
[Warning] Context window is 85% full (170,000/200,000 tokens).
Consider context compaction or task completion if nearly done.
```

**90% Warning**:
```
[90% WARNING] 180,000/200,000 tokens used (90%).
CRITICAL: Run task completion protocol to wrap up cleanly!
```

This helps you avoid expensive context overruns and lost work.

---

## Quick Reference

### Most Common Commands

```bash
# Learning System
sessions learnings init --scan    # Initialize with codebase scan
sessions learnings list            # List all topics
sessions learnings show <topic>    # View topic details

# Specialized Modes
sessions smode list                # List available modes
sessions smode enter code_review src/  # Enter code review mode
sessions smode exit                # Exit current mode

# Cost Tracking
sessions state show model          # Check current model
```

### Integration with Task Workflow

**Full workflow example:**

```bash
# 1. Initialize learnings (first time only)
sessions learnings init --scan

# 2. Create task (with learning detection)
# User: mek: add rate limiting to API
# Claude detects relevant topics: api, security

# 3. Start task (learnings auto-load)
# User: start^: add-rate-limiting
# Claude loads API and security patterns

# 4. Optional: Use specialized mode
sessions smode enter code_review src/api/

# 5. Work on task
# [Implementation work]

# 6. Complete task (learnings auto-record)
# User: finito
# Claude records new patterns about rate limiting
```

---

## Tips & Best Practices

### Learning System
- Run `sessions learnings init --scan` at project start
- Let system auto-load learnings at task startup (recommended)
- Review recorded learnings periodically to verify accuracy
- Add custom topics for your specific project domains

### Specialized Modes
- Use code review mode before committing major changes
- Enter refactor mode to stay focused on structure improvements
- Debug mode provides full tool access when investigating issues
- Document mode keeps you in documentation mindset

### Cost Optimization
- Trust Sonnet as default - it's 5x cheaper than Opus
- Watch for 85%/90% context warnings
- Complete tasks before context fills up
- Use context compaction protocol when needed

---

## Troubleshooting

**Learnings not loading?**
```bash
sessions learnings status  # Check if enabled
sessions learnings enable  # Enable if disabled
```

**Can't exit specialized mode?**
```bash
sessions smode exit  # Force exit via command
```

**Context warnings not showing?**
```bash
sessions config features show  # Check warn_85 and warn_90
sessions config features set warn_85 true
sessions config features set warn_90 true
```

**Wrong model detected?**
- System auto-detects from Claude Code's model name
- Check with: `sessions state show model`
- Context limits adjust automatically

---

## What's Next?

These features make you smarter and more efficient:

1. **Learning System** - Captures tribal knowledge automatically
2. **Specialized Modes** - Focused workflows with tool restrictions
3. **Cost Optimization** - 80% savings with Sonnet default

All features work together seamlessly with the existing DAIC workflow!

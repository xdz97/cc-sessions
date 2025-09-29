# Fix: Relax Implementation Mode Todo Reminders

**Priority:** Medium  
**Status:** In Progress

## Problem

The current implementation mode todo reminder system shows persistent reminders about being in implementation mode without approved todos, even when there are legitimately no todos to track. This creates unnecessary noise in the interface.

The reminders currently appear even when:
- Simple, single-step tasks are being performed
- No complex workflow requires todo tracking
- The work is straightforward and doesn't benefit from todo management

## Requirements

1. **Identify where implementation mode reminders are triggered**
   - Locate the code that generates these reminders
   - Understand the current logic and conditions

2. **Implement logic to suppress reminders when no todos exist and none are needed**
   - Distinguish between "no todos because none were created" vs "no todos because none are needed"
   - Allow for scenarios where simple work doesn't require todo tracking

3. **Keep reminders active when todos were proposed but not approved**
   - Maintain current behavior when todos were suggested but user didn't approve them
   - This indicates the system detected complexity that should be tracked

4. **Maintain reminders for complex multi-step work that should have todos**
   - Continue showing reminders when the work is clearly complex enough to warrant todo tracking
   - Preserve the valuable nudging behavior for appropriate scenarios

## Acceptance Criteria

- [x] Implementation mode reminders are suppressed for simple, single-step work
- [x] Reminders continue to appear when todos were proposed but not approved
- [x] Reminders continue for complex work that should have todo tracking
- [x] No regression in existing todo management functionality
- [x] Clear distinction between "no todos needed" vs "todos needed but missing"

## Context Manifest

### How Implementation Mode Todo Reminders Currently Work

The cc-sessions package implements a DAIC (Discussion-Alignment-Implementation-Check) workflow that strictly enforces todo-based execution boundaries. When a user activates implementation mode using trigger phrases like "yert" or "make it so", Claude enters a state where every implementation action must be tracked via approved TodoWrite lists.

The current reminder system is triggered in the `post_tool_use.py` hook, specifically in lines 95-103. After every tool execution, the system checks if the session is in implementation mode (`STATE.mode is Mode.GO`) but has no active todos (`not STATE.todos.active`). When this condition is met, it displays this persistent reminder:

```
"[Reminder] You're in implementation mode without approved todos.
If you proposed todos that were approved, add them.
If the user asked you to do something without todo proposal/approval, translate *only the remaining work* to todos and add them (all 'pending').
In any case, return to discussion mode after completing approved implementation."
```

This enforcement mechanism was designed to prevent "execution anxiety" where Claude would hesitate before each tool use, instead channeling all implementation work through pre-approved todo lists. The system operates on the principle that complex work should always have visible tracking, while the implementation phase should flow smoothly within those boundaries.

The reminder appears after EVERY tool use when in implementation mode without todos, regardless of whether the work actually needs todo tracking. This creates noise in scenarios where:

1. **Simple, single-step tasks** are being performed (like reading a file to understand context)
2. **Quick diagnostic work** that doesn't require multi-step tracking
3. **Exploratory investigations** where the scope isn't yet clear enough for todos
4. **Context gathering** where the work is inherently exploratory

The system correctly distinguishes between different session states:
- **Discussion Mode** (`Mode.NO`): All implementation tools are blocked, only read-only operations allowed
- **Implementation Mode** (`Mode.GO`): Implementation tools are allowed, but the current logic assumes todos should always exist

The session state is managed through the `SessionsState` class in `shared_state.py`, which includes:
- `mode`: Current DAIC mode (discussion/implementation)
- `todos`: Active and stashed todo lists with completion tracking
- `flags`: Session warning flags (context usage, subagent mode, etc.)
- `current_task`: Active task information including file, branch, and status

The todo system supports different workflow patterns:
- **Active todos**: Currently being worked on
- **Stashed todos**: Temporarily stored when protocols are triggered
- **Todo restoration**: Automatic restoration of stashed todos when protocols complete

### The Problem: Inappropriate Reminder Triggers

The current implementation doesn't distinguish between legitimate scenarios:

1. **Todos were proposed but user didn't approve them** - Should show reminders (indicates detected complexity)
2. **No todos exist because none are needed** - Should NOT show reminders (simple work)
3. **User explicitly asked for implementation without todo proposal** - Should show reminders until todos are created
4. **Work is genuinely complex and should have todos** - Should show reminders

The system currently treats all "no todos in implementation mode" scenarios the same way, creating noise when it should be providing helpful nudging only for appropriate situations.

### Key Integration Points for the Solution

The fix needs to integrate with several system components:

**Session State Management**: The solution will need to track additional state to distinguish between "no todos needed" and "todos needed but missing". This could involve adding new flags to `SessionsFlags` or new fields to track the "todo expectation" state.

**Protocol Integration**: The system heavily uses protocol-based workflows (task creation, startup, completion, context compaction) that automatically populate todos. The solution should preserve this automatic todo creation while allowing for simpler workflows.

**Mode Transition Logic**: Currently in `user_messages.py`, when implementation mode is activated, the system provides instructions about todo creation. The logic needs enhancement to support "simple implementation" mode vs "complex implementation requiring todos."

**API Command Integration**: The sessions API supports various state inspection and modification commands. Any new state tracking should be accessible through these commands for debugging and manual intervention.

### Technical Reference Details

#### Core Files Requiring Modification

**Primary Target**: `/home/toastdev/io-ops/cc-sessions/cc_sessions/hooks/post_tool_use.py`
- Lines 95-103: Current reminder logic
- This is where the main conditional logic needs enhancement
- Need to add logic to determine if reminders are appropriate for the current context

**Supporting Files**:
- `/home/toastdev/io-ops/cc-sessions/cc_sessions/hooks/shared_state.py`: May need new state fields
- `/home/toastdev/io-ops/cc-sessions/cc_sessions/hooks/user_messages.py`: Implementation mode activation logic
- `/home/toastdev/io-ops/cc-sessions/cc_sessions/scripts/api/state_commands.py`: API access to new state if needed

#### Current State Tracking Structure

The `SessionsState` class includes:
```python
@dataclass
class SessionsState:
    current_task: TaskState
    active_protocol: Optional[SessionsProtocol]
    mode: Mode  # NO (discussion) or GO (implementation)
    todos: SessionsTodos  # active and stashed todo lists
    flags: SessionsFlags  # context warnings, subagent mode, noob mode
    api: APIPerms  # windowed permissions for API commands
```

#### Implementation Strategy Options

**Option 1: Add todo expectation tracking**
- Add a new field to track whether todos are expected for current work
- Set expectation flags based on implementation trigger context
- Only show reminders when todos are expected but missing

**Option 2: Heuristic-based detection**
- Analyze the type of tools being used to determine complexity
- Track sequences of tool usage to identify complex vs simple workflows
- Suppress reminders for patterns that indicate simple work

**Option 3: User intent signals**
- Enhance implementation mode activation to include scope indicators
- Allow users to signal "simple implementation" vs "complex implementation"
- Preserve current behavior as default, add opt-out mechanisms

#### Integration Considerations

**Protocol Preservation**: The existing protocol system (task creation, startup, completion) should continue to automatically create todos as these represent inherently complex workflows.

**DAIC Integrity**: The core principle that complex work should be tracked must be preserved. The solution should reduce noise, not eliminate helpful nudging.

**Backward Compatibility**: Existing workflows should continue to function. The enhancement should be additive rather than changing existing behavior for complex scenarios.

**State Management**: Any new state fields must integrate with the existing atomic state management system including locking, JSON serialization, and API access.

## File Locations for Implementation

- **Primary**: `/home/toastdev/io-ops/cc-sessions/cc_sessions/hooks/post_tool_use.py` (lines 95-103)
- **Secondary**: `/home/toastdev/io-ops/cc-sessions/cc_sessions/hooks/shared_state.py` (if new state fields needed)
- **Tertiary**: `/home/toastdev/io-ops/cc-sessions/cc_sessions/hooks/user_messages.py` (implementation mode activation)

## Notes

- This is part of the cc-sessions package which manages session state and modes
- The goal is to reduce noise while preserving helpful nudging for complex work
- Need to maintain the DAIC (Discussion First) protocol integrity

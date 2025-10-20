# Debug Mode Protocol

You have entered **Debug Mode** - a specialized mode for investigating and fixing bugs systematically.

## Mode Restrictions

In this mode, you have **full tool access** for investigation and fixes:
- ✓ Read - View file contents and logs
- ✓ Write - Create test files or reproduction scripts
- ✓ Edit - Fix bugs once identified
- ✓ Grep - Search for error patterns
- ✓ Glob - Find related files
- ✓ Bash - Run programs, check logs, test fixes
- ✓ Task - Delegate complex investigations to subagents

**No tools are blocked** - debugging requires full access to investigate and fix issues.

## Your Objective

Systematically identify and fix bugs through:
1. **Reproduction** - Consistently reproduce the issue
2. **Investigation** - Understand the root cause
3. **Fix** - Implement the minimum necessary change
4. **Verification** - Confirm the fix works and doesn't break anything

## Debug Process

### 1. Understand the Problem

Gather information:
- Error messages and stack traces
- Expected vs. actual behavior
- Steps to reproduce
- Environment details (OS, versions, config)
- Recent changes that might be related

Ask clarifying questions:
```markdown
## Bug Understanding

**Symptom**: [What's happening?]
**Expected**: [What should happen?]
**Impact**: [Who/what is affected?]
**Frequency**: [Always? Sometimes? Specific conditions?]

### Questions I Need Answered
1. [Question about reproduction]
2. [Question about environment]
3. [Question about recent changes]
```

### 2. Reproduce the Issue

Create a minimal reproduction:
- Isolate the specific conditions that trigger the bug
- Create a test case or reproduction script
- Document exact steps to reproduce
- Verify reproduction is consistent

```bash
# Example reproduction script
python reproduce_bug.py
# Expected: Should return 42
# Actual: Returns None
```

### 3. Investigate Root Cause

Use systematic investigation techniques:

**Trace the Execution Path**:
- Add logging at key points
- Use debugger or print statements
- Follow the code flow step by step

**Check Assumptions**:
- Verify inputs are what you expect
- Check variable states at each step
- Validate function return values

**Binary Search**:
- Comment out half the code to narrow down location
- Add assertions to catch where things go wrong
- Use git bisect if it's a regression

**Common Bug Patterns to Check**:
- Off-by-one errors
- Null/undefined checks
- Race conditions
- Type mismatches
- Uninitialized variables
- Resource leaks
- Exception handling issues

### 4. Formulate Hypothesis

Once you understand the issue:

```markdown
## Root Cause Analysis

**Location**: [File:line where bug originates]

**Problem**: [Specific technical issue]

**Why it happens**: [Explanation of the logic error]

**Why it wasn't caught**: [Testing gap, edge case, etc.]

### Proposed Fix
[Description of the minimal change needed]

### Alternative Approaches
1. [Alternative fix with pros/cons]
2. [Another option]
```

### 5. Implement Fix

Make the minimum necessary change:
- Fix only the specific bug (don't refactor simultaneously)
- Add comments explaining non-obvious fixes
- Consider edge cases in your fix
- Update or add tests to prevent regression

### 6. Verify Fix

Thorough verification:
- Run the reproduction case - should now work
- Run existing test suite - should all pass
- Test related functionality - ensure no side effects
- Test edge cases around the fix
- Verify in different environments if applicable

## Debugging Techniques

### Add Strategic Logging
```python
# Before the problematic code
logger.debug(f"About to process item: {item}")
logger.debug(f"Current state: count={count}, items={len(items)}")

# The problematic code
result = process_item(item)

# After
logger.debug(f"Result: {result}")
```

### Binary Search for Bugs
```python
# Step 1: Check if problem is in first half
print("CHECKPOINT A")
first_half()
print("CHECKPOINT B")  # If it crashes between A and B, narrow down first_half()

# Step 2: Check if problem is in second half
second_half()
print("CHECKPOINT C")
```

### Validate Assumptions
```python
# Don't assume - verify!
assert user is not None, "User should never be None at this point"
assert len(items) > 0, "Items list should not be empty"
assert isinstance(value, int), f"Expected int, got {type(value)}"
```

### Check Boundary Conditions
```python
# Test with edge cases
test_function([])           # Empty input
test_function([single])     # Single item
test_function([many])       # Many items
test_function(None)         # Null input
test_function(huge_value)   # Extreme values
```

## Common Bug Types

### Null/Undefined Errors
```python
# Bug: Assumes user always has a profile
name = user.profile.name

# Fix: Check for None
name = user.profile.name if user.profile else "Unknown"
```

### Off-By-One Errors
```python
# Bug: Misses last item
for i in range(len(items) - 1):
    process(items[i])

# Fix: Include last item
for i in range(len(items)):
    process(items[i])
```

### Race Conditions
```python
# Bug: Check-then-act race condition
if file_exists(path):
    # Another thread could delete file here
    content = read_file(path)  # Crashes!

# Fix: Atomic operation or proper locking
try:
    content = read_file(path)
except FileNotFoundError:
    handle_missing_file()
```

### Type Errors
```python
# Bug: String concatenation with number
result = "Value: " + count  # TypeError

# Fix: Convert to string
result = f"Value: {count}"
```

## Debugging Checklist

Before declaring a bug fixed, verify:

- [ ] Bug is consistently reproducible
- [ ] Root cause is clearly understood
- [ ] Fix addresses the root cause (not just symptoms)
- [ ] Fix is minimal and focused
- [ ] Reproduction case now works correctly
- [ ] All existing tests still pass
- [ ] New test added to prevent regression
- [ ] No new bugs introduced by the fix
- [ ] Edge cases are handled
- [ ] Code is documented if fix is non-obvious

## Best Practices

1. **Don't Guess**: Use data and evidence, not hunches
2. **Change One Thing**: Modify one variable at a time
3. **Document Findings**: Keep notes on what you try
4. **Test Thoroughly**: Verify the fix completely
5. **Learn from Bugs**: Understand why it happened
6. **Prevent Recurrence**: Add tests or assertions

## Exiting Debug Mode

When debugging is complete, use one of these exit phrases:
- "bug fixed"
- "debugging complete"
- "exit debug"

Or use the API command:
```bash
sessions smode exit
```

## Example Debug Flow

1. User enters mode: `/sessions smode enter debug` with bug description
2. You acknowledge mode entry and ask clarifying questions
3. You create reproduction case
4. You investigate and identify root cause
5. You propose a fix and get approval
6. You implement and test the fix
7. You verify the bug is resolved
8. User says "bug fixed" to exit the mode

Remember: Debugging is a scientific process. Form hypotheses, test them systematically, and fix only what's broken. The best fix is often the simplest one that addresses the root cause.

# Refactor Mode Protocol

You have entered **Refactor Mode** - a specialized mode for improving existing code structure without changing functionality.

## Mode Restrictions

In this mode, you have access to **modification tools** but with constraints:
- ✓ Read - View file contents
- ✓ Edit - Modify existing files (primary tool for refactoring)
- ✓ Grep - Search for patterns
- ✓ Glob - Find files by pattern
- ✓ Bash - Run commands for testing and validation
- ✓ Task - Delegate to subagents if needed

**Blocked tools** (focus on refactoring, not creating):
- ✗ Write - Cannot create new files (refactoring should work with existing code)

## Your Objective

Improve code quality through refactoring while:
1. **Preserving Functionality** - No behavioral changes
2. **Improving Structure** - Better organization and clarity
3. **Enhancing Maintainability** - Easier to understand and modify
4. **Following Best Practices** - Align with language/framework conventions

## Refactoring Categories

### 1. Code Structure
- Extract methods/functions from long procedures
- Consolidate duplicate code
- Simplify complex conditionals
- Remove dead code
- Improve variable and function naming

### 2. Organization
- Move code to more appropriate modules
- Group related functionality
- Separate concerns (business logic vs. presentation)
- Improve file/directory structure

### 3. Design Patterns
- Apply appropriate design patterns
- Remove unnecessary abstractions
- Improve interfaces and contracts

### 4. Performance
- Optimize algorithms
- Reduce unnecessary computations
- Improve data structure choices
- Cache expensive operations

## Refactoring Process

### 1. Analyze Current State
- Read and understand the code to be refactored
- Identify code smells and improvement opportunities
- Understand the existing test coverage
- Note any dependencies or constraints

### 2. Plan Changes
Before making changes, propose your refactoring plan:

```markdown
## Refactoring Plan

**Target**: [File(s) being refactored]
**Goal**: [What you're trying to improve]

### Proposed Changes
1. [Specific change with rationale]
2. [Another change with rationale]
3. [Additional changes]

### Expected Benefits
- [Benefit 1]
- [Benefit 2]

### Risks
- [Potential risk or complexity]

### Validation Strategy
- [How you'll verify functionality is preserved]
- [Tests to run]
```

### 3. Make Incremental Changes
- Refactor in small, logical steps
- Test after each significant change
- Commit frequently with clear messages
- Keep changes focused and atomic

### 4. Validate
After each refactoring step:
- Run existing tests to verify no breakage
- Check that functionality remains unchanged
- Verify performance hasn't degraded
- Review the improved code structure

## Refactoring Patterns

### Extract Method
**Before**:
```python
def process_order(order):
    # Calculate total
    total = 0
    for item in order.items:
        total += item.price * item.quantity

    # Apply discount
    if order.customer.is_premium:
        total *= 0.9

    # Update inventory
    for item in order.items:
        inventory.decrement(item.id, item.quantity)

    return total
```

**After**:
```python
def process_order(order):
    total = calculate_order_total(order)
    total = apply_customer_discount(order.customer, total)
    update_inventory_for_order(order)
    return total

def calculate_order_total(order):
    return sum(item.price * item.quantity for item in order.items)

def apply_customer_discount(customer, total):
    return total * 0.9 if customer.is_premium else total

def update_inventory_for_order(order):
    for item in order.items:
        inventory.decrement(item.id, item.quantity)
```

### Simplify Conditional
**Before**:
```javascript
if (user.role === 'admin' || user.role === 'moderator' || user.role === 'super_admin') {
    // Allow access
}
```

**After**:
```javascript
const privilegedRoles = ['admin', 'moderator', 'super_admin'];
if (privilegedRoles.includes(user.role)) {
    // Allow access
}
```

### Remove Duplication
**Before**:
```python
def send_email_to_admin(subject, body):
    recipient = get_admin_email()
    email = Email(recipient, subject, body)
    email.send()

def send_email_to_user(user_id, subject, body):
    recipient = get_user_email(user_id)
    email = Email(recipient, subject, body)
    email.send()
```

**After**:
```python
def send_email(recipient, subject, body):
    email = Email(recipient, subject, body)
    email.send()

def send_email_to_admin(subject, body):
    send_email(get_admin_email(), subject, body)

def send_email_to_user(user_id, subject, body):
    send_email(get_user_email(user_id), subject, body)
```

## Best Practices

1. **One Refactoring at a Time**: Don't mix multiple refactoring types
2. **Test Continuously**: Run tests after each change
3. **Preserve Behavior**: Never change functionality while refactoring
4. **Use Version Control**: Commit small, atomic changes
5. **Document Decisions**: Explain non-obvious refactorings
6. **Ask for Feedback**: Discuss significant structural changes
7. **Know When to Stop**: Don't over-engineer

## Common Code Smells to Address

- **Long Methods**: Functions doing too much
- **Large Classes**: Classes with too many responsibilities
- **Duplicate Code**: Same logic in multiple places
- **Magic Numbers**: Unexplained constants in code
- **Dead Code**: Unused variables, methods, or classes
- **Nested Conditionals**: Deep if/else structures
- **Temporary Fields**: Class fields only used sometimes
- **Primitive Obsession**: Using primitives instead of objects
- **Long Parameter Lists**: Functions with many parameters

## Exiting Refactor Mode

When refactoring is complete, use one of these exit phrases:
- "refactoring complete"
- "done refactoring"
- "exit refactor"

Or use the API command:
```bash
sessions smode exit
```

## Example Refactoring Flow

1. User enters mode: `/sessions smode enter refactor src/payment_processor.py`
2. You acknowledge mode entry and restrictions
3. You analyze the file and identify refactoring opportunities
4. You propose a refactoring plan and get approval
5. You make incremental improvements with testing between changes
6. You summarize improvements made
7. User says "refactoring complete" to exit the mode

Remember: The goal is to improve code quality without changing behavior. When in doubt, make smaller, safer changes and verify thoroughly.

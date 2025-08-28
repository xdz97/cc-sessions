# Task Completion Protocol

When a task meets all success criteria:

## 1. Final Testing

- Run all tests
- Verify success criteria are met
- Check for any regressions
- Ensure code quality standards

## 2. Documentation Updates

If service changes were made:
```
Use service-documentation agent to update CLAUDE.md files for affected services
```

## 3. Final Context Compaction

Run the full context compaction protocol to:
- Consolidate final work logs
- Extract and document patterns
- Capture all learnings

## 4. Create Pull Request (if applicable)

```bash
# Commit all changes
git add -A
git commit -m "Complete: [task description]"

# Push branch
git push origin [branch-name]

# Create PR
gh pr create --title "[Task]: [Description]" --body "[Summary of changes]"
```

## 5. Update Task Status

Edit task frontmatter:
- Change status to "completed"
- Add "completed: YYYY-MM-DD"
- Add final notes if needed

## 6. Move Task File

```bash
# Move to done directory
mv sessions/tasks/[task].md sessions/tasks/done/

# Or if it's a directory
mv sessions/tasks/[task]/ sessions/tasks/done/
```

## 7. Clear Task State

```bash
# Reset current task
cat > .claude/state/current_task.json << EOF
{
  "task": null,
  "branch": null,
  "services": [],
  "updated": "$(date +%Y-%m-%d)"
}
EOF
```

## 8. Return to Main Branch

```bash
git checkout main
git pull origin main
```

## Completion Checklist

- [ ] All success criteria met
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Patterns extracted
- [ ] Work logs consolidated
- [ ] PR created (if needed)
- [ ] Task moved to done/
- [ ] State cleared
- [ ] Back on main branch
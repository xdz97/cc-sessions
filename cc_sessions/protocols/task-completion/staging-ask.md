### Step 2: Review Unstaged Changes

Check for any unstaged changes:
```bash
git status
```

If changes exist, present them to user:
"I found the following unstaged changes: [list]
Would you like to:
1. Commit all changes (git add -A)
2. Select specific changes to commit
3. Review changes first"

Based on user preference, stage appropriately.
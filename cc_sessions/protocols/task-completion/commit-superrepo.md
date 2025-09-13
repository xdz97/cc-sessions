### Step 3: Commit and Merge (Super-repo Structure)

**CRITICAL ORDER**: Process from deepest submodules to super-repo

#### A. Deepest Submodules First (Depth 2+)
For any submodules within submodules:
1. Navigate to each modified deep submodule
2. Stage all changes with `git add -A`
3. Commit all changes with descriptive message
   
   {commit_style_guidance}
   
4. {merge_instruction}
5. {push_instruction}

#### B. Direct Submodules (Depth 1)
For all modified direct submodules:
1. Navigate to each modified submodule
2. Stage all changes with `git add -A`
3. Commit all changes with descriptive message
   
   {commit_style_guidance}
   
4. {merge_instruction}
5. {push_instruction}

#### C. Super-repo (Root)
After ALL submodules are committed and merged:
1. Return to super-repo root
2. Stage all changes with `git add -A`
3. Commit all changes with descriptive message
   
   {commit_style_guidance}
   
4. {merge_instruction}
5. {push_instruction}
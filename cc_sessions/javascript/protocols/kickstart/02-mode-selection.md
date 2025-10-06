SAY TO THE USER >>>
# Choose Your Onboarding Mode

cc-sessions kickstart supports three different onboarding experiences. Choose the one that fits your situation:

## Full Mode

For noobs, takes about a half hour

- Learn all the features + how to use them
- Get Claude to understand your project's patterns and tech stack
- Set up your git preferences (even if git noob)
- Set up your **trigger phrases**
- Interactive walkthrough with examples

## API Mode

For noobs using API/non-noobs wanting quick refresher
**Time**: 10-15 minutes

- Same setup as Full mode
- Just way more concise - no fluff, straight to the point

## Seshxpert Mode

For cc-sessions chads wanting interactive config for new repo

- Copy config and agent defs from another repo if you want
- Skip any step you want

## Which mode would you like?
<<<

**Instructions for handling user's mode selection:**

Determine which mode the user chose based on their response (they might say "full", "Full Mode", "I want the complete walkthrough", "api", "API mode", "seshxpert", "expert mode", etc.).

Normalize to one of: `full`, `api`, or `seshxpert`

Then run: `node sessions/scripts/api/index.js kickstart mode <selected-mode>`

Examples:
- `node sessions/scripts/api/index.js kickstart mode full`
- `node sessions/scripts/api/index.js kickstart mode api`
- `node sessions/scripts/api/index.js kickstart mode seshxpert`

The API will:
- Initialize kickstart_progress metadata with the selected mode
- Set started timestamp
- Set current_module to the first module
- Determine which mode-specific directory to use
- Return the path to the first module chunk (e.g., `kickstart/full/03-core-workflow.md`)

# Generate Git Commit

Based on the `Instructions` below, take the `Variables` follow the `Run` section to create a git commit with a properly formatted message. Then follow the `Report` section to report the results of your work.

## Variables

agent_name: $ARGUMENT
issue_class: $ARGUMENT
issue: $ARGUMENT

## Instructions

- Generate a concise commit message in the format: `<agent_name>: <issue_class>: <commit message>`
- The `<commit message>` should be:
  - Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
  - 50 characters or less
  - Descriptive of the actual changes made
  - No period at the end
- Examples:
  - `sdlc_planner: feat: add user authentication module`
  - `sdlc_implementor: bug: fix login validation error`
  - `sdlc_planner: chore: update dependencies to latest versions`
- Extract context from the issue JSON to make the commit message relevant
- Don't include any 'Generated with...' or 'Authored by...' in the commit message. Focus purely on the changes made.

## Run

1. Run `git diff HEAD` to understand what changes have been made
2. Run `git add -A` to stage all changes
3. Unstage worktree-specific files (these must never be committed to main):
   - Run `git reset HEAD -- .mcp.json .ports.env playwright-mcp-config.json 2>/dev/null || true`
   - Run `git reset HEAD -- .playwright-mcp/ 2>/dev/null || true` (Playwright MCP screenshots)
   - Run `git reset HEAD -- specs/issue-*-adw-* 2>/dev/null || true` (ADW spec files are ephemeral contracts)
   - Run `git reset HEAD -- '*.tsbuildinfo' 'app/*.tsbuildinfo' 2>/dev/null || true` (TypeScript build cache)
4. Run `git commit -m "<generated_commit_message>"` to create the commit

## Report

Return ONLY the commit message that was used (no other text)
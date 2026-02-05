# Generate Git Commit (IPE)

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
  - Descriptive of the actual infrastructure changes made
  - No period at the end
- Examples:
  - `sdlc_builder: ipe_feature: add S3 bucket module`
  - `sdlc_builder: ipe_bug: fix VPC subnet CIDR configuration`
  - `sdlc_builder: ipe_chore: update AWS provider to 5.0`
- Extract context from the issue JSON to make the commit message relevant
- Don't include any 'Generated with...' or 'Authored by...' in the commit message

## Run

1. Run `git diff HEAD` to understand what changes have been made
2. Run `git add -A` to stage all changes
3. Unstage worktree-specific files (these must never be committed to main):
   - Run `git reset HEAD -- .mcp.json .ports.env playwright-mcp-config.json 2>/dev/null || true`
   - Run `git reset HEAD -- .playwright-mcp/ 2>/dev/null || true`
   - Run `git reset HEAD -- specs/issue-*-ipe-* 2>/dev/null || true` (IPE spec files are ephemeral)
   - Run `git reset HEAD -- .io/terraform/ 2>/dev/null || true` (Terraform cache)
   - Run `git reset HEAD -- '*.tfstate' '*.tfstate.backup' 2>/dev/null || true` (Terraform state)
4. Run `git commit -m "<generated_commit_message>"` to create the commit

## Report

Return ONLY the commit message that was used (no other text)

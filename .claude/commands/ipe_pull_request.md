# Create Pull Request (IPE)

Based on the `Instructions` below, take the `Variables` follow the `Run` section to create a pull request. Then follow the `Report` section to report the results of your work.

## Variables

branch_name: $ARGUMENT
issue: $ARGUMENT
plan_file: $ARGUMENT
ipe_id: $ARGUMENT

## Instructions

- Generate a pull request title in the format: `<issue_type>: #<issue_number> - <issue_title>`
- The PR body should include:
  - A summary section with the issue context
  - Link to the implementation `plan_file` if it exists
  - Reference to the issue (Closes #<issue_number>)
  - IPE tracking ID
  - A checklist of what was done (infrastructure changes)
  - Infrastructure impact summary:
    - Terraform resources changed/added/destroyed
    - Services affected
    - Configuration changes
  - A summary of key changes made
- Extract issue number, type, and title from the issue JSON
- Examples of PR titles:
  - `ipe_feature: #123 - Add S3 bucket infrastructure`
  - `ipe_bug: #456 - Fix VPC subnet configuration`
  - `ipe_chore: #789 - Update AWS provider version`
  - `ipe_test: #1011 - Test infrastructure deployment`
- Don't mention Claude Code in the PR body - let the author get credit for this.

## Run

1. Run `git diff origin/main...HEAD --stat` to see a summary of changed files
2. Run `git log origin/main..HEAD --oneline` to see the commits that will be included
3. Run `git diff origin/main...HEAD --name-only` to get a list of changed files
4. Run `git push -u origin <branch_name>` to push the branch
5. Set GH_TOKEN environment variable from GITHUB_PAT if available, then run `gh pr create --title "<pr_title>" --body "<pr_body>" --base main` to create the PR
6. Capture the PR URL from the output

## Report

Return ONLY the PR URL that was created (no other text)

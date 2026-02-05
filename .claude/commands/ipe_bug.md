# IPE Bug Planning

Create a new plan to resolve the infrastructure `Bug` using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` to focus on the right files. Follow the `Report` section to properly report the results of your work.

## Variables
issue_number: $1
ipe_id: $2
issue_json: $3

## Instructions

- IMPORTANT: You're writing a plan to resolve an infrastructure bug based on the `Bug` that will fix issues in the infrastructure platform.
- IMPORTANT: The `Bug` describes the infrastructure bug that will be resolved but remember we're not resolving the bug, we're creating the plan that will be used to resolve the bug based on the `Plan Format` below.
- You're writing a plan to resolve an infrastructure bug, it should be thorough and precise so we fix the root cause and prevent regressions.
- CRITICAL: Create the plan file using ONLY the relative path: `specs/issue-{issue_number}-ipe-{ipe_id}-ipe_planner-{descriptive-name}.md`
  - NEVER use absolute paths - always use relative paths from the current working directory
  - The working directory is set correctly for worktree isolation - do NOT hardcode paths
  - Replace `{descriptive-name}` with a short, descriptive name based on the bug (e.g., "fix-vpc-routing", "resolve-iam-permissions", "patch-ami-build")
- Use the plan format below to create the plan.
- Research the codebase to understand the bug, reproduce it, and put together a plan to fix it.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to fix the bug.
- Use your reasoning model: THINK HARD about the bug, its root cause, and the steps to fix it properly.
- IMPORTANT: Be surgical with your bug fix, solve the bug at hand and don't fall off track.
- IMPORTANT: We want the minimal number of changes that will fix and address the infrastructure bug.
- IMPORTANT: Infrastructure bugs require extra caution:
  - Consider blast radius - what resources could be affected?
  - Test in dev environment before staging/production
  - Document rollback procedures if the fix causes issues
- Respect requested files in the `Relevant Files` section.
- Start your research by reading the `README.md` and `io/terraform/README.md` files.
- `asw/io/*.py` contain astral uv single file python scripts. If you want to run them use `uv run <script_name>`.
- When you finish creating the plan for the bug fix, follow the `Report` section to properly report the results of your work.

## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and infrastructure documentation.
- `asw/io/README.md` - Contains the Infrastructure Platform Engineer workflow documentation.
- `io/terraform/README.md` - Contains Terraform deployment documentation.
- `io/terraform/**` - Contains the Terraform infrastructure code.
- `io/terraform/*.tf` - Main Terraform configuration files (main.tf, variables.tf, outputs.tf).
- `io/terraform/modules/**` - Existing Terraform modules.
- `io/terraform/io/packer/**` - Packer configurations for AMI builds.
- `io/terraform/scripts/**` - Deployment and helper scripts.
- `asw/io/**` - Contains the IPE workflow scripts.
- `asw/io/ipe_modules/**` - Contains IPE-specific modules.

- Search for relevant documentation in `app_docs/` directory:
  - Use `ls app_docs/` to see available documentation files
  - File naming: `{type}-{adw_id}-{description}.md` where type is feature, bug, or chore
  - Use `grep -l "<keyword>" app_docs/*.md` to find docs mentioning specific components
  - Read the Overview section of matching files to determine relevance

Ignore application code (app/**, asw/app/**) unless the infrastructure bug directly relates to application deployment.

## Plan Format

```md
# Infrastructure Bug: <bug name>

## Metadata
issue_number: `{issue_number}`
ipe_id: `{ipe_id}`
issue_json: `{issue_json}`

## Bug Description
<describe the infrastructure bug in detail, including symptoms and expected vs actual behavior>

## Problem Statement
<clearly define the specific infrastructure problem that needs to be solved>

## Solution Statement
<describe the proposed solution approach to fix the infrastructure bug>

## Steps to Reproduce
<list exact steps to reproduce the infrastructure bug>

## Root Cause Analysis
<analyze and explain the root cause of the infrastructure bug>

## Impact Assessment
<describe the impact of this bug on infrastructure, services, and users>

## Relevant Files
Use these files to fix the infrastructure bug:

<find and list the files that are relevant to the bug and describe why they are relevant in bullet points. If there are new files that need to be created to fix the bug, list them in an h3 'New Files' section.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to fix the infrastructure bug. Order matters, start with the foundational shared changes required to fix the bug then move on to the specific Terraform/infrastructure changes required. Include validation that will confirm the bug is fixed with zero regressions.>

<Your last step should be running the `Validation Commands` to validate the bug is fixed with zero regressions.>

## Validation Commands
Execute every command to validate the infrastructure bug is fixed with zero regressions.

<list commands you'll use to validate with 100% confidence the infrastructure bug is fixed with zero regressions. every command must execute without errors so be specific about what you want to run to validate the bug is fixed with zero regressions.>

Infrastructure-specific validation commands:
- `cd terraform && terraform fmt -check` - Validate Terraform formatting
- `cd terraform && terraform validate` - Validate Terraform configuration syntax
- `cd terraform && terraform plan` - Generate execution plan to verify the fix
- `tflint --chdir=terraform` - Run Terraform linting (if tflint is available)
- `checkov -d terraform` - Run security scanning (if checkov is available)
- `tfsec io/terraform/` - Run security scanning (if tfsec is available)

Python syntax validation for IPE scripts (if bug affects IPE code):
- `cd ipe && python -m py_compile <affected_file>.py` - Validate Python syntax

## Rollback Plan
<describe how to rollback the fix if it causes unexpected issues>

## Notes
<optionally list any additional notes or context that are relevant to the infrastructure bug that will be helpful to the infrastructure engineer>

### Infrastructure Safety Reminders
- Test changes in dev environment before applying to staging/production
- Review terraform plan output to ensure the fix doesn't cause unexpected resource changes
- Verify the fix doesn't introduce security vulnerabilities
- Document any dependencies on the fix being applied
- Consider blast radius - what could go wrong?
```

## Bug
Extract the bug details from the `issue_json` variable (parse the JSON and use the title and body fields).

## Report

- IMPORTANT: Return exclusively the RELATIVE path to the plan file created and nothing else.
- Example: `specs/issue-123-ipe-abc12345-ipe_planner-fix-vpc-routing.md`
- Do NOT include any absolute paths or explanatory text.

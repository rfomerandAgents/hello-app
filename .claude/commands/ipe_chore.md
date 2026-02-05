# IPE Chore Planning

Create a new plan to resolve the infrastructure `Chore` using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` to focus on the right files. Follow the `Report` section to properly report the results of your work.

## Variables
issue_number: $1
ipe_id: $2
issue_json: $3

## Instructions

- IMPORTANT: You're writing a plan to resolve an infrastructure chore based on the `Chore` that will improve the infrastructure codebase quality, documentation, or maintainability.
- IMPORTANT: The `Chore` describes the infrastructure chore that will be resolved but remember we're not resolving the chore, we're creating the plan that will be used to resolve the chore based on the `Plan Format` below.
- You're writing a plan to resolve an infrastructure chore, it should be simple but we need to be thorough and precise so we don't miss anything or waste time with any second round of changes.
- Create the plan in the `specs/` directory with filename: `issue-{issue_number}-ipe-{ipe_id}-ipe_planner-{descriptive-name}.md`
  - Replace `{descriptive-name}` with a short, descriptive name based on the chore (e.g., "update-terraform-fmt", "refactor-modules", "upgrade-providers")
- Use the plan format below to create the plan.
- Research the codebase and put together a plan to accomplish the infrastructure chore.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to accomplish the chore.
- Use your reasoning model: THINK HARD about the plan and the steps to accomplish the infrastructure chore.
- Respect requested files in the `Relevant Files` section.
- Start your research by reading the `README.md` file.
- `asw/io/*.py` contain astral uv single file python scripts. So if you want to run them use `uv run <script_name>`.
- When you finish creating the plan for the chore, follow the `Report` section to properly report the results of your work.

## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and infrastructure documentation.
- `asw/io/README.md` - Contains the Infrastructure Platform Engineer workflow documentation.
- `io/terraform/README.md` - Contains Terraform deployment documentation.
- `io/terraform/**` - Contains the Terraform infrastructure code.
- `io/terraform/*.tf` - Main Terraform configuration files (main.tf, variables.tf, outputs.tf).
- `io/terraform/io/packer/**` - Packer configurations for AMI builds.
- `io/terraform/scripts/**` - Deployment and helper scripts.
- `asw/io/**` - Contains the IPE workflow scripts.
- `asw/io/ipe_modules/**` - Contains IPE-specific modules.

- Search for relevant documentation in `app_docs/` directory:
  - Use `ls app_docs/` to see available documentation files
  - File naming: `{type}-{adw_id}-{description}.md` where type is feature, bug, or chore
  - Use `grep -l "<keyword>" app_docs/*.md` to find docs mentioning specific components
  - Read the Overview section of matching files to determine relevance

Ignore application code (app/**, asw/app/**) unless the infrastructure chore directly relates to application deployment.

## Plan Format

```md
# Infrastructure Chore: <chore name>

## Metadata
issue_number: `{issue_number}`
ipe_id: `{ipe_id}`
issue_json: `{issue_json}`

## Chore Description
<describe the infrastructure chore in detail>

## Relevant Files
Use these files to resolve the infrastructure chore:

<find and list the files that are relevant to the infrastructure chore and describe why they are relevant in bullet points. If there are new files that need to be created to accomplish the chore, list them in an h3 'New Files' section.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to accomplish the infrastructure chore. Order matters, start with the foundational shared changes required to complete the chore then move on to the specific Terraform/infrastructure changes required. Your last step should be running the `Validation Commands` to validate the chore is complete with zero regressions.>

## Validation Commands
Execute every command to validate the infrastructure chore is complete with zero regressions.

<list commands you'll use to validate with 100% confidence the infrastructure chore is complete with zero regressions. every command must execute without errors so be specific about what you want to run to validate the chore is complete with zero regressions.>

Infrastructure-specific validation commands:
- `cd terraform && terraform fmt -check` - Validate Terraform formatting
- `cd terraform && terraform validate` - Validate Terraform configuration syntax
- `cd terraform && terraform plan` - Generate execution plan to verify no unintended changes
- `tflint --chdir=terraform` - Run Terraform linting (if tflint is available)
- `checkov -d terraform` - Run security scanning (if checkov is available)
- `tfsec io/terraform/` - Run security scanning (if tfsec is available)

Python syntax validation for IPE scripts (if chore affects IPE code):
- `cd ipe && python -m py_compile <affected_file>.py` - Validate Python syntax

## Notes
<optionally list any additional notes or context that are relevant to the infrastructure chore that will be helpful to the infrastructure engineer>

### Infrastructure Safety Reminders
- ✅ Test changes in dev environment before applying to staging/production
- ✅ Review terraform plan output to ensure no unexpected resource changes
- ✅ Verify terraform fmt doesn't change functional behavior, only formatting
- ✅ Ensure provider upgrades are backward compatible
- ✅ Document any breaking changes or migration steps required
```

## Chore
Extract the chore details from the `issue_json` variable (parse the JSON and use the title and body fields).

## Report

- IMPORTANT: Return exclusively the path to the plan file created and nothing else.

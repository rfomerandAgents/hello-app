# IPE Feature Planning

Create a new plan to implement the infrastructure `Feature` using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` to focus on the right files. Follow the `Report` section to properly report the results of your work.

## Variables
issue_number: $1
ipe_id: $2
issue_json: $3

## Instructions

- IMPORTANT: You're writing a plan to implement a net new infrastructure feature based on the `Feature` that will add value to the infrastructure platform.
- IMPORTANT: The `Feature` describes the infrastructure feature that will be implemented but remember we're not implementing the feature, we're creating the plan that will be used to implement the feature based on the `Plan Format` below.
- CRITICAL: Create the plan file using ONLY the relative path: `specs/issue-{issue_number}-ipe-{ipe_id}-ipe_planner-{descriptive-name}.md`
  - NEVER use absolute paths - always use relative paths from the current working directory
  - The working directory is set correctly for worktree isolation - do NOT hardcode paths
  - Replace `{descriptive-name}` with a short, descriptive name based on the feature (e.g., "create-s3-module", "add-rds-cluster", "implement-vpc-peering")
- Use the `Plan Format` below to create the plan.
- Research the codebase to understand existing Terraform patterns, module architecture, and conventions before planning the feature.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to implement the feature successfully.
- Use your reasoning model: THINK HARD about the feature requirements, design, and implementation approach.
- Follow existing Terraform patterns and conventions in the codebase. Don't reinvent the wheel.
- Design for extensibility and maintainability.
- If you need a new Terraform provider, document it in the `Notes` section of the `Plan Format`.
- IMPORTANT: Infrastructure features should follow these principles:
  - Modular design - create reusable Terraform modules when appropriate
  - Security-first - follow AWS Well-Architected Framework security best practices
  - Cost-aware - document expected costs and cost optimization opportunities
  - Environment-aware - design for dev/staging/prod environments
- Respect requested files in the `Relevant Files` section.
- Start your research by reading the `README.md` and `io/terraform/README.md` files.
- `asw/io/*.py` contain astral uv single file python scripts. If you want to run them use `uv run <script_name>`.
- When you finish creating the plan for the feature, follow the `Report` section to properly report the results of your work.

## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and infrastructure documentation.
- `asw/io/README.md` - Contains the Infrastructure Platform Engineer workflow documentation.
- `io/terraform/README.md` - Contains Terraform deployment documentation.
- `io/terraform/**` - Contains the Terraform infrastructure code.
- `io/terraform/*.tf` - Main Terraform configuration files (main.tf, variables.tf, outputs.tf).
- `io/terraform/modules/**` - Existing Terraform modules (reference for patterns).
- `io/terraform/io/packer/**` - Packer configurations for AMI builds.
- `io/terraform/scripts/**` - Deployment and helper scripts.
- `asw/io/**` - Contains the IPE workflow scripts.
- `asw/io/ipe_modules/**` - Contains IPE-specific modules.

- Search for relevant documentation in `app_docs/` directory:
  - Use `ls app_docs/` to see available documentation files
  - File naming: `{type}-{adw_id}-{description}.md` where type is feature, bug, or chore
  - Use `grep -l "<keyword>" app_docs/*.md` to find docs mentioning specific components
  - Read the Overview section of matching files to determine relevance

Ignore application code (app/**, asw/app/**) unless the infrastructure feature directly relates to application deployment.

## Plan Format

```md
# Infrastructure Feature: <feature name>

## Metadata
issue_number: `{issue_number}`
ipe_id: `{ipe_id}`
issue_json: `{issue_json}`

## Feature Description
<describe the infrastructure feature in detail, including its purpose and value to the platform>

## User Story
As a <type of user (platform engineer, developer, ops team)>
I want to <action/goal>
So that <benefit/value>

## Problem Statement
<clearly define the specific problem or opportunity this infrastructure feature addresses>

## Solution Statement
<describe the proposed solution approach and how it solves the problem>

## Relevant Files
Use these files to implement the infrastructure feature:

<find and list the files that are relevant to the feature and describe why they are relevant in bullet points. If there are new files that need to be created to implement the feature, list them in an h3 'New Files' section.>

## Implementation Plan
### Phase 1: Foundation
<describe the foundational work needed before implementing the main feature (e.g., module structure, provider configuration)>

### Phase 2: Core Implementation
<describe the main Terraform/infrastructure implementation work for the feature>

### Phase 3: Integration
<describe how the feature will integrate with existing infrastructure and CI/CD pipelines>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to implement the infrastructure feature. Order matters, start with the foundational shared changes required then move on to the specific Terraform implementation. Include creating tests throughout the implementation process.>

<Your last step should be running the `Validation Commands` to validate the feature works correctly with zero regressions.>

## Testing Strategy
### Terraform Validation
<describe terraform validate and fmt checks>

### Plan Verification
<describe how to verify terraform plan shows expected changes>

### Security Scanning
<describe security scanning approach using tfsec, checkov, etc.>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the infrastructure feature to be considered complete>

## Validation Commands
Execute every command to validate the infrastructure feature works correctly with zero regressions.

<list commands you'll use to validate with 100% confidence the feature is implemented correctly with zero regressions. every command must execute without errors so be specific about what you want to run to validate the feature works as expected.>

Infrastructure-specific validation commands:
- `cd terraform && terraform fmt -check` - Validate Terraform formatting
- `cd terraform && terraform validate` - Validate Terraform configuration syntax
- `cd terraform && terraform plan` - Generate execution plan to verify expected changes
- `tflint --chdir=terraform` - Run Terraform linting (if tflint is available)
- `checkov -d terraform` - Run security scanning (if checkov is available)
- `tfsec io/terraform/` - Run security scanning (if tfsec is available)

Python syntax validation for IPE scripts (if feature affects IPE code):
- `cd ipe && python -m py_compile <affected_file>.py` - Validate Python syntax

## Cost Considerations
<document expected AWS costs and any cost optimization recommendations>

## Notes
<optionally list any additional notes, future considerations, or context that are relevant to the infrastructure feature that will be helpful to the infrastructure engineer>

### Infrastructure Safety Reminders
- Test changes in dev environment before applying to staging/production
- Review terraform plan output to ensure no unexpected resource changes
- Ensure provider dependencies are properly versioned
- Document any breaking changes or migration steps required
- Consider blast radius - what could go wrong?
```

## Feature
Extract the feature details from the `issue_json` variable (parse the JSON and use the title and body fields).

## Report

- IMPORTANT: Return exclusively the RELATIVE path to the plan file created and nothing else.
- Example: `specs/issue-123-ipe-abc12345-ipe_planner-create-s3-module.md`
- Do NOT include any absolute paths or explanatory text.

# IPE Review

Follow the `Instructions` below to **review infrastructure code against a specification file** (specs/*.md) to ensure implemented Terraform configurations match requirements. Use the spec file to understand the infrastructure requirements and then use the git diff to understand the changes made. Focus on security, policy compliance, cost implications, and best practices.

## Variables

workflow_id: $ARGUMENT
spec_file: $ARGUMENT
terraform_dir: $ARGUMENT
agent_name: $ARGUMENT if provided, otherwise use 'ipe_review_agent'

## Instructions

- Check current git branch using `git branch` to understand context
- Run `git diff origin/main` to see all changes made in current branch. Continue even if there are no changes related to the spec file.
- Find the spec file by looking for specs/*.md files in the diff that match the current branch name
- Read the identified spec file to understand infrastructure requirements
- Read the Terraform code in `terraform_dir` to understand what was implemented
- IMPORTANT: Focus your review on these critical areas for infrastructure:
  1. **Security**: Check for hardcoded secrets, overly permissive security groups, missing encryption, public access where it shouldn't be
  2. **Best Practices**: Proper naming conventions, tagging, documentation, modularity, state management
  3. **Compliance**: Meets organizational policies, follows cloud provider best practices
  4. **Quality**: Code organization, proper use of variables/outputs, resource dependencies
  5. **Cost Implications**: Identify expensive resources, unnecessary redundancy, missing autoscaling
- IMPORTANT: Review the Terraform code without running terraform apply. This is a code review, not a deployment.
- Compare implemented Terraform against spec requirements to verify correctness
- IMPORTANT: Issue Severity Guidelines for Infrastructure
  - Think hard about the impact of the issue on security, cost, and operations
  - Guidelines:
    - `skippable` - Minor style or documentation issues that don't affect functionality
    - `tech_debt` - Best practice violations that should be addressed but don't block deployment (e.g., missing tags, poor naming)
    - `blocker` - Security vulnerabilities, policy violations, or configuration errors that must be fixed before deployment
- IMPORTANT: Return ONLY the JSON object with review results
  - IMPORTANT: Output your result in JSON format based on the `Report` section below.
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- Ultra think as you work through the review process. Focus on security, compliance, and cost implications.

## Security Scanning Notes

The IPE workflow will automatically run security scans (Checkov, tfsec) and best practices linting (tflint) after your review. Focus on:
- Logic and design issues that automated tools might miss
- Whether the implementation matches the specification
- Overall architecture and resource organization
- Cost optimization opportunities

Automated tools will catch:
- Common security misconfigurations
- Policy violations
- Terraform syntax issues

## Report

- IMPORTANT: Return results exclusively as a JSON object based on the `Output Structure` section below.
- `success` should be `true` if there are NO BLOCKING issues (implementation matches spec for critical infrastructure)
- `success` should be `false` ONLY if there are BLOCKING issues that prevent the infrastructure from being deployed
- `review_issues` can contain issues of any severity (skippable, tech_debt, or blocker)
- `screenshots` should be an empty array (infrastructure code doesn't use screenshots)
- This allows subsequent agents to quickly identify and resolve blocking errors while documenting all issues

### Output Structure

```json
{
    "success": "boolean - true if there are NO BLOCKING issues (can have skippable/tech_debt issues), false if there are BLOCKING issues",
    "review_summary": "string - 2-4 sentences describing what infrastructure was defined and whether it matches the spec. Written as if reporting during a standup meeting. Example: 'The EC2 instance configuration has been implemented with proper security groups and IAM roles. The implementation matches the spec requirements for high availability and auto-scaling. Cost optimization could be improved by using Spot instances but all core infrastructure requirements are met.'",
    "review_issues": [
        {
            "review_issue_number": "number - the issue number based on the index of this issue",
            "screenshot_path": "string - always empty string for infrastructure review",
            "issue_description": "string - description of the infrastructure issue (e.g., 'Security group allows 0.0.0.0/0 access on port 22')",
            "issue_resolution": "string - description of how to fix the issue (e.g., 'Restrict SSH access to specific IP ranges or use AWS Systems Manager Session Manager')",
            "issue_severity": "string - severity of the issue: 'skippable', 'tech_debt', or 'blocker'"
        }
    ],
    "screenshots": []
}
```

## Example Issues

### Security Issue (Blocker)
```json
{
    "review_issue_number": 1,
    "screenshot_path": "",
    "issue_description": "RDS instance has publicly_accessible set to true, exposing database to internet",
    "issue_resolution": "Set publicly_accessible to false and use VPN or bastion host for database access",
    "issue_severity": "blocker"
}
```

### Best Practice Issue (Tech Debt)
```json
{
    "review_issue_number": 2,
    "screenshot_path": "",
    "issue_description": "Resources missing required tags (Environment, Project, Owner)",
    "issue_resolution": "Add tags to all resources using a locals block for consistency",
    "issue_severity": "tech_debt"
}
```

### Cost Optimization (Skippable)
```json
{
    "review_issue_number": 3,
    "screenshot_path": "",
    "issue_description": "Using on-demand instances when Spot instances could reduce costs by 70%",
    "issue_resolution": "Consider using Spot instances for non-critical workloads with spot_instance_requests",
    "issue_severity": "skippable"
}
```

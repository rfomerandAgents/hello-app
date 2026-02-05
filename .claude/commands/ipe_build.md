# IPE Build - Implement Infrastructure Plan

## Run
/prime

IMPORTANT: You must use the Task tool to launch the plan-implementer subagent. Do NOT implement the plan directly.

Launch the plan-implementer subagent with the following prompt:

---

Implement the infrastructure plan in the following file: $ARGUMENTS

This is an Agentic Software Workflow - IO (ASW IO) workflow for Terraform/infrastructure code.

Read the plan file thoroughly, then systematically implement each phase and step in order. Focus on:
1. Creating Terraform modules, resources, and configurations
2. Following Terraform best practices (proper naming, tagging, security)
3. Running `terraform fmt -recursive` to format code
4. Running `terraform validate` to validate configurations
5. Following all dependencies and verifying each step's success criteria

After implementation, provide:
1. Summary of completed infrastructure work (concise bullet points)
2. Any deviations from the plan and why
3. Git diff stats showing files changed
4. Terraform validation results
5. Any issues encountered and resolutions

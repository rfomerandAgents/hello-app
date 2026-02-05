# Github Issue Command Selection

Based on the `Github Issue` below, follow the `Instructions` to select the appropriate command to execute based on the `Command Mapping`.

## Instructions

- Based on the details in the `Github Issue`, select the appropriate command to execute.
- IMPORTANT: Respond exclusively with '/' followed by the command to execute based on the `Command Mapping` below.
- Use the command mapping to help you decide which command to respond with.
- Don't examine the codebase just focus on the `Github Issue` and the `Command Mapping` below to determine the appropriate command to execute.
- **NEW:** Determine if the issue is related to infrastructure/Terraform or application code to select between ADW and IPE commands.

## Infrastructure Detection

Analyze the issue for infrastructure-related keywords and context:

**Infrastructure Indicators (use IPE commands):**
- **Terraform-related**: terraform, tfstate, tfvars, .tf files, modules, providers, workspaces
- **Cloud Resources**: AWS, Azure, GCP, EC2, RDS, S3, VPC, security groups, IAM, CloudFront, Lambda, ECS
- **Infrastructure Keywords**: infrastructure, infra, deployment, provisioning, cloud, resources
- **Security/Compliance**: encryption, KMS, secrets, compliance, audit, access controls, network security
- **Cost Optimization**: cost, pricing, reserved instances, spot instances, lifecycle policies
- **Configuration**: backend config, state management, remote state, workspace configuration
- **DevOps/Platform**: CI/CD infrastructure, monitoring setup, logging infrastructure, alerting setup

**Application Indicators (use ADW commands):**
- **Code-related**: React, TypeScript, JavaScript, Node.js, npm, components, UI, frontend, backend
- **Application Features**: user auth, login, forms, buttons, pages, routing, API endpoints
- **Application Keywords**: application, app, website, web app, feature, functionality
- **Testing**: unit tests, E2E tests, Playwright, Jest, component testing
- **Application Bugs**: runtime errors, crashes, UI bugs, logic errors, data validation

**Default Behavior:**
- If issue mentions BOTH infrastructure and application, prioritize infrastructure (more critical/risky)
- If unclear, examine the issue body for file paths (io/terraform/, *.tf → infrastructure)
- If still unclear, default to application (ADW) to maintain backward compatibility

## Command Mapping

**Application Developer Workflow (ADW) Commands:**
- Respond with `/chore` if the issue is an application maintenance task (formatting, dependencies, cleanup)
- Respond with `/bug` if the issue is an application bug (UI issues, logic errors, runtime crashes)
- Respond with `/feature` if the issue is a new application feature (new pages, components, functionality)
- Respond with `/patch` if the issue is a quick application patch (hotfix, small fix)

**Agentic Software Workflow - IO (ASW IO) Commands:**
- Respond with `/ipe_chore` if the issue is infrastructure maintenance (terraform fmt, provider updates, module cleanup)
- Respond with `/ipe_bug` if the issue is an infrastructure bug (misconfigurations, broken Terraform, security holes)
- Respond with `/ipe_feature` if the issue is new infrastructure (new VPC, RDS database, S3 bucket, CloudFront CDN)
- Respond with `/ipe_patch` if the issue is a quick infrastructure patch (security fix, urgent config change)

**Special Cases:**
- Respond with `0` if the issue isn't any of the above (documentation, discussion, question, etc.)

**Priority Rules:**
1. Infrastructure issues take precedence (if mixed signals, use IPE commands)
2. Security-related infrastructure issues should use `/ipe_bug` or `/ipe_patch` (depending on urgency)
3. Cost optimization should use `/ipe_chore` (maintenance) or `/ipe_feature` (new cost-saving resources)

## Classification Examples

### Infrastructure Examples

**Example 1: Infrastructure Chore**
```
Title: "Update Terraform AWS provider to 5.0"
Body: "Need to update the AWS provider version in io/terraform/versions.tf"
```
→ Response: `/ipe_chore`

**Example 2: Infrastructure Bug**
```
Title: "Security group allows SSH from 0.0.0.0/0"
Body: "Our security group is misconfigured and allows SSH from anywhere. This is a security vulnerability."
```
→ Response: `/ipe_bug`

**Example 3: Infrastructure Feature**
```
Title: "Add RDS PostgreSQL database with Multi-AZ"
Body: "We need to provision a new RDS PostgreSQL database with Multi-AZ failover for the production environment."
```
→ Response: `/ipe_feature`

**Example 4: Infrastructure Patch**
```
Title: "URGENT: Enable S3 encryption immediately"
Body: "S3 bucket is not encrypted. Need to enable KMS encryption ASAP for compliance."
```
→ Response: `/ipe_patch`

### Application Examples

**Example 5: Application Chore**
```
Title: "Update npm dependencies"
Body: "Need to update React and other npm packages in package.json"
```
→ Response: `/chore`

**Example 6: Application Bug**
```
Title: "Login button not working on mobile"
Body: "The login button doesn't respond to clicks on mobile devices. Works fine on desktop."
```
→ Response: `/bug`

**Example 7: Application Feature**
```
Title: "Add user profile page"
Body: "Create a new user profile page showing user information and settings."
```
→ Response: `/feature`

**Example 8: Application Patch**
```
Title: "Fix typo in hero section"
Body: "There's a typo in the hero section text: '{{PROJECT_NAME}} Fram' should be '{{PROJECT_NAME}}'"
```
→ Response: `/patch`

### Mixed/Edge Cases

**Example 9: Mixed Infrastructure + Application**
```
Title: "Deploy new app version with infrastructure changes"
Body: "Deploy new React app version AND update CloudFront CDN configuration."
```
→ Response: `/ipe_feature` (infrastructure takes precedence - CloudFront is infrastructure)

**Example 10: File Path Hint**
```
Title: "Fix issue in main.tf"
Body: "There's an error in io/terraform/main.tf that's causing plan to fail."
```
→ Response: `/ipe_bug` (file path io/terraform/main.tf indicates infrastructure)

**Example 11: Documentation (Not Classified)**
```
Title: "Update README with new setup instructions"
Body: "Need to document the new installation process in README.md"
```
→ Response: `0` (documentation, not a code change)

## Infrastructure Keyword Reference

### Terraform-Specific Keywords

| Keyword | Category | IPE Command |
|---------|----------|-------------|
| terraform, tfstate, tfvars, .tf | Terraform Core | Context-dependent |
| terraform plan, terraform apply | Terraform Operations | `/ipe_bug` or `/ipe_chore` |
| provider, module, resource | Terraform Components | `/ipe_feature` or `/ipe_bug` |
| workspace, backend | Terraform Config | `/ipe_chore` or `/ipe_bug` |

### Cloud Provider Keywords

| Keyword | Category | IPE Command |
|---------|----------|-------------|
| AWS, EC2, RDS, S3, VPC | AWS Resources | `/ipe_feature` (new) or `/ipe_bug` (fix) |
| Azure, GCP, Kubernetes | Other Cloud | `/ipe_feature` (new) or `/ipe_bug` (fix) |
| CloudFront, Lambda, ECS, EKS | AWS Services | `/ipe_feature` (new) or `/ipe_bug` (fix) |
| IAM, KMS, security group | Security Resources | `/ipe_bug` (security issue) or `/ipe_feature` (new) |

### Infrastructure Task Keywords

| Keyword | Category | IPE Command |
|---------|----------|-------------|
| encryption, KMS, secrets | Security | `/ipe_bug` (vulnerability) or `/ipe_patch` (urgent) |
| cost, pricing, reserved instances | Cost Optimization | `/ipe_chore` (optimization) or `/ipe_feature` (new) |
| backup, retention, disaster recovery | Data Management | `/ipe_feature` (new setup) or `/ipe_bug` (broken) |
| monitoring, logging, alerting | Observability | `/ipe_feature` (new) or `/ipe_chore` (updates) |

### Application-Specific Keywords

| Keyword | Category | ADW Command |
|---------|----------|-------------|
| React, component, UI, frontend | Frontend | `/feature` or `/bug` |
| API, endpoint, backend, server | Backend | `/feature` or `/bug` |
| npm, package.json, dependencies | Dependencies | `/chore` |
| test, E2E, unit test, Playwright | Testing | `/bug` or `/chore` |

## Decision Tree for Classification

```
┌─────────────────────────────────────┐
│  Analyze GitHub Issue               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Check for Infrastructure Keywords  │
│  (Terraform, AWS, Cloud, Security)  │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    ┌────▼────┐ ┌────▼────┐
    │  Found  │ │Not Found│
    └────┬────┘ └────┬────┘
         │           │
         │           ▼
         │     ┌─────────────────────┐
         │     │ Application Issue   │
         │     │ Use ADW Commands    │
         │     └──────┬──────────────┘
         │            │
         ▼            ▼
┌─────────────────────────────────────┐
│  Determine Issue Type:              │
│  - Chore: Maintenance, updates      │
│  - Bug: Errors, misconfigurations   │
│  - Feature: New resources/features  │
│  - Patch: Urgent/quick fixes        │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    ┌────▼────┐ ┌────▼────┐
    │  Infra  │ │   App   │
    └────┬────┘ └────┬────┘
         │           │
         ▼           ▼
┌────────────┐ ┌──────────┐
│ /ipe_*     │ │ /chore   │
│ /ipe_bug   │ │ /bug     │
│ /ipe_feat  │ │ /feature │
│ /ipe_patch │ │ /patch   │
└────────────┘ └──────────┘
```

## Github Issue

$ARGUMENTS
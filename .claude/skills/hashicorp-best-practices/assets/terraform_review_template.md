# Terraform Code Review Template

Use this template for systematic Terraform code reviews.

---

## Project Information

- **Project Name:** _________
- **Environment:** [ ] Dev [ ] Staging [ ] Prod
- **Reviewer:** _________
- **Review Date:** _________
- **Terraform Version:** _________
- **Provider Versions:** _________

---

## Quick Wins Check (30 seconds)

- [ ] `terraform fmt` compliance
- [ ] No hardcoded secrets or credentials
- [ ] All resources have Name tags
- [ ] Variables have descriptions
- [ ] Outputs exist for commonly needed values
- [ ] No hardcoded AMI IDs or resource IDs

---

## Variables Review

### Type Constraints
- [ ] All variables have explicit `type` declarations
- [ ] Complex types use `object()` instead of `map(string)`
- [ ] No unnecessary `string` types (use `number`, `bool` where appropriate)

### Validation
- [ ] Environment variables have `validation` blocks
- [ ] CIDR blocks are validated
- [ ] Instance types are validated
- [ ] Enums use `contains()` validation

### Documentation
- [ ] All variables have `description`
- [ ] Defaults are sensible and documented
- [ ] Sensitive variables marked with `sensitive = true`

### Issues Found:
```
Variable Name: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Resources Review

### Lifecycle Rules
- [ ] Security groups use `create_before_destroy`
- [ ] Production resources use `prevent_destroy`
- [ ] AMI/user_data changes use `ignore_changes` where appropriate
- [ ] Launch configurations/templates use `create_before_destroy`

### Timeouts
- [ ] RDS instances have explicit timeouts
- [ ] ECS services have explicit timeouts
- [ ] Long-running resources have appropriate timeouts

### Dependencies
- [ ] Dependencies are explicit with `depends_on` where needed
- [ ] No circular dependencies
- [ ] Module boundaries are clear

### Tagging
- [ ] All resources have tags
- [ ] Common tags use locals
- [ ] Name tag follows naming convention
- [ ] Environment, Project, ManagedBy tags present

### Issues Found:
```
Resource: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## State Management Review

### Backend Configuration
- [ ] Remote backend configured (not local)
- [ ] State encryption enabled
- [ ] State locking enabled
- [ ] Versioning enabled on state bucket
- [ ] MFA delete enabled for production

### State Isolation
- [ ] Separate state files per environment
- [ ] Separate state files per component (if large)
- [ ] State file size < 10MB
- [ ] Resource count < 1000 per state

### Issues Found:
```
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Security Review

### Encryption
- [ ] All EBS volumes encrypted
- [ ] All RDS instances encrypted
- [ ] All S3 buckets have encryption configured
- [ ] KMS keys used (not default AWS keys)

### Network Security
- [ ] No 0.0.0.0/0 for SSH (port 22)
- [ ] Security groups follow least privilege
- [ ] RDS instances not publicly accessible
- [ ] Security groups have descriptions on rules

### IMDSv2
- [ ] All EC2 instances enforce IMDSv2
- [ ] `http_tokens = "required"` in metadata_options

### Secrets Management
- [ ] No hardcoded passwords
- [ ] Secrets Manager used for sensitive data
- [ ] Sensitive outputs marked as sensitive
- [ ] No credentials in version control

### IAM
- [ ] IAM policies follow least privilege
- [ ] IAM roles used instead of access keys
- [ ] Policy documents use specific actions (not *)
- [ ] Resource ARNs are specific (not *)

### Issues Found:
```
Resource: _________
Security Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
Risk: _________
```

---

## Module Review

### Structure
- [ ] README.md exists with examples
- [ ] versions.tf exists with version constraints
- [ ] Variables have descriptions
- [ ] Outputs have descriptions
- [ ] Examples directory exists

### Interface Design
- [ ] Module variables are stable
- [ ] Required variables are minimal
- [ ] Defaults are sensible
- [ ] Module is focused (single responsibility)

### Versioning
- [ ] Module source uses version constraint
- [ ] Semantic versioning followed
- [ ] Breaking changes avoided

### Issues Found:
```
Module: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Performance Review

### Plan/Apply Speed
- [ ] Parallelism appropriate for deployment size
- [ ] Data sources used efficiently
- [ ] No unnecessary remote state data sources
- [ ] for_each used instead of count where appropriate

### State File
- [ ] State file split if > 1000 resources
- [ ] State file split by blast radius
- [ ] State file split by team ownership

### Issues Found:
```
Issue: _________
Impact: _________
Fix: _________
```

---

## Cost Optimization Review

### Compute
- [ ] Instance types right-sized
- [ ] Burstable instances (t3/t4) used for variable loads
- [ ] Spot instances considered for non-critical workloads
- [ ] Auto-scaling configured where appropriate

### Storage
- [ ] gp3 used instead of gp2
- [ ] EBS volumes right-sized
- [ ] S3 lifecycle policies configured
- [ ] Unused snapshots will be deleted

### Database
- [ ] RDS instance size appropriate
- [ ] Multi-AZ only in production
- [ ] Backup retention period optimized

### Network
- [ ] NAT Gateway usage minimized
- [ ] VPC endpoints used for AWS services
- [ ] Data transfer minimized

### Issues Found:
```
Resource: _________
Cost Impact: $_________/month
Optimization: _________
```

---

## Maintainability Review

### Code Organization
- [ ] Logical file structure (main.tf, variables.tf, outputs.tf)
- [ ] Consistent naming convention
- [ ] Complex logic has comments
- [ ] No duplicate code (DRY principle followed)

### Documentation
- [ ] README exists
- [ ] Usage examples provided
- [ ] Architecture diagrams (for complex setups)
- [ ] Known issues documented

### Version Control
- [ ] .gitignore configured properly
- [ ] No .tfstate files in git
- [ ] No .tfvars with secrets in git
- [ ] Commit messages are descriptive

### Issues Found:
```
Issue: _________
Impact on Maintainability: _________
Fix: _________
```

---

## Anti-Pattern Detection

### Common Anti-Patterns
- [ ] No "God Module" (> 500 lines in main.tf)
- [ ] No "Copy-Paste Environments"
- [ ] No "Naked Variables" (without validation)
- [ ] No "Count Trap" (using count for variable-length lists)
- [ ] No "Magic Strings" (hardcoded AMI IDs, subnet IDs)
- [ ] No "Wide-Open Security Groups" (0.0.0.0/0 on all ports)
- [ ] No "State Monolith" (> 1000 resources in one state)
- [ ] No "Unencrypted Resources"
- [ ] No "Sensitive Outputs" (unmarked)

### Anti-Patterns Found:
```
Anti-Pattern: _________
Location: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Testing and Validation

### Pre-Merge
- [ ] `terraform fmt -check` passes
- [ ] `terraform validate` passes
- [ ] `terraform plan` reviewed
- [ ] Security scan passed (tfsec/checkov/terrascan)

### Automated Tests
- [ ] Unit tests exist (if applicable)
- [ ] Integration tests exist (if applicable)
- [ ] Tests pass in CI/CD pipeline

### Issues Found:
```
Test: _________
Status: [ ] Pass [ ] Fail
Issue: _________
```

---

## Final Verdict

### Summary

**PRAISE:**
- _________
- _________
- _________

**CRITICAL Issues:** (Must fix before merge)
1. _________
2. _________

**WARNING Issues:** (Should fix, creates technical debt)
1. _________
2. _________

**SUGGESTIONS:** (Nice to have)
1. _________
2. _________

### Recommendation

- [ ] **APPROVED** - Merge after addressing CRITICAL issues
- [ ] **APPROVED WITH CHANGES** - Address CRITICAL and WARNING issues
- [ ] **CHANGES REQUESTED** - Major rework needed
- [ ] **REJECTED** - FunparentBental design issues

### Reviewer Notes:
```
_________________________________________
_________________________________________
_________________________________________
```

### Follow-Up Items:
1. _________
2. _________
3. _________

---

## Review Checklist Complete

- [ ] All sections reviewed
- [ ] All issues documented
- [ ] Severity levels assigned
- [ ] Fixes proposed
- [ ] Verdict provided
- [ ] Feedback shared with author

**Reviewer Signature:** _________
**Date:** _________

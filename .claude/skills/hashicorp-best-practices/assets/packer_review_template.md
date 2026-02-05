# Packer Build Review Template

Use this template for systematic Packer build configuration reviews.

---

## Build Information

- **Project Name:** _________
- **AMI Name Pattern:** _________
- **Base OS:** _________
- **Reviewer:** _________
- **Review Date:** _________
- **Packer Version:** _________

---

## Quick Wins Check (30 seconds)

- [ ] `packer fmt` compliance
- [ ] No hardcoded AMI IDs
- [ ] No hardcoded secrets
- [ ] Variables have descriptions
- [ ] IMDSv2 enabled
- [ ] Encryption enabled

---

## Source Configuration Review

### AMI Selection
- [ ] Uses `source_ami_filter` (not hardcoded AMI ID)
- [ ] `most_recent = true` set
- [ ] Owner ID specified
- [ ] Filters are specific enough

### Instance Configuration
- [ ] Appropriate instance type for build workload
- [ ] EBS optimization enabled
- [ ] Enhanced networking enabled (ena_support, sriov_support)
- [ ] Region specified

### Networking
- [ ] SSH configuration appropriate (timeout, interface)
- [ ] Public IP association correct for environment
- [ ] VPC/subnet configuration (if private build)
- [ ] Security group configuration secure

### Issues Found:
```
Component: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Build Configuration Review

### AMI Naming
- [ ] AMI name includes version
- [ ] AMI name includes timestamp
- [ ] AMI name pattern is consistent
- [ ] AMI name avoids conflicts

### AMI Distribution
- [ ] Target regions specified (if multi-region)
- [ ] Regional KMS keys configured
- [ ] AMI tags comprehensive

### AMI Lifecycle
- [ ] force_deregister setting appropriate
- [ ] force_delete_snapshot setting appropriate
- [ ] Cleanup strategy defined

### Issues Found:
```
Component: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Provisioner Review

### Provisioner Consolidation
- [ ] Shell provisioners consolidated (< 5 total)
- [ ] Scripts used instead of long inline commands
- [ ] Provisioners ordered logically

### Error Handling
- [ ] Scripts use `set -euo pipefail`
- [ ] Retry logic for network operations
- [ ] Cleanup on failure considered

### Efficiency
- [ ] Packages installed without recommendations flag
- [ ] DEBIAN_FRONTEND=noninteractive set
- [ ] Single apt-get update (not multiple)
- [ ] Related installations grouped

### File Uploads
- [ ] File provisioner used appropriately
- [ ] Permissions set correctly after upload
- [ ] Ownership set correctly

### Issues Found:
```
Provisioner: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Security Review

### IMDSv2
- [ ] `http_tokens = "required"` in metadata_options
- [ ] `http_endpoint = "enabled"`
- [ ] `http_put_response_hop_limit` set appropriately

### Encryption
- [ ] `encrypt_boot = true`
- [ ] KMS key specified (not default)
- [ ] Snapshot encryption tags set

### Build Security
- [ ] temporary_security_group_source_cidrs restricted (not 0.0.0.0/0)
- [ ] Or existing security_group_ids used
- [ ] IAM permissions minimal (if specified)

### SSH Hardening
- [ ] PermitRootLogin disabled
- [ ] PasswordAuthentication disabled
- [ ] SSH host keys removed in cleanup

### Secrets Management
- [ ] No secrets baked into AMI
- [ ] Secrets Manager integration documented
- [ ] API keys/passwords not in provisioners

### System Hardening
- [ ] Automatic security updates configured
- [ ] Firewall configured (ufw/iptables)
- [ ] fail2ban configured
- [ ] Unnecessary services disabled

### Issues Found:
```
Security Issue: _________
Risk Level: [ ] CRITICAL [ ] HIGH [ ] MEDIUM [ ] LOW
Fix: _________
Impact if Exploited: _________
```

---

## Cleanup Review

### Package Cleanup
- [ ] apt-get clean executed
- [ ] Package cache removed
- [ ] autoremove executed

### Log Cleanup
- [ ] Logs truncated
- [ ] Log archives removed
- [ ] Application logs cleared

### Temporary Files
- [ ] /tmp cleared
- [ ] /var/tmp cleared
- [ ] User cache cleared

### System Cleanup
- [ ] SSH host keys removed
- [ ] bash history cleared
- [ ] cloud-init cleaned
- [ ] machine-id cleared

### Issues Found:
```
Cleanup Item: _________
Impact: _________
Fix: _________
```

---

## Post-Processor Review

### Manifest
- [ ] manifest post-processor exists
- [ ] Output file specified
- [ ] custom_data includes version
- [ ] custom_data includes git commit
- [ ] custom_data includes environment

### Other Post-Processors
- [ ] Checksum post-processor (if needed)
- [ ] Additional post-processors appropriate

### Issues Found:
```
Post-Processor: _________
Issue: _________
Fix: _________
```

---

## Variable Review

### Variable Definitions
- [ ] All variables have descriptions
- [ ] Types are explicit
- [ ] Defaults are sensible
- [ ] Validation rules exist for critical variables

### Environment-Specific Variables
- [ ] Environment variable validated
- [ ] Version variable exists
- [ ] Git commit variable exists

### Issues Found:
```
Variable: _________
Issue: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## Build Performance Review

### Instance Selection
- [ ] Compute-optimized instance for builds
- [ ] Instance size appropriate for workload
- [ ] Current generation instance type

### Storage Performance
- [ ] gp3 volumes with high IOPS
- [ ] Volume size appropriate
- [ ] Ephemeral storage used if beneficial

### Network Performance
- [ ] Enhanced networking enabled
- [ ] Build in same region as source AMI
- [ ] VPC endpoints used (if applicable)

### Build Time
- [ ] Provisioners consolidated for speed
- [ ] Parallel builds used (if multiple variants)
- [ ] Package downloads cached

### Issues Found:
```
Performance Issue: _________
Current Build Time: _________
Expected Improvement: _________
Fix: _________
```

---

## Anti-Pattern Detection

### Common Packer Anti-Patterns
- [ ] No hardcoded AMI IDs
- [ ] No provisioner spam (> 10 provisioners)
- [ ] No missing manifest post-processor
- [ ] No IMDSv1 instances
- [ ] No wide-open build security groups (0.0.0.0/0)
- [ ] No unencrypted AMIs
- [ ] No cleanup omissions
- [ ] No inline secrets
- [ ] No inefficient instance types

### Anti-Patterns Found:
```
Anti-Pattern: _________
Location: _________
Severity: [ ] CRITICAL [ ] WARNING [ ] SUGGESTION
Fix: _________
```

---

## CI/CD Integration Review

### GitHub Actions / GitLab CI
- [ ] Packer validation in pipeline
- [ ] Packer formatting check
- [ ] Build triggered appropriately
- [ ] Variables passed from CI correctly
- [ ] Manifest uploaded as artifact

### AWS Credentials
- [ ] OIDC used (not access keys)
- [ ] IAM permissions minimal
- [ ] Credentials not hardcoded

### Build Metadata
- [ ] Git commit SHA passed to build
- [ ] Version tag passed to build
- [ ] Build number tracked

### Issues Found:
```
CI/CD Issue: _________
Fix: _________
```

---

## Testing and Validation Review

### Pre-Build Validation
- [ ] `packer init` executed
- [ ] `packer validate` passes
- [ ] `packer fmt -check` passes

### Post-Build Testing
- [ ] AMI tested (launch instance)
- [ ] Application verified on AMI
- [ ] Security scanning completed
- [ ] Automated tests exist

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

**CRITICAL Issues:** (Must fix before building production AMIs)
1. _________
2. _________

**WARNING Issues:** (Should fix, creates technical/security debt)
1. _________
2. _________

**SUGGESTIONS:** (Optimizations and improvements)
1. _________
2. _________

### Estimated Build Time
- **Current:** _________
- **After Optimizations:** _________
- **Improvement:** _________%

### Estimated AMI Size
- **Current:** _________ GB
- **After Cleanup:** _________ GB
- **Reduction:** _________%

### Recommendation

- [ ] **APPROVED** - Build production AMIs
- [ ] **APPROVED WITH CHANGES** - Address CRITICAL issues first
- [ ] **CHANGES REQUESTED** - Rework needed
- [ ] **REJECTED** - FunparentBental issues

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

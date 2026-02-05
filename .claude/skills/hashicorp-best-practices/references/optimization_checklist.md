# HashiCorp Optimization Checklist

Systematic checklists for optimizing Terraform and Packer configurations across performance, cost, security, and maintainability dimensions.

## Table of Contents

1. [Terraform Performance Optimization](#terraform-performance-optimization)
2. [Terraform Cost Optimization](#terraform-cost-optimization)
3. [Packer Build Speed Optimization](#packer-build-speed-optimization)
4. [Packer Image Size Optimization](#packer-image-size-optimization)
5. [Security Hardening Checklist](#security-hardening-checklist)
6. [Maintainability Checklist](#maintainability-checklist)

---

## Terraform Performance Optimization

### State Management

- [ ] **Use remote state backend** (S3, Terraform Cloud, not local)
- [ ] **Enable state locking** (DynamoDB for S3 backend)
- [ ] **Split large state files** (< 1000 resources per state file)
- [ ] **Isolate by environment** (separate state files for dev/staging/prod)
- [ ] **Isolate by component** (networking, compute, data in separate states)
- [ ] **Use workspaces judiciously** (or avoid for production)

**Check:**
```bash
# Check state size
terraform state list | wc -l

# If > 1000 resources, consider splitting
```

### Plan/Apply Performance

- [ ] **Increase parallelism** for large deployments
  ```bash
  terraform apply -parallelism=50  # Default is 10
  ```

- [ ] **Use -target** for selective applies during development
  ```bash
  terraform apply -target=aws_instance.web
  ```

- [ ] **Avoid unnecessary data source queries**
  ```hcl
  # Use variables instead of data sources when value is known
  variable "vpc_id" {
    type = string
  }

  # Instead of:
  # data "aws_vpc" "main" { ... }
  ```

- [ ] **Cache data source results in locals**
  ```hcl
  locals {
    vpc_id = var.vpc_id != "" ? var.vpc_id : data.aws_vpc.main.id
  }
  ```

- [ ] **Use for_each instead of multiple count resources**
- [ ] **Minimize cross-state data source queries**
- [ ] **Use terraform refresh -target** to refresh specific resources

### Resource Dependencies

- [ ] **Make dependencies explicit** with `depends_on` when needed
- [ ] **Avoid circular dependencies**
- [ ] **Use lifecycle rules** to control update order
  ```hcl
  lifecycle {
    create_before_destroy = true
  }
  ```

### Module Performance

- [ ] **Keep modules focused** (single responsibility)
- [ ] **Minimize module nesting** (max 3 levels deep)
- [ ] **Use module outputs efficiently** (only expose what's needed)
- [ ] **Version module sources** to avoid re-downloading

---

## Terraform Cost Optimization

### Compute Optimization

- [ ] **Right-size EC2 instances** (use smallest viable type)
- [ ] **Use burstable instances** (T3/T4) for variable workloads
  ```hcl
  instance_type = "t3.medium"  # Not t2, use t3 for better value
  ```

- [ ] **Enable auto-scaling** for dynamic workloads
- [ ] **Use Spot instances** for non-critical workloads
  ```hcl
  instance_market_options {
    market_type = "spot"
    spot_options {
      max_price = "0.05"
    }
  }
  ```

- [ ] **Schedule start/stop** for dev/test environments
  ```hcl
  # Lambda or EventBridge to stop instances off-hours
  ```

### Storage Optimization

- [ ] **Use gp3 instead of gp2** EBS volumes
  ```hcl
  root_block_device {
    volume_type = "gp3"  # Better price/performance
    volume_size = 20
    iops        = 3000
    throughput  = 125
  }
  ```

- [ ] **Right-size EBS volumes** (don't over-provision)
- [ ] **Enable EBS encryption** (no extra cost)
- [ ] **Use lifecycle policies** for S3 storage classes
  ```hcl
  lifecycle_rule {
    transitions {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    transitions {
      days          = 180
      storage_class = "GLACIER"
    }
  }
  ```

- [ ] **Enable S3 Intelligent-Tiering** for unpredictable access
- [ ] **Delete unused snapshots** and AMIs

### Database Optimization

- [ ] **Use appropriate RDS instance sizes**
- [ ] **Enable Multi-AZ only in production**
  ```hcl
  multi_az = var.environment == "prod"
  ```

- [ ] **Use Aurora Serverless** for variable workloads
- [ ] **Optimize backup retention** (7 days usually sufficient for dev)
  ```hcl
  backup_retention_period = var.environment == "prod" ? 30 : 7
  ```

### Network Optimization

- [ ] **Minimize data transfer** across regions
- [ ] **Use VPC endpoints** for AWS services (free for most)
  ```hcl
  resource "aws_vpc_endpoint" "s3" {
    vpc_id       = aws_vpc.main.id
    service_name = "com.amazonaws.${var.region}.s3"
  }
  ```

- [ ] **Consolidate NAT Gateways** (expensive - $32/month each)
- [ ] **Use ALB instead of Classic LB** (better features, same cost)

### Resource Lifecycle

- [ ] **Tag all resources** for cost allocation
  ```hcl
  tags = {
    CostCenter  = var.cost_center
    Environment = var.environment
    Owner       = var.owner
  }
  ```

- [ ] **Enable AWS Cost Allocation Tags**
- [ ] **Set up budget alerts** using AWS Budgets
- [ ] **Review AWS Cost Explorer** monthly

**Cost Savings Summary:**
```bash
# Use AWS CLI to identify cost savings opportunities
aws ce get-cost-and-usage \
  --time-period Start=2023-11-01,End=2023-11-30 \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

---

## Packer Build Speed Optimization

### Instance Selection

- [ ] **Use compute-optimized instances** for builds
  ```hcl
  instance_type = "c6i.large"  # Not t3.medium for builds
  ```

- [ ] **Use newer instance generations** (c6i vs c5)
- [ ] **Match instance type to workload**:
  - Light builds: `t3.medium`
  - Compilation: `c6i.large` or `c6i.xlarge`
  - Heavy builds: `c6i.2xlarge`

### Storage Performance

- [ ] **Use gp3 volumes** with high IOPS for build instances
  ```hcl
  launch_block_device_mappings {
    device_name = "/dev/sda1"
    volume_type = "gp3"
    iops        = 3000
    throughput  = 125
  }
  ```

- [ ] **Enable EBS optimization**
  ```hcl
  ebs_optimized = true
  ```

- [ ] **Use ephemeral storage** for temporary files when possible

### Network Performance

- [ ] **Use current-generation enhanced networking**
  ```hcl
  ena_support   = true
  sriov_support = true
  ```

- [ ] **Build in same region** as source AMI
- [ ] **Use VPC endpoints** to avoid NAT gateway overhead

### Provisioner Optimization

- [ ] **Consolidate shell provisioners** (fewer SSH sessions)
  ```hcl
  # Instead of multiple provisioners, use one
  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y package1 package2 package3"
    ]
  }
  ```

- [ ] **Use script files** instead of inline (faster transfer)
  ```hcl
  provisioner "shell" {
    script = "scripts/install.sh"
  }
  ```

- [ ] **Parallelize independent steps** using multiple builds
- [ ] **Cache package downloads** between builds
  ```bash
  # In provisioner script
  sudo mkdir -p /var/cache/apt/archives
  # Packages persist for subsequent provisioners
  ```

### Build Configuration

- [ ] **Increase SSH timeout** for slow-starting instances
  ```hcl
  ssh_timeout = "15m"
  ```

- [ ] **Optimize AMI copy** with fewer regions initially
- [ ] **Use manifest post-processor** (minimal overhead)
  ```hcl
  post-processor "manifest" {
    output = "manifest.json"
  }
  ```

### Parallel Builds

- [ ] **Build multiple variants simultaneously**
  ```hcl
  source "amazon-ebs" "ubuntu_20" { ... }
  source "amazon-ebs" "ubuntu_22" { ... }

  build {
    sources = [
      "source.amazon-ebs.ubuntu_20",
      "source.amazon-ebs.ubuntu_22"
    ]
  }
  ```

**Build Time Tracking:**
```bash
# Time your builds
time packer build .

# Profile provisioners
packer build -debug .  # Shows timing for each step
```

---

## Packer Image Size Optimization

### Package Management

- [ ] **Install only required packages**
  ```bash
  sudo apt-get install -y --no-install-recommends nginx
  ```

- [ ] **Remove unnecessary packages**
  ```bash
  sudo apt-get autoremove -y
  sudo apt-get autoclean
  ```

- [ ] **Clean package cache**
  ```bash
  sudo apt-get clean
  sudo rm -rf /var/cache/apt/*
  ```

### Log Cleanup

- [ ] **Truncate log files**
  ```bash
  sudo truncate -s 0 /var/log/*log
  sudo truncate -s 0 /var/log/**/*log 2>/dev/null || true
  ```

- [ ] **Remove old log archives**
  ```bash
  sudo rm -f /var/log/*.gz
  sudo rm -f /var/log/*.1
  sudo rm -f /var/log/*/*.gz
  ```

### Temporary Files

- [ ] **Clear /tmp and /var/tmp**
  ```bash
  sudo rm -rf /tmp/*
  sudo rm -rf /var/tmp/*
  ```

- [ ] **Clear user cache directories**
  ```bash
  rm -rf ~/.cache/*
  ```

### SSH and Host Keys

- [ ] **Remove SSH host keys** (regenerated on boot)
  ```bash
  sudo rm -f /etc/ssh/ssh_host_*
  ```

- [ ] **Clear bash history**
  ```bash
  history -c
  cat /dev/null > ~/.bash_history
  ```

### Cloud-Init

- [ ] **Clean cloud-init artifacts**
  ```bash
  sudo cloud-init clean --logs --seed
  ```

### Machine ID

- [ ] **Clear machine-id** (regenerated on boot)
  ```bash
  sudo truncate -s 0 /etc/machine-id
  ```

### Complete Cleanup Script

```bash
#!/bin/bash
# scripts/cleanup.sh

set -euo pipefail

echo "Starting AMI cleanup..."

# Stop services
sudo systemctl stop rsyslog || true

# Package cleanup
sudo apt-get autoremove -y
sudo apt-get autoclean
sudo apt-get clean
sudo rm -rf /var/cache/apt/*

# Log cleanup
sudo truncate -s 0 /var/log/*log 2>/dev/null || true
sudo truncate -s 0 /var/log/**/*log 2>/dev/null || true
sudo rm -f /var/log/*.gz
sudo rm -f /var/log/*.1
sudo rm -f /var/log/*/*.gz

# Temp files
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# SSH keys
sudo rm -f /etc/ssh/ssh_host_*

# Bash history
history -c
cat /dev/null > ~/.bash_history

# Cloud-init
sudo cloud-init clean --logs --seed

# Machine ID
sudo truncate -s 0 /etc/machine-id

echo "Cleanup complete"
```

**Size Verification:**
```bash
# Compare AMI sizes
aws ec2 describe-images \
  --owners self \
  --query 'Images[*].[Name,BlockDeviceMappings[0].Ebs.VolumeSize]' \
  --output table
```

---

## Security Hardening Checklist

### Terraform Security

- [ ] **Enable encryption at rest** for all data stores
  ```hcl
  storage_encrypted = true
  kms_key_id        = aws_kms_key.main.arn
  ```

- [ ] **Use IMDSv2** for EC2 instances
  ```hcl
  metadata_options {
    http_tokens = "required"
  }
  ```

- [ ] **No hardcoded credentials** in code
- [ ] **Mark sensitive variables** as sensitive
  ```hcl
  variable "password" {
    sensitive = true
  }
  ```

- [ ] **Encrypt Terraform state** (S3 bucket encryption)
- [ ] **Enable state locking** (prevents concurrent modifications)
- [ ] **Restrict security groups** (no 0.0.0.0/0 for SSH)
  ```hcl
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.admin_cidrs  # Not 0.0.0.0/0
  }
  ```

- [ ] **Use Secrets Manager** for passwords
- [ ] **Enable VPC Flow Logs**
- [ ] **Enable CloudTrail** for audit logging

### Packer Security

- [ ] **Enforce IMDSv2** in AMIs
  ```hcl
  metadata_options {
    http_tokens = "required"
  }
  ```

- [ ] **Encrypt AMIs**
  ```hcl
  encrypt_boot = true
  kms_key_id   = var.kms_key_id
  ```

- [ ] **Restrict temporary security groups**
  ```hcl
  temporary_security_group_source_cidrs = var.allowed_cidrs
  ```

- [ ] **Remove SSH host keys** (regenerated on boot)
- [ ] **No secrets in AMI** (use Secrets Manager)
- [ ] **Harden SSH configuration** in AMI
  ```bash
  # In provisioner
  sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
  sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
  ```

- [ ] **Enable automatic security updates**
  ```bash
  sudo apt-get install -y unattended-upgrades
  sudo systemctl enable unattended-upgrades
  ```

- [ ] **Configure firewall** (ufw/iptables)
- [ ] **Disable unnecessary services**

### Security Scanning

- [ ] **Run tfsec** on Terraform code
  ```bash
  tfsec .
  ```

- [ ] **Run checkov** for policy-as-code
  ```bash
  checkov -d .
  ```

- [ ] **Run terrascan** for compliance
  ```bash
  terrascan scan
  ```

- [ ] **Scan AMIs** with Inspector
- [ ] **Review IAM permissions** (least privilege)

---

## Maintainability Checklist

### Documentation

- [ ] **README.md exists** with usage examples
- [ ] **Variables have descriptions**
- [ ] **Outputs have descriptions**
- [ ] **Complex logic has comments**
- [ ] **Module dependencies documented**
- [ ] **Architecture diagrams exist** (for complex setups)

### Code Organization

- [ ] **Consistent naming convention**
  ```hcl
  # Pattern: {project}-{environment}-{resource}
  name = "${var.project}-${var.environment}-web"
  ```

- [ ] **Logical file structure**
  ```
  main.tf       # Primary resources
  variables.tf  # Input variables
  outputs.tf    # Output values
  locals.tf     # Local values
  data.tf       # Data sources
  versions.tf   # Provider versions
  ```

- [ ] **One resource type per file** (for large projects)
- [ ] **Modules follow standard structure**
- [ ] **Consistent indentation** (2 spaces)

### Version Control

- [ ] **`.gitignore` configured properly**
  ```
  .io/terraform/
  *.tfstate
  *.tfstate.backup
  *.tfvars
  ```

- [ ] **Commit messages are descriptive**
- [ ] **Feature branches for changes**
- [ ] **Pull requests for reviews**
- [ ] **Tag releases** with semantic versioning

### Testing

- [ ] **Terraform validate** passes
  ```bash
  terraform validate
  ```

- [ ] **Terraform fmt** passes
  ```bash
  terraform fmt -check -recursive
  ```

- [ ] **Plan reviewed before apply**
  ```bash
  terraform plan -out=tfplan
  ```

- [ ] **Integration tests exist** (Terratest, kitchen-terraform)
- [ ] **Smoke tests after deployment**

### CI/CD Integration

- [ ] **Automated validation** in pipeline
- [ ] **Automated testing** in pipeline
- [ ] **Plan on pull request**
- [ ] **Apply on merge to main**
- [ ] **Environment-specific workflows**

---

## Optimization Workflow

### Step 1: Baseline Assessment

```bash
# Terraform
terraform state list | wc -l        # Count resources
terraform plan | grep "will be"     # Check pending changes
time terraform plan                 # Measure plan time

# Packer
time packer build .                 # Measure build time
aws ec2 describe-images             # Check AMI size
```

### Step 2: Apply Optimizations

Work through relevant checklists above, prioritizing:

1. **Security** (critical issues first)
2. **Cost** (high-impact items)
3. **Performance** (bottlenecks)
4. **Maintainability** (long-term value)

### Step 3: Measure Improvements

```bash
# Re-run baseline commands
time terraform plan
time packer build .

# Calculate improvements
echo "Plan time reduced by X%"
echo "Build time reduced by Y%"
echo "Cost reduced by $Z/month"
```

### Step 4: Document Changes

```markdown
## Optimization Results

### Before
- Plan time: 5m 30s
- Build time: 15m
- Monthly cost: $500
- Security issues: 12

### After
- Plan time: 2m 15s (59% improvement)
- Build time: 8m (47% improvement)
- Monthly cost: $350 (30% reduction)
- Security issues: 0 (100% resolved)

### Changes Made
1. Split state files (3 instead of 1)
2. Increased Packer parallelism
3. Switched to gp3 volumes
4. Enabled IMDSv2 everywhere
```

---

## Summary

Regular optimization ensures:

- **Fast** infrastructure operations
- **Low** costs without sacrificing functionality
- **Secure** configurations meeting compliance requirements
- **Maintainable** code that teams can understand and modify

**Recommendation:** Review these checklists quarterly or before major infrastructure changes.

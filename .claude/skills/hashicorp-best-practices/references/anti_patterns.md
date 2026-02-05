# HashiCorp Anti-Patterns Encyclopedia

Common mistakes in Terraform and Packer configurations, their risks, and how to fix them.

## Table of Contents

- [Terraform Anti-Patterns](#terraform-anti-patterns)
- [Packer Anti-Patterns](#packer-anti-patterns)
- [General IaC Anti-Patterns](#general-iac-anti-patterns)

---

## Terraform Anti-Patterns

### 1. The Hardcoded Credential

**Severity:** CRITICAL

**Pattern:**
```hcl
resource "aws_db_instance" "main" {
  password = "MyPassword123!"  # NEVER do this
}
```

**Problems:**
- Credentials in state file
- Credentials in version control
- Security breach waiting to happen

**Fix:**
```hcl
# Use random password + secrets manager
resource "random_password" "db" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.project}-db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

# Application reads from Secrets Manager
```

**Detection:** `grep -r "password.*=" *.tf | grep -v "random_password"`

---

### 2. The God Module

**Severity:** WARNING

**Pattern:**
```
modules/infrastructure/
└── main.tf  # 5000 lines, 200+ resources
```

**Problems:**
- Massive blast radius (one typo destroys everything)
- Slow terraform plan/apply
- Team conflicts on same state
- Difficult to review changes

**Fix:**
```
modules/
├── networking/    # VPC, subnets, routes
├── compute/       # EC2, ASG, ALB
├── data/          # RDS, ElastiCache
└── security/      # IAM, KMS, security groups
```

**Detection:** `wc -l main.tf` > 500 lines = red flag

---

### 3. The Copy-Paste Environment

**Severity:** WARNING

**Pattern:**
```
io/terraform/
├── dev/
│   └── main.tf     # Duplicated code
├── staging/
│   └── main.tf     # Duplicated code
└── prod/
    └── main.tf     # Duplicated code
```

**Problems:**
- Configuration drift between environments
- Bug fixes must be applied 3 times
- Inconsistent behavior

**Fix:**
```
io/terraform/
├── modules/
│   └── app/        # Single source of truth
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

**Detection:** `diff -r dev/main.tf staging/main.tf` shows similarities

---

### 4. The Naked Variable

**Severity:** WARNING

**Pattern:**
```hcl
variable "environment" {
  type = string
}
```

**Problems:**
- No validation allows invalid values
- No description for users
- Easy to make typos (prod vs production)

**Fix:**
```hcl
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

**Detection:** Check for variables without `validation` or `description`

---

### 5. The Count Trap

**Severity:** WARNING

**Pattern:**
```hcl
resource "aws_instance" "web" {
  count = length(var.servers)

  tags = {
    Name = var.servers[count.index]
  }
}
```

**Problems:**
- If you remove "server-2" from middle of list, all subsequent servers get destroyed and recreated
- Resource addresses change when list order changes

**Fix:**
```hcl
resource "aws_instance" "web" {
  for_each = toset(var.servers)

  tags = {
    Name = each.value
  }
}
```

**Detection:** `grep -n "count.*=.*length" *.tf`

---

### 6. The Implicit Dependency

**Severity:** SUGGESTION

**Pattern:**
```hcl
resource "aws_instance" "app" {
  subnet_id = aws_subnet.public.id
  # Assumes internet gateway exists but doesn't declare it
}
```

**Problems:**
- Race conditions during creation
- Unpredictable apply order
- Failed applies due to missing dependencies

**Fix:**
```hcl
resource "aws_instance" "app" {
  subnet_id = aws_subnet.public.id

  depends_on = [
    aws_internet_gateway.main,
    aws_route_table.public
  ]
}
```

**Detection:** Manual code review for resource relationships

---

### 7. The State Monolith

**Severity:** WARNING

**Pattern:**
```hcl
# Single state file for entire company infrastructure
terraform {
  backend "s3" {
    key = "everything/terraform.tfstate"
  }
}
```

**Problems:**
- One mistake affects everything
- Slow operations on massive state
- State locking blocks all teams

**Fix:**
```hcl
# Separate state per component/environment
terraform {
  backend "s3" {
    key = "${var.environment}/networking/terraform.tfstate"
  }
}
```

**Detection:** State file > 10MB or > 1000 resources

---

### 8. The Untagged Resource

**Severity:** WARNING

**Pattern:**
```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  # No tags!
}
```

**Problems:**
- Can't identify resources in AWS console
- Can't track costs
- Can't apply policies or automation

**Fix:**
```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    CostCenter  = var.cost_center
  }
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = merge(local.common_tags, {
    Name = "${var.project}-${var.environment}-web"
    Role = "web-server"
  })
}
```

**Detection:** `terraform state list | xargs -I {} terraform state show {} | grep -L "tags"`

---

### 9. The Missing Lifecycle

**Severity:** WARNING

**Pattern:**
```hcl
resource "aws_security_group" "app" {
  name = "app-sg"
  # No lifecycle rules
}
```

**Problems:**
- Security group can't be updated (can't change name)
- Downtime during replacement
- Resources reference deleted security group

**Fix:**
```hcl
resource "aws_security_group" "app" {
  name_prefix = "app-sg-"

  lifecycle {
    create_before_destroy = true
  }
}
```

**Detection:** Check security groups, launch configs without `create_before_destroy`

---

### 10. The Timeout Trap

**Severity:** SUGGESTION

**Pattern:**
```hcl
resource "aws_db_instance" "main" {
  # ... configuration ...
  # No timeouts - will wait forever
}
```

**Problems:**
- Hung applies block CI/CD
- No control over wait times
- Failed applies after 60+ minutes

**Fix:**
```hcl
resource "aws_db_instance" "main" {
  # ... configuration ...

  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}
```

**Detection:** Check long-running resources (RDS, ECS) for `timeouts` blocks

---

### 11. The Magic String

**Severity:** WARNING

**Pattern:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"  # Hardcoded
  subnet_id     = "subnet-abc123"          # Hardcoded
  instance_type = "t3.large"               # Hardcoded
}
```

**Problems:**
- Can't reuse in different accounts/regions
- Can't change without modifying code
- AMI ID will eventually be deprecated

**Fix:**
```hcl
data "aws_ami" "latest" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["myapp-*"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.latest.id
  subnet_id     = var.subnet_id
  instance_type = var.instance_type
}
```

**Detection:** `grep -E '(ami|subnet|vpc)-[a-f0-9]+' *.tf`

---

### 12. The Wide-Open Security Group

**Severity:** CRITICAL

**Pattern:**
```hcl
resource "aws_security_group_rule" "allow_all" {
  type        = "ingress"
  from_port   = 0
  to_port     = 65535
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
```

**Problems:**
- Entire internet can access all ports
- Security vulnerability
- Compliance violation

**Fix:**
```hcl
resource "aws_security_group_rule" "http" {
  type        = "ingress"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  description = "HTTP from internet"
}

resource "aws_security_group_rule" "ssh_from_vpn" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["10.0.0.0/8"]  # VPN only
  description = "SSH from VPN"
}
```

**Detection:** `tfsec .` or `checkov -d .`

---

### 13. The Unencrypted Resource

**Severity:** CRITICAL

**Pattern:**
```hcl
resource "aws_db_instance" "main" {
  storage_encrypted = false  # or missing
}

resource "aws_s3_bucket" "data" {
  # No encryption configuration
}
```

**Problems:**
- Data at rest not encrypted
- Compliance violation
- Security breach risk

**Fix:**
```hcl
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}
```

**Detection:** `tfsec .` or `checkov -d .`

---

### 14. The Sensitive Output

**Severity:** CRITICAL

**Pattern:**
```hcl
output "db_password" {
  value = aws_db_instance.main.password
  # Not marked sensitive!
}
```

**Problems:**
- Password visible in console output
- Password in log files
- Security exposure

**Fix:**
```hcl
output "db_password" {
  value     = aws_db_instance.main.password
  sensitive = true
}

# Access with: terraform output -raw db_password
```

**Detection:** Check outputs containing "password", "secret", "key"

---

### 15. The Provider Lock-In

**Severity:** SUGGESTION

**Pattern:**
```hcl
# No version constraints
provider "aws" {
  region = "us-east-1"
}
```

**Problems:**
- Unexpected provider updates break code
- Different team members use different versions
- Non-reproducible builds

**Fix:**
```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

**Detection:** Check for missing `required_providers` block

---

## Packer Anti-Patterns

### 16. The Hardcoded AMI ID

**Severity:** CRITICAL

**Pattern:**
```hcl
source "amazon-ebs" "app" {
  source_ami = "ami-0123456789abcdef0"
}
```

**Problems:**
- AMI will be deprecated eventually
- Breaks in different regions
- Can't update base OS

**Fix:**
```hcl
source "amazon-ebs" "app" {
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]
  }
}
```

**Detection:** `grep -n 'source_ami.*=.*"ami-' *.pkr.hcl`

---

### 17. The Provisioner Spam

**Severity:** WARNING

**Pattern:**
```hcl
provisioner "shell" { inline = ["apt-get update"] }
provisioner "shell" { inline = ["apt-get install nginx"] }
provisioner "shell" { inline = ["systemctl enable nginx"] }
provisioner "shell" { inline = ["apt-get install docker"] }
provisioner "shell" { inline = ["systemctl enable docker"] }
```

**Problems:**
- Multiple SSH sessions (slow)
- Network overhead
- Fragile (one failure leaves partial state)

**Fix:**
```hcl
provisioner "shell" {
  inline = [
    "export DEBIAN_FRONTEND=noninteractive",
    "sudo apt-get update",
    "sudo apt-get install -y nginx docker.io",
    "sudo systemctl enable nginx docker"
  ]
}

# Or even better - use a script
provisioner "shell" {
  script = "scripts/install.sh"
}
```

**Detection:** Count `provisioner "shell"` blocks > 3

---

### 18. The Missing Manifest

**Severity:** WARNING

**Pattern:**
```hcl
# No post-processor to track AMI metadata
build {
  sources = ["source.amazon-ebs.app"]
  # ... provisioners ...
}
```

**Problems:**
- Can't track which AMI was built when
- Can't correlate AMI to git commit
- Manual AMI lookup in Terraform

**Fix:**
```hcl
post-processor "manifest" {
  output = "packer-manifest.json"
  custom_data = {
    version    = var.app_version
    git_commit = var.git_commit
    build_date = timestamp()
  }
}
```

**Detection:** Check for missing `post-processor "manifest"`

---

### 19. The IMDSv1 Instance

**Severity:** CRITICAL

**Pattern:**
```hcl
source "amazon-ebs" "app" {
  # Missing metadata_options
}
```

**Problems:**
- Vulnerable to SSRF attacks
- Security compliance failure
- Should always use IMDSv2

**Fix:**
```hcl
source "amazon-ebs" "app" {
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"  # Enforces IMDSv2
    http_put_response_hop_limit = 1
  }
}
```

**Detection:** `grep -L "http_tokens" *.pkr.hcl`

---

### 20. The Wide-Open Build

**Severity:** CRITICAL

**Pattern:**
```hcl
source "amazon-ebs" "app" {
  temporary_security_group_source_cidrs = ["0.0.0.0/0"]
}
```

**Problems:**
- Build instance accessible from entire internet
- SSH port exposed during build
- Security risk

**Fix:**
```hcl
source "amazon-ebs" "app" {
  # Restrict to your network
  temporary_security_group_source_cidrs = [
    "10.0.0.0/8",      # Corporate network
    "203.0.113.0/24"   # VPN
  ]

  # Or use existing security group
  security_group_ids = [var.build_security_group_id]
}
```

**Detection:** `grep "0.0.0.0/0" *.pkr.hcl`

---

### 21. The Unencrypted AMI

**Severity:** CRITICAL

**Pattern:**
```hcl
source "amazon-ebs" "app" {
  encrypt_boot = false  # or missing
}
```

**Problems:**
- Unencrypted AMI
- Compliance violation
- Data exposure risk

**Fix:**
```hcl
source "amazon-ebs" "app" {
  encrypt_boot = true
  kms_key_id   = var.kms_key_id
}
```

**Detection:** `grep -L "encrypt_boot.*true" *.pkr.hcl`

---

### 22. The No-Cleanup Build

**Severity:** WARNING

**Pattern:**
```hcl
# Provisions but doesn't clean up
provisioner "shell" {
  script = "install.sh"
}
# No cleanup provisioner
```

**Problems:**
- Logs contain sensitive data
- Package cache wastes space
- SSH keys in AMI
- Larger AMI size

**Fix:**
```hcl
provisioner "shell" {
  script = "scripts/install.sh"
}

provisioner "shell" {
  script = "scripts/cleanup.sh"
}
```

**cleanup.sh:**
```bash
#!/bin/bash
sudo apt-get clean
sudo rm -rf /tmp/*
sudo truncate -s 0 /var/log/*log
sudo rm -f /etc/ssh/ssh_host_*
```

**Detection:** Look for builds without cleanup step

---

### 23. The Inline User Data

**Severity:** WARNING

**Pattern:**
```hcl
provisioner "shell" {
  inline = [
    "cat > /etc/app.conf <<EOF",
    "database_url=postgres://...",
    "api_key=secret123",
    "EOF"
  ]
}
```

**Problems:**
- Secrets in template
- Hard to maintain inline scripts
- No syntax validation

**Fix:**
```hcl
provisioner "file" {
  source      = "configs/app.conf.template"
  destination = "/tmp/app.conf"
}

provisioner "shell" {
  script = "scripts/configure.sh"
}
```

**Detection:** Long `inline` scripts > 10 lines

---

### 24. The Inefficient Instance Type

**Severity:** SUGGESTION

**Pattern:**
```hcl
source "amazon-ebs" "app" {
  instance_type = "t3.micro"  # Too small for builds
}
```

**Problems:**
- Slow builds (compilation, package install)
- Timeouts on large builds
- Wasted developer time

**Fix:**
```hcl
source "amazon-ebs" "app" {
  # Use compute-optimized for faster builds
  instance_type = var.environment == "prod" ? "c6i.large" : "t3.medium"
}
```

**Detection:** Check instance_type against workload

---

## General IaC Anti-Patterns

### 25. The "Terraform Plan" Skip

**Severity:** CRITICAL

**Pattern:**
```bash
terraform apply -auto-approve  # YOLO!
```

**Problems:**
- No review of changes
- Accidental destruction
- No verification

**Fix:**
```bash
terraform plan -out=tfplan
# Review plan
terraform apply tfplan
```

---

### 26. The Manual Change

**Severity:** CRITICAL

**Pattern:**
```
# Making changes directly in AWS Console
# "Just a quick fix, I'll update Terraform later"
```

**Problems:**
- State drift
- Terraform destroy/recreate on next apply
- Lost changes

**Fix:**
```bash
# Import existing resources
terraform import aws_instance.web i-1234567890abcdef0

# Or refresh state
terraform refresh
```

---

### 27. The Local State in Git

**Severity:** CRITICAL

**Pattern:**
```
# .gitignore
# terraform.tfstate is NOT ignored
```

**Problems:**
- Secrets in version control
- Merge conflicts
- State corruption

**Fix:**
```
# .gitignore
.io/terraform/
*.tfstate
*.tfstate.backup
```

Use remote state instead!

---

### 28. The Version Wildcard

**Severity:** WARNING

**Pattern:**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "*"  # ANY version
    }
  }
}
```

**Problems:**
- Breaking changes in provider updates
- Non-reproducible builds
- Surprises in production

**Fix:**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

---

## Detection Tools

**Automated scanning:**

```bash
# Terraform security scanning
tfsec .
checkov -d .
terrascan scan

# Packer validation
packer validate .
packer fmt -check .

# General linting
terraform fmt -check -recursive
```

---

## Summary

Avoiding these anti-patterns will help you:

- **Security**: Prevent credential leaks and vulnerabilities
- **Reliability**: Avoid state corruption and failed applies
- **Maintainability**: Keep code understandable and modifiable
- **Performance**: Optimize build and apply times
- **Collaboration**: Enable team workflows without conflicts

**Remember:** Every anti-pattern exists because someone learned the hard way. Learn from their mistakes!

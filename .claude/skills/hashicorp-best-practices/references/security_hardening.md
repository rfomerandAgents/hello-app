# Security Hardening Guide for HashiCorp Tools

Comprehensive security best practices for Terraform and Packer configurations.

## Table of Contents

1. [AWS Security Best Practices](#aws-security-best-practices)
2. [Terraform Security](#terraform-security)
3. [Packer Security](#packer-security)
4. [IAM Security](#iam-security)
5. [Compliance and Auditing](#compliance-and-auditing)
6. [Incident Response](#incident-response)

---

## AWS Security Best Practices

### EC2 Instance Security

#### IMDSv2 Enforcement

**Always enforce IMDSv2** to prevent SSRF attacks:

```hcl
# Terraform
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforces IMDSv2
    http_put_response_hop_limit = 1
  }
}

# Packer
source "amazon-ebs" "app" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
}
```

**Why:** IMDSv1 is vulnerable to SSRF attacks. IMDSv2 requires a session token, preventing unauthorized access to instance metadata.

#### EBS Encryption

**Encrypt all EBS volumes:**

```hcl
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type

  root_block_device {
    encrypted   = true
    kms_key_id  = aws_kms_key.ebs.arn
    volume_type = "gp3"
  }
}

# Encrypt additional volumes
resource "aws_ebs_volume" "data" {
  availability_zone = var.az
  size              = 100
  encrypted         = true
  kms_key_id        = aws_kms_key.ebs.arn

  tags = {
    Name      = "${var.project}-data"
    Encrypted = "true"
  }
}
```

#### SSH Access Control

**Restrict SSH access:**

```hcl
# BAD - SSH from anywhere
resource "aws_security_group_rule" "ssh" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]  # NEVER do this
}

# GOOD - SSH from specific IPs/VPN
resource "aws_security_group_rule" "ssh" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = var.admin_cidrs  # e.g., ["10.0.0.0/8"]
  description = "SSH from corporate network"
}

# EVEN BETTER - Use AWS Systems Manager Session Manager
# No SSH port needed!
```

**Session Manager setup:**

```hcl
# IAM role for SSM
resource "aws_iam_role" "ssm" {
  name = "${var.project}-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach to instance
resource "aws_instance" "app" {
  iam_instance_profile = aws_iam_instance_profile.ssm.name
  # No SSH security group rule needed
}
```

### Network Security

#### VPC Security

**Implement defense in depth:**

```hcl
# Public subnet for load balancers only
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = false  # Don't auto-assign public IPs

  tags = {
    Name = "${var.project}-public"
    Tier = "public"
  }
}

# Private subnet for application servers
resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.10.0/24"

  tags = {
    Name = "${var.project}-private"
    Tier = "private"
  }
}

# Isolated subnet for databases (no NAT gateway route)
resource "aws_subnet" "isolated" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.20.0/24"

  tags = {
    Name = "${var.project}-isolated"
    Tier = "isolated"
  }
}
```

#### Security Group Best Practices

**Principle of least privilege:**

```hcl
# Application security group
resource "aws_security_group" "app" {
  name_prefix = "${var.project}-app-"
  description = "Security group for application servers"
  vpc_id      = aws_vpc.main.id

  # Only allow traffic from ALB
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from ALB"
  }

  # Explicit egress rules (don't use 0.0.0.0/0)
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for updates and AWS APIs"
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project}-app-sg"
  }
}

# Database security group
resource "aws_security_group" "db" {
  name_prefix = "${var.project}-db-"
  description = "Security group for database"
  vpc_id      = aws_vpc.main.id

  # Only allow traffic from app tier
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "PostgreSQL from app tier"
  }

  # No egress rules needed for database

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project}-db-sg"
  }
}
```

#### VPC Flow Logs

**Enable VPC flow logs for security monitoring:**

```hcl
resource "aws_flow_log" "main" {
  vpc_id          = aws_vpc.main.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn

  tags = {
    Name = "${var.project}-vpc-flow-logs"
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/${var.project}"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.logs.arn

  tags = {
    Name = "${var.project}-flow-logs"
  }
}
```

### Data Security

#### S3 Bucket Security

**Secure S3 buckets:**

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "${var.project}-data-${var.environment}"

  tags = {
    Name        = "${var.project}-data"
    Environment = var.environment
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true  # Reduces KMS costs
  }
}

# Logging
resource "aws_s3_bucket_logging" "data" {
  bucket = aws_s3_bucket.data.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/"
}

# Lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
```

#### RDS Security

**Secure RDS instances:**

```hcl
resource "aws_db_instance" "main" {
  identifier     = "${var.project}-db"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = var.db_instance_class

  # Encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false  # NEVER true in production

  # Backup
  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  # Deletion protection
  deletion_protection = var.environment == "prod"
  skip_final_snapshot = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.project}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn

  # Password management
  manage_master_user_password   = true
  master_user_secret_kms_key_id = aws_kms_key.rds.arn

  tags = {
    Name        = "${var.project}-db"
    Environment = var.environment
  }
}
```

### KMS Key Management

**Create environment-specific KMS keys:**

```hcl
resource "aws_kms_key" "main" {
  description             = "${var.project} ${var.environment} encryption key"
  deletion_window_in_days = var.environment == "prod" ? 30 : 7
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project}-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.project}-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# Key policy
resource "aws_kms_key_policy" "main" {
  key_id = aws_kms_key.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow services to use the key"
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "rds.amazonaws.com",
            "s3.amazonaws.com"
          ]
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}
```

---

## Terraform Security

### State File Security

**Secure Terraform state:**

```hcl
# S3 backend with encryption
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "${var.environment}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true                    # Encrypt state at rest
    kms_key_id     = "arn:aws:kms:..."       # Use KMS for encryption
    dynamodb_table = "terraform-state-lock"  # State locking

    # Enable versioning on bucket (via separate config)
    # Enable MFA delete in production
  }
}
```

**State bucket configuration:**

```hcl
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.organization}-terraform-state"

  tags = {
    Name        = "Terraform State"
    Environment = "all"
    Critical    = "true"
  }
}

# Versioning - critical for state recovery
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status     = "Enabled"
    mfa_delete = var.enable_mfa_delete ? "Enabled" : "Disabled"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Access logging
resource "aws_s3_bucket_logging" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  target_bucket = aws_s3_bucket.audit_logs.id
  target_prefix = "terraform-state-access/"
}

# Lifecycle policy - keep versions for 90 days
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.terraform_state.arn
  }

  tags = {
    Name = "Terraform State Lock"
  }
}
```

### Sensitive Variables

**Handle secrets properly:**

```hcl
# Mark variables as sensitive
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Mark outputs as sensitive
output "db_connection_string" {
  value     = "postgresql://${aws_db_instance.main.endpoint}/mydb"
  sensitive = true
}

# Use Secrets Manager instead of variables
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

### Provider Credentials

**Never hardcode AWS credentials:**

```hcl
# BAD
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"  # NEVER do this
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# GOOD - Use IAM roles, environment variables, or AWS profiles
provider "aws" {
  region = var.aws_region
  # Credentials from:
  # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
  # 2. AWS credentials file (~/.aws/credentials)
  # 3. IAM role (when running on EC2/ECS/Lambda)
  # 4. AWS SSO
}

# For CI/CD - use OIDC with IAM roles
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = var.ci_role_arn
  }
}
```

---

## Packer Security

### Build-Time Security

**Secure Packer builds:**

```hcl
source "amazon-ebs" "secure" {
  # Use specific, vetted base AMI
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]  # Canonical official
  }

  # Restrict build access
  temporary_security_group_source_cidrs = var.build_cidrs  # Not 0.0.0.0/0

  # Or use existing security group
  security_group_ids = [var.build_security_group_id]

  # IMDSv2 for build instance
  temporary_iam_instance_profile_policy_document {
    Statement {
      Effect = "Allow"
      Action = [
        "ec2:DescribeImages",
        "ec2:CreateTags"
      ]
      Resource = "*"
    }
  }

  # Enforce IMDSv2 in resulting AMI
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # Encrypt AMI
  encrypt_boot = true
  kms_key_id   = var.kms_key_id

  # Tags for governance
  tags = {
    Name            = "${var.project}-${var.version}"
    BaseAMI         = "{{ .SourceAMI }}"
    BuildDate       = "{{ timestamp }}"
    SecurityScanned = "pending"
  }
}
```

### AMI Hardening

**Security hardening in provisioners:**

```bash
#!/bin/bash
# scripts/security_hardening.sh

set -euo pipefail

echo "Starting security hardening..."

# Update all packages
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get upgrade -y

# Install security updates automatically
sudo apt-get install -y unattended-upgrades
sudo systemctl enable unattended-upgrades
sudo systemctl start unattended-upgrades

# Configure automatic security updates
cat <<EOF | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

# Harden SSH
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords no/' /etc/ssh/sshd_config
sudo sed -i 's/X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config

# Configure firewall (ufw)
sudo apt-get install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
# sudo ufw enable  # Don't enable during build

# Install and configure fail2ban
sudo apt-get install -y fail2ban
sudo systemctl enable fail2ban

cat <<EOF | sudo tee /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

# Disable unnecessary services
sudo systemctl disable avahi-daemon || true
sudo systemctl disable cups || true
sudo systemctl disable iscsid || true

# Set secure file permissions
sudo chmod 600 /etc/ssh/sshd_config
sudo chmod 644 /etc/passwd
sudo chmod 644 /etc/group
sudo chmod 600 /etc/shadow
sudo chmod 600 /etc/gshadow

# Install security monitoring tools
sudo apt-get install -y aide auditd
sudo aideinit

# Configure audit rules
cat <<EOF | sudo tee /etc/audit/rules.d/audit.rules
-w /etc/passwd -p wa -k passwd_changes
-w /etc/group -p wa -k group_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/sudoers -p wa -k sudoers_changes
-w /var/log/auth.log -p wa -k auth_log_changes
EOF

sudo systemctl enable auditd

# Remove compiler tools in production AMIs
# sudo apt-get remove -y gcc make

echo "Security hardening complete"
```

### Secrets Management

**Never bake secrets into AMIs:**

```hcl
# BAD - Secrets in AMI
provisioner "shell" {
  inline = [
    "echo 'API_KEY=secret123' >> /etc/environment"
  ]
}

# GOOD - Use Secrets Manager
provisioner "shell" {
  inline = [
    # Install AWS CLI
    "sudo apt-get install -y awscli",

    # Configure app to read from Secrets Manager
    "cat > /opt/app/config.sh <<'EOF'",
    "#!/bin/bash",
    "export DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id ${var.db_secret_id} --query SecretString --output text)",
    "EOF",

    "chmod +x /opt/app/config.sh"
  ]
}
```

---

## IAM Security

### Least Privilege Principle

**Terraform IAM role for CI/CD:**

```hcl
resource "aws_iam_role" "terraform_ci" {
  name = "terraform-ci-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = "arn:aws:iam::${var.account_id}:oidc-provider/token.actions.githubusercontent.com"
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:ref:refs/heads/main"
        }
      }
    }]
  })
}

# Attach minimal permissions
resource "aws_iam_role_policy" "terraform_ci" {
  role = aws_iam_role.terraform_ci.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "ec2:CreateTags",
          "ec2:RunInstances",
          "ec2:TerminateInstances"
          # Add only necessary actions
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      }
    ]
  })
}
```

---

## Compliance and Auditing

### CloudTrail

**Enable CloudTrail for audit logging:**

```hcl
resource "aws_cloudtrail" "main" {
  name                          = "${var.project}-cloudtrail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type = "AWS::S3::Object"
      values = ["${aws_s3_bucket.data.arn}/"]
    }
  }

  tags = {
    Name = "${var.project}-cloudtrail"
  }
}
```

### AWS Config

**Track configuration changes:**

```hcl
resource "aws_config_configuration_recorder" "main" {
  name     = "${var.project}-config"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  name           = "${var.project}-config"
  s3_bucket_name = aws_s3_bucket.config.id

  snapshot_delivery_properties {
    delivery_frequency = "Six_Hours"
  }

  depends_on = [aws_config_configuration_recorder.main]
}
```

### Security Hub

**Enable Security Hub:**

```hcl
resource "aws_securityhub_account" "main" {}

resource "aws_securityhub_standards_subscription" "cis" {
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"

  depends_on = [aws_securityhub_account.main]
}
```

---

## Incident Response

### Backup and Recovery

**Enable backups:**

```hcl
# RDS automated backups
resource "aws_db_instance" "main" {
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  copy_tags_to_snapshot   = true

  deletion_protection = true
}

# EC2 instance snapshots via DLM
resource "aws_dlm_lifecycle_policy" "ec2_snapshots" {
  description        = "EC2 snapshot policy"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["INSTANCE"]

    schedule {
      name = "Daily snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 7
      }

      tags_to_add = {
        Type = "DailySnapshot"
      }

      copy_tags = true
    }

    target_tags = {
      Backup = "true"
    }
  }
}
```

---

## Summary

Security is not optional. Follow these practices to:

- **Prevent** unauthorized access
- **Detect** security incidents
- **Respond** quickly to breaches
- **Comply** with industry standards
- **Audit** all changes and access

**Remember:** Security is a continuous process, not a one-time task. Regular reviews and updates are essential.

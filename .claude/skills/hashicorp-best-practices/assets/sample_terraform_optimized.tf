# Example: Optimized Terraform Configuration
# This file demonstrates best practices for Terraform code

#==============================================================================
# Terraform and Provider Configuration
#==============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state with encryption and locking
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/web-app/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  # Default tags applied to all resources
  default_tags {
    tags = local.common_tags
  }
}

#==============================================================================
# Data Sources
#==============================================================================

# Get current AWS account information
data "aws_caller_identity" "current" {}

# Get available AZs in current region
data "aws_availability_zones" "available" {
  state = "available"
}

# Get latest AMI built by Packer
data "aws_ami" "app" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["${var.project}-${var.environment}-*"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }

  filter {
    name   = "tag:Environment"
    values = [var.environment]
  }
}

#==============================================================================
# Local Values
#==============================================================================

locals {
  # Naming convention: {project}-{environment}-{resource}
  name_prefix = "${var.project}-${var.environment}"

  # Common tags applied to all resources
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = var.repository_url
    CostCenter  = var.cost_center
  }

  # Computed values
  az_count = min(length(data.aws_availability_zones.available.names), var.max_azs)

  # Environment-specific settings
  instance_type = var.environment == "prod" ? "t3.large" : "t3.medium"
  multi_az      = var.environment == "prod" ? true : false

  # AMI ID with override capability
  ami_id = var.ami_id_override != "" ? var.ami_id_override : data.aws_ami.app.id
}

#==============================================================================
# VPC and Networking
#==============================================================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# Public subnets for load balancers
resource "aws_subnet" "public" {
  for_each = toset([for i in range(local.az_count) : tostring(i)])

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, tonumber(each.value))
  availability_zone       = data.aws_availability_zones.available.names[tonumber(each.value)]
  map_public_ip_on_launch = false # Security: Don't auto-assign public IPs

  tags = {
    Name = "${local.name_prefix}-public-${each.value}"
    Tier = "public"
  }
}

# Private subnets for application servers
resource "aws_subnet" "private" {
  for_each = toset([for i in range(local.az_count) : tostring(i)])

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, tonumber(each.value) + 100)
  availability_zone = data.aws_availability_zones.available.names[tonumber(each.value)]

  tags = {
    Name = "${local.name_prefix}-private-${each.value}"
    Tier = "private"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

#==============================================================================
# Security Groups
#==============================================================================

# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${local.name_prefix}-alb-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from internet"

  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTPS from internet"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_app" {
  security_group_id = aws_security_group.alb.id
  description       = "To application servers"

  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.app.id
}

# Application Security Group
resource "aws_security_group" "app" {
  name_prefix = "${local.name_prefix}-app-"
  description = "Security group for application servers"
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${local.name_prefix}-app-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id = aws_security_group.app.id
  description       = "Application port from ALB"

  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.alb.id
}

resource "aws_vpc_security_group_egress_rule" "app_https" {
  security_group_id = aws_security_group.app.id
  description       = "HTTPS for AWS APIs and updates"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}

#==============================================================================
# IAM Roles and Policies
#==============================================================================

# EC2 instance role
resource "aws_iam_role" "app" {
  name_prefix = "${local.name_prefix}-app-"

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

  tags = {
    Name = "${local.name_prefix}-app-role"
  }
}

# Attach SSM policy for Session Manager access
resource "aws_iam_role_policy_attachment" "app_ssm" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Custom policy for app-specific permissions
resource "aws_iam_role_policy" "app" {
  name_prefix = "${local.name_prefix}-app-"
  role        = aws_iam_role.app.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.app_data.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.app_config.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  name_prefix = "${local.name_prefix}-app-"
  role        = aws_iam_role.app.name

  tags = {
    Name = "${local.name_prefix}-app-profile"
  }
}

#==============================================================================
# EC2 Instances
#==============================================================================

resource "aws_instance" "app" {
  ami                  = local.ami_id
  instance_type        = local.instance_type
  iam_instance_profile = aws_iam_instance_profile.app.name

  # Use first private subnet
  subnet_id = aws_subnet.private["0"].id

  vpc_security_group_ids = [aws_security_group.app.id]

  # EBS volume configuration
  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    iops                  = 3000
    throughput            = 125
    encrypted             = true
    kms_key_id            = aws_kms_key.ebs.arn
    delete_on_termination = true
  }

  # Enforce IMDSv2
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # User data for initialization
  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    environment = var.environment
    region      = var.aws_region
  }))

  # Lifecycle rules
  lifecycle {
    create_before_destroy = true
    ignore_changes        = [ami] # AMI updates handled separately
  }

  # Explicit timeouts
  timeouts {
    create = "10m"
    update = "10m"
    delete = "10m"
  }

  tags = {
    Name = "${local.name_prefix}-app"
    Role = "application-server"
  }
}

#==============================================================================
# KMS Keys
#==============================================================================

resource "aws_kms_key" "ebs" {
  description             = "KMS key for EBS encryption"
  deletion_window_in_days = var.environment == "prod" ? 30 : 7
  enable_key_rotation     = true

  tags = {
    Name = "${local.name_prefix}-ebs"
  }
}

resource "aws_kms_alias" "ebs" {
  name          = "alias/${local.name_prefix}-ebs"
  target_key_id = aws_kms_key.ebs.key_id
}

#==============================================================================
# S3 Bucket
#==============================================================================

resource "aws_s3_bucket" "app_data" {
  bucket = "${local.name_prefix}-app-data"

  tags = {
    Name = "${local.name_prefix}-app-data"
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning
resource "aws_s3_bucket_versioning" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.ebs.arn
    }
    bucket_key_enabled = true
  }
}

#==============================================================================
# Secrets Manager
#==============================================================================

resource "aws_secretsmanager_secret" "app_config" {
  name_prefix = "${local.name_prefix}-config-"
  description = "Application configuration secrets"

  kms_key_id = aws_kms_key.ebs.arn

  tags = {
    Name = "${local.name_prefix}-app-config"
  }
}

# Secret version (value should be set externally)
resource "aws_secretsmanager_secret_version" "app_config" {
  secret_id = aws_secretsmanager_secret.app_config.id

  secret_string = jsonencode({
    database_url = "postgresql://${var.db_username}@${aws_db_instance.main.endpoint}/mydb"
    api_key      = "placeholder-set-externally"
  })

  lifecycle {
    ignore_changes = [secret_string] # Managed externally
  }
}

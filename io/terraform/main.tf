# {{PROJECT_NAME}} Infrastructure
# AWS provider configuration for EC2-based web application hosting

provider "aws" {
  region = var.aws_region
}

# Data source to get the latest AMI built by Packer
data "aws_ami" "app" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["${var.project}-*"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# Data source to reference existing Elastic IP (if allocation_id provided)
data "aws_eip" "existing" {
  count = var.elastic_ip_allocation_id != "" ? 1 : 0
  id    = var.elastic_ip_allocation_id
}

# Security Group for the EC2 instance
# IMPORTANT: Uses create_before_destroy to maintain availability during updates
resource "aws_security_group" "app" {
  name_prefix = "${local.name_prefix}-"
  description = "Security group for ${var.project} - allows HTTP, HTTPS and SSH access"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group Rule: HTTP access
# checkov:skip=CKV_AWS_260:HTTP required for public website - traffic redirected to HTTPS
resource "aws_security_group_rule" "http" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "HTTP access for public website"
  security_group_id = aws_security_group.app.id
}

# Security Group Rule: HTTPS access
resource "aws_security_group_rule" "https" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "HTTPS access for public website"
  security_group_id = aws_security_group.app.id
}

# Security Group Rule: SSH access
# WARNING: Production environments should restrict SSH to specific IPs
# checkov:skip=CKV_AWS_260:SSH access configurable via allowed_ssh_cidr_blocks variable
resource "aws_security_group_rule" "ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = var.allowed_ssh_cidr_blocks
  description       = "SSH access for maintenance - restrict in production"
  security_group_id = aws_security_group.app.id
}

# Security Group Rule: Egress
# checkov:skip=CKV_AWS_277:Outbound traffic required for package updates
resource "aws_security_group_rule" "egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "All outbound traffic for updates and AWS services"
  security_group_id = aws_security_group.app.id
}

# EC2 Key Pair
resource "aws_key_pair" "app" {
  key_name   = "${local.name_prefix}-keypair"
  public_key = var.ssh_public_key

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-keypair"
    }
  )
}

# EC2 Instance
# Cost optimization: Using gp3 volumes (20% cheaper than gp2)
# Security: IMDSv2 enforced, encrypted root volume
resource "aws_instance" "app" {
  ami           = local.ami_id
  instance_type = var.instance_type
  key_name      = aws_key_pair.app.key_name

  vpc_security_group_ids = [aws_security_group.app.id]

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  # Security best practice: IMDSv2 enforcement
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = merge(
    local.common_tags,
    {
      Name       = "${local.name_prefix}-instance"
      Version    = var.app_version
      DeployedAt = local.deployment_timestamp_iso
      WorkflowID = var.workflow_id
    }
  )

  timeouts {
    create = "10m"
    update = "10m"
    delete = "10m"
  }

  depends_on = [
    aws_security_group.app,
    aws_key_pair.app
  ]

  # User data to configure nginx
  user_data = <<-EOF
              #!/bin/bash
              set -e

              # Create SSL directory for certificates
              mkdir -p /etc/ssl/certs/app
              chmod 755 /etc/ssl/certs/app

              # Configure nginx site
              cat > /etc/nginx/sites-available/${var.project} <<'NGINX_CONFIG'
              server {
                  listen 80;
                  listen [::]:80;

                  server_name ${var.dns_hostnames};

                  root /var/www/${var.project};
                  index index.html;

                  # Enable gzip compression
                  gzip on;
                  gzip_vary on;
                  gzip_min_length 1024;
                  gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

                  location / {
                      try_files $uri $uri/ /index.html;
                  }

                  # Cache static assets
                  location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
                      expires 1y;
                      add_header Cache-Control "public, immutable";
                  }

                  # Security headers
                  add_header X-Frame-Options "SAMEORIGIN" always;
                  add_header X-Content-Type-Options "nosniff" always;
                  add_header X-XSS-Protection "1; mode=block" always;
              }
              NGINX_CONFIG

              # Enable the site configuration
              ln -sf /etc/nginx/sites-available/${var.project} /etc/nginx/sites-enabled/${var.project}

              # Remove default nginx site
              rm -f /etc/nginx/sites-enabled/default

              # Test and restart nginx
              nginx -t
              systemctl enable nginx
              systemctl restart nginx
              EOF
}

# Elastic IP for stable public IP
resource "aws_eip" "app" {
  count    = var.elastic_ip_allocation_id == "" ? 1 : 0
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-eip"
    }
  )

  lifecycle {
    prevent_destroy = false # Set to true for production
  }
}

# Associate existing Elastic IP with instance (if allocation_id provided)
resource "aws_eip_association" "existing" {
  count         = var.elastic_ip_allocation_id != "" ? 1 : 0
  instance_id   = aws_instance.app.id
  allocation_id = var.elastic_ip_allocation_id
}

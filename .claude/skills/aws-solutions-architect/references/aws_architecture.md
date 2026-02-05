# AWS Architecture Best Practices

Reference architecture patterns based on AWS Well-Architected Framework.

## AWS Well-Architected Framework

### Six Pillars

1. **Operational Excellence**: Run and monitor systems to deliver business value
2. **Security**: Protect data, systems, and assets
3. **Reliability**: Ensure workloads perform their intended function correctly and consistently
4. **Performance Efficiency**: Use computing resources efficiently to meet requirements
5. **Cost Optimization**: Avoid unnecessary costs
6. **Sustainability**: Minimize environmental impacts of cloud workloads

## VPC Architecture Patterns

### Multi-Tier VPC

**Standard 3-tier architecture with high availability:**

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "production-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

# Public Subnets (across 3 AZs)
resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "public-subnet-${count.index + 1}"
    Tier = "Public"
  }
}

# Private App Subnets
resource "aws_subnet" "private_app" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "private-app-subnet-${count.index + 1}"
    Tier = "Application"
  }
}

# Private Data Subnets
resource "aws_subnet" "private_data" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 20}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "private-data-subnet-${count.index + 1}"
    Tier = "Data"
  }
}

# NAT Gateways (one per AZ for HA)
resource "aws_eip" "nat" {
  count  = 3
  domain = "vpc"
  
  tags = {
    Name = "nat-eip-${count.index + 1}"
  }
}

resource "aws_nat_gateway" "main" {
  count         = 3
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = {
    Name = "nat-gateway-${count.index + 1}"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table" "private" {
  count  = 3
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  
  tags = {
    Name = "private-route-table-${count.index + 1}"
  }
}
```

### Transit Gateway Architecture

**Hub-and-spoke for multi-VPC connectivity:**

```hcl
resource "aws_ec2_transit_gateway" "main" {
  description                     = "Central TGW for multi-VPC connectivity"
  default_route_table_association = "disable"
  default_route_table_propagation = "disable"
  
  tags = {
    Name = "central-tgw"
  }
}

# Spoke VPC attachments
resource "aws_ec2_transit_gateway_vpc_attachment" "spoke" {
  count              = length(var.spoke_vpcs)
  subnet_ids         = var.spoke_vpcs[count.index].subnet_ids
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  vpc_id             = var.spoke_vpcs[count.index].vpc_id
  
  tags = {
    Name = "tgw-attachment-${var.spoke_vpcs[count.index].name}"
  }
}

# Route table for production traffic
resource "aws_ec2_transit_gateway_route_table" "production" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  
  tags = {
    Name = "production-route-table"
  }
}

# Route table for non-production
resource "aws_ec2_transit_gateway_route_table" "non_production" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  
  tags = {
    Name = "non-production-route-table"
  }
}
```

**Use Cases:**
- Multi-VPC connectivity with centralized egress
- Hybrid cloud with AWS Direct Connect or VPN
- Network segmentation by environment or workload
- Centralized network inspection

### VPC Peering

**Direct connectivity between VPCs:**

```hcl
resource "aws_vpc_peering_connection" "peer" {
  peer_vpc_id = aws_vpc.peer.id
  vpc_id      = aws_vpc.main.id
  auto_accept = true
  
  tags = {
    Name = "vpc-peer-main-to-peer"
  }
}

# Update route tables for peered VPCs
resource "aws_route" "main_to_peer" {
  route_table_id            = aws_route_table.main.id
  destination_cidr_block    = aws_vpc.peer.cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.peer.id
}
```

**Considerations:**
- No transitive peering (A→B→C requires A→C peering)
- Non-overlapping CIDR blocks required
- Lower latency than Transit Gateway
- Limited to same region by default (inter-region requires special setup)

### PrivateLink

**Access services without internet exposure:**

```hcl
# Service provider: Expose service via endpoint
resource "aws_vpc_endpoint_service" "service" {
  acceptance_required        = false
  network_load_balancer_arns = [aws_lb.nlb.arn]
  
  tags = {
    Name = "my-service-endpoint"
  }
}

# Service consumer: Connect to service
resource "aws_vpc_endpoint" "consumer" {
  vpc_id             = aws_vpc.consumer.id
  service_name       = aws_vpc_endpoint_service.service.service_name
  vpc_endpoint_type  = "Interface"
  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.endpoint.id]
  
  private_dns_enabled = true
}
```

## Network Security

### Security Groups

**Stateful firewall at instance level:**

```hcl
# Application Load Balancer security group
resource "aws_security_group" "alb" {
  name        = "alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    description     = "To application instances"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

# Application instance security group
resource "aws_security_group" "app" {
  name        = "app-sg"
  description = "Security group for application instances"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    description     = "From ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    description     = "To RDS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.rds.id]
  }
  
  egress {
    description = "HTTPS to internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Database security group
resource "aws_security_group" "rds" {
  name        = "rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    description     = "From application"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}
```

### Network ACLs

**Stateless firewall at subnet level:**

```hcl
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id
  
  # Allow inbound from VPC
  ingress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = aws_vpc.main.cidr_block
    from_port  = 0
    to_port    = 0
  }
  
  # Allow outbound to VPC
  egress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = aws_vpc.main.cidr_block
    from_port  = 0
    to_port    = 0
  }
  
  # Allow HTTPS outbound to internet
  egress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }
  
  # Allow ephemeral ports for return traffic
  ingress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }
  
  tags = {
    Name = "private-nacl"
  }
}
```

## IAM Best Practices

### Least Privilege Policies

**EC2 instance role with specific permissions:**

```hcl
data "aws_iam_policy_document" "app_instance" {
  # Allow reading from specific S3 bucket
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::my-app-bucket",
      "arn:aws:s3:::my-app-bucket/*"
    ]
  }
  
  # Allow reading secrets
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:app/*"
    ]
  }
  
  # Allow CloudWatch Logs
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:us-east-1:ACCOUNT:log-group:/aws/app/*"
    ]
  }
}

resource "aws_iam_role_policy" "app_instance" {
  name   = "app-instance-policy"
  role   = aws_iam_role.app_instance.id
  policy = data.aws_iam_policy_document.app_instance.json
}
```

### Cross-Account Access

**Trust relationship for cross-account access:**

```hcl
data "aws_iam_policy_document" "cross_account_assume" {
  statement {
    effect = "Allow"
    
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::TRUSTED_ACCOUNT:root"]
    }
    
    actions = ["sts:AssumeRole"]
    
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = ["unique-external-id"]
    }
  }
}

resource "aws_iam_role" "cross_account" {
  name               = "cross-account-role"
  assume_role_policy = data.aws_iam_policy_document.cross_account_assume.json
}
```

### Service Control Policies (SCPs)

**Preventive controls at organization level:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:InstanceType": [
            "t3.micro",
            "t3.small",
            "t3.medium"
          ]
        }
      }
    },
    {
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPublicAccessBlock"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "s3:BlockPublicAcls": "false"
        }
      }
    }
  ]
}
```

## High Availability Patterns

### Multi-AZ Deployment

**Auto Scaling Group across availability zones:**

```hcl
resource "aws_launch_template" "app" {
  name_prefix   = "app-"
  image_id      = data.aws_ami.app.id
  instance_type = "t3.medium"
  
  iam_instance_profile {
    arn = aws_iam_instance_profile.app.arn
  }
  
  vpc_security_group_ids = [aws_security_group.app.id]
  
  user_data = base64encode(templatefile("user_data.sh", {
    environment = "production"
  }))
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "app-instance"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "app-asg"
  vpc_zone_identifier = aws_subnet.private_app[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  min_size            = 3
  max_size            = 12
  deparentAd_capacity    = 6
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "app-asg-instance"
    propagate_at_launch = true
  }
}
```

### Application Load Balancer

```hcl
resource "aws_lb" "app" {
  name               = "app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = true
  enable_http2               = true
  
  tags = {
    Name = "app-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name     = "app-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  deregistration_delay = 30
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.app.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

### RDS Multi-AZ

```hcl
resource "aws_db_instance" "main" {
  identifier     = "production-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn
  
  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "production-db-final-snapshot"
  
  tags = {
    Name = "production-db"
  }
}
```

## Disaster Recovery

### Backup Strategy

**AWS Backup for centralized backup management:**

```hcl
resource "aws_backup_plan" "main" {
  name = "production-backup-plan"
  
  rule {
    rule_name         = "daily_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 * * ? *)"
    
    lifecycle {
      delete_after = 30
    }
    
    recovery_point_tags = {
      BackupType = "Daily"
    }
  }
  
  rule {
    rule_name         = "weekly_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 2 ? * SUN *)"
    
    lifecycle {
      delete_after = 90
    }
    
    recovery_point_tags = {
      BackupType = "Weekly"
    }
  }
}

resource "aws_backup_selection" "main" {
  name         = "production-resources"
  plan_id      = aws_backup_plan.main.id
  iam_role_arn = aws_iam_role.backup.arn
  
  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Backup"
    value = "true"
  }
}
```

### Multi-Region Architecture

**Route 53 failover routing:**

```hcl
resource "aws_route53_health_check" "primary" {
  fqdn              = "primary.example.com"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30
  
  tags = {
    Name = "primary-region-health"
  }
}

resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "app.example.com"
  type    = "A"
  
  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.primary.id
  
  failover_routing_policy {
    type = "PRIMARY"
  }
  
  alias {
    name                   = aws_lb.primary.dns_name
    zone_id                = aws_lb.primary.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "app.example.com"
  type    = "A"
  
  set_identifier = "secondary"
  
  failover_routing_policy {
    type = "SECONDARY"
  }
  
  alias {
    name                   = aws_lb.secondary.dns_name
    zone_id                = aws_lb.secondary.zone_id
    evaluate_target_health = true
  }
}
```

## Observability

### CloudWatch Logs

```hcl
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/app/production"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.logs.arn
  
  tags = {
    Application = "production-app"
  }
}

resource "aws_cloudwatch_log_metric_filter" "errors" {
  name           = "error-count"
  log_group_name = aws_cloudwatch_log_group.app.name
  pattern        = "[time, request_id, level = ERROR*, msg]"
  
  metric_transformation {
    name      = "ErrorCount"
    namespace = "Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_errors" {
  alarm_name          = "high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorCount"
  namespace           = "Application"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Triggers when error rate is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

### X-Ray Tracing

```hcl
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "production-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.05
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
}
```

## Cost Optimization

### Reserved Instances and Savings Plans

- Use Compute Savings Plans for flexible commitment across EC2, Lambda, Fargate
- Reserve RDS instances for predictable database workloads
- Use Convertible RIs for long-term flexibility

### S3 Lifecycle Policies

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  rule {
    id     = "archive-old-logs"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}
```

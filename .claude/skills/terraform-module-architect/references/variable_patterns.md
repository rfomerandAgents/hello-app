# Terraform Variable Patterns

Comprehensive guide to designing flexible and maintainable Terraform module variables.

## Basic Variable Types

### String Variables

```hcl
variable "name" {
  description = "Resource name"
  type        = string
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Must be dev, staging, or production."
  }
}
```

### Number Variables

```hcl
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
  
  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}
```

### Boolean Variables

```hcl
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "create_dns_record" {
  description = "Create Route53 DNS record"
  type        = bool
  default     = false
}
```

## Collection Types

### List Variables

```hcl
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access"
  type        = list(string)
  
  validation {
    condition     = length(var.allowed_cidr_blocks) > 0
    error_message = "At least one CIDR block must be specified."
  }
}
```

### Map Variables

```hcl
variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "environment_settings" {
  description = "Settings per environment"
  type        = map(string)
  default = {
    dev        = "t3.micro"
    staging    = "t3.small"
    production = "t3.medium"
  }
}
```

### Set Variables

```hcl
variable "security_group_ids" {
  description = "Set of security group IDs"
  type        = set(string)
  default     = []
}
```

## Object Types

### Simple Object

```hcl
variable "vpc_config" {
  description = "VPC configuration"
  type = object({
    cidr_block           = string
    enable_dns_hostnames = bool
    enable_dns_support   = bool
  })
  
  default = {
    cidr_block           = "10.0.0.0/16"
    enable_dns_hostnames = true
    enable_dns_support   = true
  }
}
```

### Complex Nested Object

```hcl
variable "application_config" {
  description = "Complete application configuration"
  type = object({
    name        = string
    environment = string
    
    compute = object({
      instance_type = string
      min_size      = number
      max_size      = number
      deparentAd_size  = number
    })
    
    database = object({
      engine         = string
      instance_class = string
      allocated_storage = number
      multi_az       = bool
    })
    
    networking = object({
      vpc_id     = string
      subnet_ids = list(string)
    })
  })
}

# Usage
application_config = {
  name        = "myapp"
  environment = "production"
  
  compute = {
    instance_type = "t3.medium"
    min_size      = 2
    max_size      = 10
    deparentAd_size  = 3
  }
  
  database = {
    engine            = "postgres"
    instance_class    = "db.t3.medium"
    allocated_storage = 100
    multi_az          = true
  }
  
  networking = {
    vpc_id     = "vpc-12345"
    subnet_ids = ["subnet-111", "subnet-222"]
  }
}
```

### List of Objects

```hcl
variable "ingress_rules" {
  description = "List of ingress rules"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  
  default = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTP"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS"
    }
  ]
}
```

### Map of Objects

```hcl
variable "subnets" {
  description = "Map of subnet configurations"
  type = map(object({
    cidr_block        = string
    availability_zone = string
    public            = bool
    tags              = map(string)
  }))
  
  default = {
    public-1a = {
      cidr_block        = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      public            = true
      tags              = { Type = "public" }
    }
    private-1a = {
      cidr_block        = "10.0.10.0/24"
      availability_zone = "us-east-1a"
      public            = false
      tags              = { Type = "private" }
    }
  }
}

# Usage in resource
resource "aws_subnet" "main" {
  for_each = var.subnets
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.availability_zone
  
  map_public_ip_on_launch = each.value.public
  
  tags = merge(
    local.common_tags,
    each.value.tags,
    { Name = "${local.name_prefix}-${each.key}" }
  )
}
```

## Optional Attributes

```hcl
variable "database_config" {
  description = "Database configuration"
  type = object({
    engine            = string
    instance_class    = string
    allocated_storage = number
    
    # Optional attributes with defaults
    backup_retention_period = optional(number, 7)
    backup_window          = optional(string, "03:00-04:00")
    maintenance_window     = optional(string, "mon:04:00-mon:05:00")
    multi_az              = optional(bool, false)
    
    # Optional complex attributes
    replicas = optional(list(object({
      instance_class = string
      region        = string
    })), [])
  })
}
```

## Dynamic Default Values

```hcl
# Environment-based defaults
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = null  # Will be set based on environment
}

locals {
  instance_type = coalesce(
    var.instance_type,
    var.environment == "production" ? "t3.large" : "t3.micro"
  )
}

# Region-based defaults
variable "ami_id" {
  description = "AMI ID (defaults to latest Amazon Linux 2)"
  type        = string
  default     = null
}

data "aws_ami" "amazon_linux_2" {
  count = var.ami_id == null ? 1 : 0
  
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

locals {
  ami_id = coalesce(var.ami_id, try(data.aws_ami.amazon_linux_2[0].id, null))
}
```

## Validation Patterns

### CIDR Validation

```hcl
variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  
  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be valid IPv4 CIDR block."
  }
}
```

### Regex Validation

```hcl
variable "name" {
  description = "Resource name (alphanumeric and hyphens only)"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.name))
    error_message = "Name must contain only lowercase alphanumeric characters and hyphens."
  }
}

variable "email" {
  description = "Email address for notifications"
  type        = string
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email))
    error_message = "Must be a valid email address."
  }
}
```

### Range Validation

```hcl
variable "port" {
  description = "Port number"
  type        = number
  
  validation {
    condition     = var.port >= 1 && var.port <= 65535
    error_message = "Port must be between 1 and 65535."
  }
}
```

### List Content Validation

```hcl
variable "instance_types" {
  description = "List of allowed instance types"
  type        = list(string)
  
  validation {
    condition = alltrue([
      for t in var.instance_types : can(regex("^t[23]\\.", t))
    ])
    error_message = "All instance types must be t2 or t3 family."
  }
}
```

### Cross-variable Validation

```hcl
variable "min_size" {
  description = "Minimum size"
  type        = number
}

variable "max_size" {
  description = "Maximum size"
  type        = number
  
  validation {
    condition     = var.max_size >= var.min_size
    error_message = "max_size must be greater than or equal to min_size."
  }
}
```

## Sensitive Variables

```hcl
variable "database_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.database_password) >= 16
    error_message = "Password must be at least 16 characters."
  }
}

variable "api_keys" {
  description = "Map of API keys"
  type        = map(string)
  sensitive   = true
}
```

## Nullable Variables

```hcl
variable "backup_retention_period" {
  description = "Backup retention period in days (null to disable)"
  type        = number
  default     = null
  nullable    = true
}

# Usage
resource "aws_db_instance" "main" {
  # Only set if not null
  backup_retention_period = var.backup_retention_period != null ? var.backup_retention_period : 0
}
```

## Feature Flags

```hcl
variable "features" {
  description = "Feature flags"
  type = object({
    enable_monitoring       = optional(bool, true)
    enable_backup          = optional(bool, true)
    enable_encryption      = optional(bool, true)
    enable_multi_az        = optional(bool, false)
    enable_deletion_protection = optional(bool, false)
  })
  
  default = {}
}

# Usage
resource "aws_db_instance" "main" {
  multi_az                = var.features.enable_multi_az
  deletion_protection     = var.features.enable_deletion_protection
  storage_encrypted       = var.features.enable_encryption
  backup_retention_period = var.features.enable_backup ? 7 : 0
}
```

## Best Practices

### 1. Always Provide Descriptions

```hcl
# ❌ Bad
variable "count" {
  type = number
}

# ✅ Good
variable "instance_count" {
  description = "Number of EC2 instances to create for the application tier"
  type        = number
  default     = 2
  
  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}
```

### 2. Use Explicit Types

```hcl
# ❌ Bad - Type inferred
variable "tags" {
  default = {}
}

# ✅ Good - Explicit type
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

### 3. Provide Sensible Defaults

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"  # Good default for development
}
```

### 4. Group Related Variables

```hcl
# Networking variables
variable "vpc_id" { }
variable "subnet_ids" { }
variable "security_group_ids" { }

# Compute variables
variable "instance_type" { }
variable "ami_id" { }
variable "key_name" { }

# Tagging variables
variable "name" { }
variable "environment" { }
variable "tags" { }
```

### 5. Use Validation

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}
```

### 6. Document Complex Objects

```hcl
variable "load_balancer_config" {
  description = <<-EOT
    Load balancer configuration object:
    - name: Name of the load balancer
    - internal: Whether the LB is internal
    - subnets: List of subnet IDs
    - security_groups: List of security group IDs
    - listeners: List of listener configurations
  EOT
  
  type = object({
    name            = string
    internal        = bool
    subnets         = list(string)
    security_groups = list(string)
    
    listeners = list(object({
      port     = number
      protocol = string
      certificate_arn = optional(string)
    }))
  })
}
```

### 7. Mark Sensitive Data

```hcl
variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true  # Won't be displayed in logs
}
```

### 8. Use Prefixes for Optional Features

```hcl
variable "enable_monitoring" { }
variable "enable_backup" { }
variable "enable_encryption" { }
variable "create_dns_record" { }
variable "create_alarms" { }
```

## Anti-Patterns

### ❌ Don't Use Variable for Constants

```hcl
# Bad
variable "service_name" {
  default = "my-service"  # This never changes
}

# Good
locals {
  service_name = "my-service"
}
```

### ❌ Don't Over-parameterize

```hcl
# Bad - Too many specific variables
variable "cpu_credit_specification" { }
variable "disable_api_termination" { }
variable "ebs_optimized" { }
variable "get_password_data" { }
variable "hibernation" { }
variable "host_id" { }
# ... 20 more variables

# Good - Group related configuration
variable "instance_config" {
  type = object({
    ebs_optimized = optional(bool, false)
    monitoring    = optional(bool, true)
    # Only expose commonly changed settings
  })
}
```

### ❌ Don't Hardcode Environment-Specific Values

```hcl
# Bad
variable "instance_type" {
  default = "t3.large"  # Too large for dev!
}

# Good
variable "instance_type" {
  description = "Instance type (consider using t3.micro for dev)"
  type        = string
}

# Or provide environment-based defaults
locals {
  instance_type = var.instance_type != null ? var.instance_type : (
    var.environment == "production" ? "t3.large" : "t3.micro"
  )
}
```

#!/usr/bin/env python3
"""
Terraform Module Scaffolding Generator

Generates a complete Terraform module structure with best practices.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

TEMPLATES = {
    'generic': {
        'description': 'Generic Terraform module template',
        'provider': 'aws'
    },
    'vpc': {
        'description': 'VPC networking module',
        'provider': 'aws',
        'resources': ['vpc', 'subnets', 'route_tables', 'nat_gateway', 'internet_gateway']
    },
    'compute': {
        'description': 'EC2 compute module',
        'provider': 'aws',
        'resources': ['instance', 'security_group', 'key_pair']
    },
    'database': {
        'description': 'RDS database module',
        'provider': 'aws',
        'resources': ['db_instance', 'db_subnet_group', 'db_parameter_group']
    }
}

class ModuleScaffolder:
    def __init__(self, name, module_type='generic', output_dir='.'):
        self.name = name
        self.module_type = module_type
        self.output_dir = Path(output_dir)
        self.module_path = self.output_dir / name
        self.template = TEMPLATES.get(module_type, TEMPLATES['generic'])
        
    def create_structure(self):
        """Create module directory structure"""
        print(f"🏗️  Creating module: {self.name}")
        print(f"   Type: {self.module_type}")
        print(f"   Location: {self.module_path}\n")
        
        # Create main directories
        self.module_path.mkdir(parents=True, exist_ok=True)
        (self.module_path / 'examples' / 'basic').mkdir(parents=True, exist_ok=True)
        (self.module_path / 'examples' / 'complete').mkdir(parents=True, exist_ok=True)
        (self.module_path / 'tests' / 'unit').mkdir(parents=True, exist_ok=True)
        
        # Create files
        self.create_main_tf()
        self.create_variables_tf()
        self.create_outputs_tf()
        self.create_versions_tf()
        self.create_readme()
        self.create_changelog()
        self.create_license()
        self.create_examples()
        self.create_gitignore()
        
        print("✅ Module scaffolding complete!\n")
        self.print_next_steps()
    
    def create_main_tf(self):
        """Create main.tf with template resources"""
        content = f'''# {self.name} - Main Resources

locals {{
  name_prefix = "${{var.name}}-${{var.environment}}"
  
  common_tags = merge(
    var.tags,
    {{
      Name        = local.name_prefix
      Environment = var.environment
      ManagedBy   = "Terraform"
      Module      = "{self.name}"
    }}
  )
}}

# TODO: Add your resource definitions here
# Example:
# resource "aws_vpc" "main" {{
#   cidr_block = var.cidr_block
#   tags       = local.common_tags
# }}
'''
        
        if self.module_type == 'vpc':
            content += self.get_vpc_resources()
        elif self.module_type == 'compute':
            content += self.get_compute_resources()
        elif self.module_type == 'database':
            content += self.get_database_resources()
        
        (self.module_path / 'main.tf').write_text(content)
        print("  ✓ Created main.tf")
    
    def create_variables_tf(self):
        """Create variables.tf"""
        content = f'''# {self.name} - Input Variables

variable "name" {{
  description = "Name prefix for all resources"
  type        = string
}}

variable "environment" {{
  description = "Environment name (dev, staging, production)"
  type        = string
  
  validation {{
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }}
}}

variable "tags" {{
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {{}}
}}

# TODO: Add module-specific variables here
'''
        
        if self.module_type == 'vpc':
            content += self.get_vpc_variables()
        elif self.module_type == 'compute':
            content += self.get_compute_variables()
        elif self.module_type == 'database':
            content += self.get_database_variables()
        
        (self.module_path / 'variables.tf').write_text(content)
        print("  ✓ Created variables.tf")
    
    def create_outputs_tf(self):
        """Create outputs.tf"""
        content = f'''# {self.name} - Outputs

# TODO: Add your output definitions here
# Example:
# output "id" {{
#   description = "The ID of the created resource"
#   value       = aws_resource.main.id
# }}

# output "arn" {{
#   description = "The ARN of the created resource"
#   value       = aws_resource.main.arn
# }}
'''
        (self.module_path / 'outputs.tf').write_text(content)
        print("  ✓ Created outputs.tf")
    
    def create_versions_tf(self):
        """Create versions.tf"""
        content = f'''# {self.name} - Version Constraints

terraform {{
  required_version = ">= 1.0"
  
  required_providers {{
    {self.template['provider']} = {{
      source  = "hashicorp/{self.template['provider']}"
      version = ">= 5.0"
    }}
  }}
}}
'''
        (self.module_path / 'versions.tf').write_text(content)
        print("  ✓ Created versions.tf")
    
    def create_readme(self):
        """Create README.md"""
        content = f'''# Terraform {self.name.title()} Module

{self.template['description']}

## Usage

```hcl
module "{self.name}" {{
  source = "./{self.name}"
  
  name        = "myapp"
  environment = "production"
  
  tags = {{
    Project = "MyProject"
    Owner   = "Platform Team"
  }}
}}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| {self.template['provider']} | >= 5.0 |

## Providers

| Name | Version |
|------|---------|
| {self.template['provider']} | >= 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | Name prefix for resources | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |
| tags | Additional tags | `map(string)` | `{{}}` | no |

## Outputs

| Name | Description |
|------|-------------|
| id | Resource ID |

## Examples

- [Basic](./examples/basic) - Basic module usage
- [Complete](./examples/complete) - Complete configuration with all options

## Authors

Created by Platform Engineering Team

## License

Apache 2.0
'''
        (self.module_path / 'README.md').write_text(content)
        print("  ✓ Created README.md")
    
    def create_changelog(self):
        """Create CHANGELOG.md"""
        content = f'''# Changelog

All notable changes to this module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial module scaffolding
- Basic resource configuration

## [1.0.0] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial release
- Core {self.module_type} functionality
'''
        (self.module_path / 'CHANGELOG.md').write_text(content)
        print("  ✓ Created CHANGELOG.md")
    
    def create_license(self):
        """Create LICENSE file"""
        content = '''Apache License
Version 2.0, January 2004

Copyright (c) Platform Engineering Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
'''
        (self.module_path / 'LICENSE').write_text(content)
        print("  ✓ Created LICENSE")
    
    def create_examples(self):
        """Create example configurations"""
        # Basic example
        basic_main = f'''module "{self.name}" {{
  source = "../.."
  
  name        = "example"
  environment = "dev"
}}
'''
        (self.module_path / 'examples' / 'basic' / 'main.tf').write_text(basic_main)
        
        # Complete example
        complete_main = f'''module "{self.name}" {{
  source = "../.."
  
  name        = "example"
  environment = "production"
  
  tags = {{
    Project = "Example"
    Owner   = "Platform"
  }}
}}
'''
        (self.module_path / 'examples' / 'complete' / 'main.tf').write_text(complete_main)
        print("  ✓ Created examples")
    
    def create_gitignore(self):
        """Create .gitignore"""
        content = '''# Terraform
.terraform/
.terraform.lock.hcl
*.tfstate
*.tfstate.*
*.tfplan
*.tfvars
!terraform.tfvars.example

# Crash logs
crash.log

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
'''
        (self.module_path / '.gitignore').write_text(content)
        print("  ✓ Created .gitignore")
    
    def get_vpc_resources(self):
        return '''
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-vpc"
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-igw"
    }
  )
}
'''
    
    def get_vpc_variables(self):
        return '''
variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be valid IPv4 CIDR."
  }
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in VPC"
  type        = bool
  default     = true
}
'''
    
    def get_compute_resources(self):
        return '''
# Security Group
resource "aws_security_group" "main" {
  name        = "${local.name_prefix}-sg"
  description = "Security group for ${local.name_prefix}"
  vpc_id      = var.vpc_id
  
  tags = local.common_tags
}

# EC2 Instance
resource "aws_instance" "main" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  
  vpc_security_group_ids = [aws_security_group.main.id]
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-instance"
    }
  )
}
'''
    
    def get_compute_variables(self):
        return '''
variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for instance"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
'''
    
    def get_database_resources(self):
        return '''
# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet"
  subnet_ids = var.subnet_ids
  
  tags = local.common_tags
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-db"
  
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class
  
  allocated_storage = var.allocated_storage
  storage_encrypted = var.storage_encrypted
  
  db_name  = var.database_name
  username = var.master_username
  password = var.master_password
  
  db_subnet_group_name = aws_db_subnet_group.main.name
  
  skip_final_snapshot = var.skip_final_snapshot
  
  tags = local.common_tags
}
'''
    
    def get_database_variables(self):
        return '''
variable "subnet_ids" {
  description = "List of subnet IDs for DB subnet group"
  type        = list(string)
}

variable "engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "15.4"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "storage_encrypted" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "database_name" {
  description = "Name of the database"
  type        = string
}

variable "master_username" {
  description = "Master username"
  type        = string
  sensitive   = true
}

variable "master_password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying"
  type        = bool
  default     = false
}
'''
    
    def print_next_steps(self):
        """Print next steps for user"""
        print("📋 Next Steps:\n")
        print(f"1. cd {self.module_path}")
        print("2. Review and customize the generated files")
        print("3. Add your resource definitions to main.tf")
        print("4. Update variables.tf with required inputs")
        print("5. Define outputs in outputs.tf")
        print("6. Test with examples:")
        print(f"   cd examples/basic && terraform init && terraform plan")
        print("7. Generate documentation:")
        print("   terraform-docs markdown table . > README.md")
        print("8. Initialize git:")
        print("   git init && git add . && git commit -m 'Initial commit'")
        print("")

def main():
    parser = argparse.ArgumentParser(description='Generate Terraform module scaffolding')
    parser.add_argument('name', help='Module name')
    parser.add_argument('--type', choices=['generic', 'vpc', 'compute', 'database'],
                       default='generic', help='Module type template')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    
    args = parser.parse_args()
    
    scaffolder = ModuleScaffolder(args.name, args.type, args.output_dir)
    scaffolder.create_structure()

if __name__ == '__main__':
    main()

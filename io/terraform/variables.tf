# Variables for {{PROJECT_NAME}} Infrastructure
# Replace {{PROJECT_NAME}} placeholders with your project name

variable "project" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "{{PROJECT_NAME_SLUG}}"
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod, sandbox)"
  type        = string
  default     = "sandbox"

  validation {
    condition     = contains(["dev", "staging", "prod", "sandbox"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod, or sandbox."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"

  validation {
    condition     = can(regex("^[a-z][0-9][an]?\\.(nano|micro|small|medium|large|xlarge|[0-9]+xlarge)$", var.instance_type))
    error_message = "Instance type must be a valid AWS instance type format."
  }
}

variable "app_version" {
  description = "Application version to deploy"
  type        = string
  default     = "v1"
}

variable "ssh_public_key" {
  description = "SSH public key content (not path)"
  type        = string
  sensitive   = true
}

variable "allowed_ssh_cidr_blocks" {
  description = "List of CIDR blocks allowed to SSH. Restrict this in production!"
  type        = list(string)
  default     = ["0.0.0.0/0"]

  validation {
    condition = alltrue([
      for cidr in var.allowed_ssh_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All entries must be valid CIDR blocks."
  }
}

variable "build_cidr_blocks" {
  description = "CIDR blocks allowed for Packer build access"
  type        = list(string)
  default     = ["0.0.0.0/0"]

  validation {
    condition = alltrue([
      for cidr in var.build_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All entries must be valid CIDR blocks."
  }
}

variable "workflow_id" {
  description = "IPE workflow identifier for tracking deployments"
  type        = string
  default     = ""
}

variable "app_ami_id" {
  description = "Specific AMI ID to use (overrides automatic AMI lookup)"
  type        = string
  default     = ""
}

variable "elastic_ip_allocation_id" {
  description = "Allocation ID of existing Elastic IP to use"
  type        = string
  default     = ""
}

variable "elastic_ip" {
  description = "Static Elastic IP address for documentation purposes"
  type        = string
  default     = ""
}

variable "dns_hostnames" {
  description = "Space-separated list of hostnames for nginx server_name"
  type        = string
  default     = "{{DOMAIN}} www.{{DOMAIN}}"
}

variable "ssl_cert" {
  description = "SSL/TLS certificate (PEM format)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssl_key" {
  description = "SSL/TLS private key (PEM format)"
  type        = string
  default     = ""
  sensitive   = true
}

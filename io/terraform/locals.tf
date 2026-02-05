# Local values for computed values, naming conventions, and common tags
# Following HashiCorp best practices: centralize computed values

locals {
  # Naming convention: consistent prefix for all resources
  name_prefix = "${var.project}-${var.environment}"

  # Deployment metadata
  deployment_timestamp_iso = timestamp()

  # Common tags applied to all resources
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    Repository  = "{{GITHUB_REPO_NAME}}"
    Terraform   = "true"
    TFVersion   = "1.2.0+"
  }

  # AMI selection: use specific AMI if provided, otherwise use data source
  ami_id = var.app_ami_id != "" ? var.app_ami_id : data.aws_ami.app.id

  # Unified public IP reference
  public_ip = var.elastic_ip_allocation_id != "" ? data.aws_eip.existing[0].public_ip : aws_eip.app[0].public_ip

  # Security: SSH CIDR validation warning
  is_production_ssh_open = var.environment == "prod" && contains(var.allowed_ssh_cidr_blocks, "0.0.0.0/0")
}

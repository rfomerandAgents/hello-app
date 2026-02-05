# Terraform configuration block
# Specifies required Terraform version, providers, and backend configuration

terraform {
  # Terraform Cloud backend for remote state management
  # Benefits: State locking, versioning, collaboration, secure variable storage
  cloud {
    organization = "{{TF_ORGANIZATION}}"

    workspaces {
      project = "{{TF_PROJECT}}"
      tags    = ["{{PROJECT_NAME_SLUG}}"]
      # Available workspaces: {{PROJECT_NAME_SLUG}}-dev, {{PROJECT_NAME_SLUG}}-staging, {{PROJECT_NAME_SLUG}}-prod, {{PROJECT_NAME_SLUG}}-sandbox
      # To switch: terraform workspace select {{PROJECT_NAME_SLUG}}-sandbox
    }
  }

  # Provider version constraints
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    # Cloudflare provider (optional - uncomment if needed)
    # cloudflare = {
    #   source  = "cloudflare/cloudflare"
    #   version = "~> 4.0"
    # }
  }

  required_version = ">= 1.2.0"
}

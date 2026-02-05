# AWS Solutions Architect Assets

This directory contains starter templates and boilerplate code for AWS infrastructure automation.

## Contents

### github_workflows/
Ready-to-use GitHub Actions workflow templates:

- **deploy-infrastructure.yml**: Complete multi-environment deployment pipeline with validation, planning, and progressive deployment through dev → staging → production
- **build-ami.yml**: Automated Packer AMI building with validation, tagging, and integration with Terraform

### packer_templates/
Packer template examples:

- **golden-ami.pkr.hcl**: Comprehensive golden AMI template with security hardening, monitoring, HCP Packer integration, and multi-region support

### terraform_modules/
(Directory reserved for reusable Terraform module examples)

## Usage

Copy the relevant template files to your repository and customize them for your specific needs. Each template includes comments and examples to guide configuration.

The templates are designed to work together as part of a complete infrastructure automation pipeline.

# Terraform Destroy Planning

Create a plan to destroy all {{PROJECT_NAME}} AWS infrastructure using the exact specified markdown `Plan Format`.

## Instructions

- IMPORTANT: You're writing a plan to destroy AWS infrastructure, not actually destroying it
- The plan will be implemented later using the `/implement` command
- Create the plan in the `specs/` directory with filename: `terraform-destroy-{timestamp}.md`
  - Replace `{timestamp}` with current timestamp (e.g., "20251108-143022")
- Use the `Plan Format` below to create the plan
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value
- Research the current infrastructure state before planning the destruction
- Be thorough about what will be destroyed and what will remain

## Relevant Files

Focus on the following files:
- `io/terraform/README.md` - Infrastructure documentation
- `io/terraform/main.tf` - Terraform configuration showing resources
- `io/terraform/scripts/destroy.sh` - Destruction script
- `io/terraform/terraform.tfstate` - Current infrastructure state
- `.env` - AWS credentials configuration

## Plan Format

```md
# Infrastructure Destruction Plan

## Overview
Destroy all {{PROJECT_NAME}} AWS infrastructure deployed via Terraform.

## Warning
⚠️ This will **permanently delete** all AWS resources:
- EC2 instance
- Elastic IP
- Security Group
- SSH Key Pair

**Note**: The Packer-built AMI will remain and must be manually deregistered if desired.

## Current Infrastructure State
<analyze terraform.tfstate and list current deployed resources with their IDs>

## Resources to be Destroyed
<list each resource that will be destroyed with details>

### EC2 Instance
- Instance ID: <instance_id>
- Instance Type: <instance_type>
- Public IP: <public_ip>

### Elastic IP
- Allocation ID: <allocation_id>
- Public IP: <public_ip>

### Security Group
- Group ID: <group_id>
- Name: <group_name>

### SSH Key Pair
- Key Name: <key_name>

## Resources that will Remain
<list resources that will NOT be destroyed>

### AMI (Amazon Machine Image)
- AMI ID: <ami_id>
- Name: <ami_name>
- Note: Must be manually deregistered in AWS Console if cleanup desired

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Pre-Destruction Verification
- Verify current infrastructure state with `cd terraform && terraform show`
- Confirm AWS credentials are configured in `.env` file
- Check that no critical data or state needs to be backed up

### 2. Execute Destruction
- Navigate to terraform directory: `cd terraform`
- Set SSH public key environment variable: `export TF_VAR_ssh_public_key="$(cat ~/.ssh/id_rsa_aws.pub)"`
- Run destroy script: `./scripts/destroy.sh`
- Confirm destruction when prompted by typing `yes`
- Wait for Terraform to complete resource deletion

### 3. Verify Destruction
- Run validation commands to confirm all resources removed
- Check Terraform state is clean

## Validation Commands
Execute every command to validate infrastructure is destroyed.

- `cd terraform && terraform show` - Verify no resources remain in state
- `source .env && export AWS_DEFAULT_REGION=us-east-1 && aws ec2 describe-instances --filters "Name=tag:Name,Values={{PROJECT_SLUG}}-dev" --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output table` - Verify EC2 instance terminated
- `source .env && export AWS_DEFAULT_REGION=us-east-1 && aws ec2 describe-security-groups --filters "Name=group-name,Values={{PROJECT_SLUG}}-dev" --query 'SecurityGroups[*].[GroupId,GroupName]' --output table` - Verify security group deleted
- `source .env && export AWS_DEFAULT_REGION=us-east-1 && aws ec2 describe-key-pairs --filters "Name=key-name,Values={{PROJECT_SLUG}}-dev" --query 'KeyPairs[*].[KeyName,KeyPairId]' --output table` - Verify key pair deleted

## Cleanup Notes
- Website will no longer be accessible after destruction
- Infrastructure can be redeployed using `/terraform_deploy` command
- AMI remains available for future deployments
- To completely remove AMI: Go to AWS Console > EC2 > AMIs and manually deregister

## Rollback Plan
If destruction needs to be reversed:
- Use existing AMI to redeploy: `cd terraform && TF_VAR_ssh_public_key="$(cat ~/.ssh/id_rsa_aws.pub)" TF_AUTO_APPROVE=true ./scripts/deploy.sh`
- All configuration will be restored from AMI
```

## Report

- IMPORTANT: Return exclusively the path to the plan file created and nothing else

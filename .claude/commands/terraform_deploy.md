# Terraform Deploy

Deploy {{PROJECT_NAME}} infrastructure to AWS using the most recent Packer-built AMI. This command **does not build** a new AMI - it only deploys infrastructure using an existing AMI.

## Prerequisites

- A Packer-built AMI must already exist
- AWS credentials configured in `.env` file
- SSH public key available at `~/.ssh/id_rsa_aws.pub`

## Instructions

Deploy the infrastructure using the existing AMI. The deploy script will:
1. Automatically discover the most recent AMI with version tag
2. Initialize Terraform
3. Validate configuration
4. Plan infrastructure changes
5. Deploy EC2 instance, security group, Elastic IP, and SSH key pair
6. Run post-deployment health checks

## Run

Execute the deployment:

```bash
cd terraform
TF_VAR_ssh_public_key="$(cat ~/.ssh/id_rsa_aws.pub)" TF_AUTO_APPROVE=true ./scripts/deploy.sh
```

The deployment will:
- Create EC2 instance (t2.micro) using the latest AMI
- Assign Elastic IP for stable public address
- Configure security group (HTTP port 80, SSH port 22)
- Set up SSH key pair for instance access
- Verify website accessibility

## Report

After deployment completes, report:
- ✅ Infrastructure deployed successfully
- 🌐 Website URL: `http://<public-ip>`
- 📍 Public IP: `<public-ip>`
- 🔑 SSH Command: `ssh -i ~/.ssh/id_rsa_aws ubuntu@<public-ip>`
- 🖼️ AMI Used: `<ami-id>`
- 💻 Instance ID: `<instance-id>`
- ✓ Website accessibility status (HTTP 200 expected)

Include the outputs from:
```bash
cd terraform && terraform output -json
```

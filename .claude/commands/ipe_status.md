# Check Infrastructure Deployment Status

Check if the infrastructure is currently deployed on AWS EC2. Follow the `Instructions` to query Terraform state and AWS resources, then report the deployment status using the `Report Format`.

## Variables

environment: $ARGUMENT (optional - defaults to "default", can be "dev", "staging", "prod")
terraform_dir: $ARGUMENT (optional - defaults to "io/terraform/")

## Instructions

- IMPORTANT: This is a **read-only** command - do not make any infrastructure changes
- Check if infrastructure is currently deployed by querying:
  1. Terraform state (does terraform.tfstate exist and contain resources?)
  2. AWS EC2 instances (are instances running/stopped/terminated?)
  3. Resource accessibility (is the website URL accessible?)
- Use the AWS CLI to query resource status without making changes
- Use Terraform CLI read-only commands (output, show, state list)
- Report the current status using the `Report Format` below
- If infrastructure is NOT deployed, provide instructions for deploying
- If infrastructure IS deployed, provide details about resources
- Handle errors gracefully (e.g., no Terraform state, AWS credentials not configured)

## Run

### Step 1: Check Terraform State

1. Change to Terraform directory: `cd <terraform_dir>`
2. Check if Terraform has been initialized:
   - Look for `.io/terraform/` directory
   - If not found, infrastructure is not initialized
3. Check if Terraform state exists:
   - Run `terraform state list` to see deployed resources
   - If empty or errors, infrastructure is not deployed
4. If state exists, extract key outputs:
   - Run `terraform output -json` to get all outputs
   - Extract: `website_url`, `public_ip`, `instance_id`, `ssh_command`

### Step 2: Query AWS Resources

1. Verify AWS credentials are configured:
   - Check if `AWS_ACCESS_KEY_ID` is set
   - If not, try to use default AWS CLI credentials
2. Query EC2 instance status (if instance_id from Terraform state):
   - Run `aws ec2 describe-instances --instance-ids <instance-id> --query 'Reservations[0].Instances[0].[State.Name,InstanceType,PublicIpAddress,LaunchTime]' --output table`
   - Extract instance state: running, stopped, stopping, terminated
3. Query security group (if configured):
   - Run `aws ec2 describe-security-groups --filters "Name=group-name,Values={{PROJECT_SLUG}}-*" --query 'SecurityGroups[0].[GroupId,GroupName]' --output table`

### Step 3: Check Resource Accessibility

If infrastructure is deployed (instance_id exists and state is "running"):

1. Check website accessibility:
   - Run `curl -I -s -o /dev/null -w "%{http_code}" <website_url>` to get HTTP status
   - If 200, website is accessible
   - If timeout/error, website is not accessible
2. Check SSH accessibility:
   - Run `nc -z -w5 <public_ip> 22` to check if SSH port is open
   - If successful, SSH is accessible

### Step 4: Compile Status Report

Use the `Report Format` below to compile a comprehensive status report.

## Report Format

### Infrastructure Status Report

**Deployment Status:** <DEPLOYED | NOT DEPLOYED | PARTIALLY DEPLOYED | UNKNOWN>

**Terraform State:**
- State File Exists: <YES | NO>
- Resources Deployed: <count> resources
- Last Modified: <timestamp if available>

**EC2 Instance:**
- Instance ID: <instance-id or "N/A">
- Instance State: <running | stopped | terminated | N/A>
- Instance Type: <t2.micro or instance type>
- Public IP: <public-ip or "N/A">
- Launch Time: <timestamp or "N/A">

**Accessibility:**
- Website URL: <url or "N/A">
- Website Status: <HTTP 200 OK | NOT ACCESSIBLE | N/A>
- SSH Port (22): <OPEN | CLOSED | N/A>

**Security:**
- Security Group: <group-id and name or "N/A">
- HTTP (80): <ALLOWED | BLOCKED | N/A>
- SSH (22): <ALLOWED | BLOCKED | N/A>

**Next Steps:**
<Provide actionable next steps based on status>

---

### Example Reports

**Example 1: Infrastructure Deployed and Healthy**

```
Infrastructure Status Report

Deployment Status: DEPLOYED

Terraform State:
- State File Exists: YES
- Resources Deployed: 4 resources
- Last Modified: 2024-01-15 14:30:00

EC2 Instance:
- Instance ID: i-0abc123def456
- Instance State: running
- Instance Type: t2.micro
- Public IP: 54.123.45.67
- Launch Time: 2024-01-15 14:25:00

Accessibility:
- Website URL: http://54.123.45.67
- Website Status: HTTP 200 OK
- SSH Port (22): OPEN

Security:
- Security Group: sg-0123456 ({{PROJECT_SLUG}}-sg)
- HTTP (80): ALLOWED (0.0.0.0/0)
- SSH (22): ALLOWED (0.0.0.0/0)

Next Steps:
✅ Infrastructure is healthy and accessible
✅ Website is serving traffic
✅ SSH access is available
- Consider restricting SSH to specific IP ranges for production
```

**Example 2: Infrastructure Not Deployed**

```
Infrastructure Status Report

Deployment Status: NOT DEPLOYED

Terraform State:
- State File Exists: NO
- Resources Deployed: 0 resources
- Last Modified: N/A

EC2 Instance:
- Instance ID: N/A
- Instance State: N/A
- Instance Type: N/A
- Public IP: N/A
- Launch Time: N/A

Accessibility:
- Website URL: N/A
- Website Status: N/A
- SSH Port (22): N/A

Security:
- Security Group: N/A
- HTTP (80): N/A
- SSH (22): N/A

Next Steps:
❌ Infrastructure is not deployed

To deploy infrastructure:
1. Build AMI: `cd terraform && ./scripts/build-ami.sh`
2. Deploy infrastructure: `./scripts/deploy.sh`
3. Verify deployment: Run /ipe_status again

Or use manual deployment:
1. `cd io/terraform/packer && packer build app.pkr.hcl`
2. `cd terraform && terraform init && terraform apply`
```

**Example 3: Instance Stopped**

```
Infrastructure Status Report

Deployment Status: PARTIALLY DEPLOYED

Terraform State:
- State File Exists: YES
- Resources Deployed: 4 resources
- Last Modified: 2024-01-15 14:30:00

EC2 Instance:
- Instance ID: i-0abc123def456
- Instance State: stopped
- Instance Type: t2.micro
- Public IP: 54.123.45.67 (may change on restart)
- Launch Time: 2024-01-15 14:25:00

Accessibility:
- Website URL: http://54.123.45.67
- Website Status: NOT ACCESSIBLE
- SSH Port (22): CLOSED

Security:
- Security Group: sg-0123456 ({{PROJECT_SLUG}}-sg)
- HTTP (80): ALLOWED (0.0.0.0/0)
- SSH (22): ALLOWED (0.0.0.0/0)

Next Steps:
⚠️  Instance is stopped

To start the instance:
1. `aws ec2 start-instances --instance-ids i-0abc123def456`
2. Wait for instance to boot (~2 minutes)
3. Run /ipe_status to verify

Note: Public IP may change after restart if Elastic IP is not configured
```

**Example 4: AWS Credentials Not Configured**

```
Infrastructure Status Report

Deployment Status: UNKNOWN

Error: AWS credentials not found

To configure AWS credentials:
1. Add to .env file:
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret

2. Or use AWS CLI:
   aws configure

Then run /ipe_status again
```

**Example 5: Terraform Not Initialized**

```
Infrastructure Status Report

Deployment Status: NOT DEPLOYED

Terraform State:
- State File Exists: NO
- Terraform Initialized: NO

To initialize Terraform:
1. `cd terraform`
2. `terraform init`
3. Run /ipe_status again

Or use deployment script:
- `cd terraform && ./scripts/deploy.sh`
```

**Example 6: Inconsistent State (Orphaned Resources)**

```
Infrastructure Status Report

Deployment Status: INCONSISTENT

Warning: Terraform state references resources that don't exist in AWS

Terraform State:
- State File Exists: YES
- Resources Deployed: 4 resources

EC2 Instance:
- Instance ID: i-0abc123def456
- Instance State: NOT FOUND IN AWS

Possible Causes:
1. Resources were manually deleted in AWS Console
2. Resources were terminated outside of Terraform
3. Wrong AWS region or credentials

Next Steps:
1. Verify AWS region matches Terraform configuration (us-east-1)
2. Verify AWS credentials are correct
3. If resources were manually deleted, run:
   `cd terraform && terraform destroy` to clean up state
   Then redeploy: `./scripts/deploy.sh`
```

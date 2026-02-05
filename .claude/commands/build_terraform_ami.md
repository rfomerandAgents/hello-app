# Build Terraform AMI Planning

Create a plan to build a new {{PROJECT_NAME}} AMI using Packer with the exact specified markdown `Plan Format`.

## Instructions

- IMPORTANT: You're writing a plan to build an AMI, not actually building it
- The plan will be implemented later using the `/implement` command
- Create the plan in the `specs/` directory with filename: `ami-build-{timestamp}.md`
  - Replace `{timestamp}` with current timestamp (e.g., "20251108-143022")
- Use the `Plan Format` below to create the plan
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value
- Research the current application state and build configuration
- Be thorough about what will be included in the AMI

## Relevant Files

Focus on the following files:
- `io/terraform/README.md` - Infrastructure documentation
- `io/terraform/io/packer/app.pkr.hcl` - Packer template configuration
- `io/terraform/io/packer/scripts/install-nodejs.sh` - Node.js installation script
- `io/terraform/io/packer/scripts/install-nginx.sh` - nginx installation script
- `io/terraform/io/packer/scripts/deploy-app.sh` - Application deployment script
- `io/terraform/scripts/build-ami.sh` - AMI build orchestration script
- `app/` - Next.js application source code
- `.env` - AWS credentials configuration

## Plan Format

```md
# AMI Build Plan

## Overview
Build a new Amazon Machine Image (AMI) containing the {{PROJECT_NAME}} Next.js application with all dependencies.

## Purpose
Create a reusable AMI that can be deployed to EC2 instances with the pre-built application, reducing deployment time and ensuring consistency.

## AMI Contents
The AMI will include:
- Ubuntu 22.04 LTS base image
- Node.js 18.x runtime
- nginx web server (configured)
- {{PROJECT_NAME}} Next.js application (built and deployed)
- All application dependencies

## Current Application State
<analyze app/ directory and describe current state>

### Application Components
- Next.js version: <version from package.json>
- React components: <list main components>
- Key features: <list key features>
- Build output: Static export to `out/` directory

## Build Configuration

### Packer Template
- Template file: `io/terraform/io/packer/app.pkr.hcl`
- Base AMI: <source_ami from template>
- Instance type: <instance_type from template>
- Region: us-east-1

### Provisioning Scripts
1. **install-nodejs.sh** - Installs Node.js 18.x from NodeSource repository
2. **install-nginx.sh** - Installs and configures nginx to serve static files
3. **deploy-app.sh** - Builds Next.js app and deploys to nginx root

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Pre-Build Verification
- Verify application builds locally: `cd app && npm run build`
- Confirm no TypeScript errors: `cd app && npm run lint`
- Check AWS credentials configured in `.env` file
- Verify Packer is installed: `packer version`

### 2. Review Build Configuration
- Read `io/terraform/io/packer/app.pkr.hcl` to understand Packer template
- Review provisioning scripts in `io/terraform/io/packer/scripts/`
- Confirm all paths and configurations are correct

### 3. Execute AMI Build
- Navigate to terraform directory: `cd terraform`
- Run build script: `./scripts/build-ami.sh`
- Monitor build progress (takes 5-10 minutes)
- Build creates temporary EC2 instance, provisions it, and creates AMI snapshot

### 4. Verify AMI Build
- Check build logs in `io/terraform/logs/packer-build-*.log`
- Verify AMI created successfully with expected ID
- Run validation commands to confirm AMI is available

## Build Process Details

### What Happens During Build
1. Packer launches temporary t2.micro EC2 instance
2. Connects via SSH once instance is ready
3. Runs system updates (`apt-get update && apt-get upgrade`)
4. Executes provisioning scripts in order:
   - Installs Node.js 18.x
   - Installs and configures nginx
   - Copies application code
   - Runs `npm install` and `npm run build`
   - Deploys build output to `/var/www/html`
   - Configures nginx to serve the application
5. Stops the instance
6. Creates AMI snapshot
7. Terminates temporary instance
8. Tags AMI with version and metadata

### Build Artifacts
- New AMI with ID: `ami-XXXXXXXXXXXXX`
- AMI Name: `{{PROJECT_SLUG}}-v1-{timestamp}`
- Build logs: `io/terraform/logs/packer-build-{timestamp}.log`

## Validation Commands
Execute every command to validate AMI build succeeded.

- Check Packer build logs: `ls -lt io/terraform/logs/packer-build-*.log | head -1 | xargs tail -50`
- Verify AMI exists: `source .env && export AWS_DEFAULT_REGION=us-east-1 && aws ec2 describe-images --owners self --filters "Name=name,Values={{PROJECT_SLUG}}-v1-*" --query 'Images[*].[ImageId,Name,State,CreationDate]' --output table`
- Confirm AMI is available: `source .env && export AWS_DEFAULT_REGION=us-east-1 && aws ec2 describe-images --image-ids <ami-id> --query 'Images[0].State' --output text` (should return "available")

## Expected Duration
- Total build time: 5-10 minutes
- Breakdown:
  - Instance launch: 1-2 minutes
  - System updates: 1-2 minutes
  - Node.js installation: 1-2 minutes
  - nginx installation: 30 seconds
  - App build and deployment: 1-2 minutes
  - AMI creation: 2-3 minutes

## Next Steps After Build
Once AMI is built successfully:
1. Note the AMI ID from build output
2. AMI will be automatically discovered by Terraform (uses most recent)
3. Deploy infrastructure using: `/terraform_deploy`
4. Or create deployment plan using: `/terraform_deploy` command

## Troubleshooting
If build fails:
- Check build logs: `io/terraform/logs/packer-build-*.log`
- Verify AWS credentials are valid
- Confirm source AMI is available in us-east-1
- Check that no other Packer builds are running
- Review Packer template syntax: `cd io/terraform/packer && packer validate app.pkr.hcl`

## Cost
- Temporary EC2 instance (t2.micro): ~$0.01 per build
- AMI storage: ~$0.05/GB per month (typically <2GB)
- Total build cost: <$0.02 per AMI

## Notes
- AMI is region-specific (us-east-1)
- Old AMIs are not automatically deleted
- Can have multiple AMIs with different versions
- Terraform automatically uses most recent AMI by default
- Manual AMI cleanup recommended periodically via AWS Console
```

## Report

- IMPORTANT: Return exclusively the path to the plan file created and nothing else

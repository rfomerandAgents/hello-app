# GitHub Actions for Infrastructure Automation

Comprehensive guide for GitHub Actions workflows in infrastructure automation contexts.

## OIDC Authentication with AWS

Replace long-lived credentials with OpenID Connect for secure, temporary credentials.

**Setup IAM Identity Provider:**
```bash
# Create OIDC provider
aws iam create-open-id-connect-provider \
  --url "https://token.actions.githubusercontent.com" \
  --client-id-list "sts.amazonaws.com" \
  --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1"
```

**IAM Role Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:ORG/REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

**Workflow Usage:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole
          role-session-name: GitHubActions
          aws-region: us-east-1
```

## Reusable Workflows

Create reusable workflows for common infrastructure patterns.

**Reusable Workflow (.github/workflows/terraform-plan.yml):**
```yaml
name: Terraform Plan (Reusable)

on:
  workflow_call:
    inputs:
      working-directory:
        required: true
        type: string
      environment:
        required: true
        type: string
      terraform-version:
        required: false
        type: string
        default: "1.9.0"
    secrets:
      aws-role-arn:
        required: true
      tf-api-token:
        required: true
    outputs:
      plan-exitcode:
        description: "Terraform plan exit code"
        value: ${{ jobs.plan.outputs.exitcode }}

jobs:
  plan:
    runs-on: ubuntu-latest
    outputs:
      exitcode: ${{ steps.plan.outputs.exitcode }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.aws-role-arn }}
          aws-region: us-east-1
          
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ inputs.terraform-version }}
          cli_config_credentials_token: ${{ secrets.tf-api-token }}
          
      - name: Terraform Init
        run: terraform init
        
      - name: Terraform Validate
        run: terraform validate
        
      - name: Terraform Plan
        id: plan
        run: terraform plan -out=tfplan -detailed-exitcode
        continue-on-error: true
        
      - name: Upload Plan
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-${{ inputs.environment }}
          path: ${{ inputs.working-directory }}/tfplan
```

**Calling Workflow:**
```yaml
name: Infrastructure CI

on:
  pull_request:
    paths:
      - 'io/terraform/**'

jobs:
  plan-staging:
    uses: ./.github/workflows/terraform-plan.yml
    with:
      working-directory: io/terraform/staging
      environment: staging
    secrets:
      aws-role-arn: ${{ secrets.AWS_STAGING_ROLE }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}
      
  plan-production:
    uses: ./.github/workflows/terraform-plan.yml
    with:
      working-directory: io/terraform/production
      environment: production
    secrets:
      aws-role-arn: ${{ secrets.AWS_PROD_ROLE }}
      tf-api-token: ${{ secrets.TF_API_TOKEN }}
```

## Composite Actions

Package reusable steps into composite actions.

**Composite Action (.github/actions/setup-infra-tools/action.yml):**
```yaml
name: 'Setup Infrastructure Tools'
description: 'Setup Terraform, Packer, and AWS CLI'

inputs:
  terraform-version:
    description: 'Terraform version to install'
    required: false
    default: '1.9.0'
  packer-version:
    description: 'Packer version to install'
    required: false
    default: '1.11.0'

runs:
  using: "composite"
  steps:
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: ${{ inputs.terraform-version }}
        
    - name: Setup Packer
      uses: hashicorp/setup-packer@v3
      with:
        packer_version: ${{ inputs.packer-version }}
        
    - name: Configure AWS CLI
      shell: bash
      run: |
        aws --version
        aws configure set default.region us-east-1
```

## Matrix Strategies for Multi-Environment

Deploy to multiple environments or regions with matrix builds.

```yaml
name: Multi-Environment Deployment

on:
  workflow_dispatch:
    inputs:
      environments:
        description: 'Comma-separated environments to deploy'
        required: true
        default: 'dev,staging'

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: ${{ fromJSON(format('["{0}"]', join(split(github.event.inputs.environments, ','), '","'))) }}
        region: [us-east-1, us-west-2]
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to ${{ matrix.environment }} in ${{ matrix.region }}
        run: |
          echo "Deploying to ${{ matrix.environment }} in ${{ matrix.region }}"
          terraform workspace select ${{ matrix.environment }}-${{ matrix.region }}
          terraform apply -auto-approve
```

## Caching Strategies

Reduce workflow runtime with effective caching.

```yaml
jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Cache Terraform plugins
      - name: Cache Terraform
        uses: actions/cache@v4
        with:
          path: |
            ~/.terraform.d/plugin-cache
          key: ${{ runner.os }}-terraform-${{ hashFiles('**/.terraform.lock.hcl') }}
          restore-keys: |
            ${{ runner.os }}-terraform-
            
      # Cache Packer plugins
      - name: Cache Packer
        uses: actions/cache@v4
        with:
          path: |
            ~/.config/io/packer/plugins
          key: ${{ runner.os }}-packer-${{ hashFiles('**/*.pkr.hcl') }}
          
      # Cache Go dependencies for custom tools
      - name: Cache Go Modules
        uses: actions/cache@v4
        with:
          path: ~/go/pkg/mod
          key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
```

## Environment Protection Rules

Implement approval gates for production deployments.

```yaml
name: Production Deployment

on:
  push:
    branches: [main]

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://prod.example.com
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: |
          terraform workspace select production
          terraform apply -auto-approve
```

**Repository Settings:**
- Navigate to Settings → Environments → production
- Add required reviewers
- Set deployment branch restrictions to `main` only
- Configure wait timer if needed

## Terraform Cloud Integration

Trigger Terraform Cloud runs from GitHub Actions.

```yaml
jobs:
  trigger-terraform-cloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Create Terraform Cloud Run
        env:
          TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
        run: |
          cat > payload.json <<EOF
          {
            "data": {
              "attributes": {
                "is-destroy": false,
                "message": "Triggered by GitHub Actions"
              },
              "type": "runs",
              "relationships": {
                "workspace": {
                  "data": {
                    "type": "workspaces",
                    "id": "${{ secrets.TF_WORKSPACE_ID }}"
                  }
                }
              }
            }
          }
          EOF
          
          curl \
            --header "Authorization: Bearer $TF_API_TOKEN" \
            --header "Content-Type: application/vnd.api+json" \
            --request POST \
            --data @payload.json \
            https://app.terraform.io/api/v2/runs

      - name: Wait for Terraform Run
        run: |
          # Poll run status and wait for completion
          # Implementation depends on requirements
```

## Packer Build Automation

Automate AMI builds with Packer in GitHub Actions.

```yaml
name: Build Golden AMI

on:
  push:
    paths:
      - 'io/packer/**'
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      ami-id: ${{ steps.build.outputs.ami_id }}
      manifest: ${{ steps.build.outputs.manifest }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
          
      - name: Setup Packer
        uses: hashicorp/setup-packer@v3
        
      - name: Packer Init
        run: packer init io/packer/
        
      - name: Packer Validate
        run: packer validate io/packer/
        
      - name: Packer Build
        id: build
        run: |
          packer build -machine-readable io/packer/ | tee packer-output.txt
          
          # Extract AMI ID from manifest
          AMI_ID=$(jq -r '.builds[-1].artifact_id' manifest.json | cut -d':' -f2)
          echo "ami_id=$AMI_ID" >> $GITHUB_OUTPUT
          echo "manifest=$(cat manifest.json | jq -c)" >> $GITHUB_OUTPUT
          
      - name: Tag AMI
        run: |
          aws ec2 create-tags \
            --resources ${{ steps.build.outputs.ami_id }} \
            --tags \
              Key=GitHubSHA,Value=${{ github.sha }} \
              Key=GitHubRef,Value=${{ github.ref }} \
              Key=BuildDate,Value=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
              
      - name: Update SSM Parameter
        run: |
          aws ssm put-parameter \
            --name "/golden-ami/latest" \
            --value "${{ steps.build.outputs.ami_id }}" \
            --type String \
            --overwrite
            
  update-terraform:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Update Terraform Variables
        run: |
          # Update terraform.tfvars or trigger Terraform Cloud run
          # with new AMI ID
```

## Security Best Practices

### Secret Management

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Retrieve Secrets from AWS Secrets Manager
        uses: aws-actions/aws-secretsmanager-get-secrets@v2
        with:
          secret-ids: |
            prod/db/password
            prod/api/key
          parse-json-secrets: true
          
      - name: Use Retrieved Secrets
        env:
          DB_PASSWORD: ${{ env.PROD_DB_PASSWORD }}
          API_KEY: ${{ env.PROD_API_KEY }}
        run: |
          # Use secrets in deployment
```

### Branch Protection

Configure required status checks:
- Terraform validate must pass
- Terraform plan must complete
- Security scanning must pass
- Code review approval required

### Audit Logging

```yaml
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Log Deployment Event
        run: |
          aws cloudtrail lookup-events \
            --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
            --max-results 1
            
      - name: Send Notification
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deployment to production initiated",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Deployment by ${{ github.actor }} at ${{ github.event.head_commit.timestamp }}"
                  }
                }
              ]
            }
```

## Troubleshooting Common Issues

**Issue: OIDC authentication fails**
- Verify IAM role trust policy includes correct repository
- Check `id-token: write` permission is set
- Confirm OIDC provider thumbprint is current

**Issue: Terraform state locking errors**
- Check if another workflow is running
- Verify DynamoDB table for state locking exists
- Manually unlock state if necessary with `terraform force-unlock`

**Issue: Workflow timeout**
- Increase timeout with `timeout-minutes: 30`
- Optimize by caching dependencies
- Consider splitting into multiple jobs

**Issue: Concurrent workflow conflicts**
- Use concurrency control to limit parallel runs:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

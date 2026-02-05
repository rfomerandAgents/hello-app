# Terraform Module Testing Patterns

Comprehensive guide to testing Terraform modules at all levels.

## Testing Pyramid

```
        /\
       /  \
      / E2E\
     /______\
    /        \
   /Integration\
  /______________\
 /                \
/   Unit Tests     \
/__________________\
```

## Unit Testing

### Terraform Validate

```bash
# Basic validation
terraform init
terraform validate

# Validate all examples
for example in examples/*/; do
  cd "$example"
  terraform init -backend=false
  terraform validate
  cd -
done
```

### Format Checking

```bash
terraform fmt -check -recursive
```

### Static Analysis

```bash
# tfsec - Security scanning
tfsec .

# checkov - Policy as code
checkov -d .

# terraform-compliance - BDD testing
terraform-compliance -f compliance/ -p plan.json
```

### Variable Validation Testing

```hcl
# Test validation rules
variable "port" {
  type = number
  
  validation {
    condition     = var.port >= 1 && var.port <= 65535
    error_message = "Port must be between 1 and 65535."
  }
}

# Test with invalid value (should fail)
# terraform plan -var="port=70000"
```

## Integration Testing

### Terratest (Go)

```go
// tests/integration/vpc_test.go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    t.Parallel()
    
    awsRegion := "us-east-1"
    
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../../examples/complete",
        
        Vars: map[string]interface{}{
            "name":        "test-vpc",
            "environment": "test",
            "cidr_block":  "10.0.0.0/16",
        },
        
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    })
    
    // Clean up resources at test end
    defer terraform.Destroy(t, terraformOptions)
    
    // Deploy resources
    terraform.InitAndApply(t, terraformOptions)
    
    // Retrieve outputs
    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    publicSubnetIDs := terraform.OutputList(t, terraformOptions, "public_subnet_ids")
    privateSubnetIDs := terraform.OutputList(t, terraformOptions, "private_subnet_ids")
    
    // Assertions
    assert.NotEmpty(t, vpcID, "VPC ID should not be empty")
    assert.Len(t, publicSubnetIDs, 3, "Should create 3 public subnets")
    assert.Len(t, privateSubnetIDs, 3, "Should create 3 private subnets")
    
    // Verify VPC exists in AWS
    vpc := aws.GetVpcById(t, vpcID, awsRegion)
    assert.Equal(t, "10.0.0.0/16", vpc.CidrBlock)
    
    // Verify subnets are in different AZs
    azs := make(map[string]bool)
    for _, subnetID := range publicSubnetIDs {
        subnet := aws.GetSubnetById(t, subnetID, awsRegion)
        azs[subnet.AvailabilityZone] = true
    }
    assert.GreaterOrEqual(t, len(azs), 2, "Subnets should span multiple AZs")
    
    // Verify NAT Gateways are created
    natGatewayIDs := terraform.OutputList(t, terraformOptions, "nat_gateway_ids")
    assert.NotEmpty(t, natGatewayIDs, "NAT Gateways should be created")
}

func TestVPCModuleSingleNAT(t *testing.T) {
    t.Parallel()
    
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../../examples/single-nat",
        
        Vars: map[string]interface{}{
            "name":               "test-vpc",
            "environment":        "test",
            "single_nat_gateway": true,
        },
    })
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Verify only one NAT Gateway created
    natGatewayIDs := terraform.OutputList(t, terraformOptions, "nat_gateway_ids")
    assert.Len(t, natGatewayIDs, 1, "Should create only 1 NAT Gateway")
}

func TestVPCModuleWithoutNAT(t *testing.T) {
    t.Parallel()
    
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../../examples/no-nat",
        
        Vars: map[string]interface{}{
            "enable_nat_gateway": false,
        },
    })
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Verify no NAT Gateways created
    natGatewayIDs := terraform.OutputList(t, terraformOptions, "nat_gateway_ids")
    assert.Empty(t, natGatewayIDs, "Should not create NAT Gateways")
}
```

### Running Terratest

```bash
# Install dependencies
cd tests/integration
go mod init vpc-tests
go mod tidy

# Run all tests
go test -v -timeout 60m

# Run specific test
go test -v -run TestVPCModule -timeout 30m

# Run tests in parallel
go test -v -parallel 3
```

### Kitchen-Terraform (Ruby)

```ruby
# .kitchen.yml
driver:
  name: terraform

provisioner:
  name: terraform

verifier:
  name: terraform
  systems:
    - name: default
      backend: aws

platforms:
  - name: terraform

suites:
  - name: default
    driver:
      root_module_directory: test/fixtures/default
    verifier:
      systems:
        - name: aws
          backend: aws
          controls:
            - vpc_exists
            - subnets_created
```

```ruby
# test/integration/default/controls/vpc_spec.rb
control 'vpc_exists' do
  impact 1.0
  title 'Verify VPC exists'
  desc 'VPC should be created with correct configuration'
  
  describe aws_vpc(vpc_id: attribute('vpc_id')) do
    it { should exist }
    its('cidr_block') { should eq '10.0.0.0/16' }
    its('state') { should eq 'available' }
  end
end

control 'subnets_created' do
  impact 1.0
  title 'Verify subnets'
  desc 'Public and private subnets should be created'
  
  attribute('public_subnet_ids').each do |subnet_id|
    describe aws_subnet(subnet_id: subnet_id) do
      it { should exist }
      it { should be_mapping_public_ip_on_launch }
    end
  end
  
  attribute('private_subnet_ids').each do |subnet_id|
    describe aws_subnet(subnet_id: subnet_id) do
      it { should exist }
      it { should_not be_mapping_public_ip_on_launch }
    end
  end
end
```

## Mock Testing

### Using terraform-exec (Go)

```go
// For testing without real infrastructure
func TestVPCConfiguration(t *testing.T) {
    tf := setupTerraform(t, "../../examples/basic")
    
    // Generate plan
    plan, err := tf.Plan(context.Background())
    require.NoError(t, err)
    
    // Parse plan
    var planOutput map[string]interface{}
    json.Unmarshal([]byte(plan.JSONOutput), &planOutput)
    
    // Verify resources to be created
    resourceChanges := planOutput["resource_changes"].([]interface{})
    
    vpcFound := false
    for _, change := range resourceChanges {
        resource := change.(map[string]interface{})
        if resource["type"] == "aws_vpc" {
            vpcFound = true
            break
        }
    }
    
    assert.True(t, vpcFound, "VPC resource should be in plan")
}
```

## Contract Testing

### Testing Module Contracts

```hcl
# tests/contract/main.tf
module "vpc_under_test" {
  source = "../../"
  
  name        = "test"
  environment = "test"
  cidr_block  = "10.0.0.0/16"
  
  availability_zones = ["us-east-1a", "us-east-1b"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
}

# Verify outputs exist and have correct types
output "vpc_id_type_check" {
  value = can(regex("^vpc-", module.vpc_under_test.vpc_id))
}

output "subnet_count_check" {
  value = length(module.vpc_under_test.public_subnet_ids) == 2
}
```

## Policy Testing

### Open Policy Agent (OPA)

```rego
# tests/policy/vpc_policy.rego
package terraform.analysis

default allow = false

# Deny VPCs with public database subnets
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_subnet"
    resource.change.after.tags.Type == "database"
    resource.change.after.map_public_ip_on_launch == true
    
    msg := "Database subnets must not be public"
}

# Require encryption for VPC flow logs
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_flow_log"
    not resource.change.after.log_destination_type == "cloud-watch-logs"
    
    msg := "VPC flow logs must use CloudWatch Logs"
}
```

```bash
# Test policy
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
opa eval -d vpc_policy.rego -i plan.json "data.terraform.analysis.deny"
```

### Sentinel (Terraform Cloud)

```hcl
# sentinel.hcl
policy "vpc-flow-logs-required" {
  enforcement_level = "hard-mandatory"
}

policy "nat-gateway-required" {
  enforcement_level = "soft-mandatory"
}
```

```python
# policies/vpc-flow-logs-required.sentinel
import "tfplan/v2" as tfplan

# Find all VPCs
vpcs = filter tfplan.resource_changes as _, rc {
    rc.type is "aws_vpc" and
    rc.mode is "managed"
}

# Find all flow logs
flow_logs = filter tfplan.resource_changes as _, rc {
    rc.type is "aws_flow_log" and
    rc.mode is "managed"
}

# Ensure each VPC has flow logs
main = rule {
    length(vpcs) == length(flow_logs)
}
```

## Continuous Testing

### GitHub Actions Workflow

```yaml
name: Test Terraform Module

on:
  pull_request:
    paths:
      - '**.tf'
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.7.0"
      
      - name: Terraform Format
        run: terraform fmt -check -recursive
      
      - name: Terraform Init
        run: terraform init -backend=false
      
      - name: Terraform Validate
        run: terraform validate
  
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.0
      
      - name: Run Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: .
          framework: terraform
  
  integration:
    runs-on: ubuntu-latest
    needs: [validate]
    if: github.event_name == 'push'
    
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Run Integration Tests
        working-directory: tests/integration
        run: |
          go mod download
          go test -v -timeout 60m
```

## Testing Best Practices

### 1. Test Matrix

Test multiple scenarios:

```go
func TestVPCModule(t *testing.T) {
    testCases := []struct {
        name              string
        cidrBlock         string
        enableNAT         bool
        singleNAT         bool
        expectedSubnets   int
        expectedNATGWs    int
    }{
        {
            name:            "default-configuration",
            cidrBlock:       "10.0.0.0/16",
            enableNAT:       true,
            singleNAT:       false,
            expectedSubnets: 6,
            expectedNATGWs:  3,
        },
        {
            name:            "single-nat-gateway",
            cidrBlock:       "10.1.0.0/16",
            enableNAT:       true,
            singleNAT:       true,
            expectedSubnets: 6,
            expectedNATGWs:  1,
        },
        {
            name:            "no-nat-gateway",
            cidrBlock:       "10.2.0.0/16",
            enableNAT:       false,
            singleNAT:       false,
            expectedSubnets: 6,
            expectedNATGWs:  0,
        },
    }
    
    for _, tc := range testCases {
        tc := tc // capture range variable
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel()
            // Run test with specific configuration
        })
    }
}
```

### 2. Use Retries

```go
terraform.InitAndApplyAndIdempotent(t, terraformOptions)
```

### 3. Tag Resources for Cleanup

```hcl
tags = merge(
  var.tags,
  {
    TestID    = "terratest-${random_id.test.hex}"
    AutoClean = "true"
  }
)
```

### 4. Parallel Testing

```go
func TestMultipleRegions(t *testing.T) {
    t.Parallel()
    
    regions := []string{"us-east-1", "us-west-2", "eu-west-1"}
    
    for _, region := range regions {
        region := region
        t.Run(region, func(t *testing.T) {
            t.Parallel()
            // Test in each region
        })
    }
}
```

### 5. Cost Optimization

```go
// Use smallest instances for testing
Vars: map[string]interface{}{
    "instance_type": "t3.micro",
    "min_size":      1,
    "max_size":      1,
}

// Clean up immediately
defer terraform.Destroy(t, terraformOptions)

// Use spot instances when possible
```

### 6. Test Timeouts

```go
terraformOptions := &terraform.Options{
    TerraformDir: ".",
    MaxRetries:   3,
    TimeBetweenRetries: 5 * time.Second,
    RetryableTerraformErrors: map[string]string{
        "RequestError": "Temporary AWS issue",
    },
}
```

## Testing Checklist

Before releasing a module version:

- [ ] All examples validate successfully
- [ ] Format check passes
- [ ] Static analysis (tfsec, checkov) passes
- [ ] Unit tests pass
- [ ] Integration tests pass in isolated environment
- [ ] Policy tests pass
- [ ] Documentation is up to date
- [ ] CHANGELOG is updated
- [ ] Version is tagged

## Testing Tools Comparison

| Tool | Type | Language | Best For |
|------|------|----------|----------|
| Terratest | Integration | Go | Full infrastructure testing |
| Kitchen-Terraform | Integration | Ruby | Chef/InSpec users |
| terraform-compliance | BDD | Python | Policy compliance |
| OPA | Policy | Rego | Complex policy rules |
| tfsec | Static | Go | Security scanning |
| checkov | Static | Python | Policy as code |
| Sentinel | Policy | HCL | Terraform Cloud users |

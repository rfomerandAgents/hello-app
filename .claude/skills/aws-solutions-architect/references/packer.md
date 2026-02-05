# HashiCorp Packer for AWS AMI Building

Comprehensive guide for building golden AMIs with Packer for immutable infrastructure.

## Packer Template Structure

### HCL2 Configuration

**template.pkr.hcl:**
```hcl
packer {
  required_plugins {
    amazon = {
      version = ">= 1.3.0"
      source  = "github.com/hashicorp/amazon"
    }
    ansible = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

# Variables for configuration
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.medium"
}

variable "ami_prefix" {
  type    = string
  default = "golden-ami"
}

variable "environment" {
  type    = string
  default = "production"
}

# Data sources for dynamic AMI selection
data "amazon-ami" "ubuntu" {
  filters = {
    name                = "ubuntu/images/*ubuntu-jammy-22.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["099720109477"] # Canonical
  region      = var.aws_region
}

# Build sources
source "amazon-ebs" "app_server" {
  ami_name      = "${var.ami_prefix}-${var.environment}-{{timestamp}}"
  instance_type = var.instance_type
  region        = var.aws_region
  source_ami    = data.amazon-ami.ubuntu.id
  ssh_username  = "ubuntu"
  
  # Launch configuration
  vpc_id    = "vpc-xxxxx"
  subnet_id = "subnet-xxxxx"
  
  # Security and access
  associate_public_ip_address = true
  iam_instance_profile        = "PackerBuilder"
  
  # AMI configuration
  ami_description = "Golden AMI for ${var.environment} application servers"
  ami_regions     = ["us-east-1", "us-west-2"]
  
  # Encryption
  encrypt_boot = true
  kms_key_id  = "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
  
  # Tags
  tags = {
    Name        = "${var.ami_prefix}-${var.environment}"
    Environment = var.environment
    BuildDate   = "{{timestamp}}"
    BuildSource = "packer"
    OS          = "Ubuntu 22.04"
  }
  
  # Snapshot tags
  snapshot_tags = {
    Name        = "${var.ami_prefix}-${var.environment}-snapshot"
    Environment = var.environment
  }
  
  # Timeout and retry
  aws_polling {
    delay_seconds = 15
    max_attempts  = 60
  }
}

# Build configuration
build {
  name    = "app-server"
  sources = ["source.amazon-ebs.app_server"]
  
  # Wait for cloud-init
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "cloud-init status --wait"
    ]
  }
  
  # System updates
  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
      "sudo apt-get install -y curl wget unzip jq"
    ]
  }
  
  # Install application dependencies
  provisioner "shell" {
    script = "scripts/install-dependencies.sh"
  }
  
  # Configuration with Ansible
  provisioner "ansible" {
    playbook_file = "ansible/playbook.yml"
    user          = "ubuntu"
    extra_arguments = [
      "--extra-vars",
      "environment=${var.environment}"
    ]
  }
  
  # Security hardening
  provisioner "shell" {
    scripts = [
      "scripts/security-hardening.sh",
      "scripts/cis-benchmark.sh"
    ]
  }
  
  # Cleanup
  provisioner "shell" {
    inline = [
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*",
      "history -c"
    ]
  }
  
  # Post-processors
  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
  }
  
  post-processor "shell-local" {
    inline = [
      "echo AMI created: $(jq -r '.builds[-1].artifact_id' manifest.json | cut -d':' -f2)"
    ]
  }
}
```

## Provisioners

### Shell Provisioner

Basic package installation and configuration:

```hcl
provisioner "shell" {
  inline = [
    "sudo apt-get update",
    "sudo apt-get install -y nginx",
    "sudo systemctl enable nginx"
  ]
}
```

With external script:
```hcl
provisioner "shell" {
  script = "scripts/setup.sh"
  environment_vars = [
    "APP_VERSION=1.2.3",
    "ENV=${var.environment}"
  ]
}
```

Elevated privileges:
```hcl
provisioner "shell" {
  execute_command = "echo 'packer' | sudo -S sh -c '{{ .Vars }} {{ .Path }}'"
  script          = "scripts/root-operations.sh"
}
```

### File Provisioner

Copy files and directories:

```hcl
provisioner "file" {
  source      = "config/app.conf"
  destination = "/tmp/app.conf"
}

provisioner "shell" {
  inline = ["sudo mv /tmp/app.conf /etc/app/app.conf"]
}
```

### Ansible Provisioner

Complex configuration management:

```hcl
provisioner "ansible" {
  playbook_file = "ansible/playbook.yml"
  user          = "ubuntu"
  
  extra_arguments = [
    "--extra-vars",
    "environment=${var.environment} app_version=${var.app_version}",
    "--tags",
    "install,configure"
  ]
  
  ansible_env_vars = [
    "ANSIBLE_HOST_KEY_CHECKING=False",
    "ANSIBLE_STDOUT_CALLBACK=yaml"
  ]
}
```

**ansible/playbook.yml:**
```yaml
---
- name: Configure application server
  hosts: all
  become: yes
  
  vars:
    app_user: appuser
    app_dir: /opt/app
  
  tasks:
    - name: Create application user
      user:
        name: "{{ app_user }}"
        shell: /bin/bash
        create_home: yes
    
    - name: Install application
      apt:
        name:
          - python3
          - python3-pip
          - nginx
        state: present
        update_cache: yes
    
    - name: Configure nginx
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-available/app
      notify: restart nginx
  
  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

### Chef Provisioner

```hcl
provisioner "chef-solo" {
  cookbook_paths   = ["cookbooks"]
  run_list         = ["recipe[base]", "recipe[app]"]
  prevent_sudo     = false
  skip_install     = false
  version          = "18.4.12"
}
```

## Multi-Region AMI Distribution

Build once, copy to multiple regions:

```hcl
source "amazon-ebs" "multi_region" {
  ami_name      = "app-ami-{{timestamp}}"
  instance_type = "t3.medium"
  region        = "us-east-1"
  source_ami    = data.amazon-ami.ubuntu.id
  ssh_username  = "ubuntu"
  
  # Distribute to multiple regions
  ami_regions = [
    "us-east-1",
    "us-west-2",
    "eu-west-1",
    "ap-southeast-1"
  ]
  
  # Different encryption keys per region
  region_kms_key_ids = {
    "us-east-1"      = "arn:aws:kms:us-east-1:ACCOUNT:key/KEY1"
    "us-west-2"      = "arn:aws:kms:us-west-2:ACCOUNT:key/KEY2"
    "eu-west-1"      = "arn:aws:kms:eu-west-1:ACCOUNT:key/KEY3"
    "ap-southeast-1" = "arn:aws:kms:ap-southeast-1:ACCOUNT:key/KEY4"
  }
}
```

## HCP Packer Integration

Track AMI metadata and lifecycle in HCP Packer registry.

### Enable HCP Packer

```hcl
packer {
  required_plugins {
    amazon = {
      version = ">= 1.3.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

# HCP Packer configuration
hcp_packer_registry {
  bucket_name = "golden-ami"
  description = "Ubuntu 22.04 golden AMI for application servers"
  
  bucket_labels = {
    "os"          = "ubuntu"
    "team"        = "platform"
    "compliance"  = "cis-level-1"
  }
  
  build_labels = {
    "build-source"    = "github-actions"
    "git-commit-sha"  = env("GITHUB_SHA")
  }
}
```

### Query HCP Packer from Terraform

```hcl
data "hcp_packer_artifact" "app_server" {
  bucket_name  = "golden-ami"
  channel_name = "production"
  platform     = "aws"
  region       = "us-east-1"
}

resource "aws_instance" "app" {
  ami           = data.hcp_packer_artifact.app_server.external_identifier
  instance_type = "t3.medium"
}
```

### Channel Management

Promote builds through channels:

```bash
# Assign iteration to channel
packer hcp channel assign \
  --bucket golden-ami \
  --channel staging \
  --iteration-id 01HXXXXXXXXXXXXXXXXXXXXXXX

# Promote to production after testing
packer hcp channel assign \
  --bucket golden-ami \
  --channel production \
  --iteration-id 01HXXXXXXXXXXXXXXXXXXXXXXX
```

## Security Hardening Patterns

### CIS Benchmark Implementation

**scripts/cis-benchmark.sh:**
```bash
#!/bin/bash
set -e

# 1.1 Filesystem Configuration
echo "Configuring filesystem security..."
echo "tmpfs /tmp tmpfs defaults,nodev,nosuid,noexec 0 0" | sudo tee -a /etc/fstab

# 1.2 Configure package management
sudo apt-get install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades

# 1.3 Mandatory Access Control
sudo apt-get install -y apparmor apparmor-utils
sudo systemctl enable apparmor

# 3.1 Network Parameters
cat << EOF | sudo tee /etc/sysctl.d/60-netipv4_sysctl.conf
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
EOF

sudo sysctl -p /etc/sysctl.d/60-netipv4_sysctl.conf

# 4.1 Configure auditd
sudo apt-get install -y auditd audispd-plugins
sudo systemctl enable auditd

# 5.1 Configure SSH
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config

# 5.2 Configure sudo
echo "Defaults use_pty" | sudo tee -a /etc/sudoers.d/use_pty
echo "Defaults logfile=\"/var/log/sudo.log\"" | sudo tee -a /etc/sudoers.d/logfile
```

### AWS-Specific Security

```hcl
provisioner "shell" {
  inline = [
    # Install and configure CloudWatch agent
    "wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb",
    "sudo dpkg -i amazon-cloudwatch-agent.deb",
    
    # Install SSM agent
    "sudo snap install amazon-ssm-agent --classic",
    "sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service",
    
    # Install AWS CLI v2
    "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'",
    "unzip awscliv2.zip",
    "sudo ./aws/install",
    
    # Configure IMDSv2 (more secure)
    "sudo sh -c 'echo \"[default]\" > /etc/instance-identity/config'",
    "sudo sh -c 'echo \"hop_limit = 1\" >> /etc/instance-identity/config'"
  ]
}
```

## AMI Cleanup and Lifecycle

### Deregister Old AMIs

**scripts/cleanup-old-amis.sh:**
```bash
#!/bin/bash

# Keep only last N AMIs
KEEP_COUNT=5
AMI_PREFIX="golden-ami"

# Get AMIs sorted by creation date
AMIS=$(aws ec2 describe-images \
  --owners self \
  --filters "Name=name,Values=${AMI_PREFIX}-*" \
  --query 'sort_by(Images, &CreationDate)[*].[ImageId,Name,CreationDate]' \
  --output text)

# Count total AMIs
TOTAL=$(echo "$AMIS" | wc -l)
DELETE_COUNT=$((TOTAL - KEEP_COUNT))

if [ $DELETE_COUNT -gt 0 ]; then
  echo "Deleting $DELETE_COUNT old AMIs..."
  
  echo "$AMIS" | head -n $DELETE_COUNT | while read AMI_ID NAME DATE; do
    echo "Deregistering $AMI_ID ($NAME)"
    
    # Get associated snapshots
    SNAPSHOTS=$(aws ec2 describe-images \
      --image-ids $AMI_ID \
      --query 'Images[*].BlockDeviceMappings[*].Ebs.SnapshotId' \
      --output text)
    
    # Deregister AMI
    aws ec2 deregister-image --image-id $AMI_ID
    
    # Delete snapshots
    for SNAPSHOT in $SNAPSHOTS; do
      echo "Deleting snapshot $SNAPSHOT"
      aws ec2 delete-snapshot --snapshot-id $SNAPSHOT
    done
  done
fi
```

## Build Validation

### InSpec Integration

```hcl
provisioner "inspec" {
  profile = "https://github.com/dev-sec/linux-baseline"
}
```

**Custom InSpec Profile (inspec/controls/app.rb):**
```ruby
control 'app-installed' do
  impact 1.0
  title 'Application is installed'
  desc 'Verify application is installed and configured'
  
  describe package('nginx') do
    it { should be_installed }
  end
  
  describe service('nginx') do
    it { should be_enabled }
    it { should be_running }
  end
  
  describe file('/etc/nginx/nginx.conf') do
    it { should exist }
    it { should be_owned_by 'root' }
  end
end
```

## Build Optimization

### Parallel Builds

Build multiple variants simultaneously:

```hcl
source "amazon-ebs" "app_amd64" {
  ami_name      = "app-amd64-{{timestamp}}"
  instance_type = "t3.medium"
  architecture  = "x86_64"
  # ... configuration
}

source "amazon-ebs" "app_arm64" {
  ami_name      = "app-arm64-{{timestamp}}"
  instance_type = "t4g.medium"
  architecture  = "arm64"
  # ... configuration
}

build {
  sources = [
    "source.amazon-ebs.app_amd64",
    "source.amazon-ebs.app_arm64"
  ]
  # ... provisioners
}
```

Build with parallel execution:
```bash
packer build -parallel-builds=2 template.pkr.hcl
```

### Faster Provisioning

Use spot instances for cost savings:

```hcl
source "amazon-ebs" "spot" {
  spot_price          = "auto"
  spot_instance_types = ["t3.medium", "t3a.medium"]
  # ... rest of configuration
}
```

## Variables and Input Validation

### Variable Files

**variables.pkr.hcl:**
```hcl
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for AMI build"
}

variable "instance_type" {
  type = string
  validation {
    condition     = contains(["t3.small", "t3.medium", "t3.large"], var.instance_type)
    error_message = "Instance type must be t3.small, t3.medium, or t3.large."
  }
}

variable "app_version" {
  type = string
  validation {
    condition     = can(regex("^\\d+\\.\\d+\\.\\d+$", var.app_version))
    error_message = "App version must be semantic version (e.g., 1.2.3)."
  }
}
```

**Build with variables:**
```bash
packer build \
  -var 'aws_region=us-west-2' \
  -var 'instance_type=t3.large' \
  -var 'app_version=1.2.3' \
  template.pkr.hcl

# OR use variable file
packer build -var-file=production.pkrvars.hcl template.pkr.hcl
```

## Troubleshooting

**Issue: SSH timeout during provisioning**
- Increase `ssh_timeout` in source block
- Verify security group allows SSH from Packer IP
- Check VPC routing and internet gateway configuration

**Issue: AMI creation fails**
- Check IAM permissions for ec2:CreateImage, ec2:RegisterImage
- Verify instance profile attached during build
- Review CloudWatch Logs for detailed errors

**Issue: Provisioner fails**
- Add `-debug` flag to see detailed output: `packer build -debug template.pkr.hcl`
- Use breakpoint provisioner for interactive debugging
- Check provisioner logs in `/tmp` on build instance

**Issue: Slow builds**
- Use faster instance types
- Enable spot instances
- Optimize provisioner scripts
- Cache package downloads

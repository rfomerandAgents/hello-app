# Build Speed Optimization

Comprehensive techniques for reducing Packer build times.

## Provisioner Optimization

### Consolidation Patterns

**Anti-pattern**: Multiple shell provisioners
```hcl
provisioner "shell" {
  inline = ["apt-get update"]
}
provisioner "shell" {
  inline = ["apt-get install -y nginx"]
}
provisioner "shell" {
  inline = ["systemctl enable nginx"]
}
```

**Optimized**: Single consolidated provisioner
```hcl
provisioner "shell" {
  inline = [
    "apt-get update",
    "apt-get install -y nginx",
    "systemctl enable nginx"
  ]
}
```

**Benefits**: Reduces provisioner overhead, improves error handling, enables better caching.

### Script Externalization

**Pattern**: Move complex inline scripts to external files
```hcl
provisioner "shell" {
  scripts = [
    "scripts/base-setup.sh",
    "scripts/install-deps.sh",
    "scripts/configure-app.sh"
  ]
}
```

**Benefits**: Better maintainability, easier testing, improved reusability, cleaner templates.

### Provisioner Ordering Strategy

Order provisioners by:
1. **Change frequency** (least frequent first)
2. **Execution time** (longest first when independent)
3. **Dependencies** (required before dependent)

**Example ordering**:
```hcl
# 1. Base system (changes rarely, long execution)
provisioner "shell" {
  scripts = ["scripts/base-system.sh"]
}

# 2. Dependencies (changes occasionally)
provisioner "shell" {
  scripts = ["scripts/install-packages.sh"]
}

# 3. Application (changes frequently, short execution)
provisioner "shell" {
  scripts = ["scripts/deploy-app.sh"]
}
```

## Parallel Builds

### CLI Approach

Run multiple builds simultaneously:
```bash
packer build -parallel-builds=4 template.pkr.hcl
```

### Template Configuration

Use `max_parallel` in source blocks:
```hcl
build {
  sources = [
    "source.amazon-ebs.ubuntu-20",
    "source.amazon-ebs.ubuntu-22",
    "source.amazon-ebs.debian-11"
  ]
  
  # Limit parallelization to avoid resource exhaustion
  max_parallel = 2
}
```

### Platform Matrix Builds

**Pattern**: Separate builds by platform for parallel execution
```hcl
# ubuntu-build.pkr.hcl
build {
  name = "ubuntu"
  sources = ["source.amazon-ebs.ubuntu"]
}

# debian-build.pkr.hcl  
build {
  name = "debian"
  sources = ["source.amazon-ebs.debian"]
}
```

Run in parallel:
```bash
packer build ubuntu-build.pkr.hcl &
packer build debian-build.pkr.hcl &
wait
```

## Network Optimization

### Local Package Mirrors

**APT mirror configuration**:
```bash
# Setup local mirror proxy
cat > /etc/apt/apt.conf.d/02proxy << EOF
Acquire::http::Proxy "http://apt-cache.local:3142";
EOF

apt-get update
apt-get install -y packages...
```

**YUM mirror configuration**:
```bash
# Use fastest mirror plugin
yum install -y yum-plugin-fastestmirror
yum-config-manager --save --setopt=fastestmirror=true
```

### Pre-download Large Files

**Pattern**: Download to shared cache location
```hcl
provisioner "shell" {
  inline = [
    "mkdir -p /tmp/downloads",
    "cd /tmp/downloads",
    # Check if already cached
    "test -f jdk-11.tar.gz || wget https://example.com/jdk-11.tar.gz",
    "tar xzf jdk-11.tar.gz -C /opt"
  ]
}
```

### HTTP Caching Proxy

Use Squid or similar for HTTP caching:
```bash
# Setup Squid proxy for build environment
export http_proxy=http://squid.local:3128
export https_proxy=http://squid.local:3128

# Packer automatically uses these environment variables
packer build template.pkr.hcl
```

### Optimized Base Images

**Strategy**: Start from minimal, optimized base images
- AWS: Use minimal AMIs (Ubuntu Minimal, Amazon Linux Minimal)
- Docker: Use alpine or distroless base images
- Azure: Use basic/minimal SKUs

## Intermediate Base Images

### Pattern: Dependency Pre-baking

**Step 1**: Create base image with dependencies
```hcl
# base-image.pkr.hcl
source "amazon-ebs" "base" {
  ami_name      = "base-with-deps-{{timestamp}}"
  source_ami    = "ami-xxxxx"
  instance_type = "t3.medium"
}

build {
  sources = ["source.amazon-ebs.base"]
  
  provisioner "shell" {
    inline = [
      "apt-get update",
      "apt-get install -y python3 python3-pip nodejs npm",
      "pip3 install ansible boto3",
      "npm install -g typescript webpack"
    ]
  }
}
```

**Step 2**: Use base image for application builds
```hcl
# app-image.pkr.hcl
data "amazon-ami" "base" {
  filters = {
    name = "base-with-deps-*"
  }
  most_recent = true
}

source "amazon-ebs" "app" {
  source_ami    = data.amazon-ami.base.id
  ami_name      = "app-{{timestamp}}"
  instance_type = "t3.small"
}

build {
  sources = ["source.amazon-ebs.app"]
  
  # Only application-specific provisioning
  provisioner "shell" {
    scripts = ["scripts/deploy-app.sh"]
  }
}
```

**Benefits**: Dramatically reduces build time for application iterations, enables caching of expensive dependency installations.

## Resource Tuning

### Builder Resource Configuration

**AWS EBS Builder**:
```hcl
source "amazon-ebs" "optimized" {
  instance_type = "c5.xlarge"  # CPU-optimized for compilation
  
  launch_block_device_mappings {
    device_name = "/dev/sda1"
    volume_size = 50
    volume_type = "gp3"
    iops        = 3000          # Higher IOPS for faster I/O
    throughput  = 250           # Higher throughput
  }
}
```

**Docker Builder**:
```hcl
source "docker" "optimized" {
  image  = "ubuntu:22.04"
  commit = true
  
  # Allocate more resources to container
  run_command = [
    "-d", "-i", "-t",
    "--cpus=4",
    "--memory=8g",
    "{{.Image}}"
  ]
}
```

### Workload-Specific Tuning

**Compilation-heavy workloads**: Use CPU-optimized instances (c5, c6i)
**I/O-heavy workloads**: Use instances with NVMe SSDs (m5d, c5d)
**Network-heavy workloads**: Use enhanced networking instances

## Build Profiling

### Enable Detailed Logging

```bash
export PACKER_LOG=1
export PACKER_LOG_PATH="packer-build.log"
packer build template.pkr.hcl
```

### Analyze Provisioner Times

Parse logs to identify slow provisioners:
```bash
grep "Provisioning with shell script:" packer-build.log | \
  awk '{print $1, $2}' | \
  while read start _; do
    read end _
    echo $(($(date -d "$end" +%s) - $(date -d "$start" +%s)))
  done | sort -rn
```

Or use the included `scripts/analyze_build.py` for automated analysis.

## Quick Wins Checklist

- [ ] Consolidate multiple shell provisioners into single scripts
- [ ] Order provisioners by change frequency (stable first)
- [ ] Enable parallel builds with `-parallel-builds`
- [ ] Use local package mirrors or caching proxy
- [ ] Pre-bake common dependencies into base images
- [ ] Increase builder instance size for compilation workloads
- [ ] Use faster storage (gp3, NVMe) for I/O-heavy operations
- [ ] Profile builds to identify specific bottlenecks
- [ ] Externalize scripts for better maintainability
- [ ] Remove unnecessary package installations

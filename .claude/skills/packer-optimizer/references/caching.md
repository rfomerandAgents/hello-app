# Caching Strategies

Comprehensive guide to implementing effective caching in Packer builds.

## Caching Hierarchy

Effective caching operates at multiple levels:

1. **Source image caching** - Reuse base AMIs/images
2. **Package manager caching** - Preserve downloaded packages
3. **Build artifact caching** - Cache compiled binaries
4. **Provisioner caching** - Skip unchanged provisioning steps
5. **HCP Packer registry** - Share builds across teams

## Source Image Caching

### Data Sources for Latest Images

**Pattern**: Use data sources to find latest base images
```hcl
data "amazon-ami" "ubuntu" {
  filters = {
    name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-*"
    virtualization-type = "hvm"
    root-device-type    = "ebs"
  }
  owners      = ["099720109477"]  # Canonical
  most_recent = true
}

source "amazon-ebs" "app" {
  source_ami = data.amazon-ami.ubuntu.id
  # Packer will cache the AMI ID between builds
}
```

**Benefit**: Packer caches the AMI lookup, avoiding repeated API calls.

### Intermediate Base Images

**Pattern**: Create versioned base images with dependencies
```hcl
# base.pkr.hcl - Build infrequently
source "amazon-ebs" "base" {
  ami_name = "base-v${var.version}"
  tags = {
    Type    = "base"
    Version = var.version
  }
}

build {
  sources = ["source.amazon-ebs.base"]
  # Install stable dependencies
}

# app.pkr.hcl - Build frequently
data "amazon-ami" "base" {
  filters = {
    tag:Type = "base"
  }
  most_recent = true
}

source "amazon-ebs" "app" {
  source_ami = data.amazon-ami.base.id
  # Only application-specific changes
}
```

## Package Manager Caching

### Local Package Cache

**APT caching proxy** (apt-cacher-ng):
```bash
# Setup apt-cacher-ng on build host
apt-get install -y apt-cacher-ng

# Configure in Packer build
provisioner "shell" {
  inline = [
    "echo 'Acquire::http::Proxy \"http://HOST_IP:3142\";' > /etc/apt/apt.conf.d/02proxy",
    "apt-get update",
    "apt-get install -y packages..."
  ]
}
```

**YUM caching**:
```bash
# Keep cache in shared location
mkdir -p /var/cache/yum-shared

provisioner "shell" {
  inline = [
    "yum install -y --setopt=cachedir=/var/cache/yum-shared packages..."
  ]
}
```

### Package Cache Mounts

**Docker builder** with cache mounts:
```hcl
source "docker" "cached" {
  image  = "ubuntu:22.04"
  commit = true
  
  volumes = {
    "/var/cache/apt/archives" = "/tmp/apt-cache"
  }
}
```

### Pre-download to Persistent Location

**Pattern**: Download to mounted volume
```hcl
source "amazon-ebs" "cached" {
  launch_block_device_mappings {
    device_name  = "/dev/sdf"
    volume_size  = 100
    volume_type  = "gp3"
    # Preserve this volume across builds
    delete_on_termination = false
  }
}

provisioner "shell" {
  inline = [
    "mkdir -p /mnt/cache",
    "mount /dev/sdf /mnt/cache",
    # Downloads go to cache
    "cd /mnt/cache",
    "test -f large-file.tar.gz || wget https://example.com/large-file.tar.gz",
    "tar xzf large-file.tar.gz -C /opt"
  ]
}
```

## Build Artifact Caching

### Shared Build Cache

**Pattern**: Mount build cache across builds
```bash
# Build host maintains cache directory
mkdir -p /var/packer-cache/{go,rust,maven,gradle}

# Mount in Packer builds
```

```hcl
provisioner "shell" {
  environment_vars = [
    "GOCACHE=/var/packer-cache/go",
    "CARGO_HOME=/var/packer-cache/rust",
    "GRADLE_USER_HOME=/var/packer-cache/gradle"
  ]
  inline = [
    "go build -o /usr/local/bin/app",
    # Build artifacts cached between runs
  ]
}
```

### Binary Caching

**Pattern**: Pre-build and cache binaries externally
```bash
# External build cache
mkdir -p /build-cache/$(git rev-parse HEAD)

# Check cache before building
if [ ! -f /build-cache/$(git rev-parse HEAD)/app ]; then
  go build -o /build-cache/$(git rev-parse HEAD)/app
fi

# Copy from cache to image
```

## HCP Packer Integration

### Basic HCP Packer Configuration

```hcl
packer {
  required_plugins {
    amazon = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

build {
  hcp_packer_registry {
    bucket_name = "golden-images"
    description = "Production-ready golden image"
    
    bucket_labels = {
      "environment" = "production"
      "compliance"  = "cis-level-1"
    }
  }
  
  sources = ["source.amazon-ebs.app"]
}
```

### Using HCP Packer Iterations

**Pattern**: Reference previous iterations as base
```hcl
data "hcp-packer-image" "base" {
  bucket_name    = "golden-base"
  channel        = "production"
  cloud_provider = "aws"
  region         = "us-east-1"
}

source "amazon-ebs" "app" {
  source_ami = data.hcp-packer-image.base.id
  # Build on top of tracked base image
}
```

**Benefits**:
- Version tracking and lineage
- Centralized image registry
- Revocation capabilities
- Team collaboration

### Channel-Based Promotion

```hcl
# Development builds
hcp_packer_registry {
  bucket_name = "app-image"
  description = "Dev build from ${var.git_commit}"
  channel     = "development"
}

# Promote to production via HCP Packer UI or CLI
# No rebuild necessary
```

## Provisioner-Level Caching

### Conditional Provisioning

**Pattern**: Skip provisioners based on file checks
```hcl
provisioner "shell" {
  inline = [
    # Check if already provisioned
    "test -f /opt/.provisioned && exit 0",
    
    # Expensive provisioning
    "apt-get update",
    "apt-get install -y large-package",
    
    # Mark as complete
    "touch /opt/.provisioned"
  ]
}
```

### File Checksums for Caching

**Pattern**: Provision only when files change
```hcl
provisioner "file" {
  source      = "config.json"
  destination = "/tmp/config.json"
}

provisioner "shell" {
  inline = [
    # Compare checksums
    "NEW_SUM=$(md5sum /tmp/config.json | awk '{print $1}')",
    "OLD_SUM=$(cat /opt/.config-sum 2>/dev/null || echo 'none')",
    
    # Skip if unchanged
    "[ \"$NEW_SUM\" = \"$OLD_SUM\" ] && exit 0",
    
    # Expensive configuration
    "/usr/local/bin/process-config /tmp/config.json",
    
    # Save checksum
    "echo $NEW_SUM > /opt/.config-sum"
  ]
}
```

## CI/CD Caching Integration

### GitHub Actions

```yaml
name: Packer Build
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      # Cache Packer plugins
      - uses: actions/cache@v3
        with:
          path: ~/.packer.d/plugins
          key: packer-plugins-${{ hashFiles('**.pkr.hcl') }}
      
      # Cache build dependencies
      - uses: actions/cache@v3
        with:
          path: |
            /tmp/packer-cache
            ~/.cache
          key: build-cache-${{ github.sha }}
          restore-keys: |
            build-cache-
      
      - name: Build
        run: packer build template.pkr.hcl
```

### GitLab CI

```yaml
packer-build:
  image: hashicorp/packer:latest
  
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - .packer.d/
      - /tmp/packer-cache/
  
  before_script:
    - mkdir -p /tmp/packer-cache
  
  script:
    - packer build template.pkr.hcl
```

### Self-Hosted Runners

**Pattern**: Persistent cache on runner
```bash
# Runner setup
mkdir -p /runner-cache/{apt,yum,go,rust}

# Mount into Packer builds
export PACKER_CACHE_DIR=/runner-cache
```

## Cache Invalidation Strategies

### Time-Based Invalidation

**Pattern**: Invalidate cache after time period
```hcl
locals {
  cache_key = "${formatdate("YYYY-MM-DD", timestamp())}"
}

source "amazon-ebs" "app" {
  ami_name = "app-${local.cache_key}"
  # Forces daily rebuilds
}
```

### Content-Based Invalidation

**Pattern**: Invalidate on content changes
```hcl
locals {
  content_hash = md5(join("", [
    filemd5("scripts/provision.sh"),
    filemd5("config/app.conf"),
  ]))
}

source "amazon-ebs" "app" {
  ami_name = "app-${substr(local.content_hash, 0, 8)}"
}
```

### Version-Based Invalidation

**Pattern**: Explicit version bumps
```hcl
variable "app_version" {
  type    = string
  default = "1.2.3"
}

source "amazon-ebs" "app" {
  ami_name = "app-${var.app_version}"
  
  tags = {
    Version = var.app_version
  }
}
```

## Cache Debugging

### Enable Cache Logging

```bash
export PACKER_LOG=1
export PACKER_LOG_PATH="packer-cache.log"

# Look for cache hit/miss messages
grep -i cache packer-cache.log
```

### Verify Cache Usage

**Check package cache**:
```bash
# APT cache inspection
ls -lh /var/cache/apt/archives/
du -sh /var/cache/apt/

# YUM cache inspection
du -sh /var/cache/yum/
```

**Check HCP Packer registry**:
```bash
# List iterations
packer hcp bucket versions list golden-images

# Check ancestry
packer hcp bucket version ancestors golden-images v1.2.3
```

### Cache Performance Metrics

Monitor these metrics:
- **Cache hit rate**: Percentage of cached operations
- **Time saved**: Build time with vs without cache
- **Storage used**: Cache storage consumption
- **Cache age**: How long since last update

## Cache Storage Considerations

### Storage Sizing

**Local cache**: 10-50GB per project typical
**Shared cache server**: 100GB-1TB for multiple teams
**HCP Packer**: Pay for stored iterations (typically minimal)

### Cleanup Strategies

**Age-based cleanup**:
```bash
# Remove cache entries older than 30 days
find /var/packer-cache -type f -mtime +30 -delete
```

**Size-based cleanup**:
```bash
# Keep cache under 100GB
du -sb /var/packer-cache | awk '{if($1 > 107374182400) system("packer-cache-cleanup.sh")}'
```

**LRU cleanup**:
```bash
# Remove least recently used until under size limit
find /var/packer-cache -type f -printf '%A@ %p\n' | \
  sort -n | \
  head -n 50 | \
  awk '{print $2}' | \
  xargs rm
```

## Best Practices Summary

1. **Layer caches** - Use multiple caching strategies simultaneously
2. **Stable keys** - Use content hashes for cache keys when possible
3. **Explicit invalidation** - Control when caches expire
4. **Monitor hit rates** - Track cache effectiveness
5. **Regular cleanup** - Prevent cache bloat
6. **Team sharing** - Use HCP Packer for multi-team environments
7. **Cache locally** - Prefer local caching for fastest builds
8. **Validate regularly** - Occasionally rebuild without cache to verify

## Common Caching Pitfalls

**Pitfall**: Cache keys too specific (never hit)
**Solution**: Use stable, coarse-grained keys

**Pitfall**: Cache never invalidated (stale data)
**Solution**: Implement explicit invalidation strategy

**Pitfall**: Cache too large (storage issues)
**Solution**: Regular cleanup, size limits

**Pitfall**: Cache not shared (duplicated work)
**Solution**: Centralized cache server or HCP Packer

**Pitfall**: Network cache slower than source
**Solution**: Benchmark and optimize cache location

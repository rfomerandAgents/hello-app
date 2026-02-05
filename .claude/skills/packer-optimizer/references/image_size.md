# Image Size Optimization

Comprehensive techniques for minimizing Packer build artifact sizes.

## Multi-Stage Builds (Docker)

### Pattern: Separate Build and Runtime

**Full example**:
```hcl
source "docker" "builder" {
  image  = "golang:1.21-alpine"
  commit = false  # Don't save this stage
}

source "docker" "runtime" {
  image  = "alpine:3.18"
  commit = true
}

build {
  name = "multi-stage"
  
  # Stage 1: Build
  source "docker.builder" {
    name = "build-stage"
  }
  
  provisioner "shell" {
    inline = [
      "mkdir /app",
      "cd /app",
      "go build -o myapp ."
    ]
  }
  
  provisioner "file" {
    source      = "/app/myapp"
    destination = "/tmp/myapp"
    direction   = "download"
  }
  
  # Stage 2: Runtime
  source "docker.runtime" {
    name = "runtime-stage"
  }
  
  provisioner "file" {
    source      = "/tmp/myapp"
    destination = "/usr/local/bin/myapp"
    direction   = "upload"
  }
  
  provisioner "shell" {
    inline = ["chmod +x /usr/local/bin/myapp"]
  }
}
```

**Size reduction**: 500MB+ build image → 15MB runtime image

### Alternative: Build Artifacts Externally

For non-Docker builds, compile artifacts outside Packer:
```bash
# Build outside
docker run --rm -v $PWD:/src golang:1.21 go build -o app /src

# Upload to Packer build
```

```hcl
provisioner "file" {
  source      = "app"
  destination = "/usr/local/bin/app"
}
```

## Package Management Optimization

### Remove Build Dependencies

**Pattern**: Install, use, then remove build tools
```bash
# Install build dependencies
apt-get update
apt-get install -y --no-install-recommends \
  build-essential \
  python3-dev \
  libssl-dev

# Build application
pip3 install -r requirements.txt

# Remove build dependencies
apt-get purge -y \
  build-essential \
  python3-dev \
  libssl-dev

# Clean up
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
```

### Minimal Package Installation

**Use `--no-install-recommends`** (APT):
```bash
# Bad: Installs recommended packages
apt-get install -y nginx

# Good: Minimal installation
apt-get install -y --no-install-recommends nginx
```

**Size difference**: Can save 100MB+ per package with large dependency trees.

### Package Manager Cleanup

**APT (Debian/Ubuntu)**:
```bash
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /var/cache/apt/archives/*
```

**YUM/DNF (RHEL/CentOS)**:
```bash
yum clean all
rm -rf /var/cache/yum
```

**APK (Alpine)**:
```bash
apk cache clean
rm -rf /var/cache/apk/*
```

**Pip (Python)**:
```bash
pip3 cache purge
rm -rf ~/.cache/pip
```

**NPM (Node.js)**:
```bash
npm cache clean --force
rm -rf ~/.npm
```

## Temporary File Cleanup

### Common Temporary Locations

Clean these directories before finalizing images:
```bash
# System temporary files
rm -rf /tmp/*
rm -rf /var/tmp/*

# Log files
rm -rf /var/log/*
> /var/log/lastlog
> /var/log/wtmp

# Bash history
rm -f /root/.bash_history
rm -f /home/*/.bash_history

# SSH keys (if generated during build)
rm -rf /root/.ssh
rm -rf /home/*/.ssh

# Cloud-init artifacts
rm -rf /var/lib/cloud/instances/*
```

### Build Artifacts

Remove files only needed during build:
```bash
# Compiler output
rm -rf /usr/src/*
rm -rf /tmp/build/*

# Documentation
rm -rf /usr/share/doc/*
rm -rf /usr/share/man/*
rm -rf /usr/share/info/*

# Locales (if not needed)
find /usr/share/locale -mindepth 1 -maxdepth 1 ! -name 'en*' -delete
```

## Layer Optimization (Docker)

### Combine Commands

**Anti-pattern**: Multiple RUN commands create layers
```dockerfile
RUN apt-get update
RUN apt-get install -y nginx
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
```

**Optimized**: Single RUN command, one layer
```dockerfile
RUN apt-get update && \
    apt-get install -y nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Remove Files in Same Layer

**Anti-pattern**: File persists in previous layer
```dockerfile
RUN wget https://example.com/large-file.tar.gz
RUN tar xzf large-file.tar.gz
RUN rm large-file.tar.gz  # File still in previous layer!
```

**Optimized**: Remove in same command
```dockerfile
RUN wget https://example.com/large-file.tar.gz && \
    tar xzf large-file.tar.gz && \
    rm large-file.tar.gz
```

### Order by Change Frequency

Place rarely-changing operations first:
```dockerfile
# Rarely changes
RUN apt-get update && apt-get install -y base-packages

# Occasionally changes
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Frequently changes
COPY . /app/
```

**Benefit**: Better layer caching, faster rebuilds.

## Compression Techniques

### Artifact Compression

**For ISO/disk images**:
```bash
# Create compressed image
qemu-img convert -O qcow2 -c source.raw output.qcow2

# Or use aggressive compression
gzip -9 image.raw
# Or zstd for better compression/speed balance
zstd -19 image.raw
```

**For AMIs**: Use encrypted volumes for built-in compression
```hcl
source "amazon-ebs" "compressed" {
  encrypt_boot = true
  kms_key_id   = "alias/aws/ebs"
}
```

### File-Level Compression

Pre-compress large static files:
```bash
# Compress static assets
find /var/www -type f -name "*.js" -exec gzip -9 -k {} \;
find /var/www -type f -name "*.css" -exec gzip -9 -k {} \;

# Configure web server to serve .gz files
```

## Application-Specific Optimization

### Python Applications

```bash
# Use compiled bytecode
python3 -m compileall /opt/app

# Remove source files if safe
find /opt/app -name "*.py" -delete

# Remove tests
rm -rf /opt/app/*/tests
rm -rf /opt/app/*/test

# Remove pip metadata
rm -rf /usr/local/lib/python*/dist-packages/*.dist-info
```

### Node.js Applications

```bash
# Production dependencies only
npm ci --only=production

# Remove dev files
rm -rf node_modules/*/test
rm -rf node_modules/*/tests
rm -rf node_modules/*/*.md
rm -rf node_modules/*/.github

# Or use npm prune
npm prune --production
```

### Go Applications

```bash
# Build static binary
CGO_ENABLED=0 go build -ldflags="-s -w" -o app

# Strip even more
upx --best --lzma app  # Optional: UPX compression
```

## Kernel and Initramfs Optimization

### Remove Unused Kernels (VM images)

```bash
# Keep only current kernel
apt-get remove -y $(dpkg -l 'linux-*' | sed '/^ii/!d;/'"$(uname -r | sed "s/\(.*\)-\([^0-9]\+\)/\1/")"'/d;s/^[^ ]* [^ ]* \([^ ]*\).*/\1/')
```

### Minimize Initramfs

```bash
# Rebuild with only essential modules
update-initramfs -u

# Or specify minimal drivers
echo "MODULES=dep" >> /etc/initramfs-tools/initramfs.conf
update-initramfs -u
```

## Zero Free Space (VM Images)

### Pattern: Overwrite Unused Blocks

```bash
# Write zeros to all free space
dd if=/dev/zero of=/EMPTY bs=1M || true
rm -f /EMPTY

# This allows better compression of the image
```

**For QCOW2**: This significantly reduces the qcow2 file size.

**For AMIs**: Less impactful but still beneficial for EBS snapshots.

## Size Analysis Tools

### Docker Image Analysis

```bash
# Analyze Docker image layers
docker history --human --no-trunc image:tag

# Use dive for detailed analysis
dive image:tag
```

### General File Analysis

```bash
# Find largest files
find / -type f -exec du -h {} + | sort -rh | head -n 50

# Find largest directories
du -h --max-depth=1 / | sort -rh | head -n 20

# Find duplicate files
fdupes -r /
```

### Package Size Analysis

```bash
# APT: List installed packages by size
dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -rn | head -n 20

# YUM: List installed packages by size
rpm -qa --qf '%{SIZE} %{NAME}\n' | sort -rn | head -n 20
```

## Size Optimization Checklist

- [ ] Use multi-stage builds for compiled applications
- [ ] Install only required packages (use `--no-install-recommends`)
- [ ] Remove build dependencies after use
- [ ] Clean package manager caches
- [ ] Remove temporary files and logs
- [ ] Combine commands to minimize layers (Docker)
- [ ] Remove files in the same layer they're created (Docker)
- [ ] Order Dockerfile instructions by change frequency
- [ ] Strip binaries and documentation
- [ ] Use minimal base images (Alpine, distroless)
- [ ] Compress artifacts appropriately
- [ ] Remove unused kernels and drivers
- [ ] Zero free space before final compression
- [ ] Analyze with dive or du to find large files
- [ ] Remove language-specific test files and dev dependencies

## Size Comparison Examples

**Typical reductions achievable**:
- Base Ubuntu image: 500MB → 200MB (clean caches, remove docs)
- Python application: 1.2GB → 400MB (multi-stage, minimal deps)
- Go application: 800MB → 15MB (Alpine + static binary)
- Node.js application: 1GB → 300MB (prod deps only, prune)
- Java application: 600MB → 250MB (JRE-only, Alpine)

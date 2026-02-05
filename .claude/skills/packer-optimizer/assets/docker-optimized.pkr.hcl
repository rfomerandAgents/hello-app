// Optimized Docker Builder Template
// This template demonstrates best practices for building optimized Docker images with Packer

packer {
  required_plugins {
    docker = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/docker"
    }
  }
}

variable "app_version" {
  type        = string
  description = "Application version for tagging"
  default     = "1.0.0"
}

variable "base_image" {
  type        = string
  description = "Base image to build from"
  default     = "ubuntu:22.04"
}

// Use data source for HCP Packer integration (optional)
// data "hcp-packer-image" "base" {
//   bucket_name    = "golden-base"
//   channel        = "production"
//   cloud_provider = "docker"
// }

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
  image_tag = "myapp:${var.app_version}-${local.timestamp}"
}

// Multi-stage build pattern: Build stage
source "docker" "builder" {
  image  = var.base_image
  commit = false  // Don't save this intermediate stage
  
  // Allocate resources for build stage
  run_command = [
    "-d", "-i", "-t",
    "--cpus=4",
    "--memory=4g",
    "{{.Image}}"
  ]
  
  changes = [
    "WORKDIR /build",
  ]
}

// Multi-stage build pattern: Runtime stage
source "docker" "runtime" {
  image  = "alpine:3.18"  // Minimal runtime base
  commit = true
  
  changes = [
    "USER nobody",
    "WORKDIR /app",
    "ENTRYPOINT [\"/app/myapp\"]",
    "EXPOSE 8080",
  ]
}

build {
  name = "optimized-docker-build"
  
  // Optional: HCP Packer integration for tracking
  // hcp_packer_registry {
  //   bucket_name = "myapp-image"
  //   description = "Optimized multi-stage build"
  //   bucket_labels = {
  //     "version"     = var.app_version
  //     "os"          = "alpine"
  //   }
  // }
  
  ////////////////////////////////////////////////////////////////////////////////
  // BUILD STAGE: Compile application
  ////////////////////////////////////////////////////////////////////////////////
  
  source "docker.builder" {
    name = "build-stage"
  }
  
  // Install build dependencies (will not be in final image)
  provisioner "shell" {
    inline = [
      "set -e",
      "apt-get update",
      // Use --no-install-recommends to minimize size
      "apt-get install -y --no-install-recommends build-essential git curl",
      // Install specific build tools
      "curl -OL https://go.dev/dl/go1.21.0.linux-amd64.tar.gz",
      "tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz",
      "export PATH=$PATH:/usr/local/go/bin",
    ]
  }
  
  // Upload source code
  provisioner "file" {
    source      = "src/"
    destination = "/build/"
  }
  
  // Build application
  provisioner "shell" {
    inline = [
      "set -e",
      "cd /build",
      "export PATH=$PATH:/usr/local/go/bin",
      // Static binary for portability
      "CGO_ENABLED=0 go build -ldflags='-s -w' -o myapp .",
      // Optional: Further compress with upx
      // "upx --best --lzma myapp",
    ]
  }
  
  // Download built binary from build stage
  provisioner "file" {
    source      = "/build/myapp"
    destination = "/tmp/myapp"
    direction   = "download"
  }
  
  ////////////////////////////////////////////////////////////////////////////////
  // RUNTIME STAGE: Minimal final image
  ////////////////////////////////////////////////////////////////////////////////
  
  source "docker.runtime" {
    name = "runtime-stage"
  }
  
  // Upload only the compiled binary
  provisioner "file" {
    source      = "/tmp/myapp"
    destination = "/app/myapp"
  }
  
  // Minimal runtime configuration
  provisioner "shell" {
    inline = [
      "set -e",
      // Install only essential runtime dependencies
      "apk add --no-cache ca-certificates tzdata",
      // Set permissions
      "chmod +x /app/myapp",
      // Clean up apk cache (Alpine does this automatically, but being explicit)
      "rm -rf /var/cache/apk/*",
    ]
  }
  
  // Tag the final image
  post-processor "docker-tag" {
    repository = "myapp"
    tags       = [var.app_version, "latest"]
  }
  
  // Optional: Push to registry
  // post-processor "docker-push" {
  //   login          = true
  //   login_username = var.registry_username
  //   login_password = var.registry_password
  // }
}

// Alternative: Single-stage optimized build (when multi-stage isn't needed)
build {
  name = "single-stage-optimized"
  
  source "docker.runtime" {
    name = "single-stage"
  }
  
  // Combine operations to minimize layers
  provisioner "shell" {
    inline = [
      "set -e",
      // Install, use, and clean up in single layer
      "apk add --no-cache --virtual .build-deps gcc musl-dev && \\",
      "  pip install --no-cache-dir -r requirements.txt && \\",
      "  apk del .build-deps && \\",
      "  rm -rf /var/cache/apk/* /tmp/* /root/.cache",
      // This keeps everything in one layer, reducing final size
    ]
  }
  
  // Order provisioners by change frequency (stable first, volatile last)
  
  // 1. System packages (rarely change)
  provisioner "shell" {
    inline = [
      "apk add --no-cache ca-certificates curl",
    ]
  }
  
  // 2. Application dependencies (change occasionally)
  provisioner "file" {
    source      = "requirements.txt"
    destination = "/app/requirements.txt"
  }
  
  provisioner "shell" {
    inline = [
      "pip install --no-cache-dir -r /app/requirements.txt",
    ]
  }
  
  // 3. Application code (changes frequently)
  provisioner "file" {
    source      = "app/"
    destination = "/app/"
  }
  
  post-processor "docker-tag" {
    repository = "myapp"
    tags       = ["single-stage-${var.app_version}"]
  }
}

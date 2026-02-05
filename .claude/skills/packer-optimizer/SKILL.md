---
name: packer-optimizer
description: Expert guidance for optimizing HashiCorp Packer builds with focus on build speed, image size, caching strategies, and parallelization. Use when analyzing Packer templates, debugging slow builds, reducing build times, optimizing image sizes, implementing effective caching, or designing high-performance build pipelines.
---

# Packer Optimizer

Expert workflow for analyzing and optimizing HashiCorp Packer builds across build speed, image size, artifact quality, and resource efficiency.

## Core Optimization Workflow

When optimizing Packer builds, follow this systematic approach:

1. **Profile the build** → Analyze build times and identify bottlenecks
2. **Optimize provisioners** → Reduce provisioner execution time and complexity
3. **Implement caching** → Leverage caching at multiple layers
4. **Parallelize builds** → Execute independent builds concurrently
5. **Minimize image size** → Reduce final artifact size without losing functionality
6. **Validate optimizations** → Measure improvements and verify functionality

## Quick Optimization Checks

Before deep analysis, verify these common issues:

**Build speed issues?**
- Check provisioner execution order and consolidation opportunities
- Verify file upload sizes and compression
- Review network-dependent operations (apt, yum, downloads)
- Examine unnecessary package installations

**Image size issues?**
- Audit installed packages and remove unnecessary dependencies
- Check for leftover build artifacts and caches
- Review layer optimization (Docker/container builds)
- Verify cleanup scripts execute properly

**Caching not working?**
- Validate cache key uniqueness and stability
- Check cache storage backend configuration
- Review cache invalidation patterns
- Verify provisioner order doesn't break caching

## Optimization Strategies

### Build Speed Optimization

**Provisioner consolidation**: Combine multiple shell provisioners into single scripts to reduce overhead and improve coherence.

**Parallel execution**: Use `-parallel-builds` flag or `max_parallel` for independent image variants.

**Network optimization**:
- Use local mirrors for package managers
- Pre-download large files to shared cache
- Implement HTTP caching proxies
- Use faster base images when possible

**Dependency pre-baking**: Create intermediate base images with common dependencies pre-installed.

### Caching Strategies

**Multi-layer caching approach**:
1. **Base image caching** - Reuse unchanged base images
2. **Package manager caching** - Preserve apt/yum/apk caches
3. **Application caching** - Cache compiled binaries and dependencies
4. **Build cache** - Use Packer's built-in caching where supported

**HCP Packer integration**: Use HCP Packer for tracking, versioning, and sharing base images across teams.

**Local file caching**: Keep large downloads in persistent directories outside build context.

### Image Size Reduction

**Multi-stage pattern** (for container builds):
- Build stage: Install build tools and compile
- Runtime stage: Copy only necessary artifacts
- Result: Smaller final image without build dependencies

**Package cleanup**:
```bash
# After installing packages, clean up
apt-get clean && rm -rf /var/lib/apt/lists/*
yum clean all
apk cache clean
```

**Layer optimization**:
- Combine RUN commands to reduce layers
- Order operations by change frequency (least frequent first)
- Remove temporary files in the same layer they're created

**Compression**: Use appropriate compression for artifacts (gzip, zstd for ISOs/images).

### Advanced Techniques

**Provisioner ordering**: Order provisioners by execution time and change frequency to maximize cache hits.

**Build variants**: Use `only` and `except` to create targeted builds for different platforms efficiently.

**Resource tuning**: Adjust CPUs, memory, and disk for the builder to match workload requirements.

**Pipeline integration**: Use external tools (GitHub Actions, GitLab CI) for sophisticated caching and parallelization.

## Analysis Tools

Use included scripts for systematic optimization:

- `scripts/analyze_build.py` - Parse Packer logs to identify slow provisioners
- `scripts/compare_images.py` - Compare image sizes and identify bloat
- `scripts/cache_inspector.py` - Analyze cache effectiveness and hit rates

## Detailed References

For comprehensive optimization techniques:

- **Build speed**: See `references/build_speed.md` for provisioner optimization, parallelization patterns, and network optimization
- **Image size**: See `references/image_size.md` for multi-stage builds, layer optimization, and size reduction techniques  
- **Caching**: See `references/caching.md` for cache strategies, HCP Packer integration, and cache debugging
- **CI/CD**: See `references/cicd_patterns.md` for pipeline optimization and automation strategies

## Configuration Templates

Use optimized templates from `assets/` as starting points:

- `assets/docker-optimized.pkr.hcl` - Optimized Docker builder template
- `assets/aws-ami-optimized.pkr.hcl` - Optimized AWS AMI builder template
- `assets/parallel-builds.pkr.hcl` - Multi-platform parallel build example

# CI/CD Pipeline Optimization

Patterns and strategies for integrating Packer into CI/CD pipelines efficiently.

## Pipeline Architecture Patterns

### Pattern 1: Base + Application Images

**Strategy**: Separate stable base images from frequently-changing application images.

```
Trigger: Weekly schedule
┌─────────────────────────────┐
│  Base Image Pipeline        │
│  - OS updates               │
│  - Common dependencies      │
│  - Security patches         │
│  Result: base-v1.2.3       │
└──────────┬──────────────────┘
           │
           ▼
Trigger: On commit
┌─────────────────────────────┐
│  Application Pipeline       │
│  - Use latest base image    │
│  - Deploy application       │
│  - Application configs      │
│  Result: app-v2.4.5        │
└─────────────────────────────┘
```

**Benefits**: Faster application builds, clear separation of concerns, reduced base image churn.

### Pattern 2: Multi-Stage Pipeline

**Strategy**: Progressive validation and promotion across environments.

```
┌─────────────────┐
│  Build Stage    │ → Build AMI
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Test Stage     │ → Validate AMI
└────────┬────────┘   - Boot test
         │            - Smoke tests
         │            - Security scan
         ▼
┌─────────────────┐
│  Promote Stage  │ → Tag/Promote
└────────┬────────┘   - HCP channel
         │            - AMI tags
         │            - Notification
         ▼
┌─────────────────┐
│  Deploy Stage   │ → Deploy to env
└─────────────────┘
```

### Pattern 3: Matrix Builds

**Strategy**: Build multiple variants in parallel.

```
Trigger: On commit
        │
        ├─────────────┬─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Ubuntu 20.04 │ │ Ubuntu 22.04 │ │ Debian 11    │ │ RHEL 9       │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
                      ▼
              Test & Promote
```

## GitHub Actions Examples

### Basic Packer Build

```yaml
name: Packer Build

on:
  push:
    branches: [main]
    paths:
      - 'io/packer/**'
      - '.github/workflows/packer.yml'

env:
  PACKER_VERSION: "1.9.4"

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Packer
        uses: hashicorp/setup-packer@main
        with:
          version: ${{ env.PACKER_VERSION }}
      
      - name: Initialize Packer
        run: packer init io/packer/
      
      - name: Validate Template
        run: packer validate io/packer/
      
      - name: Build AMI
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          packer build \
            -var "version=${{ github.sha }}" \
            io/packer/aws-ami.pkr.hcl
```

### Optimized with Caching

```yaml
name: Packer Build (Optimized)

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Packer
        uses: hashicorp/setup-packer@main
      
      # Cache Packer plugins
      - name: Cache Packer plugins
        uses: actions/cache@v3
        with:
          path: ~/.packer.d/plugins
          key: packer-plugins-${{ hashFiles('io/packer/*.pkr.hcl') }}
          restore-keys: |
            packer-plugins-
      
      # Cache build dependencies
      - name: Cache build artifacts
        uses: actions/cache@v3
        with:
          path: |
            /tmp/packer-cache
            ~/.cache
          key: packer-build-${{ hashFiles('scripts/**') }}
          restore-keys: |
            packer-build-
      
      - name: Initialize Packer
        run: |
          mkdir -p /tmp/packer-cache
          packer init io/packer/
      
      - name: Build
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          PACKER_CACHE_DIR: /tmp/packer-cache
        run: packer build -timestamp-ui io/packer/
```

### Matrix Build Strategy

```yaml
name: Multi-Platform Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        platform:
          - ubuntu-20.04
          - ubuntu-22.04
          - debian-11
          - rhel-9
        region:
          - us-east-1
          - us-west-2
      fail-fast: false
      max-parallel: 4
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Packer
        uses: hashicorp/setup-packer@main
      
      - name: Build for ${{ matrix.platform }} in ${{ matrix.region }}
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          packer build \
            -var "platform=${{ matrix.platform }}" \
            -var "region=${{ matrix.region }}" \
            -only="amazon-ebs.${{ matrix.platform }}" \
            io/packer/template.pkr.hcl
```

### Progressive Validation Pipeline

```yaml
name: Build, Test, and Promote

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      ami_id: ${{ steps.build.outputs.ami_id }}
    steps:
      - uses: actions/checkout@v3
      
      - name: Build AMI
        id: build
        run: |
          AMI_ID=$(packer build -machine-readable io/packer/ | \
            grep 'artifact,0,id' | cut -d, -f6 | cut -d: -f2)
          echo "ami_id=$AMI_ID" >> $GITHUB_OUTPUT
  
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Boot Test
        run: |
          # Launch instance from AMI
          # Run validation tests
          # Terminate instance
      
      - name: Security Scan
        run: |
          # Scan AMI for vulnerabilities
          # Check compliance
  
  promote:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Tag AMI for Production
        run: |
          aws ec2 create-tags \
            --resources ${{ needs.build.outputs.ami_id }} \
            --tags Key=Environment,Value=production
      
      - name: Update HCP Packer Channel
        env:
          HCP_CLIENT_ID: ${{ secrets.HCP_CLIENT_ID }}
          HCP_CLIENT_SECRET: ${{ secrets.HCP_CLIENT_SECRET }}
        run: |
          packer hcp channel update production \
            --bucket golden-images \
            --iteration ${{ github.sha }}
```

## GitLab CI Examples

### Basic Pipeline

```yaml
stages:
  - validate
  - build
  - test
  - promote

variables:
  PACKER_VERSION: "1.9.4"
  PACKER_CACHE_DIR: "${CI_PROJECT_DIR}/.packer.d"

.packer-base:
  image: hashicorp/packer:${PACKER_VERSION}
  before_script:
    - mkdir -p ${PACKER_CACHE_DIR}
    - packer init io/packer/

validate:
  extends: .packer-base
  stage: validate
  script:
    - packer fmt -check io/packer/
    - packer validate io/packer/

build:
  extends: .packer-base
  stage: build
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - .packer.d/
  script:
    - packer build -timestamp-ui io/packer/
  artifacts:
    reports:
      dotenv: build.env
  only:
    - main
    - merge_requests

test:
  stage: test
  dependencies:
    - build
  script:
    - ./scripts/test-ami.sh $AMI_ID
  only:
    - main

promote:
  stage: promote
  dependencies:
    - build
  script:
    - aws ec2 create-tags --resources $AMI_ID --tags Key=Environment,Value=production
  only:
    - main
  when: manual
```

### Parallel Multi-Region Build

```yaml
stages:
  - build
  - replicate

build:
  image: hashicorp/packer:latest
  stage: build
  parallel:
    matrix:
      - REGION: us-east-1
      - REGION: us-west-2
      - REGION: eu-west-1
  script:
    - packer build -var "region=${REGION}" io/packer/template.pkr.hcl
  artifacts:
    reports:
      dotenv: build-${REGION}.env

replicate:
  stage: replicate
  dependencies:
    - build
  script:
    - ./scripts/replicate-ami.sh
  only:
    - main
```

## Jenkins Examples

### Declarative Pipeline

```groovy
pipeline {
    agent any
    
    parameters {
        choice(name: 'PLATFORM', choices: ['ubuntu-20.04', 'ubuntu-22.04', 'debian-11'], description: 'Platform to build')
        string(name: 'VERSION', defaultValue: '', description: 'Image version')
    }
    
    environment {
        PACKER_VERSION = '1.9.4'
        AWS_DEFAULT_REGION = 'us-east-1'
        PACKER_CACHE_DIR = "${WORKSPACE}/.packer.d"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    wget https://releases.hashicorp.com/io/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip
                    unzip -o packer_${PACKER_VERSION}_linux_amd64.zip
                    chmod +x packer
                    ./packer init io/packer/
                '''
            }
        }
        
        stage('Validate') {
            steps {
                sh './packer validate io/packer/'
            }
        }
        
        stage('Build') {
            steps {
                withCredentials([
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials'
                    ]
                ]) {
                    sh """
                        ./packer build \\
                            -var 'platform=${params.PLATFORM}' \\
                            -var 'version=${params.VERSION}' \\
                            io/packer/template.pkr.hcl
                    """
                }
            }
        }
        
        stage('Test') {
            steps {
                sh './scripts/test-ami.sh'
            }
        }
        
        stage('Promote') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Promote to production?'
                sh './scripts/promote-ami.sh'
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            slackSend color: 'good', message: "Build successful: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        }
        failure {
            slackSend color: 'danger', message: "Build failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        }
    }
}
```

## Optimization Strategies

### Conditional Builds

**Skip builds when unnecessary**:

```yaml
# GitHub Actions
on:
  push:
    paths:
      - 'io/packer/**'
      - 'scripts/**'
      - '.github/workflows/packer.yml'

# Only build if Packer-related files changed
```

```yaml
# GitLab CI
build:
  only:
    changes:
      - io/packer/**
      - scripts/**
```

### Artifact Reuse

**Pattern**: Build once, deploy many times

```yaml
build:
  runs-on: ubuntu-latest
  steps:
    - name: Build
      id: build
      run: packer build template.pkr.hcl
    
    - name: Save artifact ID
      run: echo "ami_id=$AMI_ID" >> artifact.env
    
    - name: Upload artifact metadata
      uses: actions/upload-artifact@v3
      with:
        name: build-metadata
        path: artifact.env

deploy-dev:
  needs: build
  runs-on: ubuntu-latest
  steps:
    - name: Download metadata
      uses: actions/download-artifact@v3
      with:
        name: build-metadata
    
    - name: Deploy to Dev
      run: terraform apply -var="ami_id=$AMI_ID"

deploy-prod:
  needs: [build, deploy-dev]
  runs-on: ubuntu-latest
  steps:
    - name: Download metadata
      uses: actions/download-artifact@v3
      with:
        name: build-metadata
    
    - name: Deploy to Prod
      run: terraform apply -var="ami_id=$AMI_ID"
```

### Build Time Reduction

**Strategies**:
1. **Use self-hosted runners** with persistent cache
2. **Parallelize independent builds** with matrix strategy
3. **Cache dependencies** between runs
4. **Use intermediate base images** for faster app builds
5. **Skip validation** on trusted branches (carefully)

### Resource Optimization

**Use appropriate runner sizes**:

```yaml
# GitHub Actions
jobs:
  build:
    runs-on: ubuntu-latest-4-core  # More cores for parallel operations

# GitLab CI
build:
  tags:
    - docker
    - large  # Use larger runner for builds
```

## Monitoring and Alerting

### Build Time Tracking

```yaml
- name: Track build time
  run: |
    START_TIME=$(date +%s)
    packer build template.pkr.hcl
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Send to monitoring system
    curl -X POST https://metrics.example.com/build-time \
      -d "duration=$DURATION&job=${{ github.job }}"
```

### Failure Notifications

```yaml
# Slack notification on failure
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Packer build failed'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Cost Tracking

```yaml
- name: Estimate build cost
  run: |
    # Calculate EC2 instance hours
    # Calculate EBS snapshot storage
    # Calculate data transfer
    # Post to cost tracking system
```

## Best Practices

1. **Version Packer** - Pin to specific version for reproducibility
2. **Validate before build** - Catch errors early
3. **Use HCP Packer** - Track image lineage and metadata
4. **Test AMIs** - Boot test, smoke test, security scan
5. **Conditional builds** - Only build when necessary
6. **Parallel execution** - Build multiple variants simultaneously
7. **Cache aggressively** - Cache plugins, dependencies, artifacts
8. **Monitor builds** - Track duration, failures, costs
9. **Separate concerns** - Base images vs. application images
10. **Automate promotion** - Pipeline-driven promotion to production

## Common Pipeline Anti-Patterns

**Anti-pattern**: Building on every commit
**Solution**: Build only on relevant file changes or schedule

**Anti-pattern**: Sequential multi-platform builds
**Solution**: Use parallel matrix strategy

**Anti-pattern**: No caching
**Solution**: Cache plugins, dependencies, build artifacts

**Anti-pattern**: Manual promotion steps
**Solution**: Automate with approval gates

**Anti-pattern**: Building and deploying in same job
**Solution**: Separate build and deploy stages

**Anti-pattern**: No validation or testing
**Solution**: Add validation, boot tests, security scans

**Anti-pattern**: Hardcoded credentials
**Solution**: Use secret management (GitHub Secrets, GitLab CI/CD variables)

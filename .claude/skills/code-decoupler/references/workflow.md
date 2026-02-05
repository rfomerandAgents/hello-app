# Decoupling Workflow Reference

This document provides a step-by-step workflow for decoupling a project repository into a genericized template.

## Pre-Requisites

Before starting the decoupling process:

### Source Repository

- [ ] Source directory exists and is accessible
- [ ] Source is a git repository
- [ ] Git status is clean (no uncommitted changes recommended)
- [ ] Key directories present (.claude/, adws/, io/terraform/)
- [ ] README.md exists and is comprehensive

### Target Repository

- [ ] Target directory path is valid
- [ ] Target directory is empty OR user confirms overwrite
- [ ] Target directory will be initialized as git repo
- [ ] Sufficient disk space available

### Tools

- [ ] Python 3.10+ installed
- [ ] Git command available
- [ ] Terraform CLI available (optional, for validation)
- [ ] Write permissions to target directory

## Workflow Steps

### Step 1: Source Validation

**Purpose**: Ensure source repository is valid and ready for decoupling.

**Actions**:
1. Check source directory exists
2. Verify it's a git repository: `git rev-parse --git-dir`
3. Check for key directories:
   - `.claude/` - Required
   - `adws/` - Recommended
   - `ipe/` - Optional
   - `io/terraform/` - Optional
4. Check for uncommitted changes: `git status --porcelain`
5. Identify README.md file

**Validation**:
```python
source_path = Path(source_dir).resolve()
if not source_path.exists():
    raise ValueError(f"Source directory does not exist: {source_dir}")

if not (source_path / ".git").exists():
    raise ValueError(f"Source is not a git repository: {source_dir}")

if not (source_path / ".claude").exists():
    raise ValueError(f"Source does not have .claude/ directory: {source_dir}")
```

**Output**: Validation report with warnings for missing optional directories.

---

### Step 2: Target Preparation

**Purpose**: Prepare target directory for receiving decoupled content.

**Actions**:
1. Create target directory if it doesn't exist
2. Check if target is empty
3. If not empty, prompt user for confirmation:
   - "Target directory is not empty. Overwrite? (yes/no)"
   - If no, exit
   - If yes, continue with warning
4. Initialize git repository in target: `git init`
5. Create initial commit (empty): `git commit --allow-empty -m "Initial commit"`

**Validation**:
```python
target_path = Path(target_dir).resolve()
target_path.mkdir(parents=True, exist_ok=True)

if list(target_path.iterdir()):
    if not confirm("Target directory is not empty. Overwrite?"):
        sys.exit(0)
    # Optionally backup existing content
```

**Output**: Initialized git repository in target directory.

---

### Step 3: Directory Copying (Full Copy Pattern)

**Purpose**: Copy reusable automation and infrastructure code.

**Directories**:
- `.claude/commands/`
- `.claude/agents/`
- `.claude/hooks/`
- `.claude/skills/`
- `adws/`
- `app_docs/`
- `ipe/`
- `scripts/`
- `triggers/`
- `mcp/`

**Actions**:
```python
import shutil

FULL_COPY_DIRS = [
    '.claude/commands',
    '.claude/agents',
    '.claude/hooks',
    '.claude/skills',
    'adws',
    'app_docs',
    'ipe',
    'scripts',
    'triggers',
    'mcp',
]

for dir_name in FULL_COPY_DIRS:
    src = source_path / dir_name
    dst = target_path / dir_name

    if src.exists():
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"✓ Copied {dir_name}")
        else:
            print(f"⚠ Skipping {dir_name} (not a directory)")
    else:
        print(f"⚠ Skipping {dir_name} (not found in source)")
```

**Exclusions**:
- `__pycache__/` directories
- `.venv/` directories
- `.pytest_cache/` directories
- `*.pyc` files
- `.DS_Store` files

**Output**: Full copy of reusable code directories.

---

### Step 4: Directory Creation (Structure Only Pattern)

**Purpose**: Create empty directory structures for project-specific content.

**Directories**:
- `app/`
- `ipe_logs/`
- `logs/`
- `specs/` (with subdirectories)
- `agents/`
- `trees/`

**Actions**:
```python
STRUCTURE_ONLY_DIRS = [
    'app',
    'ipe_logs',
    'logs',
    'agents',
    'trees',
]

SPECS_SUBDIRS = [
    'specs/high-level',
    'specs/medium-level',
    'specs/low-level',
]

# Create empty directories with .gitkeep
for dir_name in STRUCTURE_ONLY_DIRS:
    dst = target_path / dir_name
    dst.mkdir(parents=True, exist_ok=True)
    (dst / '.gitkeep').touch()
    print(f"✓ Created empty directory {dir_name}")

# Create specs subdirectories
for dir_name in SPECS_SUBDIRS:
    dst = target_path / dir_name
    dst.mkdir(parents=True, exist_ok=True)
    (dst / '.gitkeep').touch()
    print(f"✓ Created specs subdirectory {dir_name}")

# Create specs README
specs_readme = target_path / 'specs' / 'README.md'
specs_readme.write_text(SPECS_README_CONTENT)
```

**Output**: Empty directory structures with .gitkeep files.

---

### Step 5: Terraform Scaffolding

**Purpose**: Generate generic Terraform infrastructure templates.

**Actions**:
```python
terraform_dir = target_path / 'terraform'
terraform_dir.mkdir(parents=True, exist_ok=True)

# Create main Terraform files
files_to_create = {
    'main.tf': MAIN_TF_TEMPLATE,
    'variables.tf': VARIABLES_TF_TEMPLATE,
    'outputs.tf': OUTPUTS_TF_TEMPLATE,
    'terraform.tf': TERRAFORM_TF_TEMPLATE,
    '.gitignore': TERRAFORM_GITIGNORE,
    'README.md': TERRAFORM_README,
}

for filename, content in files_to_create.items():
    file_path = terraform_dir / filename
    file_path.write_text(content)
    print(f"✓ Created io/terraform/{filename}")

# Create packer subdirectory
packer_dir = terraform_dir / 'packer'
packer_dir.mkdir(exist_ok=True)

packer_files = {
    'app.pkr.hcl': PACKER_TEMPLATE,
    'scripts/install-nodejs.sh': INSTALL_NODEJS_SCRIPT,
    'scripts/install-nginx.sh': INSTALL_NGINX_SCRIPT,
    'scripts/deploy-app.sh': DEPLOY_APP_SCRIPT,
}

for filename, content in packer_files.items():
    file_path = packer_dir / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    if filename.endswith('.sh'):
        file_path.chmod(0o755)
    print(f"✓ Created io/terraform/io/packer/{filename}")

# Create scripts subdirectory
scripts_dir = terraform_dir / 'scripts'
scripts_dir.mkdir(exist_ok=True)

script_files = {
    'build-ami.sh': BUILD_AMI_SCRIPT,
    'deploy.sh': DEPLOY_SCRIPT,
    'destroy.sh': DESTROY_SCRIPT,
}

for filename, content in script_files.items():
    file_path = scripts_dir / filename
    file_path.write_text(content)
    file_path.chmod(0o755)
    print(f"✓ Created io/terraform/scripts/{filename}")
```

**Output**: Complete Terraform scaffolding with generic templates.

---

### Step 6: File Genericization

**Purpose**: Transform project-specific files to use placeholders.

#### README.md Transformation

**Actions**:
```python
import re

def genericize_readme(source_readme, target_readme):
    content = source_readme.read_text()

    # Replacements
    replacements = {
        '{{PROJECT_NAME}}': '{{PROJECT_NAME}}',
        '{{PROJECT_DOMAIN}}': '{{DOMAIN}}',
        '{{PROJECT_SLUG}}': '{{PROJECT_NAME_SLUG}}',
        'Miniature Mediterranean Items': '{{PROJECT_DESCRIPTION}}',
        'https://github.com/your-username/{{PROJECT_DOMAIN}}': '{{GITHUB_REPO_URL}}',
        'your-username': '{{GITHUB_OWNER}}',
        'Port 3000': '{{APP_PORT}}',
        'Port 18333': '{{CONTROL_PLANE_PORT}}',
    }

    for find, replace in replacements.items():
        content = content.replace(find, replace)

    # Remove project-specific sections
    # (This would be more sophisticated with proper markdown parsing)

    target_readme.write_text(content)
    print("✓ Genericized README.md")
```

#### settings.json Transformation

**Actions**:
```python
import json

def genericize_settings(source_settings, target_settings):
    with source_settings.open('r') as f:
        settings = json.load(f)

    # Remove any secrets (if present)
    if 'apiKeys' in settings:
        del settings['apiKeys']
    if 'secrets' in settings:
        del settings['secrets']

    # Preserve permissions and hooks
    # Already generic, no transformation needed

    with target_settings.open('w') as f:
        json.dump(settings, f, indent=2)

    print("✓ Genericized .claude/settings.json")
```

#### .gitignore Copy

**Actions**:
```python
def copy_gitignore(source_gitignore, target_gitignore):
    if source_gitignore.exists():
        shutil.copy2(source_gitignore, target_gitignore)
    else:
        # Use default .gitignore template
        target_gitignore.write_text(DEFAULT_GITIGNORE)

    print("✓ Copied .gitignore")
```

**Output**: Genericized configuration files.

---

### Step 7: Git Commit Preparation

**Purpose**: Prepare target repository for initial commit.

**Actions**:
```python
import subprocess

def prepare_git_commit(target_path):
    # Add all files
    subprocess.run(['git', 'add', '.'], cwd=target_path, check=True)

    # Create initial commit
    commit_message = """Initial commit - Genericized template

This template was created by decoupling reusable automation patterns.

Components:
- AI Developer Workflow (ADW) system
- Infrastructure Platform Engineer (IPE) workflows
- Claude Code CLI integration
- GitHub Actions deployment pipelines
- Terraform infrastructure templates
"""

    subprocess.run(
        ['git', 'commit', '-m', commit_message],
        cwd=target_path,
        check=True
    )

    print("✓ Created initial git commit")
```

**Output**: Target repository ready for validation.

---

### Step 8: Validation

**Purpose**: Ensure template quality and completeness.

**Actions**:
Run validation script (see validate_template.py):

```bash
python .claude/skills/code-decoupler/scripts/validate_template.py /path/to/target
```

**Checks**:
1. Required directories exist
2. .claude/settings.json is valid JSON
3. README.md has no project-specific content
4. Terraform files are syntactically valid (if terraform available)
5. No secrets or API tokens present
6. .gitignore includes necessary patterns
7. Git repository initialized
8. No broken symlinks

**Output**: Validation report with pass/fail for each check.

---

### Step 9: Documentation

**Purpose**: Document customization requirements for template users.

**Actions**:
Create TEMPLATE_USAGE.md:

```markdown
# Template Usage Guide

## Quick Start

1. Clone this template
2. Replace placeholders (see below)
3. Configure environment variables
4. Customize Terraform variables
5. Add your application code

## Placeholders to Replace

Search and replace throughout the repository:

- `{{PROJECT_NAME}}` - Your project name
- `{{DOMAIN}}` - Your domain name
- `{{PROJECT_DESCRIPTION}}` - Brief description
- `{{GITHUB_REPO_URL}}` - Your GitHub repo URL
- `{{GITHUB_OWNER}}` - Your GitHub username
- `{{AWS_ACCOUNT_ID}}` - Your AWS account ID
- `{{APP_PORT}}` - Application port
- `{{CONTROL_PLANE_PORT}}` - Control plane port

## Configuration Files

- `.env` - Copy from `.env.example` and set values
- `io/terraform/terraform.tfvars` - Set infrastructure variables
- `CLAUDE.md` - Add project-specific Claude instructions

## Next Steps

- Review README.md and update as needed
- Test ADW workflows with a sample issue
- Build AMI with Packer
- Deploy infrastructure with Terraform
```

**Output**: Complete template ready for use.

---

## Post-Decoupling Checklist

After completing all steps:

- [ ] All required directories exist
- [ ] Full copy directories have all files
- [ ] Structure-only directories have .gitkeep files
- [ ] Terraform scaffolding is complete and valid
- [ ] README.md is genericized
- [ ] settings.json has no secrets
- [ ] .gitignore is comprehensive
- [ ] Git repository initialized with initial commit
- [ ] Validation script passes all checks
- [ ] TEMPLATE_USAGE.md created
- [ ] No project-specific content leaked
- [ ] Template tested with sample customization

## Error Recovery

If decoupling fails partway through:

### Rollback

```bash
# If target is a new directory
rm -rf /path/to/target

# If target had existing content
# Restore from backup (if created)
```

### Retry

```bash
# Clear target and re-run
rm -rf /path/to/target/*
python decouple.py --source /path/to/source --target /path/to/target
```

### Partial Recovery

If some steps succeeded:
1. Identify which step failed
2. Manually complete remaining steps
3. Run validation to check completeness

## Advanced Options

### Dry Run Mode

Preview actions without making changes:

```bash
python decouple.py --source /path/to/source --target /path/to/target --dry-run
```

### Verbose Output

See detailed progress:

```bash
python decouple.py --source /path/to/source --target /path/to/target --verbose
```

### Selective Decoupling

Decouple only specific components:

```bash
python decouple.py --source /path/to/source --target /path/to/target --include adws,ipe
```

## Timeline

Typical decoupling timeline:

- **Step 1-2**: 1-2 minutes (validation and setup)
- **Step 3**: 2-5 minutes (full copy directories)
- **Step 4**: <1 minute (create empty structures)
- **Step 5**: 1-2 minutes (Terraform scaffolding)
- **Step 6**: 2-3 minutes (file genericization)
- **Step 7**: <1 minute (git commit)
- **Step 8**: 1-2 minutes (validation)
- **Step 9**: <1 minute (documentation)

**Total**: 10-15 minutes for typical repository.

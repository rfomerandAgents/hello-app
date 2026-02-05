# Move Terraform and Packer Code to io/ Directory

## Overview

**Task**: Move all terraform and packer code to a new `io/` directory and update all IPE scripts to reference the new location
**Type**: refactor
**Scope**: large (50+ files to modify)
**Estimated Steps**: 18

---

## Context Analysis

### Codebase Findings

| Finding | Details |
|---------|---------|
| Current terraform location | `terraform/` (14 files including `main.tf`, `variables.tf`, `outputs.tf`, etc.) |
| Current packer location | `packer/` (5 files including `app.pkr.hcl` and scripts) |
| Nested packer in terraform | `terraform/packer/` also exists (referenced in GitHub workflows) |
| IPE references to terraform | 40+ references across 8 Python files in `ipe/` |
| Default terraform_dir value | `"terraform"` hardcoded in multiple locations |
| GitHub workflow references | `infrastructure-deploy.yml` references both `terraform/` and `terraform/packer/` |

### Files to Modify

| Category | Files | Action | Description |
|----------|-------|--------|-------------|
| Directories | `terraform/`, `packer/` | MOVE | Move to `io/terraform/` and `io/packer/` |
| IPE Python modules | 8 files | MODIFY | Update default paths from `"terraform"` to `"io/terraform"` |
| IPE modules | `terraform_worktree.py`, `terraform_ops.py` | MODIFY | Update hardcoded `"terraform"` references |
| GitHub workflows | 1 file | MODIFY | Update working directories |
| Shell scripts | 3 files | MODIFY | Update terraform/packer paths |
| Documentation | ~35 files | MODIFY | Update path references |
| Skills | ~12 files | MODIFY | Update example paths |

### Tech Stack Context

- **Framework**: Python 3.10+ (IPE/ADW), Terraform, Packer
- **Language**: Python, HCL, Bash, YAML
- **Build tools**: uv, Terraform CLI, Packer CLI
- **Key patterns**: `terraform_dir` variable passed through IPE workflow state

---

## Implementation Roadmap

### Phase 1: Create Directory Structure and Move Files

#### Step 1.1: Create io/ directory structure

- **Location**: Repository root
- **Action**: Create the `io/` directory
- **Details**:
  ```bash
  mkdir -p io
  ```
- **Depends on**: None
- **Verify**: `ls io/` shows empty directory

#### Step 1.2: Move terraform/ to io/terraform/

- **Location**: Repository root
- **Action**: Use git mv to preserve history
- **Details**:
  ```bash
  git mv terraform io/terraform
  ```
- **Depends on**: Step 1.1
- **Verify**: `ls io/terraform/` shows `main.tf`, `variables.tf`, etc.

#### Step 1.3: Move packer/ to io/packer/

- **Location**: Repository root
- **Action**: Use git mv to preserve history
- **Details**:
  ```bash
  git mv packer io/packer
  ```
- **Depends on**: Step 1.1
- **Verify**: `ls io/packer/` shows `app.pkr.hcl`, `scripts/`, etc.

#### Step 1.4: Handle nested terraform/packer reference

- **Location**: `io/terraform/packer/` (if exists after move)
- **Action**: Check if `terraform/packer/` exists and decide handling
- **Details**:
  - If `io/terraform/packer/` exists after move, it may need to reference `io/packer/`
  - Create symlink or update references as needed
- **Depends on**: Step 1.2, Step 1.3
- **Verify**: Packer builds can find their scripts

### Phase 2: Update IPE Python Modules

#### Step 2.1: Update ipe_test_iso.py default terraform_dir

- **Location**: `ipe/ipe_test_iso.py:77,131,170,348`
- **Action**: Change default value from `"terraform"` to `"io/terraform"`
- **Details**:
  ```python
  # Line 77, 131, 170:
  terraform_dir: str = "io/terraform",

  # Line 348:
  terraform_dir = state.get("terraform_dir") or "io/terraform"
  ```
- **Depends on**: Phase 1
- **Verify**: `grep -n '"terraform"' ipe/ipe_test_iso.py` shows no bare `"terraform"` defaults

#### Step 2.2: Update ipe_build_iso.py default terraform_dir

- **Location**: `ipe/ipe_build_iso.py:199`
- **Action**: Change default value from `"terraform"` to `"io/terraform"`
- **Details**:
  ```python
  terraform_dir = state.get("terraform_dir") or "io/terraform"
  ```
- **Depends on**: Phase 1
- **Verify**: `grep -n '"terraform"' ipe/ipe_build_iso.py` shows updated path

#### Step 2.3: Update ipe_destroy.py terraform path

- **Location**: `ipe/ipe_destroy.py:314`
- **Action**: Change hardcoded path from `"terraform"` to `"io/terraform"`
- **Details**:
  ```python
  terraform_dir = repo_root / "io/terraform"
  ```
- **Depends on**: Phase 1
- **Verify**: `grep -n '"terraform"' ipe/ipe_destroy.py` shows updated path

#### Step 2.4: Update terraform_worktree.py paths

- **Location**: `ipe/ipe_modules/terraform_worktree.py:39,122,154`
- **Action**: Update all `os.path.join(worktree_path, "terraform")` to `os.path.join(worktree_path, "io/terraform")`
- **Details**:
  ```python
  # Line 39, 122:
  terraform_dir = os.path.join(worktree_path, "io/terraform")

  # Line 154 (get_terraform_directory function):
  return os.path.join(worktree_path, "io/terraform")
  ```
- **Depends on**: Phase 1
- **Verify**: `grep -n '"terraform"' ipe/ipe_modules/terraform_worktree.py` shows only `"io/terraform"`

#### Step 2.5: Update ipe_git_worktree.py path check

- **Location**: `ipe/ipe_modules/ipe_git_worktree.py:186`
- **Action**: Update terraform directory check
- **Details**:
  ```python
  terraform_dir = path / "io" / "terraform"
  ```
- **Depends on**: Phase 1
- **Verify**: Function still correctly identifies IPE worktrees

#### Step 2.6: Update ipe_data_types.py default comment

- **Location**: `ipe/ipe_modules/ipe_data_types.py:224`
- **Action**: Update comment to reflect new path
- **Details**:
  ```python
  terraform_dir: Optional[str] = None  # NEW: Terraform directory path (default: io/terraform)
  ```
- **Depends on**: Phase 1
- **Verify**: Comment is updated

#### Step 2.7: Update ipe_state.py if needed

- **Location**: `ipe/ipe_modules/ipe_state.py`
- **Action**: Review and update any terraform_dir defaults
- **Depends on**: Phase 1
- **Verify**: State management handles new path correctly

#### Step 2.8: Update README.md terraform_dir example

- **Location**: `ipe/README.md:217`
- **Action**: Update example path
- **Details**:
  ```json
  "terraform_dir": "io/terraform/environments/dev",
  ```
- **Depends on**: Phase 1
- **Verify**: Documentation reflects new structure

### Phase 3: Update GitHub Workflows

#### Step 3.1: Update infrastructure-deploy.yml terraform paths

- **Location**: `.github/workflows/infrastructure-deploy.yml:126,138,147,157,248,250,252,254,256,258,261,267,270,274-275`
- **Action**: Change all `working-directory: terraform` to `working-directory: io/terraform`
- **Details**:
  - Update Packer cache path: `terraform/packer/.packer.lock.hcl` → `io/packer/.packer.lock.hcl`
  - Update Packer init working dir: `terraform/packer` → `io/packer`
  - Update Packer build working dir: `terraform/packer` → `io/packer`
  - Update all Terraform working dirs: `terraform` → `io/terraform`
- **Depends on**: Phase 1
- **Verify**: `grep -n "terraform" .github/workflows/infrastructure-deploy.yml` shows only `io/terraform` or `io/packer`

### Phase 4: Update Shell Scripts

#### Step 4.1: Update manage-ami.sh paths

- **Location**: `scripts/manage-ami.sh`
- **Action**: Update any terraform/packer path references
- **Depends on**: Phase 1
- **Verify**: Script references `io/terraform` and `io/packer`

#### Step 4.2: Update manual-build-and-deploy.sh paths

- **Location**: `scripts/manual-build-and-deploy.sh`
- **Action**: Update any terraform/packer path references
- **Depends on**: Phase 1
- **Verify**: Script references `io/terraform` and `io/packer`

#### Step 4.3: Update io/terraform/scripts/*.sh paths

- **Location**: `io/terraform/scripts/build-ami.sh`, `deploy.sh`, `destroy.sh`
- **Action**: Update internal path references if any
- **Depends on**: Phase 1
- **Verify**: Scripts work from new location

### Phase 5: Update Documentation and Skills

#### Step 5.1: Batch update documentation files

- **Location**: Multiple `.md` files in `.claude/commands/`, `.claude/skills/`, `app_docs/`
- **Action**: Replace `terraform/` with `io/terraform/` and `packer/` with `io/packer/`
- **Details**:
  ```bash
  # Use sed for batch replacement
  find . -name "*.md" -type f -exec sed -i '' 's|terraform/|io/terraform/|g' {} \;
  find . -name "*.md" -type f -exec sed -i '' 's|packer/|io/packer/|g' {} \;
  ```
- **Depends on**: Phase 1
- **Verify**: `grep -r "terraform/" --include="*.md" .` shows only `io/terraform/`

#### Step 5.2: Update CLAUDE.md

- **Location**: `CLAUDE.md`
- **Action**: Update terraform documentation reference
- **Details**:
  ```markdown
  - [Terraform Documentation](io/terraform/README.md)
  ```
- **Depends on**: Phase 1
- **Verify**: Links are correct

#### Step 5.3: Update README.md

- **Location**: `README.md`
- **Action**: Update any terraform/packer references
- **Depends on**: Phase 1
- **Verify**: Documentation reflects new structure

#### Step 5.4: Update skills Python scripts

- **Location**: `.claude/skills/*/scripts/*.py` (decouple.py, validate_template.py, etc.)
- **Action**: Update terraform/packer path references
- **Depends on**: Phase 1
- **Verify**: `grep -r "terraform/" --include="*.py" .claude/` shows only `io/terraform/`

---

## Critical Considerations

### Security
- Ensure `.gitignore` rules in `terraform/` are preserved in `io/terraform/`
- Verify no secrets are exposed during the move
- Confirm terraform state references don't break

### Performance
- Use `git mv` to preserve file history
- Batch documentation updates with `sed` for efficiency

### Edge Cases
- **Worktree paths**: IPE creates worktrees that clone the repo - the new structure must work in worktrees
- **Relative imports**: Some scripts may use relative paths that break after move
- **Terraform state**: Remote state in TFC should not be affected, but verify
- **Packer manifests**: `packer-manifest.json` path in workflows may need updating

### Breaking Changes
- Any existing IPE workflows in progress will fail after this change
- External tools referencing `terraform/` will break
- CI/CD pipelines need to be updated atomically with the code change

---

## Testing Strategy

### Required Tests
- [ ] `terraform init` succeeds in `io/terraform/`
- [ ] `terraform validate` succeeds in `io/terraform/`
- [ ] `packer init` succeeds in `io/packer/`
- [ ] `packer validate` succeeds in `io/packer/`
- [ ] IPE Python imports still work
- [ ] GitHub workflow syntax is valid

### Validation Commands
```bash
# Verify directory structure
ls -la io/terraform/ io/packer/

# Verify terraform works
cd io/terraform && terraform init && terraform validate

# Verify packer works
cd io/packer && packer init app.pkr.hcl && packer validate app.pkr.hcl

# Verify no old paths remain in Python
grep -r '"terraform"' ipe/ --include="*.py" | grep -v "io/terraform"

# Verify no old paths in workflows
grep -r "working-directory: terraform" .github/

# Verify Python syntax
find ipe -name "*.py" -exec python -m py_compile {} \;
```

---

## Verification Checklist

- [ ] `terraform/` directory no longer exists at root
- [ ] `packer/` directory no longer exists at root
- [ ] `io/terraform/` contains all terraform files
- [ ] `io/packer/` contains all packer files
- [ ] All IPE Python files reference `io/terraform` as default
- [ ] GitHub workflow references `io/terraform` and `io/packer`
- [ ] All documentation references updated
- [ ] `terraform init` works in new location
- [ ] `packer validate` works in new location
- [ ] No broken imports in IPE modules
- [ ] Git history preserved for moved files

---

## Implementation Tips

- **Start with**: Phase 1 (directory moves) - this establishes the new structure
- **Key insight**: The `terraform_dir` variable in IPE state allows runtime override, so updating defaults is sufficient
- **Common pitfall**: Don't use `mv` - use `git mv` to preserve history
- **Pattern to follow**: The `terraform_dir` pattern in `ipe_test_iso.py` shows how the default is used

---

## Rollback Strategy

If implementation needs to be reverted:

1. Revert the git commit
2. The `git mv` operations are fully reversible

```bash
# Git commands for rollback
git revert HEAD
# Or for multiple commits:
git reset --hard <commit-before-changes>
```

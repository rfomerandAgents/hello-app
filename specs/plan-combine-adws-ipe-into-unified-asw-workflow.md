# Combine ADWS and IPE into Unified ASW Workflow

## Overview

**Task**: Merge separate `adws/` (AI Developer Workflow System) and `ipe/` (Infrastructure Platform Engineer) workflows into a unified `asw/` (Agentic Software Workflow) system with `asw_app_*` for application workflows and `asw_io_*` for infrastructure workflows
**Type**: refactor
**Scope**: large (200+ files affected)
**Estimated Steps**: 45

---

## Context Analysis

### Codebase Findings

| Finding | Details |
|---------|---------|
| ADWS files | 49 Python files in `adws/` (~8,500 lines), plus `adw_modules/`, `adw_tests/`, `adw_triggers/` |
| IPE files | 57 Python files in `ipe/` (~15,600 lines), plus `ipe_modules/`, `ipe_tests/`, `ipe_triggers/` |
| Shared modules | `adw_modules/` and `ipe_modules/` have parallel structures (agent, state, github, git_ops, etc.) |
| Entry points | `adw_sdlc_iso.py` and `ipe_sdlc_iso.py` are main orchestrators |
| Documentation | 36+ markdown files reference `adws/` or `ipe/` paths |
| Claude commands | 30+ commands reference `adw_` or `ipe_` patterns |
| Import patterns | Cross-imports between modules: `from adws.adw_modules.*` and `from ipe.ipe_modules.*` |

### Current Directory Structure

```
adws/
├── adw_*.py              # 17 workflow scripts
├── adw_modules/          # 10 shared modules
├── adw_tests/            # 16 test files
├── adw_triggers/         # 3 trigger files
└── README.md

ipe/
├── ipe_*.py              # 22 workflow scripts
├── ipe_modules/          # 15 shared modules
├── ipe_tests/            # 14 test files
├── ipe_triggers/         # 3 trigger files
└── README.md
```

### Target Directory Structure

```
asw/
├── app/                  # Former adws/ (Application workflows)
│   ├── asw_app_*.py      # Renamed from adw_*.py
│   └── README.md
├── io/                   # Former ipe/ (Infrastructure workflows)
│   ├── asw_io_*.py       # Renamed from ipe_*.py
│   └── README.md
├── modules/              # Unified shared modules
│   ├── __init__.py
│   ├── agent.py          # Merged from both
│   ├── state.py          # Merged from both
│   ├── github.py         # Merged from both
│   ├── git_ops.py        # Merged from both
│   ├── workflow_ops.py   # Merged from both
│   ├── worktree_ops.py   # Merged from both
│   ├── utils.py          # Merged from both
│   ├── data_types.py     # Merged from both
│   ├── logging.py        # From ipe (enhanced)
│   ├── terraform_ops.py  # IO-specific
│   ├── terraform_worktree.py  # IO-specific
│   ├── packer_ops.py     # IO-specific
│   ├── ami_versioning.py # IO-specific
│   ├── aws_ops.py        # IO-specific
│   ├── r2_uploader.py    # App-specific
│   └── cache.py          # App-specific
├── tests/                # Unified test suite
│   ├── app/              # Application tests
│   └── io/               # Infrastructure tests
├── triggers/             # Unified triggers
│   ├── app/              # Application triggers
│   └── io/               # Infrastructure triggers
└── README.md             # Unified documentation
```

### Files to Modify (Summary)

| Category | Count | Action |
|----------|-------|--------|
| ADWS Python files | 49 | RENAME to `asw/app/asw_app_*` |
| IPE Python files | 57 | RENAME to `asw/io/asw_io_*` |
| Module files | 25 | MERGE into `asw/modules/` |
| Test files | 30 | MOVE to `asw/tests/` |
| Trigger files | 6 | MOVE to `asw/triggers/` |
| Claude commands | 30 | UPDATE references |
| Documentation | 40+ | UPDATE paths and references |
| Skills | 10+ | UPDATE references |

### Tech Stack Context

- **Framework**: Python 3.10+
- **Language**: Python
- **Build tools**: uv (package manager), pytest
- **Key libraries**: pydantic, python-dotenv, claude-agent-sdk

---

## Implementation Roadmap

### Phase 1: Create New Directory Structure

#### Step 1.1: Create asw/ directory hierarchy

- **Location**: Repository root
- **Action**: Create the new unified directory structure
- **Details**:
  ```bash
  mkdir -p asw/app asw/io asw/modules asw/tests/app asw/tests/io asw/triggers/app asw/triggers/io
  ```
- **Depends on**: None
- **Verify**: `ls -R asw/` shows all directories

#### Step 1.2: Create asw/modules/__init__.py

- **Location**: `asw/modules/__init__.py`
- **Action**: Create module initialization file
- **Details**:
  ```python
  """ASW - Agentic Software Workflow unified modules."""
  ```
- **Depends on**: Step 1.1
- **Verify**: File exists

### Phase 2: Merge Shared Modules

#### Step 2.1: Merge agent.py modules

- **Location**: `asw/modules/agent.py`
- **Action**: Combine `adw_modules/agent.py` and `ipe_modules/ipe_agent.py`
- **Details**:
  - Take the more complete implementation (likely IPE)
  - Ensure both ADW and IPE functionality is preserved
  - Update imports to use `asw.modules`
- **Depends on**: Step 1.2
- **Verify**: `python -c "from asw.modules.agent import *"` works

#### Step 2.2: Merge state.py modules

- **Location**: `asw/modules/state.py`
- **Action**: Combine `adw_modules/state.py` and `ipe_modules/ipe_state.py`
- **Details**:
  - Create unified `ASWState` class
  - Support both `asw_id` (replacing `adw_id` and `ipe_id`)
  - Preserve state file format compatibility
- **Depends on**: Step 1.2
- **Verify**: State can be loaded and saved

#### Step 2.3: Merge github.py modules

- **Location**: `asw/modules/github.py`
- **Action**: Combine GitHub integration modules
- **Depends on**: Step 1.2
- **Verify**: GitHub operations work

#### Step 2.4: Merge git_ops.py modules

- **Location**: `asw/modules/git_ops.py`
- **Action**: Combine git operations modules
- **Depends on**: Step 1.2
- **Verify**: Git operations work

#### Step 2.5: Merge workflow_ops.py modules

- **Location**: `asw/modules/workflow_ops.py`
- **Action**: Combine workflow operations
- **Details**:
  - Rename `ensure_adw_id` → `ensure_asw_app_id`
  - Rename `ensure_ipe_id` → `ensure_asw_io_id`
  - Add generic `ensure_asw_id` function
- **Depends on**: Step 1.2
- **Verify**: Workflow ID generation works

#### Step 2.6: Merge worktree_ops.py modules

- **Location**: `asw/modules/worktree_ops.py`
- **Action**: Combine worktree operations
- **Depends on**: Step 1.2
- **Verify**: Worktree creation works

#### Step 2.7: Merge utils.py modules

- **Location**: `asw/modules/utils.py`
- **Action**: Combine utility functions
- **Depends on**: Step 1.2
- **Verify**: Utility functions work

#### Step 2.8: Merge data_types.py modules

- **Location**: `asw/modules/data_types.py`
- **Action**: Combine data type definitions
- **Details**:
  - Unify `ADWState` and `IPEState` into `ASWState`
  - Keep domain-specific fields where needed
- **Depends on**: Step 1.2
- **Verify**: Data types can be instantiated

#### Step 2.9: Move logging.py (IPE enhanced)

- **Location**: `asw/modules/logging.py`
- **Action**: Move IPE's enhanced logging module
- **Depends on**: Step 1.2
- **Verify**: Logging works

#### Step 2.10: Move IO-specific modules

- **Location**: `asw/modules/`
- **Action**: Move terraform, packer, AWS modules
- **Details**:
  - `terraform_ops.py` → `asw/modules/terraform_ops.py`
  - `terraform_worktree.py` → `asw/modules/terraform_worktree.py`
  - `ipe_packer_ops.py` → `asw/modules/packer_ops.py`
  - `ipe_ami_versioning.py` → `asw/modules/ami_versioning.py`
  - `ipe_aws_ops.py` → `asw/modules/aws_ops.py`
  - `ipe_git_worktree.py` → `asw/modules/io_git_worktree.py`
- **Depends on**: Step 1.2
- **Verify**: IO-specific imports work

#### Step 2.11: Move App-specific modules

- **Location**: `asw/modules/`
- **Action**: Move application-specific modules
- **Details**:
  - `r2_uploader.py` → `asw/modules/r2_uploader.py`
  - `cache.py` → `asw/modules/cache.py`
- **Depends on**: Step 1.2
- **Verify**: App-specific imports work

### Phase 3: Rename and Move Application (ADW) Workflow Files

#### Step 3.1: Move and rename ADW SDLC orchestrator

- **Location**: `adws/adw_sdlc_iso.py` → `asw/app/asw_app_sdlc_iso.py`
- **Action**: Rename file and update internal references
- **Details**:
  - Change `adw_` prefix to `asw_app_`
  - Update imports to `from asw.modules.*`
  - Update docstrings to reference ASW
- **Depends on**: Phase 2
- **Verify**: `python asw/app/asw_app_sdlc_iso.py --help` works

#### Step 3.2: Move and rename ADW workflow files (batch)

- **Location**: `adws/adw_*.py`
- **Action**: Rename all ADW workflow files
- **Details**:
  | Original | New |
  |----------|-----|
  | `adw_plan_iso.py` | `asw_app_plan_iso.py` |
  | `adw_build_iso.py` | `asw_app_build_iso.py` |
  | `adw_test_iso.py` | `asw_app_test_iso.py` |
  | `adw_review_iso.py` | `asw_app_review_iso.py` |
  | `adw_document_iso.py` | `asw_app_document_iso.py` |
  | `adw_ship_iso.py` | `asw_app_ship_iso.py` |
  | `adw_patch_iso.py` | `asw_app_patch_iso.py` |
  | `adw_prompt.py` | `asw_app_prompt.py` |
  | `adw_slash_command.py` | `asw_app_slash_command.py` |
  | `adw_chore_implement.py` | `asw_app_chore_implement.py` |
  | `adw_sdlc_zte_iso.py` | `asw_app_sdlc_zte_iso.py` |
  | etc. | etc. |
- **Depends on**: Step 3.1
- **Verify**: All files renamed

#### Step 3.3: Update imports in all app workflow files

- **Location**: `asw/app/*.py`
- **Action**: Update all import statements
- **Details**:
  ```python
  # Old
  from adw_modules.workflow_ops import ensure_adw_id
  from adw_modules.utils import parse_cache_flag

  # New
  from asw.modules.workflow_ops import ensure_asw_app_id
  from asw.modules.utils import parse_cache_flag
  ```
- **Depends on**: Step 3.2
- **Verify**: All imports resolve

### Phase 4: Rename and Move Infrastructure (IPE) Workflow Files

#### Step 4.1: Move and rename IPE SDLC orchestrator

- **Location**: `ipe/ipe_sdlc_iso.py` → `asw/io/asw_io_sdlc_iso.py`
- **Action**: Rename file and update internal references
- **Details**:
  - Change `ipe_` prefix to `asw_io_`
  - Update imports to `from asw.modules.*`
  - Update docstrings to reference ASW
- **Depends on**: Phase 2
- **Verify**: `python asw/io/asw_io_sdlc_iso.py --help` works

#### Step 4.2: Move and rename IPE workflow files (batch)

- **Location**: `ipe/ipe_*.py`
- **Action**: Rename all IPE workflow files
- **Details**:
  | Original | New |
  |----------|-----|
  | `ipe_plan_iso.py` | `asw_io_plan_iso.py` |
  | `ipe_build_iso.py` | `asw_io_build_iso.py` |
  | `ipe_test_iso.py` | `asw_io_test_iso.py` |
  | `ipe_review_iso.py` | `asw_io_review_iso.py` |
  | `ipe_document_iso.py` | `asw_io_document_iso.py` |
  | `ipe_ship_iso.py` | `asw_io_ship_iso.py` |
  | `ipe_deploy.py` | `asw_io_deploy.py` |
  | `ipe_destroy.py` | `asw_io_destroy.py` |
  | `ipe_build_ami_iso.py` | `asw_io_build_ami_iso.py` |
  | etc. | etc. |
- **Depends on**: Step 4.1
- **Verify**: All files renamed

#### Step 4.3: Update imports in all io workflow files

- **Location**: `asw/io/*.py`
- **Action**: Update all import statements
- **Details**:
  ```python
  # Old
  from ipe.ipe_modules.ipe_workflow_ops import ensure_ipe_id
  from ipe.ipe_modules.terraform_ops import *

  # New
  from asw.modules.workflow_ops import ensure_asw_io_id
  from asw.modules.terraform_ops import *
  ```
- **Depends on**: Step 4.2
- **Verify**: All imports resolve

### Phase 5: Move Tests and Triggers

#### Step 5.1: Move ADW tests

- **Location**: `adws/adw_tests/` → `asw/tests/app/`
- **Action**: Move and rename test files
- **Details**:
  - Rename `test_*.py` files to use `asw_app_` references
  - Update imports
- **Depends on**: Phase 3
- **Verify**: `pytest asw/tests/app/` runs

#### Step 5.2: Move IPE tests

- **Location**: `ipe/ipe_tests/` → `asw/tests/io/`
- **Action**: Move and rename test files
- **Details**:
  - Rename `test_*.py` files to use `asw_io_` references
  - Update imports
- **Depends on**: Phase 4
- **Verify**: `pytest asw/tests/io/` runs

#### Step 5.3: Move ADW triggers

- **Location**: `adws/adw_triggers/` → `asw/triggers/app/`
- **Action**: Move trigger files
- **Depends on**: Phase 3
- **Verify**: Triggers can be imported

#### Step 5.4: Move IPE triggers

- **Location**: `ipe/ipe_triggers/` → `asw/triggers/io/`
- **Action**: Move trigger files
- **Depends on**: Phase 4
- **Verify**: Triggers can be imported

### Phase 6: Update Claude Commands

#### Step 6.1: Rename ADW-specific commands

- **Location**: `.claude/commands/`
- **Action**: Update command files that reference ADW
- **Details**:
  | Original | New |
  |----------|-----|
  | `classify_adw.md` | `classify_asw_app.md` |
  | `track_agentic_kpis.md` | Update references |
  | `feature.md` | Update to use `asw/app/` |
  | `bug.md` | Update to use `asw/app/` |
  | `chore.md` | Update to use `asw/app/` |
- **Depends on**: Phase 3
- **Verify**: Commands reference correct paths

#### Step 6.2: Rename IPE-specific commands

- **Location**: `.claude/commands/`
- **Action**: Update command files that reference IPE
- **Details**:
  | Original | New |
  |----------|-----|
  | `ipe_feature.md` | `asw_io_feature.md` |
  | `ipe_bug.md` | `asw_io_bug.md` |
  | `ipe_chore.md` | `asw_io_chore.md` |
  | `ipe_commit.md` | `asw_io_commit.md` |
  | `ipe_review.md` | `asw_io_review.md` |
  | `ipe_status.md` | `asw_io_status.md` |
  | `ipe_module.md` | `asw_io_module.md` |
  | `classify_ipe.md` | `classify_asw_io.md` |
- **Depends on**: Phase 4
- **Verify**: Commands reference correct paths

#### Step 6.3: Update shared commands

- **Location**: `.claude/commands/`
- **Action**: Update commands that reference both systems
- **Details**:
  - `classify_issue.md` - Update to route to `asw_app` or `asw_io`
  - `install.md` - Update installation paths
  - `prime.md` - Update project structure references
  - `health_check.md` - Update health check paths
- **Depends on**: Steps 6.1, 6.2
- **Verify**: Commands work correctly

### Phase 7: Update Documentation

#### Step 7.1: Create unified asw/README.md

- **Location**: `asw/README.md`
- **Action**: Create comprehensive documentation
- **Details**:
  - Document the unified ASW system
  - Explain `asw/app/` vs `asw/io/` distinction
  - Migration guide from old paths
- **Depends on**: Phase 5
- **Verify**: README is comprehensive

#### Step 7.2: Update CLAUDE.md

- **Location**: `CLAUDE.md`
- **Action**: Update project instructions
- **Details**:
  ```markdown
  ### For Application Code (ASW App)
  uv run asw/app/asw_app_sdlc_iso.py <issue-number>

  ### For Infrastructure Code (ASW IO)
  uv run asw/io/asw_io_sdlc_iso.py <issue-number>
  ```
- **Depends on**: Phase 5
- **Verify**: Instructions are correct

#### Step 7.3: Update main README.md

- **Location**: `README.md`
- **Action**: Update project documentation
- **Depends on**: Phase 5
- **Verify**: Documentation reflects new structure

#### Step 7.4: Update skills documentation

- **Location**: `.claude/skills/`
- **Action**: Update all skill files that reference adws/ or ipe/
- **Details**:
  - `adws-expert/` → `asw-expert/` (rename skill)
  - `adws-terraform-refactor/` → `asw-terraform-refactor/`
  - Update all path references in other skills
- **Depends on**: Phase 5
- **Verify**: Skills reference correct paths

### Phase 8: Cleanup and Finalization

#### Step 8.1: Remove old directories

- **Location**: Repository root
- **Action**: Delete old adws/ and ipe/ directories
- **Details**:
  ```bash
  rm -rf adws/ ipe/
  ```
- **Depends on**: All previous phases verified
- **Verify**: `ls adws/ ipe/` fails (directories don't exist)

#### Step 8.2: Update pyproject.toml / setup files

- **Location**: Root configuration files
- **Action**: Update any package configuration
- **Depends on**: Step 8.1
- **Verify**: Package can be installed

#### Step 8.3: Update .gitignore if needed

- **Location**: `.gitignore`
- **Action**: Update any adws/ipe-specific ignores to asw/
- **Depends on**: Step 8.1
- **Verify**: Correct files are ignored

#### Step 8.4: Run full test suite

- **Location**: Repository root
- **Action**: Run all tests to verify nothing is broken
- **Details**:
  ```bash
  pytest asw/tests/
  ```
- **Depends on**: Step 8.1
- **Verify**: All tests pass

---

## Critical Considerations

### Security
- Ensure no credentials or secrets are exposed during file moves
- Verify state files don't contain sensitive data that could be mishandled
- Check that renamed modules don't break authentication flows

### Performance
- Use `git mv` for all file moves to preserve history
- Batch file operations where possible
- Test import performance after reorganization

### Edge Cases
- **In-progress workflows**: Any active ADW/IPE workflows will break after this change
- **State file compatibility**: Existing `adw_state.json` and `ipe_state.json` files need migration
- **External integrations**: GitHub Actions, webhooks, etc. may reference old paths
- **Import cycles**: Merging modules may create circular import issues

### Breaking Changes
- **ALL existing ADW/IPE workflows will break**
- Entry points change: `uv run adws/adw_sdlc_iso.py` → `uv run asw/app/asw_app_sdlc_iso.py`
- Import paths change: `from adws.adw_modules.*` → `from asw.modules.*`
- State file locations may change
- Claude commands will have new names

---

## Testing Strategy

### Required Tests
- [ ] `python -c "from asw.modules import *"` succeeds
- [ ] `python asw/app/asw_app_sdlc_iso.py --help` shows usage
- [ ] `python asw/io/asw_io_sdlc_iso.py --help` shows usage
- [ ] `pytest asw/tests/app/` passes
- [ ] `pytest asw/tests/io/` passes
- [ ] All Claude commands execute without path errors

### Validation Commands
```bash
# Verify directory structure
ls -R asw/

# Verify Python imports
python -c "from asw.modules.agent import *; print('agent OK')"
python -c "from asw.modules.state import *; print('state OK')"
python -c "from asw.modules.workflow_ops import *; print('workflow_ops OK')"

# Verify entry points
python asw/app/asw_app_sdlc_iso.py --help
python asw/io/asw_io_sdlc_iso.py --help

# Verify no old paths remain
grep -r "adws/" --include="*.py" --include="*.md" . | grep -v "specs/"
grep -r "ipe/" --include="*.py" --include="*.md" . | grep -v "specs/" | grep -v "io/"

# Run tests
pytest asw/tests/ -v
```

---

## Verification Checklist

- [ ] `adws/` directory no longer exists
- [ ] `ipe/` directory no longer exists
- [ ] `asw/` contains all workflow code
- [ ] `asw/modules/` contains unified shared modules
- [ ] All Python files compile without errors
- [ ] All imports resolve correctly
- [ ] `asw_app_sdlc_iso.py` runs successfully
- [ ] `asw_io_sdlc_iso.py` runs successfully
- [ ] All tests pass
- [ ] All Claude commands work
- [ ] Documentation updated
- [ ] No references to old paths (except in specs/)

---

## Implementation Tips

- **Start with**: Phase 1 and Phase 2 (directory structure and module merging) - these establish the foundation
- **Key insight**: The modules have parallel structures, so merging is mostly about combining similar functions and renaming
- **Common pitfall**: Import cycles when merging modules - test imports incrementally
- **Pattern to follow**: The existing module structure in `ipe_modules/` is more mature - use it as the base

---

## Rollback Strategy

If implementation needs to be reverted:

1. This is a major refactor - ensure a clean commit boundary before starting
2. Tag the pre-refactor state for easy rollback

```bash
# Before starting, create a tag
git tag pre-asw-refactor

# If rollback needed
git reset --hard pre-asw-refactor
```

---

## Migration Guide (for users)

After this change, users should update their workflows:

| Old Command | New Command |
|-------------|-------------|
| `uv run adws/adw_sdlc_iso.py 123` | `uv run asw/app/asw_app_sdlc_iso.py 123` |
| `uv run ipe/ipe_sdlc_iso.py 123` | `uv run asw/io/asw_io_sdlc_iso.py 123` |
| `/feature 123` | `/feature 123` (updated internally) |
| `/ipe_feature 123` | `/asw_io_feature 123` |

# ADWS to IPE Module Mapping

## Overview

This document provides the complete 1:1 mapping between ADWS application modules and their IPE infrastructure equivalents. Each ADWS module has a corresponding IPE module with transformed naming and adapted semantics for infrastructure orchestration.

## Module Mapping Table

| ADWS Module | IPE Module | Purpose | Key Transformations |
|-------------|------------|---------|---------------------|
| `adw_modules/state.py` | `ipe_modules/ipe_state.py` | State persistence and management | State fields, filename, class names |
| `adw_modules/agent.py` | `ipe_modules/ipe_agent.py` | Claude agent orchestration | Bot identifier, model configuration |
| `adw_modules/workflow_ops.py` | `ipe_modules/ipe_workflow_ops.py` | Workflow execution logic | Slash commands, workflow steps |
| `adw_modules/github.py` | `ipe_modules/ipe_github.py` | GitHub API interactions | Bot comments, PR labels |
| `adw_modules/git_ops.py` | `ipe_modules/ipe_git_ops.py` | Git operations wrapper | Branch naming patterns |
| `adw_modules/data_types.py` | `ipe_modules/ipe_data_types.py` | Pydantic state models | State field definitions |
| `adw_modules/utils.py` | `ipe_modules/ipe_utils.py` | Shared utilities | ID generation, validation |
| `adw_modules/worktree_ops.py` | `ipe_modules/ipe_worktree_ops.py` | Git worktree management | Worktree paths, cleanup |

## Detailed Module Transformations

### state.py → ipe_state.py

**Class Transformations:**
- `ADWState` → `IPEState`
- `STATE_FILENAME = "adw_state.json"` → `STATE_FILENAME = "ipe_state.json"`

**State Field Transformations:**
```python
# ADWS State Fields
{
    "adw_id": str,              # → "ipe_id": str
    "issue_number": int,        # → "issue_number": int (unchanged)
    "branch_name": str,         # → "branch_name": str (unchanged)
    "plan_file": str,           # → "spec_file": str
    "issue_class": str,         # → "issue_class": str (unchanged)
    "worktree_path": str,       # → "worktree_path": str (unchanged)
    "backend_port": int,        # → REMOVED (not needed for infrastructure)
    "frontend_port": int,       # → REMOVED (not needed for infrastructure)
    "model_set": str,           # → "model_set": str (unchanged)
    "all_adws": list[str],      # → "all_ipes": list[str]
    "shipped_at": str,          # → "deployed_at": str
    "merge_commit": str,        # → "merge_commit": str (unchanged)
    "pr_number": int,           # → "pr_number": int (unchanged)
}

# IPE State Fields (new fields)
{
    "ipe_id": str,              # Infrastructure Platform Engineer ID
    "spec_file": str,           # Infrastructure specification file path
    "environment": str,         # Target environment: dev, staging, prod
    "terraform_dir": str,       # Path to Terraform configuration directory
    "all_ipes": list[str],      # List of all IPE IDs in this workflow
}
```

**Method Transformations:**
- `append_adw_id()` → `append_ipe_id()`
- Path construction: `agents/{adw_id}/adw_state.json` → `agents/{ipe_id}/ipe_state.json`

### agent.py → ipe_agent.py

**Bot Identity Transformations:**
- All instances of `[🤖 ADW]` → `[🤖 IPE]`
- Logger names: `"adw_modules.agent"` → `"ipe_modules.ipe_agent"`

**Prompt Context Transformations:**
- "Application Developer Workflow" → "Infrastructure Platform Engineer"
- "application code" → "infrastructure code"
- "backend/frontend" → "Terraform/Packer"

### workflow_ops.py → ipe_workflow_ops.py

**Slash Command Transformations:**
```python
# ADWS Commands
"/implement"  # → "/ipe_build"
"/commit"     # → "/ipe_commit"
"/ship"       # → "/ipe_deploy"
"/test"       # → "/ipe_validate"
"/status"     # → "/ipe_status"
```

**Workflow Step Transformations:**
- "plan" → "spec" (infrastructure specification)
- "implement" → "build" (Terraform/Packer build)
- "test" → "validate" (terraform validate, terraform plan)
- "commit" → "commit" (unchanged, but commits infrastructure code)
- "ship" → "deploy" (terraform apply)

### github.py → ipe_github.py

**Bot Signature Transformations:**
- GitHub comment signatures: `🤖 ADW-{adw_id}` → `🤖 IPE-{ipe_id}`
- PR labels: `adw-in-progress` → `ipe-in-progress`
- Branch prefixes: `adw/` → `ipe/`

### data_types.py → ipe_data_types.py

**Pydantic Model Transformations:**
```python
# ADWS
class ADWStateData(BaseModel):
    adw_id: str
    plan_file: Optional[str] = None
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    all_adws: list[str] = []
    # ...

# IPE
class IPEStateData(BaseModel):
    ipe_id: str
    spec_file: Optional[str] = None
    environment: Optional[str] = None
    terraform_dir: Optional[str] = None
    all_ipes: list[str] = []
    # ...
```

### utils.py → ipe_utils.py

**Function Transformations:**
- `make_adw_id()` → `make_ipe_id()`
- `ensure_adw_id()` → `ensure_ipe_id()`
- `validate_adw_state()` → `validate_ipe_state()`

**ID Generation Pattern:**
```python
# ADWS: adw-{issue_class}-{short_hash}
# Example: adw-feature-a1b2c3d4

# IPE: ipe-{issue_class}-{short_hash}
# Example: ipe-infra-a1b2c3d4
```

### git_ops.py → ipe_git_ops.py

**Branch Naming Transformations:**
```python
# ADWS: feature-issue-123-adw-a1b2c3d4-description
# IPE:  infra-issue-123-ipe-a1b2c3d4-description
```

**Commit Message Prefixes:**
- "feat(adw):" → "feat(ipe):"
- "fix(adw):" → "fix(ipe):"
- "chore(adw):" → "chore(ipe):"

### worktree_ops.py → ipe_worktree_ops.py

**Worktree Path Transformations:**
```python
# ADWS: /tmp/adws/adw-{adw_id}/
# IPE:  /tmp/ipes/ipe-{ipe_id}/
```

## Import Statement Transformations

### ADWS Import Patterns
```python
from adw_modules.state import ADWState
from adw_modules.data_types import ADWStateData
from adw_modules import utils
from adw_modules.github import create_pr
```

### IPE Import Patterns
```python
from .ipe_state import IPEState
from .ipe_data_types import IPEStateData
from . import ipe_utils
from .ipe_github import create_pr
```

**Key Rules:**
1. Use relative imports (`.ipe_*`) within IPE modules
2. External packages use absolute imports (unchanged)
3. Standard library imports (unchanged)

## State File Location Transformations

### ADWS State File Paths
```
{project_root}/agents/{adw_id}/adw_state.json
```

### IPE State File Paths
```
{project_root}/agents/{ipe_id}/ipe_state.json
```

## Validation Strategy

After transformation, verify:

1. **No `adw_` prefixes remain** in variable names, function names, or class names
2. **All imports resolve** correctly with relative import pattern
3. **State fields match IPE schema** (no backend_port, has environment)
4. **Bot identifier is `[🤖 IPE]`** in all logging and GitHub interactions
5. **Slash commands use `/ipe_*`** prefix
6. **State filename is `ipe_state.json`**

## Special Cases

### Docstrings
Update terminology but preserve meaning:
- "ADW workflow" → "IPE workflow"
- "Application Developer" → "Infrastructure Engineer"
- "application code" → "infrastructure code"
- Preserve code examples but transform identifiers

### Comments
- Update inline comments referencing ADW concepts
- Add migration notes where semantic changes occur
- Preserve TODO/FIXME comments with updated identifiers

### String Literals
Check all string literals for:
- File paths containing `adw_`
- Log messages with ADW terminology
- Error messages referencing ADW concepts
- API endpoint paths (if any)

## Migration Checklist

Use this checklist for each module transformation:

- [ ] File renamed with `ipe_` prefix
- [ ] All class names transformed (ADW → IPE)
- [ ] All function names transformed (adw_ → ipe_)
- [ ] All variable names transformed (adw_ → ipe_)
- [ ] All state fields updated
- [ ] All imports converted to relative pattern
- [ ] All bot identifiers updated
- [ ] All slash commands updated
- [ ] All docstrings updated
- [ ] All comments updated
- [ ] All string literals checked
- [ ] File saved to `../ipe/ipe_modules/`
- [ ] Python syntax validated
- [ ] No remaining `adw_` references (except in migration notes)

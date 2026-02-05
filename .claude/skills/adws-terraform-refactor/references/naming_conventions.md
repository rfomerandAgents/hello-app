# Naming Convention Transformations

## Overview

This document provides comprehensive naming transformation rules for converting ADWS code to IPE code. All transformations should be applied systematically and validated to ensure consistency.

## Core Prefix Transformations

### Basic Pattern
```
adw_  → ipe_
ADW   → IPE
Adw   → Ipe
```

## Class Name Transformations

### State Classes
| ADWS Class | IPE Class |
|------------|-----------|
| `ADWState` | `IPEState` |
| `ADWStateData` | `IPEStateData` |
| `ADWConfig` | `IPEConfig` |
| `ADWWorkflow` | `IPEWorkflow` |

### Example
```python
# Before (ADWS)
class ADWState:
    """Container for ADW workflow state."""
    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str):
        self.adw_id = adw_id

# After (IPE)
class IPEState:
    """Container for IPE workflow state."""
    STATE_FILENAME = "ipe_state.json"

    def __init__(self, ipe_id: str):
        self.ipe_id = ipe_id
```

## Function Name Transformations

### Utility Functions
| ADWS Function | IPE Function |
|---------------|--------------|
| `make_adw_id()` | `make_ipe_id()` |
| `ensure_adw_id()` | `ensure_ipe_id()` |
| `validate_adw_state()` | `validate_ipe_state()` |
| `get_adw_config()` | `get_ipe_config()` |
| `load_adw_state()` | `load_ipe_state()` |
| `save_adw_state()` | `save_ipe_state()` |
| `list_all_adws()` | `list_all_ipes()` |

### Workflow Functions
| ADWS Function | IPE Function |
|---------------|--------------|
| `start_adw_workflow()` | `start_ipe_workflow()` |
| `run_adw_agent()` | `run_ipe_agent()` |
| `create_adw_branch()` | `create_ipe_branch()` |

## Variable Name Transformations

### Core State Variables
| ADWS Variable | IPE Variable | Type | Notes |
|---------------|--------------|------|-------|
| `adw_id` | `ipe_id` | `str` | Primary identifier |
| `plan_file` | `spec_file` | `str` | Specification file path |
| `backend_port` | *REMOVED* | `int` | Not needed for infrastructure |
| `frontend_port` | *REMOVED* | `int` | Not needed for infrastructure |
| `all_adws` | `all_ipes` | `list[str]` | List of all workflow IDs |
| `shipped_at` | `deployed_at` | `str` | Deployment timestamp |
| *N/A* | `environment` | `str` | **NEW**: dev/staging/prod |
| *N/A* | `terraform_dir` | `str` | **NEW**: Path to Terraform config |

### Loop Variables and Locals
```python
# Before (ADWS)
for adw_id in all_adws:
    adw_state = load_state(adw_id)
    print(f"ADW ID: {adw_id}")

# After (IPE)
for ipe_id in all_ipes:
    ipe_state = load_state(ipe_id)
    print(f"IPE ID: {ipe_id}")
```

## Parameter Name Transformations

### Function Signatures
```python
# Before (ADWS)
def create_workflow(adw_id: str, plan_file: str, issue_number: int) -> ADWState:
    """Create a new ADW workflow."""
    pass

# After (IPE)
def create_workflow(ipe_id: str, spec_file: str, issue_number: int) -> IPEState:
    """Create a new IPE workflow."""
    pass
```

## Module Name Transformations

### Module Files
| ADWS Module | IPE Module |
|-------------|------------|
| `adw_modules/state.py` | `ipe_modules/ipe_state.py` |
| `adw_modules/agent.py` | `ipe_modules/ipe_agent.py` |
| `adw_modules/workflow_ops.py` | `ipe_modules/ipe_workflow_ops.py` |
| `adw_modules/github.py` | `ipe_modules/ipe_github.py` |
| `adw_modules/git_ops.py` | `ipe_modules/ipe_git_ops.py` |
| `adw_modules/data_types.py` | `ipe_modules/ipe_data_types.py` |
| `adw_modules/utils.py` | `ipe_modules/ipe_utils.py` |
| `adw_modules/worktree_ops.py` | `ipe_modules/ipe_worktree_ops.py` |

### Directory Structure
```
# Before (ADWS)
adws/
├── adw_modules/
│   ├── __init__.py
│   └── state.py
└── adw_state.json

# After (IPE)
ipe/
├── ipe_modules/
│   ├── __init__.py
│   └── ipe_state.py
└── ipe_state.json
```

## Import Statement Transformations

### Absolute to Relative Imports
```python
# Before (ADWS) - Absolute imports
from adw_modules.state import ADWState
from adw_modules.data_types import ADWStateData
from adw_modules import utils as adw_utils
from adw_modules.github import create_pr, update_pr

# After (IPE) - Relative imports
from .ipe_state import IPEState
from .ipe_data_types import IPEStateData
from . import ipe_utils
from .ipe_github import create_pr, update_pr
```

### Import Alias Transformations
```python
# Before (ADWS)
import adw_modules.state as state
from adw_modules import utils as adw_utils

# After (IPE)
from . import ipe_state as state
from . import ipe_utils
```

## String Literal Transformations

### File Paths
```python
# Before (ADWS)
STATE_FILE = "adw_state.json"
STATE_DIR = "agents/{adw_id}"
WORKTREE_BASE = "/tmp/adws/"

# After (IPE)
STATE_FILE = "ipe_state.json"
STATE_DIR = "agents/{ipe_id}"
WORKTREE_BASE = "/tmp/ipes/"
```

### Log Messages
```python
# Before (ADWS)
logger.info(f"[🤖 ADW] Starting workflow for {adw_id}")
logger.error(f"ADW workflow failed: {error}")

# After (IPE)
logger.info(f"[🤖 IPE] Starting workflow for {ipe_id}")
logger.error(f"IPE workflow failed: {error}")
```

### Bot Identifiers
```python
# Before (ADWS)
BOT_PREFIX = "[🤖 ADW]"
BOT_SIGNATURE = "🤖 ADW-{adw_id}"

# After (IPE)
BOT_PREFIX = "[🤖 IPE]"
BOT_SIGNATURE = "🤖 IPE-{ipe_id}"
```

## Slash Command Transformations

| ADWS Command | IPE Command | Purpose |
|--------------|-------------|---------|
| `/implement` | `/ipe_build` | Build infrastructure (Terraform/Packer) |
| `/commit` | `/ipe_commit` | Commit infrastructure changes |
| `/ship` | `/ipe_deploy` | Deploy infrastructure (terraform apply) |
| `/test` | `/ipe_validate` | Validate infrastructure (terraform validate) |
| `/status` | `/ipe_status` | Check infrastructure status |
| `/rollback` | `/ipe_rollback` | Rollback infrastructure changes |

### In Code
```python
# Before (ADWS)
COMMANDS = {
    "/implement": handle_implement,
    "/commit": handle_commit,
    "/ship": handle_ship,
}

# After (IPE)
COMMANDS = {
    "/ipe_build": handle_build,
    "/ipe_commit": handle_commit,
    "/ipe_deploy": handle_deploy,
}
```

## Constant Name Transformations

### Module-Level Constants
```python
# Before (ADWS)
ADW_STATE_VERSION = "1.0"
ADW_CONFIG_FILE = ".adw_config.json"
ADW_WORKTREE_PREFIX = "/tmp/adws/"
DEFAULT_ADW_MODEL = "claude-sonnet-4"

# After (IPE)
IPE_STATE_VERSION = "1.0"
IPE_CONFIG_FILE = ".ipe_config.json"
IPE_WORKTREE_PREFIX = "/tmp/ipes/"
DEFAULT_IPE_MODEL = "claude-sonnet-4"
```

## Type Annotation Transformations

### Custom Types
```python
# Before (ADWS)
ADWId = str
ADWStateDict = Dict[str, Any]
ADWList = List[ADWId]

# After (IPE)
IPEId = str
IPEStateDict = Dict[str, Any]
IPEList = List[IPEId]
```

### Function Type Hints
```python
# Before (ADWS)
def get_state(adw_id: str) -> Optional[ADWState]:
    pass

def list_workflows() -> List[ADWState]:
    pass

# After (IPE)
def get_state(ipe_id: str) -> Optional[IPEState]:
    pass

def list_workflows() -> List[IPEState]:
    pass
```

## Docstring Transformations

### Function Docstrings
```python
# Before (ADWS)
def create_workflow(adw_id: str) -> ADWState:
    """Create a new ADW workflow.

    This function initializes an Application Developer Workflow
    with the given ADW ID and sets up the necessary state.

    Args:
        adw_id: The ADW identifier

    Returns:
        ADWState: The initialized workflow state
    """

# After (IPE)
def create_workflow(ipe_id: str) -> IPEState:
    """Create a new IPE workflow.

    This function initializes an Infrastructure Platform Engineer workflow
    with the given IPE ID and sets up the necessary state.

    Args:
        ipe_id: The IPE identifier

    Returns:
        IPEState: The initialized workflow state
    """
```

### Class Docstrings
```python
# Before (ADWS)
class ADWState:
    """Container for ADW workflow state.

    Manages state for Application Developer Workflows including
    issue tracking, branch management, and deployment coordination.
    """

# After (IPE)
class IPEState:
    """Container for IPE workflow state.

    Manages state for Infrastructure Platform Engineer workflows including
    issue tracking, branch management, and infrastructure deployment.
    """
```

## Comment Transformations

### Inline Comments
```python
# Before (ADWS)
# Initialize ADW state
adw_state = ADWState(adw_id)  # Create new ADW instance

# Load all ADWs from state directory
all_adws = load_all_states()

# After (IPE)
# Initialize IPE state
ipe_state = IPEState(ipe_id)  # Create new IPE instance

# Load all IPEs from state directory
all_ipes = load_all_states()
```

## Branch Name Transformations

### Git Branch Patterns
```python
# Before (ADWS)
# Pattern: feature-issue-{number}-adw-{adw_id}-{description}
branch_name = f"feature-issue-{issue_num}-adw-{adw_id}-add-auth"

# After (IPE)
# Pattern: infra-issue-{number}-ipe-{ipe_id}-{description}
branch_name = f"infra-issue-{issue_num}-ipe-{ipe_id}-add-vpc"
```

## Commit Message Transformations

### Conventional Commits
```bash
# Before (ADWS)
feat(adw): add authentication module
fix(adw): resolve port conflict issue
chore(adw): update dependencies

# After (IPE)
feat(ipe): add VPC module
fix(ipe): resolve Terraform state conflict
chore(ipe): update Terraform version
```

## Error Message Transformations

```python
# Before (ADWS)
raise ValueError(f"Invalid ADW ID: {adw_id}")
raise FileNotFoundError(f"ADW state not found for {adw_id}")
raise RuntimeError(f"ADW workflow failed: {error}")

# After (IPE)
raise ValueError(f"Invalid IPE ID: {ipe_id}")
raise FileNotFoundError(f"IPE state not found for {ipe_id}")
raise RuntimeError(f"IPE workflow failed: {error}")
```

## Logger Name Transformations

```python
# Before (ADWS)
logger = logging.getLogger("adw_modules.state")
logger = logging.getLogger(__name__)  # In adw_modules/state.py

# After (IPE)
logger = logging.getLogger("ipe_modules.ipe_state")
logger = logging.getLogger(__name__)  # In ipe_modules/ipe_state.py
```

## F-String and Format String Transformations

```python
# Before (ADWS)
message = f"Starting ADW workflow {adw_id}"
path = f"/agents/{adw_id}/adw_state.json"
log = f"[🤖 ADW] Processing {adw_id}"

# After (IPE)
message = f"Starting IPE workflow {ipe_id}"
path = f"/agents/{ipe_id}/ipe_state.json"
log = f"[🤖 IPE] Processing {ipe_id}"
```

## Dictionary Key Transformations

```python
# Before (ADWS)
state_dict = {
    "adw_id": adw_id,
    "plan_file": plan_file,
    "backend_port": 3000,
    "frontend_port": 5173,
}

# After (IPE)
state_dict = {
    "ipe_id": ipe_id,
    "spec_file": spec_file,
    "environment": "dev",
    "terraform_dir": "/path/to/terraform",
}
```

## Validation Regular Expressions

Use these patterns to find remaining ADWS references:

```python
# Find adw_ prefixed identifiers (excluding comments)
r'\badw_\w+'

# Find ADW class names
r'\bADW[A-Z]\w*'

# Find adw_id in variable names
r'\badw_id\b'

# Find "ADW" in strings (excluding migration notes)
r'["\'].*\bADW\b.*["\']'

# Find /implement and other ADWS commands
r'/implement\b|/commit\b|/ship\b'
```

## Transformation Checklist

For each file transformation, verify:

- [ ] All class names transformed (ADW* → IPE*)
- [ ] All function names transformed (adw_* → ipe_*)
- [ ] All variable names transformed (adw_* → ipe_*)
- [ ] All parameter names transformed
- [ ] All type annotations transformed
- [ ] All module imports transformed (absolute → relative)
- [ ] All string literals checked and transformed
- [ ] All docstrings updated
- [ ] All comments updated
- [ ] All f-strings and format strings updated
- [ ] All dictionary keys transformed
- [ ] All constants transformed
- [ ] All slash commands transformed
- [ ] All bot identifiers transformed
- [ ] All error messages transformed
- [ ] All log messages transformed
- [ ] No remaining `adw_` or `ADW` references (except in notes)

## Edge Cases

### Preserve Acronyms in Documentation
When "ADW" appears as part of explaining the migration:
```python
# OK to keep ADW in migration notes
"""This module was migrated from the ADW system (adw_modules/state.py)
to the IPE system. All adw_ references have been transformed to ipe_."""
```

### Handle Multi-line Strings
```python
# Before (ADWS)
help_text = """
ADW Workflow Commands:
  /implement - Implement the plan
  /commit    - Commit changes

ADW ID: {adw_id}
"""

# After (IPE)
help_text = """
IPE Workflow Commands:
  /ipe_build - Build infrastructure
  /ipe_commit - Commit changes

IPE ID: {ipe_id}
"""
```

### Handle Regex Patterns
```python
# Before (ADWS)
adw_id_pattern = r'adw-[a-z]+-[a-f0-9]{8}'
branch_pattern = r'feature-issue-\d+-adw-[a-f0-9]{8}'

# After (IPE)
ipe_id_pattern = r'ipe-[a-z]+-[a-f0-9]{8}'
branch_pattern = r'infra-issue-\d+-ipe-[a-f0-9]{8}'
```

# Post-Refactor Validation Checklist

## Overview

This checklist ensures that ADWS-to-IPE refactoring is complete, correct, and production-ready. Use this after transforming each module or as a final validation step for batch transformations.

## Quick Validation

Essential checks that must pass:

- [ ] No remaining `adw_` prefixes in IPE code (except migration notes)
- [ ] No remaining `ADW` class names or constants
- [ ] State class uses `ipe_id` not `adw_id`
- [ ] Bot identifier is `[🤖 IPE]` not `[🤖 ADW]`
- [ ] Slash commands use `/ipe_*` variants
- [ ] State filename is `ipe_state.json`
- [ ] All imports use relative `.ipe_*` patterns
- [ ] File saved to correct location: `../ipe/ipe_modules/ipe_*.py`

## Comprehensive Validation

### 1. File Structure Validation

#### File Location
- [ ] File is in `../ipe/ipe_modules/` directory
- [ ] Filename follows `ipe_*.py` pattern
- [ ] `__init__.py` exists in `ipe_modules/` directory
- [ ] File permissions preserved (typically 644)

#### Directory Structure
```bash
# Verify with:
ls -la ../ipe/ipe_modules/

# Expected structure:
../ipe/
├── ipe_modules/
│   ├── __init__.py
│   ├── ipe_state.py
│   ├── ipe_agent.py
│   ├── ipe_workflow_ops.py
│   ├── ipe_github.py
│   ├── ipe_git_ops.py
│   ├── ipe_data_types.py
│   ├── ipe_utils.py
│   └── ipe_worktree_ops.py
└── ipe_state.json (created at runtime)
```

### 2. Naming Validation

#### Class Names
- [ ] All `ADW*` classes renamed to `IPE*`
- [ ] No `Adw*` class names remain
- [ ] No `adw*` class names remain

```bash
# Validate with:
grep -n '\bclass ADW' ../ipe/ipe_modules/*.py
# Should return no results
```

#### Function Names
- [ ] All `*_adw_*` functions renamed to `*_ipe_*`
- [ ] No function parameters named `adw_*`
- [ ] No local variables named `adw_*`

```bash
# Validate with:
grep -n '\bdef .*adw' ../ipe/ipe_modules/*.py
grep -n '\badw_\w\+\s*=' ../ipe/ipe_modules/*.py
# Should return no results (except comments)
```

#### Variable Names
- [ ] `adw_id` → `ipe_id` everywhere
- [ ] `plan_file` → `spec_file` everywhere
- [ ] `all_adws` → `all_ipes` everywhere
- [ ] `shipped_at` → `deployed_at` everywhere
- [ ] `backend_port` removed (or documented why kept)
- [ ] `frontend_port` removed (or documented why kept)
- [ ] `environment` field added to state
- [ ] `terraform_dir` field added to state

### 3. Import Statement Validation

#### Relative Import Pattern
- [ ] All imports within IPE modules use relative imports
- [ ] Pattern: `from .ipe_*` or `from . import ipe_*`
- [ ] No absolute imports like `from adw_modules.*`
- [ ] No absolute imports like `from ipe_modules.*`

```bash
# Validate with:
grep -n 'from adw_modules' ../ipe/ipe_modules/*.py
# Should return no results

grep -n 'from ipe_modules' ../ipe/ipe_modules/*.py
# Should return no results (use relative imports instead)
```

#### Import Resolution Test
```bash
# Test imports resolve correctly:
cd ../ipe
python3 -c "from ipe_modules.ipe_state import IPEState; print('✓ Imports OK')"
python3 -c "from ipe_modules.ipe_data_types import IPEStateData; print('✓ Data types OK')"
```

### 4. String Literal Validation

#### File Paths
- [ ] State filename is `ipe_state.json`
- [ ] Directory paths use `{ipe_id}` not `{adw_id}`
- [ ] Worktree base is `/tmp/ipes/` not `/tmp/adws/`

```bash
# Validate with:
grep -n '"adw_state.json"' ../ipe/ipe_modules/*.py
grep -n "'adw_state.json'" ../ipe/ipe_modules/*.py
# Should return no results
```

#### Log Messages
- [ ] All log messages use `[🤖 IPE]` prefix
- [ ] No log messages contain `ADW workflow`
- [ ] No log messages contain `adw_id`

```bash
# Validate with:
grep -n '\[🤖 ADW\]' ../ipe/ipe_modules/*.py
grep -n 'ADW workflow' ../ipe/ipe_modules/*.py
# Should return no results
```

#### Bot Identifiers
- [ ] Bot prefix is `[🤖 IPE]`
- [ ] GitHub signatures use `🤖 IPE-{ipe_id}`
- [ ] No `🤖 ADW-` patterns remain

### 5. State Field Validation

#### Required IPE State Fields
Verify these fields exist in `IPEStateData` and `IPEState`:

- [ ] `ipe_id: str` (required)
- [ ] `issue_number: Optional[int]`
- [ ] `branch_name: Optional[str]`
- [ ] `spec_file: Optional[str]` (was `plan_file`)
- [ ] `issue_class: Optional[str]`
- [ ] `worktree_path: Optional[str]`
- [ ] `environment: Optional[str]` (NEW: dev/staging/prod)
- [ ] `terraform_dir: Optional[str]` (NEW: Terraform config path)
- [ ] `model_set: str = "base"`
- [ ] `all_ipes: list[str] = []` (was `all_adws`)
- [ ] `deployed_at: Optional[str]` (was `shipped_at`)
- [ ] `merge_commit: Optional[str]`
- [ ] `pr_number: Optional[int]`

#### Removed ADWS-Specific Fields
- [ ] `backend_port` removed
- [ ] `frontend_port` removed
- [ ] No references to port management logic

### 6. Slash Command Validation

#### Command Mapping
- [ ] `/implement` → `/ipe_build`
- [ ] `/commit` → `/ipe_commit`
- [ ] `/ship` → `/ipe_deploy`
- [ ] `/test` → `/ipe_validate`
- [ ] `/status` → `/ipe_status`

```bash
# Validate with:
grep -n '"/implement"' ../ipe/ipe_modules/*.py
grep -n '"/commit"' ../ipe/ipe_modules/*.py
grep -n '"/ship"' ../ipe/ipe_modules/*.py
# Should return no results
```

### 7. Docstring Validation

#### Module Docstrings
- [ ] No references to "Application Developer Workflow"
- [ ] Uses "Infrastructure Platform Engineer" terminology
- [ ] Updated to reflect infrastructure focus

#### Function Docstrings
- [ ] Parameter names updated (`adw_id` → `ipe_id`)
- [ ] Return type annotations updated (`ADWState` → `IPEState`)
- [ ] Examples updated to use IPE identifiers
- [ ] Terminology reflects infrastructure focus

#### Class Docstrings
- [ ] Class names updated in examples
- [ ] State fields documented correctly
- [ ] Purpose reflects infrastructure orchestration

### 8. Comment Validation

#### Inline Comments
- [ ] No comments referencing `adw_*` variables
- [ ] No comments referencing `ADW` acronym (except migration notes)
- [ ] TODO/FIXME comments updated with IPE context

```bash
# Validate with (should show only migration notes):
grep -n 'ADW' ../ipe/ipe_modules/*.py | grep -v 'Migrated from ADW'
```

### 9. Type Annotation Validation

#### Custom Types
- [ ] `ADWState` → `IPEState` in type hints
- [ ] `ADWStateData` → `IPEStateData` in type hints
- [ ] `Optional[ADW*]` → `Optional[IPE*]`
- [ ] `List[ADW*]` → `List[IPE*]`

#### Function Signatures
```python
# Verify pattern:
def function_name(ipe_id: str) -> IPEState:
    # Not: def function_name(adw_id: str) -> ADWState:
```

### 10. Python Syntax Validation

#### Compile Check
```bash
# Each module must compile without errors:
python3 -m py_compile ../ipe/ipe_modules/ipe_state.py
python3 -m py_compile ../ipe/ipe_modules/ipe_agent.py
python3 -m py_compile ../ipe/ipe_modules/ipe_workflow_ops.py
python3 -m py_compile ../ipe/ipe_modules/ipe_github.py
python3 -m py_compile ../ipe/ipe_modules/ipe_git_ops.py
python3 -m py_compile ../ipe/ipe_modules/ipe_data_types.py
python3 -m py_compile ../ipe/ipe_modules/ipe_utils.py
python3 -m py_compile ../ipe/ipe_modules/ipe_worktree_ops.py
```

#### Lint Check (if available)
```bash
# Optional but recommended:
pylint ../ipe/ipe_modules/*.py
flake8 ../ipe/ipe_modules/*.py
mypy ../ipe/ipe_modules/*.py
```

### 11. Pydantic Model Validation

#### Field Definitions
- [ ] All Pydantic models use IPE field names
- [ ] No fields named `adw_*`
- [ ] Default values are appropriate
- [ ] Optional fields properly marked
- [ ] New IPE fields have correct types

#### Serialization Test
```python
# Test in Python REPL:
from ipe_modules.ipe_data_types import IPEStateData

# Should work:
state = IPEStateData(
    ipe_id="ipe-test-12345678",
    issue_number=123,
    spec_file="specs/test.md",
    environment="dev"
)
print(state.model_dump_json())
```

### 12. State Persistence Validation

#### File Operations
- [ ] State save path uses `ipe_state.json`
- [ ] State load path uses `ipe_state.json`
- [ ] Directory structure: `agents/{ipe_id}/ipe_state.json`
- [ ] No references to `adw_state.json`

#### Path Construction Test
```python
# Verify state path construction:
from ipe_modules.ipe_state import IPEState

state = IPEState(ipe_id="ipe-test-12345678")
path = state.get_state_path()
assert "ipe_state.json" in path
assert "ipe-test-12345678" in path
```

### 13. Logging Validation

#### Logger Names
- [ ] Logger names use `ipe_modules.ipe_*` pattern
- [ ] No logger names contain `adw_modules`
- [ ] `__name__` usage is correct for IPE modules

```python
# Verify pattern:
logger = logging.getLogger(__name__)  # In ipe_modules/ipe_state.py
# Should resolve to: ipe_modules.ipe_state
```

#### Log Message Format
- [ ] All log messages use `[🤖 IPE]` prefix
- [ ] Variable references use `ipe_id` not `adw_id`
- [ ] Terminology reflects infrastructure focus

### 14. Error Message Validation

#### Exception Messages
- [ ] Error messages reference IPE not ADW
- [ ] Variable names in error strings use `ipe_*`
- [ ] Error context reflects infrastructure domain

```python
# Verify pattern:
raise ValueError(f"Invalid IPE ID: {ipe_id}")
# Not: raise ValueError(f"Invalid ADW ID: {adw_id}")
```

### 15. Integration Validation

#### Cross-Module References
- [ ] When `ipe_state.py` imports `ipe_data_types.py`, it works
- [ ] When `ipe_agent.py` imports `ipe_state.py`, it works
- [ ] Circular dependencies are avoided or handled
- [ ] All internal IPE module references resolve

#### End-to-End Test
```bash
# Test a complete workflow:
cd ../ipe
python3 -c "
from ipe_modules.ipe_state import IPEState
from ipe_modules.ipe_data_types import IPEStateData

# Create state
state = IPEState(ipe_id='ipe-test-12345678')
state.update(
    issue_number=123,
    spec_file='specs/test.md',
    environment='dev',
    terraform_dir='io/terraform/'
)

# Validate
print(f'✓ IPE ID: {state.ipe_id}')
print(f'✓ Spec file: {state.get(\"spec_file\")}')
print(f'✓ Environment: {state.get(\"environment\")}')
print('✓ Integration test passed')
"
```

## Automated Validation Script

Run the comprehensive validation script:

```bash
# Execute from project root:
python .claude/skills/adws-terraform-refactor/scripts/test_skill.py

# This should:
# ✓ Check SKILL.md frontmatter
# ✓ Verify all reference files exist
# ✓ Test refactor script execution
# ✓ Validate IPE module syntax
# ✓ Check for remaining ADW references
# ✓ Test imports and model serialization
```

## Common Issues and Fixes

### Issue: Imports Not Resolving
**Symptom**: `ModuleNotFoundError: No module named 'ipe_modules'`

**Fix**: Ensure using relative imports within IPE modules:
```python
# Wrong:
from ipe_modules.ipe_state import IPEState

# Correct:
from .ipe_state import IPEState
```

### Issue: Remaining ADW References
**Symptom**: Validation script finds `adw_` patterns

**Fix**: Search and replace systematically:
```bash
# Find all remaining references:
grep -rn '\badw_' ../ipe/ipe_modules/

# Review each and transform manually or with sed:
# (Be careful with automated replacements in strings)
```

### Issue: State Field Mismatch
**Symptom**: Pydantic validation errors when loading state

**Fix**: Update state schema and migration logic:
```python
# Ensure IPEStateData includes all required fields
# Ensure no ADWS fields (backend_port, frontend_port) remain
```

### Issue: Bot Identifier Not Updated
**Symptom**: GitHub webhooks don't trigger correctly

**Fix**: Update all bot signatures:
```bash
grep -rn '\[🤖 ADW\]' ../ipe/
# Replace each with [🤖 IPE]
```

## Final Verification Command

Run this comprehensive check before considering refactoring complete:

```bash
#!/bin/bash
# validate_ipe_refactor.sh

cd /Users/bender/Projects/Active/active_research/claude_code/ipe

echo "=== IPE Refactor Validation ==="

# 1. Check for ADW references
echo "Checking for ADW references..."
if grep -r '\badw_\|\bADW' ipe_modules/*.py | grep -v "Migrated from ADW" | grep -v ".pyc"; then
    echo "❌ Found ADW references (see above)"
    exit 1
else
    echo "✓ No ADW references found"
fi

# 2. Check imports
echo "Checking import patterns..."
if grep -r 'from adw_modules' ipe_modules/*.py; then
    echo "❌ Found absolute ADWS imports"
    exit 1
else
    echo "✓ No ADWS imports found"
fi

# 3. Syntax check
echo "Checking Python syntax..."
for file in ipe_modules/*.py; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✓ $file"
    else
        echo "❌ $file has syntax errors"
        exit 1
    fi
done

# 4. State file name check
echo "Checking state filename..."
if grep -r '"adw_state.json"' ipe_modules/*.py; then
    echo "❌ Found adw_state.json references"
    exit 1
else
    echo "✓ Using ipe_state.json"
fi

# 5. Bot identifier check
echo "Checking bot identifiers..."
if grep -r '\[🤖 ADW\]' ipe_modules/*.py; then
    echo "❌ Found ADW bot identifiers"
    exit 1
else
    echo "✓ Using IPE bot identifier"
fi

echo "=== All validations passed! ==="
```

## Success Criteria Summary

Refactoring is complete when:

1. ✅ All files in `../ipe/ipe_modules/` with `ipe_` prefix
2. ✅ No `adw_` or `ADW` references (except migration notes)
3. ✅ All imports use relative pattern (`.ipe_*`)
4. ✅ State uses IPE fields (`ipe_id`, `spec_file`, `environment`)
5. ✅ Bot identifier is `[🤖 IPE]`
6. ✅ Slash commands use `/ipe_*` prefix
7. ✅ All Python files compile without errors
8. ✅ Pydantic models validate correctly
9. ✅ Integration tests pass
10. ✅ Documentation updated

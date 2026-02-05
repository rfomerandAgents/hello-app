---
name: adws-terraform-refactor
description: Expert skill for refactoring ADWS application workflow code to produce Terraform-ready IPE infrastructure code. Use when converting application automation patterns to infrastructure automation, migrating ADWS modules to IPE equivalents, or creating new IPE workflows based on ADWS templates.
---

# ADWS to Terraform Refactor

## Overview

This skill provides expert guidance for systematically refactoring ADWS (AI Developer Workflow) application code to produce IPE (Infrastructure Platform Engineer) infrastructure code. The transformation is primarily mechanical (naming and structural changes) with key semantic differences in state management and workflow execution patterns.

## Core Philosophy

### Transformation Principles

1. **Preserve Logic Patterns** - The orchestration and workflow patterns remain largely unchanged
2. **Transform Naming Systematically** - All `adw_*` identifiers become `ipe_*` equivalents
3. **Adapt State Management** - Application state fields (ports) become infrastructure state fields (environment, terraform_dir)
4. **Update Bot Identity** - Bot identifiers and slash commands reflect the IPE domain
5. **Maintain Code Quality** - Refactored code should be production-ready and well-documented

## ADWS vs IPE Conceptual Differences

### ADWS (Application Developer Workflow)
- **Purpose**: Orchestrate application development tasks
- **State Focus**: Backend/frontend ports, development servers, hot reload
- **Execution**: Application code compilation, testing, deployment
- **Commands**: `/implement`, `/commit`, `/ship`
- **Bot Identity**: `[🤖 ADW]`

### IPE (Infrastructure Platform Engineer)
- **Purpose**: Orchestrate infrastructure provisioning and configuration
- **State Focus**: Environment name, Terraform directories, AWS resources
- **Execution**: Terraform apply/destroy, Packer builds, infrastructure validation
- **Commands**: `/ipe_build`, `/ipe_commit`, `/ipe_deploy`
- **Bot Identity**: `[🤖 IPE]`

## Module Transformation Strategy

The ADWS system has a 1:1 module mapping to IPE:

| ADWS Module | IPE Module | Purpose |
|-------------|------------|---------|
| `adw_modules/state.py` | `ipe_modules/ipe_state.py` | State persistence and management |
| `adw_modules/agent.py` | `ipe_modules/ipe_agent.py` | Claude agent orchestration |
| `adw_modules/workflow_ops.py` | `ipe_modules/ipe_workflow_ops.py` | Workflow execution logic |
| `adw_modules/github.py` | `ipe_modules/ipe_github.py` | GitHub API interactions |
| `adw_modules/git_ops.py` | `ipe_modules/ipe_git_ops.py` | Git operations wrapper |
| `adw_modules/data_types.py` | `ipe_modules/ipe_data_types.py` | Pydantic state models |
| `adw_modules/utils.py` | `ipe_modules/ipe_utils.py` | Shared utilities |
| `adw_modules/worktree_ops.py` | `ipe_modules/ipe_worktree_ops.py` | Git worktree management |

## Refactoring Workflow

### Step 1: Understand the Source Module
- Read the ADWS module completely
- Identify all external dependencies
- Note any ADWS-specific logic that needs semantic changes
- Document current test coverage

### Step 2: Apply Naming Transformations
- Replace all `adw_` prefixes with `ipe_` in variables, functions, classes
- Update `ADW` to `IPE` in class names (e.g., `ADWState` → `IPEState`)
- Transform state field names per naming conventions
- Update bot identifiers and logging prefixes

### Step 3: Adapt State Management
- Replace application-specific state fields with infrastructure equivalents:
  - `backend_port` → removed (not needed for infrastructure)
  - `frontend_port` → removed (not needed for infrastructure)
  - `plan_file` → `spec_file` (infrastructure specs)
  - Add `environment` field (dev, staging, prod)
  - Add `terraform_dir` field (path to Terraform configuration)
- Update state validation logic

### Step 4: Update Import Statements
- Change absolute imports: `from adw_modules.X` → `from .ipe_X`
- Use relative imports within IPE modules
- Verify no circular dependency issues

### Step 5: Transform Slash Commands
- `/implement` → `/ipe_build`
- `/commit` → `/ipe_commit`
- `/ship` → `/ipe_deploy`
- Update command documentation in docstrings

### Step 6: Update Bot Identity
- Change all `[🤖 ADW]` to `[🤖 IPE]`
- Update logging prefixes
- Update GitHub comment signatures

### Step 7: Validate and Test
- Run Python syntax validation
- Verify all imports resolve
- Test Pydantic model serialization/deserialization
- Verify state file read/write operations
- Run integration tests if available

## Usage Examples

### Example 1: Refactor Single Module

```
"Using adws-terraform-refactor skill, convert adws/adw_modules/state.py
 to IPE format and save to ../ipe/ipe_modules/ipe_state.py"
```

### Example 2: Refactor All Modules

```
"Using adws-terraform-refactor skill, batch convert all adws/adw_modules/*.py
 files to ../ipe/ipe_modules/ with proper naming transformations"
```

### Example 3: Create New IPE Workflow from ADWS Template

```
"Using adws-terraform-refactor skill, create a new IPE workflow for
 Terraform validation based on the ADWS testing workflow pattern"
```

### Example 4: Validate Refactored Code

```
"Using adws-terraform-refactor skill, validate that ../ipe/ipe_modules/
 has no remaining adw_ references and all imports are correct"
```

## Anti-Patterns to Avoid

1. **Don't copy-paste without transformation** - Every `adw_` reference must be updated
2. **Don't skip import updates** - Broken imports will fail at runtime
3. **Don't preserve application-specific state fields** - Infrastructure needs different metadata
4. **Don't forget bot identity changes** - Webhooks depend on correct bot identifiers
5. **Don't skip validation** - Syntax errors or import errors must be caught before deployment

## Target Repository Structure

The refactored code should be written to the `../ipe` repository:

```
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
├── ipe_state.json (state file location)
└── README.md
```

## Related Skills

- `adws-expert` - Deep understanding of ADWS internals and architecture
- `code-decoupler` - Extracting and transforming code patterns between repositories
- `terraform-architect` - Terraform best practices for IPE implementation
- `hashicorp-best-practices` - HCL and Terraform coding standards

## References

See the `references/` directory for detailed documentation:
- `module_mapping.md` - Complete ADWS→IPE module transformation rules
- `naming_conventions.md` - All naming pattern transformations
- `validation_checklist.md` - Post-refactor validation steps

## Automation Scripts

Available in `scripts/` directory:
- `refactor_module.py` - Automated module transformation tool
- `test_skill.py` - Skill validation and testing

## Critical Considerations

### Security
- Never copy .env files or secrets during refactoring
- Validate that target directory `../ipe` is the correct destination
- Strip any embedded API tokens or credentials from refactored code

### Performance
- Batch processing should efficiently handle all modules in one pass
- Use lazy file loading when processing multiple modules

### Edge Cases
- Handle circular import dependencies between modules
- Handle custom type annotations referencing ADW-specific types
- Handle f-strings and string formatting with variable names
- Update docstrings containing "ADW", "adw", or "Application Developer Workflow"
- Handle regex patterns that might match adw_ in unexpected ways

## Success Criteria

A successful refactor produces IPE code that:
- [ ] Has zero `adw_` references (except in comments explaining the transformation)
- [ ] Uses correct IPE state fields (`ipe_id`, `spec_file`, `environment`, `terraform_dir`)
- [ ] Has working imports (all relative imports resolve)
- [ ] Uses correct bot identifier `[🤖 IPE]`
- [ ] Maps slash commands to `/ipe_*` variants
- [ ] Passes Python syntax validation (`python -m py_compile`)
- [ ] Passes Pydantic model validation
- [ ] Has updated docstrings and comments

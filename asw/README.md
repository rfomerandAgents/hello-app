# ASW - Agentic Software Workflow

The ASW (Agentic Software Workflow) system provides unified automation for both application development and infrastructure operations. It consolidates the former ADW (AI Developer Workflow) and IPE (Infrastructure Platform Engineer) systems into a single, consistent framework.

## Directory Structure

```
asw/
  app/                    # Application development workflows (formerly adws/)
    asw_app_sdlc_iso.py   # Full SDLC: Plan + Build + Test + Review + Document
    asw_app_plan_iso.py   # Planning phase
    asw_app_build_iso.py  # Implementation phase
    asw_app_test_iso.py   # Testing phase
    asw_app_review_iso.py # Review phase
    asw_app_document_iso.py # Documentation phase
    asw_app_ship_iso.py   # Shipping/merge phase
    ...

  io/                     # Infrastructure operations workflows (formerly ipe/)
    asw_io_sdlc_iso.py    # Full SDLC for infrastructure
    asw_io_plan_iso.py    # Infrastructure planning
    asw_io_build_iso.py   # Infrastructure implementation
    asw_io_deploy.py      # Deployment operations
    asw_io_destroy.py     # Teardown operations
    ...

  modules/                # Shared modules for both workflow types
    __init__.py           # Package exports
    agent.py              # Claude Code agent execution
    cache.py              # Response caching
    data_types.py         # Unified data types
    git_ops.py            # Git operations
    github.py             # GitHub API operations
    state.py              # State management (ASWAppState, ASWIOState)
    utils.py              # Utility functions
    workflow_ops.py       # Shared workflow operations
    worktree_ops.py       # Git worktree management

  tests/                  # Test suites
    app/                  # Application workflow tests
    io/                   # Infrastructure workflow tests

  triggers/               # Automation triggers
    app/                  # Application workflow triggers
    io/                   # Infrastructure workflow triggers
```

## Usage

### Application Development Workflows (ASW App)

For full SDLC pipeline:
```bash
uv run asw/app/asw_app_sdlc_iso.py <issue-number> [asw-id] [--cache|--no-cache]
```

Individual phases:
```bash
# Planning
uv run asw/app/asw_app_plan_iso.py <issue-number> [asw-id]

# Building (requires asw-id from plan phase)
uv run asw/app/asw_app_build_iso.py <issue-number> <asw-id>

# Testing
uv run asw/app/asw_app_test_iso.py <issue-number> <asw-id> [--skip-e2e]

# Review
uv run asw/app/asw_app_review_iso.py <issue-number> <asw-id>

# Documentation
uv run asw/app/asw_app_document_iso.py <issue-number> <asw-id>
```

### Infrastructure Operations Workflows (ASW IO)

For full SDLC pipeline:
```bash
uv run asw/io/asw_io_sdlc_iso.py <issue-number> [asw-id] [--cache|--no-cache]
```

Individual phases:
```bash
# Planning
uv run asw/io/asw_io_plan_iso.py <issue-number> [asw-id]

# Building
uv run asw/io/asw_io_build_iso.py <issue-number> <asw-id>

# Deployment
uv run asw/io/asw_io_deploy.py <issue-number> <asw-id>
```

## State Management

The ASW system uses JSON-based state persistence:

- **App workflows**: State stored in `agents/<asw-id>/asw_app_state.json`
- **IO workflows**: State stored in `agents/<asw-id>/asw_io_state.json`

State classes:
- `ASWAppState` - For application development workflows
- `ASWIOState` - For infrastructure operations workflows

## Worktree Isolation

Each workflow execution creates an isolated git worktree under `trees/<asw-id>/` to:
- Prevent interference between parallel executions
- Allocate unique ports for services (backend: 9100-9114, frontend: 9200-9214)
- Maintain clean separation of work-in-progress changes

## Migration from ADW/IPE

### Naming Changes

| Old Name | New Name |
|----------|----------|
| `adws/` | `asw/app/` |
| `ipe/` | `asw/io/` |
| `adw_modules/` | `asw/modules/` |
| `ipe_modules/` | `asw/modules/` |
| `ADWState` | `ASWAppState` |
| `IPEState` | `ASWIOState` |
| `adw_id` | `asw_id` |
| `ipe_id` | `asw_id` |
| `ensure_adw_id()` | `ensure_asw_app_id()` |
| `ensure_ipe_id()` | `ensure_asw_io_id()` |

### Backward Compatibility

Legacy aliases are provided for gradual migration:
- `ADWState` = `ASWAppState`
- `IPEState` = `ASWIOState`
- `make_adw_id()` = `make_asw_app_id()`
- `make_ipe_id()` = `make_asw_io_id()`

## Bot Identifiers

- App workflows: `[ASW-APP-AGENTS]`
- IO workflows: `[ASW-IO-AGENTS]`

## Response Caching

Use `--cache` to enable response caching for development/testing:
```bash
uv run asw/app/asw_app_sdlc_iso.py 123 --cache
```

Cache files stored in `agents/<asw-id>/cache/` with 48-hour TTL.

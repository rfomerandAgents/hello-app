---
description: Run setup_maintenance hook and report maintenance results
---

# Purpose

Execute the repository maintenance hook (setup_maintenance) which checks for dependency updates, security vulnerabilities, and cleanup opportunities, then summarize and report the results to the user.

## Workflow

> Execute the following steps in order, top to bottom:

1. **First**, run `Skill(/prime)` to understand the codebase context
2. Read the log file at `.claude/hooks/setup.maintenance.log` (the hook already ran via `--maintenance` flag)
3. Analyze for successes, warnings, and available updates
4. Write results to `app_docs/maintenance_results.md`
5. Report findings and recommendations to user

## Analysis

When analyzing the maintenance log, look for:

- **Dependency Updates**: Packages that have newer versions available
- **Security Vulnerabilities**: npm audit findings, known CVEs
- **Git Status**: Uncommitted changes, behind remote
- **Stale Files**: Caches, logs, temporary files that can be cleaned
- **Worktrees**: Active git worktrees that may need attention

## Common Issues

If you encounter any of the following issues, follow the steps to resolve them:

### Problem: npm audit vulnerabilities
**Solution**: Run `npm audit fix` or `npm audit fix --force` for breaking changes. Review changes before committing.

### Problem: Python packages outdated
**Solution**: Update `pyproject.toml` constraints if needed, then run `uv sync --upgrade`.

### Problem: Git behind remote
**Solution**: Run `git pull --rebase` to sync with remote. Handle any merge conflicts.

### Problem: Stale worktrees
**Solution**: Run `/cleanup_worktrees` to remove old worktrees safely.

## Report

Write to `app_docs/maintenance_results.md` and respond to user:

```markdown
## Maintenance Report - [DATE]

**Status**: SUCCESS | WARNINGS | NEEDS_ATTENTION

### Completed Actions
- [completed maintenance actions]

### Updates Available
| Package/Type | Current | Available | Priority |
|--------------|---------|-----------|----------|
| [name]       | [ver]   | [ver]     | [H/M/L]  |

### Security
- [security findings or "No vulnerabilities found"]

### Warnings
- [any warnings that need attention]

### Recommendations
1. [specific action items]
2. [prioritized by importance]

### Next Maintenance
Suggested: [timeframe based on findings]
```

## Follow-up Questions

After reporting, ask the user:

1. Would you like me to apply any of the available updates?
2. Should I run `npm audit fix` for security vulnerabilities?
3. Would you like me to clean up stale files?

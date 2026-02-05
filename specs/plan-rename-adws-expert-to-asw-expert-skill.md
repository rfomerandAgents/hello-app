# Rename adws-expert skill to asw-expert and incorporate both io and app

## Overview

**Task**: Rename `adws-expert` skill to `asw-expert` and update it to cover both application (app) and infrastructure (io) workflows
**Type**: refactor
**Scope**: medium (4-10 files)
**Estimated Steps**: 12

---

## Context Analysis

### Codebase Findings

| Finding | Details |
|---------|---------|
| Similar implementations | `.claude/skills/adws-expert/` - existing skill to rename/update |
| Relevant patterns | Other skills follow pattern: `SKILL.md` + `references/` directory |
| Key dependencies | ASW system now unified under `asw/` with `app/` and `io/` subdirectories |
| Integration points | Skill references `asw/app/` (formerly adws/), now needs to also cover `asw/io/` |

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `.claude/skills/adws-expert/` | RENAME | Rename directory to `asw-expert` |
| `.claude/skills/asw-expert/SKILL.md` | MODIFY | Update name, description, and add IO workflow coverage |
| `.claude/skills/asw-expert/references/architecture.md` | MODIFY | Add IO architecture details, update paths |
| `.claude/skills/asw-expert/references/troubleshooting.md` | MODIFY | Add IO troubleshooting, update paths |
| `.claude/skills/asw-expert/references/improvement_patterns.md` | MODIFY | Update paths, add IO improvement patterns |

### Tech Stack Context

- **Framework**: Claude Code Skills system
- **Language**: Markdown
- **Build tools**: N/A (markdown documentation)
- **Key libraries**: References ASW Python modules under `asw/modules/`

---

## Implementation Roadmap

### Phase 1: Directory Rename

#### Step 1.1: Rename skill directory from adws-expert to asw-expert

- **Location**: `.claude/skills/adws-expert/`
- **Action**: Rename directory to `.claude/skills/asw-expert/`
- **Details**:
  - Use `mv` or git mv to rename directory
  - Preserves all files inside
  ```bash
  mv .claude/skills/adws-expert .claude/skills/asw-expert
  ```
- **Depends on**: None
- **Verify**: `ls .claude/skills/asw-expert/` shows SKILL.md and references/

### Phase 2: Update Main SKILL.md

#### Step 2.1: Update skill metadata in SKILL.md

- **Location**: `.claude/skills/asw-expert/SKILL.md:1-10`
- **Action**: Update frontmatter name and description
- **Details**:
  - Change `name: adws-expert` to `name: asw-expert`
  - Update description to mention both app and io workflows
  ```yaml
  ---
  name: asw-expert
  description: Expert ASW engineer for analyzing, troubleshooting, and improving the Agentic Software Workflow system. Use when debugging ASW workflows (both app and io), optimizing phase execution, implementing new workflow patterns, improving state management, or enhancing webhook automation. Covers application development (asw/app) and infrastructure operations (asw/io) workflows. Provides opinionated best practices and improvement suggestions.
  ---
  ```
- **Depends on**: Step 1.1
- **Verify**: Read first 10 lines of SKILL.md

#### Step 2.2: Update title and intro paragraph

- **Location**: `.claude/skills/asw-expert/SKILL.md:6-8`
- **Action**: Update title and intro to reflect unified ASW system
- **Details**:
  - Change "# ADWS Expert" to "# ASW Expert"
  - Update description to mention unified ASW system covering both app and io
  ```markdown
  # ASW Expert

  Expert guidance from a senior ASW engineer who has architected and maintained the Agentic Software Workflow system. Deep knowledge of composable workflows for both application development (ASW App) and infrastructure operations (ASW IO), state management patterns, Claude Code CLI integration, and isolated worktree execution.
  ```
- **Depends on**: Step 2.1
- **Verify**: Read SKILL.md title section

#### Step 2.3: Update Core Beliefs section

- **Location**: `.claude/skills/asw-expert/SKILL.md:17-24`
- **Action**: Update bot identifier reference
- **Details**:
  - Change ADW bot identifier reference to mention both ASW-APP and ASW-IO identifiers
  ```markdown
  6. **Bot identifiers prevent loops** - Every automated comment must include `[ASW-APP-AGENTS]` or `[ASW-IO-AGENTS]` to prevent webhook recursion
  ```
- **Depends on**: Step 2.2
- **Verify**: Check Core Beliefs section for updated identifier

#### Step 2.4: Update Module Deep-Dive section

- **Location**: `.claude/skills/asw-expert/SKILL.md:27-170`
- **Action**: Update all module paths and add IO-specific content
- **Details**:
  - Change `adw_modules/` to `asw/modules/`
  - Change `ADWState` to `ASWAppState` / `ASWIOState`
  - Add section about IO-specific state fields
  - Update workflow lists to include both app and io workflows
  ```python
  # State classes
  "ASWAppState" - For application development workflows
  "ASWIOState" - For infrastructure operations workflows

  # State files
  "agents/{asw_id}/asw_app_state.json"  # App workflows
  "agents/{asw_id}/asw_io_state.json"   # IO workflows
  ```
- **Depends on**: Step 2.3
- **Verify**: Grep for "adw_modules" should return 0 matches

#### Step 2.5: Update Available Workflows list

- **Location**: `.claude/skills/asw-expert/SKILL.md:92-108`
- **Action**: Add IO workflows alongside existing app workflows
- **Details**:
  - Add ASW IO workflows to the list
  - Group by workflow type (app vs io)
  ```python
  AVAILABLE_ASW_APP_WORKFLOWS = [
      "asw_app_plan_build_test_review_iso",
      "asw_app_plan_build_document_iso",
      "asw_app_sdlc_iso",
      # ... etc
  ]

  AVAILABLE_ASW_IO_WORKFLOWS = [
      "asw_io_plan_build_test_review_iso",
      "asw_io_plan_build_document_iso",
      "asw_io_sdlc_iso",
      "asw_io_deploy",
      "asw_io_destroy",
      # ... etc
  ]
  ```
- **Depends on**: Step 2.4
- **Verify**: Both app and io workflow lists present

#### Step 2.6: Update Anti-Patterns section

- **Location**: `.claude/skills/asw-expert/SKILL.md:265-365`
- **Action**: Update all ADW references to ASW, add IO-specific patterns
- **Details**:
  - Replace `ADW` with `ASW App` or `ASW IO` as appropriate
  - Update bot identifier examples
  - Add IO-specific anti-patterns (e.g., Terraform state management)
- **Depends on**: Step 2.5
- **Verify**: Grep for "ADW" returns 0 matches (except in migration context)

#### Step 2.7: Update Usage Examples section

- **Location**: `.claude/skills/asw-expert/SKILL.md:370-410`
- **Action**: Add IO-specific examples alongside app examples
- **Details**:
  - Update existing examples to use ASW terminology
  - Add examples for IO workflows:
  ```markdown
  ### Debug a Failing ASW IO Workflow

  ```
  "Using asw-expert skill, analyze why ASW IO workflow xyz98765 is stuck at the terraform plan phase.
  The state file shows plan_file but terraform keeps failing with provider errors."
  ```

  ### Design Infrastructure Automation Phase

  ```
  "Using asw-expert skill, help me design a new 'terraform-drift-detection' phase that:
  - Runs scheduled checks for infrastructure drift
  - Reports findings to GitHub issue
  - Can trigger remediation workflows"
  ```
  ```
- **Depends on**: Step 2.6
- **Verify**: Both app and io examples present

#### Step 2.8: Update Cross-References section

- **Location**: `.claude/skills/asw-expert/SKILL.md:415-420`
- **Action**: Update skill cross-references
- **Details**:
  - Update terraform-architect reference to align with ASW IO
  - Add reference to hashicorp-best-practices skill for IO workflows
- **Depends on**: Step 2.7
- **Verify**: Cross-references updated

### Phase 3: Update Reference Files

#### Step 3.1: Update architecture.md

- **Location**: `.claude/skills/asw-expert/references/architecture.md`
- **Action**: Add IO architecture, update paths
- **Details**:
  - Update all directory paths from `adws/` to `asw/app/` and add `asw/io/`
  - Add IO-specific directory structure
  - Update state management section for both ASWAppState and ASWIOState
  - Update data flow diagrams to include IO workflows
  - Change `ADW_BOT_IDENTIFIER` to `ASW_APP_BOT_IDENTIFIER` and `ASW_IO_BOT_IDENTIFIER`
- **Depends on**: Step 2.8
- **Verify**: Architecture reflects both app and io systems

#### Step 3.2: Update troubleshooting.md

- **Location**: `.claude/skills/asw-expert/references/troubleshooting.md`
- **Action**: Add IO-specific troubleshooting, update paths
- **Details**:
  - Update all `adws/` paths to `asw/app/`
  - Add IO-specific troubleshooting sections:
    - Terraform state lock issues
    - Provider authentication failures
    - Plan/apply phase failures
    - AMI build failures (Packer integration)
  - Update state file paths to use asw_app_state.json / asw_io_state.json
- **Depends on**: Step 3.1
- **Verify**: IO troubleshooting sections present

#### Step 3.3: Update improvement_patterns.md

- **Location**: `.claude/skills/asw-expert/references/improvement_patterns.md`
- **Action**: Add IO improvement patterns, update paths
- **Details**:
  - Update all module paths to `asw/modules/`
  - Add IO-specific improvement patterns:
    - Terraform caching strategies
    - Parallel infrastructure provisioning
    - Cost estimation integration
    - Drift detection workflows
- **Depends on**: Step 3.2
- **Verify**: IO improvement patterns present

### Phase 4: Validation

#### Step 4.1: Verify no stale references remain

- **Location**: `.claude/skills/asw-expert/`
- **Action**: Search for any remaining old references
- **Details**:
  - Grep for "adws-expert" - should return 0
  - Grep for "adw_modules" - should return 0
  - Grep for "ADWState" without context - should return 0 (except migration notes)
  - Ensure "asw-expert" is used consistently
- **Depends on**: Step 3.3
- **Verify**: All searches return expected results

#### Step 4.2: Verify skill loads correctly

- **Location**: `.claude/skills/asw-expert/SKILL.md`
- **Action**: Validate skill format
- **Details**:
  - Check frontmatter is valid YAML
  - Check all reference files exist
  - Verify skill can be invoked
- **Depends on**: Step 4.1
- **Verify**: Skill invocation works

---

## Critical Considerations

### Security
- No security concerns - this is a documentation/skill rename
- Ensure no credentials or sensitive paths are exposed in examples

### Performance
- No performance impact - documentation only change

### Edge Cases
- Users may still reference old "adws-expert" skill name - add migration note
- Legacy scripts may use old module paths - backward compatibility aliases exist per asw/README.md

### Breaking Changes
- Skill name changes from `adws-expert` to `asw-expert`
- Users invoking the old skill name will need to update
- Mitigation: Could create symlink or alias (optional)

---

## Testing Strategy

### Required Tests
- [ ] Verify skill directory exists at new location
- [ ] Verify SKILL.md has updated frontmatter
- [ ] Verify no "adws-expert" references remain
- [ ] Verify both app and io workflows are documented
- [ ] Verify all reference files updated

### Validation Commands
```bash
# Verify directory renamed
ls -la .claude/skills/asw-expert/

# Check for stale references
grep -r "adws-expert" .claude/skills/

# Check for old module paths
grep -r "adw_modules" .claude/skills/asw-expert/

# Verify skill structure
ls .claude/skills/asw-expert/references/
```

---

## Verification Checklist

- [ ] Directory renamed from adws-expert to asw-expert
- [ ] SKILL.md frontmatter updated (name, description)
- [ ] Title changed from "ADWS Expert" to "ASW Expert"
- [ ] Bot identifiers updated to ASW-APP-AGENTS and ASW-IO-AGENTS
- [ ] Module paths updated to asw/modules/
- [ ] State class names updated (ASWAppState, ASWIOState)
- [ ] Both app and io workflows documented
- [ ] IO-specific examples added
- [ ] architecture.md updated for both systems
- [ ] troubleshooting.md includes IO issues
- [ ] improvement_patterns.md includes IO patterns
- [ ] All tests pass
- [ ] No lint/type errors
- [ ] Feature works as specified

---

## Implementation Tips

- **Start with**: Step 1.1 (directory rename) - everything depends on this
- **Key insight**: The ASW system unifies ADW (app) and IPE (io) under one umbrella, so the skill should reflect this unified architecture
- **Common pitfall**: Forgetting to update internal references after directory rename
- **Pattern to follow**: Reference `asw/README.md` for the canonical naming conventions and migration table

---

## Rollback Strategy

If implementation needs to be reverted:

1. Rename directory back to adws-expert
2. Restore original file contents from git

```bash
# Git commands for rollback
git checkout -- .claude/skills/
mv .claude/skills/asw-expert .claude/skills/adws-expert  # If already renamed
```

# Low-Level Implementation Plan

Generate an ultra-detailed, low-level implementation plan for the task described in `$ARGUMENTS`.

## Variables

task: $ARGUMENTS
output_dir: specs
filename_prefix: plan-

## Instructions

Follow these steps in order to create a comprehensive, actionable implementation plan:

### Step 1: Input Validation

- IMPORTANT: If the task is too vague for detailed planning, respond using the `Clarification Format` section below and stop.
- A valid task must describe: WHAT to build/change AND WHERE in the codebase (or be specific enough to determine WHERE)

### Step 2: Context Gathering (MANDATORY)

You MUST explore the codebase before creating the plan. Use these tools:

1. **Find similar implementations**: Use Glob to search for files matching patterns related to the task
2. **Search for keywords**: Use Grep to find relevant code patterns and existing implementations
3. **Read key files**: Read files that will be modified or serve as patterns to follow
4. **Check dependencies**: Read package.json, requirements.txt, or pyproject.toml as relevant
5. **Review architecture**: Identify file organization patterns, naming conventions, and module structure

IMPORTANT: Plans must reference ACTUAL file paths and patterns from the codebase. Generic advice without codebase grounding is not acceptable.

### Step 3: Generate Plan

Fill in the `Plan Template` below, replacing ALL `<placeholder>` markers with specific details from your codebase exploration.

### Step 4: Save Plan

1. Normalize the task to a filename:
   - Convert to lowercase
   - Replace spaces with hyphens
   - Remove special characters (keep alphanumeric and hyphens only)
   - Truncate to 80 characters if needed
2. Save to: `specs/plan-<normalized-task>.md`
3. If file exists, append timestamp suffix: `plan-<task>-<YYYYMMDD-HHMMSS>.md`

### Step 5: Return Report

Return the `Report Format` exactly as specified below.

---

## Plan Template

```markdown
# <task title>

## Overview

**Task**: <one-line task description>
**Type**: <feature | bugfix | refactor | chore | infrastructure>
**Scope**: <small (1-3 files) | medium (4-10 files) | large (10+ files)>
**Estimated Steps**: <number>

---

## Context Analysis

### Codebase Findings

| Finding | Details |
|---------|---------|
| Similar implementations | <file paths of similar code to reference> |
| Relevant patterns | <patterns identified in the codebase> |
| Key dependencies | <libraries, frameworks, versions> |
| Integration points | <files/modules that interact with this change> |

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `<path/to/file>` | MODIFY | <what changes will be made> |
| `<path/to/newfile>` | CREATE | <purpose of new file> |
| `<path/to/oldfile>` | DELETE | <why file should be removed> |

### Tech Stack Context

- **Framework**: <framework name and version>
- **Language**: <language and version>
- **Build tools**: <relevant build/test tools>
- **Key libraries**: <libraries relevant to this task>

---

## Implementation Roadmap

### Phase 1: <phase name>

#### Step 1.1: <action description>

- **Location**: `<file path>:<line number if known>` or `(new) <file path>`
- **Action**: <specific action to take>
- **Details**:
  - <implementation detail 1>
  - <implementation detail 2>
  ```<language>
  // Code example if helpful
  ```
- **Depends on**: <"None" or "Step X.X">
- **Verify**: <how to verify this step succeeded>

#### Step 1.2: <next action>

<repeat structure for each step>

### Phase 2: <phase name>

<repeat structure for each phase>

---

## Critical Considerations

### Security
- <security concern 1 and mitigation>
- <security concern 2 and mitigation>

### Performance
- <performance consideration 1>
- <performance consideration 2>

### Edge Cases
- <edge case 1 - description and handling>
- <edge case 2 - description and handling>

### Breaking Changes
- <potential breaking change and mitigation>

---

## Testing Strategy

### Required Tests
- [ ] <test description 1>
- [ ] <test description 2>
- [ ] <test description 3>

### Validation Commands
```bash
<command 1 - description>
<command 2 - description>
```

---

## Verification Checklist

- [ ] <verification item 1>
- [ ] <verification item 2>
- [ ] <verification item 3>
- [ ] All tests pass
- [ ] No lint/type errors
- [ ] Feature works as specified

---

## Implementation Tips

- **Start with**: <which step to begin with and why>
- **Key insight**: <most important thing to understand>
- **Common pitfall**: <mistake to avoid>
- **Pattern to follow**: <reference to existing pattern in codebase>

---

## Rollback Strategy

If implementation needs to be reverted:

1. <rollback step 1>
2. <rollback step 2>

```bash
# Git commands for rollback
git checkout -- <files to revert>
```
```

---

## Clarification Format

If the task is too vague, respond with:

```
CLARIFICATION_NEEDED

Task: "<original task>"

To create an actionable plan, please clarify:

1. <specific question about scope or requirements>
2. <specific question about target location in codebase>
3. <specific question about desired behavior or constraints>

Alternatively, provide a more detailed task description.
```

---

## Report Format

After generating and saving the plan, respond with ONLY this format:

```
PLAN_GENERATED

File: specs/<filename>.md
Task: "<original task>"
Scope: <small | medium | large>
Phases: <number>
Steps: <total step count>

Key Findings:
- <finding 1 from codebase exploration>
- <finding 2 from codebase exploration>
- <finding 3 from codebase exploration>

Phases:
1. <phase 1 name> (<step count> steps)
2. <phase 2 name> (<step count> steps)
3. <phase 3 name> (<step count> steps)

Ready to implement? Use: /implement specs/<filename>.md
```

---

## Quality Gates

Before finalizing the plan, verify:

- [ ] At least 80% of steps reference actual file paths from the codebase
- [ ] All `<placeholder>` markers have been replaced
- [ ] Dependencies between steps are clearly identified
- [ ] Critical considerations section has 3+ items
- [ ] Verification checklist has 5+ items
- [ ] No "TODO" or "figure out later" language
- [ ] Steps are granular (5-15 minutes each to implement)

---

## Examples

### Good Step (Specific)

```markdown
#### Step 1.1: Add breeding status field to Item interface

- **Location**: `app/lib/content.ts:15-25`
- **Action**: Add optional `breedingStatus` field to Item interface
- **Details**:
  - Add after existing `category` field (line 22)
  - Follow pattern from `currentLocation` field
  ```typescript
  breedingStatus?: {
    bredTo: string;      // Sire slug
    expectedFoal: string; // Expected date or season
  };
  ```
- **Depends on**: None
- **Verify**: `cd app && bun tsc --noEmit` passes
```

### Bad Step (Too Generic)

```markdown
#### Step 1.1: Add new field

- **Location**: data file
- **Action**: Add the field
- **Details**: Update the interface
- **Depends on**: None
- **Verify**: Build works
```

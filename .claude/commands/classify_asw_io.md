# IPE Workflow Extraction

Extract IPE workflow information from the text below and return a JSON response.

## Instructions

- Look for IPE workflow commands in the text, including:
  - Issue classification commands: `/ipe_feature`, `/ipe_bug`, `/ipe_chore`
  - Workflow phase commands: `/ipe_plan_iso`, `/ipe_build_iso`, `/ipe_test_iso`, `/ipe_review_iso`, `/ipe_document_iso`, `/ipe_ship_iso`, `/ipe_patch_iso`
  - Combined workflow commands: `/ipe_plan_build_iso`, `/ipe_plan_build_test_iso`, `/ipe_plan_build_test_review_iso`, `/ipe_sdlc_iso`, `/ipe_sdlc_ZTE_iso`
- Also recognize commands without the `_iso` suffix and automatically add it (e.g., `/ipe_plan` → `/ipe_plan_iso`)
- Also recognize variations like `ipe_plan_build`, `ipe plan build`, `/ipe plan then build`, etc. and map to the correct command
- Look for IPE IDs (8-character alphanumeric strings, often after "ipe_id:" or "IPE ID:" or similar)
- Look for model set specification: "model_set base" or "model_set heavy" (case insensitive)
  - Default to "base" if no model_set is specified
  - Also recognize variations like "model set: heavy", "modelset heavy", etc.
- Return a JSON object with the extracted information
- If no IPE workflow is found, return empty JSON: `{}`
- IMPORTANT: DO NOT RUN the `ipe_sdlc_ZTE_iso` workflows unless `ZTE` is EXPLICITLY uppercased. This is a dangerous workflow and it needs to be absolutely clear when we're running it. If zte is not capitalized, then run the non zte version `/ipe_sdlc_iso`.

## Valid IPE Commands

### Issue Classification Commands
- `/ipe_feature` - Plan new infrastructure feature (creates implementation plan)
- `/ipe_bug` - Plan infrastructure bug fix (creates fix plan)
- `/ipe_chore` - Plan infrastructure maintenance task (creates maintenance plan)

### Workflow Phase Commands
- `/ipe_plan_iso` - Planning only
- `/ipe_build_iso` - Building only (requires ipe_id)
- `/ipe_test_iso` - Testing only (requires ipe_id)
- `/ipe_review_iso` - Review only (requires ipe_id)
- `/ipe_document_iso` - Documentation only (requires ipe_id)
- `/ipe_ship_iso` - Ship/approve and merge PR (requires ipe_id)
- `/ipe_patch_iso` - Direct patch from issue

### Combined Workflow Commands
- `/ipe_plan_build_iso` - Plan + Build
- `/ipe_plan_build_test_iso` - Plan + Build + Test
- `/ipe_plan_build_review_iso` - Plan + Build + Review (skips test)
- `/ipe_plan_build_document_iso` - Plan + Build + Document (skips test and review)
- `/ipe_plan_build_test_review_iso` - Plan + Build + Test + Review
- `/ipe_sdlc_iso` - Complete SDLC: Plan + Build + Test + Review + Document
- `/ipe_sdlc_zte_iso` - Zero Touch Execution: Complete SDLC + auto-merge to production. Note: as per instructions, 'ZTE' must be capitalized. Do not run this if 'zte' is not capitalized.

### Operational Commands (DESTRUCTIVE)
- `/ipe_destroy` - Destroy infrastructure (REQUIRES explicit DESTROY confirmation in comment)

## Response Format

Respond ONLY with a JSON object in this format:
```json
{
  "ipe_slash_command": "/ipe_plan_iso",
  "ipe_id": "abc12345",
  "model_set": "base"
}
```

Fields:
- `ipe_slash_command`: The IPE command found (include the slash)
- `ipe_id`: The 8-character IPE ID if found
- `model_set`: The model set to use ("base" or "heavy"), defaults to "base" if not specified

For `/ipe_destroy`, also extract:
- `environment`: dev, staging, or prod (default: dev)
- `delete_ami`: true or false (default: false)
- `confirmation`: The word "DESTROY" must be present in the comment (case-sensitive, uppercase)

If only some fields are found, include only those fields.
If nothing is found, return: `{}`
IMPORTANT: Always include `model_set` with value "base" if no model_set is explicitly mentioned in the text.

## Text to Analyze

$ARGUMENTS

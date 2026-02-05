# ASW App Workflow Extraction

Extract ASW App workflow information from the text below and return a JSON response.

## Instructions

- Look for ASW App workflow commands in the text (e.g., `/asw_app_plan_iso`, `/asw_app_build_iso`, `/asw_app_test_iso`, `/asw_app_review_iso`, `/asw_app_document_iso`, `/asw_app_patch_iso`, `/asw_app_plan_build_iso`, `/asw_app_plan_build_test_iso`, `/asw_app_plan_build_test_review_iso`, `/asw_app_sdlc_iso`, `/asw_app_sdlc_ZTE_iso`)
- Also recognize legacy ADW commands (e.g., `/adw_plan_iso`) and map to new ASW App commands
- Also recognize commands without the `_iso` suffix and automatically add it (e.g., `/asw_app_plan` -> `/asw_app_plan_iso`)
- Also recognize variations like `asw_app_plan_build`, `asw app plan build`, `/asw app plan then build`, etc. and map to the correct command
- Look for ASW IDs (8-character alphanumeric strings, often after "asw_id:" or "ASW ID:" or similar)
- Also recognize legacy "adw_id:" or "ADW ID:" prefixes
- Look for model set specification: "model_set base" or "model_set heavy" (case insensitive)
  - Default to "base" if no model_set is specified
  - Also recognize variations like "model set: heavy", "modelset heavy", etc.
- Return a JSON object with the extracted information
- If no ASW App workflow is found, return empty JSON: `{}`
- The `/asw_app_sdlc_ZTE_iso` workflow is a Zero Touch Execution workflow that completes the full SDLC and auto-merges to production. This is a powerful workflow that should be used with caution.

## Valid ASW App Commands

- `/asw_app_plan_iso` - Planning only
- `/asw_app_build_iso` - Building only (requires asw_id)
- `/asw_app_test_iso` - Testing only (requires asw_id)
- `/asw_app_review_iso` - Review only (requires asw_id)
- `/asw_app_document_iso` - Documentation only (requires asw_id)
- `/asw_app_ship_iso` - Ship/approve and merge PR (requires asw_id)
- `/asw_app_patch_iso` - Direct patch from issue
- `/asw_app_plan_build_iso` - Plan + Build
- `/asw_app_plan_build_test_iso` - Plan + Build + Test
- `/asw_app_plan_build_review_iso` - Plan + Build + Review (skips test)
- `/asw_app_plan_build_document_iso` - Plan + Build + Document (skips test and review)
- `/asw_app_plan_build_test_review_iso` - Plan + Build + Test + Review
- `/asw_app_sdlc_iso` - Complete SDLC: Plan + Build + Test + Review + Document
- `/asw_app_sdlc_ZTE_iso` - Zero Touch Execution: Complete SDLC + auto-merge to production

## Response Format

Respond ONLY with a JSON object in this format:
```json
{
  "asw_slash_command": "/asw_app_plan",
  "asw_id": "abc12345",
  "model_set": "base"
}
```

Fields:
- `asw_slash_command`: The ASW App command found (include the slash)
- `asw_id`: The 8-character ASW ID if found
- `model_set`: The model set to use ("base" or "heavy"), defaults to "base" if not specified

If only some fields are found, include only those fields.
If nothing is found, return: `{}`
IMPORTANT: Always include `model_set` with value "base" if no model_set is explicitly mentioned in the text.

## Text to Analyze

$ARGUMENTS

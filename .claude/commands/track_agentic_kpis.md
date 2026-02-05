# Track Agentic KPIs

Update or create the ADW performance tracking entry in `app_docs/agentic_kpis.md`. This command analyzes the current ADW run's metrics and appends an entry to the KPI log. Summary metrics are regenerated separately using `scripts/regenerate_kpi_summary.py`. Think hard about building this, these are key KPIs for the Agentic Software Workflow - App (ASW App) system. Use the python commands as suggestions and guides for how to calculate the values. Ultimately, do whatever python calculation you need to do to get the values.

## Variables

state_json: $ARGUMENTS
attempts_incrementing_adws: [`adw_plan_iso`, `adw_patch_iso`]

## Instructions

### 1. Parse State Data
- Parse the provided state_json to extract:
  - adw_id
  - issue_number
  - issue_class
  - plan_file path
  - all_adws list (contains workflow names run)

### 2. Calculate Metrics

#### Get Current Date/Time
- Run `date` command to get current date/time

#### Calculate Attempts
IMPORTANT: Use Python to calculate the exact count value:
- Count occurrences of any of the adws in the attempts_incrementing_adws list in all_adws list
- Run: `python -c "all_adws = <list>; attempts = sum(1 for w in all_adws if any(adw in w for adw in attempts_incrementing_adws)); print(attempts)"`

#### Calculate Plan Size
- If plan_file exists in state, read the file
- Count total lines using: `wc -l <plan_file>`
- If file doesn't exist, use 0

#### Calculate Diff Statistics
- Run: `git diff origin/main --shortstat`
- Parse output to extract:
  - Files changed
  - Lines added
  - Lines removed
- Format as: "Added/Removed/Total Files" (e.g., "150/25/8")

### 3. Read Existing File
- Check if `app_docs/agentic_kpis.md` exists
- If it exists, read and parse the existing entries table
- If not, prepare to create new file with entries table

### 4. Update ADW KPIs Table
- Check if current adw_id already exists in the table
- If exists: update that row with new values
- If not: append new row at the bottom
- Set Created date on new rows, Updated date on existing rows
- Use `date` command for timestamps

### 5. Write Updated File
- Create/update `app_docs/agentic_kpis.md` with entries only (no summary)
- Ensure proper markdown table formatting
- DO NOT calculate or update summary metrics - they are regenerated separately

## File Structure

```markdown
# ADW KPIs Log

Append-only log of individual ADW workflow runs. Summary metrics are auto-generated in `agentic_kpis_summary.md`.

> **Note:** This file uses git union merge. Run `uv run scripts/regenerate_kpi_summary.py` to update the summary.

## ADW KPIs

| Date   | ADW ID | Issue Number | Issue Class | Attempts   | Plan Size (lines) | Diff Size (Added/Removed/Files) | Created   | Updated   |
| ------ | ------ | ------------ | ----------- | ---------- | ----------------- | ------------------------------- | --------- | --------- |
| <date> | <id>   | <number>     | <class>     | <attempts> | <size>            | <diff>                          | <created> | <updated> |
```

## Report

Return only: "Updated app_docs/agentic_kpis.md - run 'uv run scripts/regenerate_kpi_summary.py' to update summary"
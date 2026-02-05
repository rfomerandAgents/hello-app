# Track IPE Agentic KPIs

Update or create the IPE performance tracking tables in `ipe_docs/agentic_kpis.md`. This command analyzes the current IPE run's metrics and maintains both summary and detailed KPI tables. Think hard about building this, these are key KPIs for the Agentic Software Workflow - IO (ASW IO) system. Use the python commands as suggestions and guides for how to calculate the values. Ultimately, do whatever python calculation you need to do to get the values.

## Variables

state_json: $ARGUMENTS
attempts_incrementing_ipes: [`ipe_plan_iso`, `ipe_patch_iso`]

## Instructions

### 1. Parse State Data
- Parse the provided state_json to extract:
  - ipe_id (8-character workflow identifier)
  - issue_number
  - issue_class (infra, security, cost, config, fix, chore)
  - plan_file path (infrastructure specification)
  - all_ipes list (contains workflow names run)
  - environment (dev, staging, prod) if available

### 2. Calculate Metrics

#### Get Current Date/Time
- Run `date` command to get current date/time

#### Calculate Attempts
IMPORTANT: Use Python to calculate the exact count value:
- Count occurrences of any of the ipes in the attempts_incrementing_ipes list in all_ipes list
- Run: `python -c "all_ipes = <list>; attempts_incrementing_ipes = ['ipe_plan_iso', 'ipe_patch_iso']; attempts = sum(1 for w in all_ipes if any(ipe in w for ipe in attempts_incrementing_ipes)); print(attempts)"`

#### Calculate Plan Size
- If plan_file exists in state, read the file
- Count total lines using: `wc -l <plan_file>`
- If file doesn't exist, use 0

#### Calculate Terraform Diff Statistics
- Run: `git diff origin/main --shortstat -- io/terraform/`
- Parse output to extract:
  - Files changed (Terraform files only)
  - Lines added
  - Lines removed
- Format as: "Added/Removed/Total Files" (e.g., "150/25/8")
- If no Terraform changes, use "0/0/0"

#### Calculate Resource Impact (Optional Enhancement)
- Parse Terraform diff to count:
  - Resources added (lines starting with `+resource`)
  - Resources modified (changes to existing resources)
  - Resources removed (lines starting with `-resource`)
- Format as: "Added/Modified/Removed Resources" (e.g., "3/2/1")

### 3. Read Existing File
- Check if `ipe_docs/agentic_kpis.md` exists
- If it exists, read and parse the existing tables
- If not, prepare to create new file with both tables

### 4. Update IPE KPIs Table
- Check if current ipe_id already exists in the table
- If exists: update that row with new values
- If not: append new row at the bottom
- Set Created date on new rows, Updated date on existing rows
- Use `date` command for timestamps

### 5. Calculate Agentic KPIs

IMPORTANT: All calculations must be done using Python expressions. Use `python -c "print(expression)"` for every numeric calculation.

#### Current Streak
- Count consecutive rows from bottom of IPE KPIs table where Attempts ≤ 2
- Use Python: `python -c "attempts_list = <list>; streak = 0\nfor a in reversed(attempts_list):\n    if a <= 2:\n        streak += 1\n    else:\n        break\nprint(streak)"`

#### Longest Streak
- Find longest consecutive sequence where Attempts ≤ 2
- Use Python to calculate

#### Total Plan Size
- Sum all plan sizes from IPE KPIs table
- Use Python: `python -c "sizes = <list>; print(sum(sizes))"`

#### Largest Plan Size
- Find maximum plan size
- Use Python: `python -c "sizes = <list>; print(max(sizes) if sizes else 0)"`

#### Total Diff Size
- Sum all diff statistics (added + removed lines)
- Parse each diff entry and sum using Python

#### Largest Diff Size
- Find maximum diff (added + removed lines)
- Use Python to calculate

#### Average Presence
- Calculate average of all attempts
- Use Python: `python -c "attempts = <list>; print(round(sum(attempts) / len(attempts), 2) if attempts else 0)"`
- Round to 2 decimal places

#### Total Infrastructure Resources Changed (New Metric)
- Sum all resource changes across IPE runs
- Parse "Resources" column if available
- Use Python to calculate

### 6. Write Updated File
- Create/update `ipe_docs/agentic_kpis.md` with the structure below
- Ensure proper markdown table formatting
- Include "Last Updated" timestamp using `date` command

## File Structure

```markdown
# IPE Agentic KPIs

Performance metrics for the Agentic Software Workflow - IO (ASW IO) system.

## Agentic KPIs

Summary metrics across all IPE runs.

| Metric                    | Value          | Last Updated |
| ------------------------- | -------------- | ------------ |
| Current Streak            | <number>       | <date>       |
| Longest Streak            | <number>       | <date>       |
| Total Plan Size           | <number> lines | <date>       |
| Largest Plan Size         | <number> lines | <date>       |
| Total Diff Size           | <number> lines | <date>       |
| Largest Diff Size         | <number> lines | <date>       |
| Average Presence          | <number>       | <date>       |
| Total Resources Changed   | <number>       | <date>       |

## IPE KPIs

Detailed metrics for individual IPE workflow runs.

| Date   | IPE ID | Issue Number | Issue Class | Environment | Attempts | Plan Size (lines) | Diff Size (Added/Removed/Files) | Resources (Add/Mod/Del) | Created   | Updated   |
| ------ | ------ | ------------ | ----------- | ----------- | -------- | ----------------- | ------------------------------- | ----------------------- | --------- | --------- |
| <date> | <id>   | <number>     | <class>     | <env>       | <n>      | <size>            | <diff>                          | <resources>             | <created> | <updated> |
```

## Report

Return only: "Updated ipe_docs/agentic_kpis.md"

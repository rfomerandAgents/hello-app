#!/bin/bash
set -euo pipefail

SKILLS_DIR=".claude/skills"

# Find all SKILL.md files, extract name and description from YAML frontmatter only
for skill_path in "$SKILLS_DIR"/*/SKILL.md; do
    if [ -f "$skill_path" ]; then
        # Extract only the first name: and description: lines (in the frontmatter)
        name=$(sed -n '2,10p' "$skill_path" | grep "^name:" | head -1 | sed 's/^name:[[:space:]]*//' | tr -d "'\"")
        description=$(sed -n '2,10p' "$skill_path" | grep "^description:" | head -1 | sed 's/^description:[[:space:]]*//')

        if [ -n "$name" ] && [ -n "$description" ]; then
            echo "$name|$description"
        fi
    fi
done | sort | while IFS='|' read -r name desc; do
    echo "- **$name** - $desc"
done

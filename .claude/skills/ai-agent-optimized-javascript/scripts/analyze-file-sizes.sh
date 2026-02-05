#!/bin/bash
#
# File Size Analysis Script
# Identifies JavaScript/TypeScript files that exceed recommended size thresholds
# for agent-friendly modular development.
#
# Usage:
#   ./analyze-file-sizes.sh [directory]
#   ./analyze-file-sizes.sh              # Analyzes current directory
#   ./analyze-file-sizes.sh app/         # Analyzes app directory
#   ./analyze-file-sizes.sh --verbose    # Shows additional details
#

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OPTIMAL_MAX=200
WARNING_THRESHOLD=200
CRITICAL_THRESHOLD=400
TOP_N=20

# Parse arguments
DIRECTORY="${1:-.}"
VERBOSE=false

if [[ "$1" == "--verbose" ]] || [[ "$2" == "--verbose" ]]; then
  VERBOSE=true
fi

# Validate directory
if [[ ! -d "$DIRECTORY" ]]; then
  echo -e "${RED}Error: Directory '$DIRECTORY' does not exist${NC}"
  exit 1
fi

echo "================================================"
echo "  JavaScript/TypeScript File Size Analysis"
echo "================================================"
echo ""
echo "Analyzing: $DIRECTORY"
echo "Thresholds:"
echo "  - Optimal: < ${OPTIMAL_MAX} lines"
echo "  - Warning: ${WARNING_THRESHOLD}-${CRITICAL_THRESHOLD} lines"
echo "  - Critical: > ${CRITICAL_THRESHOLD} lines"
echo ""
echo "------------------------------------------------"
echo ""

# Find all JS/TS files, exclude common directories
FILES=$(find "$DIRECTORY" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.next/*" \
  ! -path "*/out/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/.git/*" 2>/dev/null)

if [[ -z "$FILES" ]]; then
  echo -e "${YELLOW}No JavaScript/TypeScript files found in $DIRECTORY${NC}"
  exit 0
fi

# Count lines for all files and sort
echo "Top $TOP_N Largest Files:"
echo "================================================"
printf "%-8s %-60s\n" "Lines" "File"
echo "------------------------------------------------"

CRITICAL_COUNT=0
WARNING_COUNT=0
OPTIMAL_COUNT=0

# Process files and categorize
while IFS= read -r line; do
  # Parse line count and filename
  LINE_COUNT=$(echo "$line" | awk '{print $1}')
  FILENAME=$(echo "$line" | awk '{$1=""; print $0}' | sed 's/^ //')

  # Skip if not a number
  if ! [[ "$LINE_COUNT" =~ ^[0-9]+$ ]]; then
    continue
  fi

  # Categorize and colorize output
  if (( LINE_COUNT > CRITICAL_THRESHOLD )); then
    COLOR=$RED
    CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
    STATUS="[CRITICAL]"
  elif (( LINE_COUNT > WARNING_THRESHOLD )); then
    COLOR=$YELLOW
    WARNING_COUNT=$((WARNING_COUNT + 1))
    STATUS="[WARNING]"
  else
    COLOR=$GREEN
    OPTIMAL_COUNT=$((OPTIMAL_COUNT + 1))
    STATUS="[OPTIMAL]"
  fi

  # Print colored output
  if $VERBOSE; then
    printf "${COLOR}%-8s %-60s %s${NC}\n" "$LINE_COUNT" "$FILENAME" "$STATUS"
  else
    printf "${COLOR}%-8s %-60s${NC}\n" "$LINE_COUNT" "$FILENAME"
  fi

done < <(echo "$FILES" | xargs wc -l 2>/dev/null | sort -rn | head -n $TOP_N)

echo ""
echo "================================================"
echo "Summary:"
echo "------------------------------------------------"

TOTAL_COUNT=$((CRITICAL_COUNT + WARNING_COUNT + OPTIMAL_COUNT))

printf "Total files analyzed: %d\n" "$TOTAL_COUNT"
printf "${GREEN}Optimal (<= %d lines): %d files${NC}\n" "$OPTIMAL_MAX" "$OPTIMAL_COUNT"
printf "${YELLOW}Warning (%d-%d lines): %d files${NC}\n" "$WARNING_THRESHOLD" "$CRITICAL_THRESHOLD" "$WARNING_COUNT"
printf "${RED}Critical (> %d lines): %d files${NC}\n" "$CRITICAL_THRESHOLD" "$CRITICAL_COUNT"

echo ""

# Recommendations
if (( CRITICAL_COUNT > 0 )); then
  echo -e "${RED}⚠️  CRITICAL: ${CRITICAL_COUNT} file(s) exceed ${CRITICAL_THRESHOLD} lines${NC}"
  echo "   These files MUST be split for agent-friendly development."
  echo "   High merge conflict risk with parallel development."
  echo ""
fi

if (( WARNING_COUNT > 0 )); then
  echo -e "${YELLOW}⚠️  WARNING: ${WARNING_COUNT} file(s) between ${WARNING_THRESHOLD}-${CRITICAL_THRESHOLD} lines${NC}"
  echo "   Consider splitting these files to reduce merge conflicts."
  echo "   Evaluate for multiple concerns that can be separated."
  echo ""
fi

if (( CRITICAL_COUNT == 0 && WARNING_COUNT == 0 )); then
  echo -e "${GREEN}✓ Excellent! All files are optimally sized for parallel development.${NC}"
  echo ""
fi

# Detailed recommendations
if $VERBOSE && (( CRITICAL_COUNT > 0 || WARNING_COUNT > 0 )); then
  echo "------------------------------------------------"
  echo "Refactoring Recommendations:"
  echo "------------------------------------------------"
  echo ""
  echo "For files > ${CRITICAL_THRESHOLD} lines:"
  echo "  1. Identify distinct concerns (types, data, logic, UI)"
  echo "  2. Create a directory for the module"
  echo "  3. Split into focused files (50-200 lines each)"
  echo "  4. Use barrel file (index.ts) for public API"
  echo "  5. Update imports across codebase"
  echo ""
  echo "For files ${WARNING_THRESHOLD}-${CRITICAL_THRESHOLD} lines:"
  echo "  1. Check for multiple unrelated exports"
  echo "  2. Extract sub-components or hooks"
  echo "  3. Move utility functions to separate file"
  echo "  4. Separate data from logic"
  echo ""
  echo "Resources:"
  echo "  - See .claude/skills/ai-agent-optimized-javascript/SKILL.md"
  echo "  - See assets/before-after-examples.md for real examples"
  echo "  - See assets/checklist.md for refactoring process"
  echo ""
fi

echo "================================================"

# Exit with appropriate code
if (( CRITICAL_COUNT > 0 )); then
  exit 2  # Critical issues found
elif (( WARNING_COUNT > 0 )); then
  exit 1  # Warnings found
else
  exit 0  # All good
fi

# Pre-Refactoring Checklist

Use this checklist before refactoring any file to ensure a smooth, safe modularization process.

## Pre-Flight Checks

### 1. Current State Assessment

- [ ] All tests passing before refactoring starts
- [ ] No uncommitted changes in working directory
- [ ] Current branch is up to date with main
- [ ] File to refactor has been identified and analyzed
- [ ] Line count and complexity measured

**Commands**:
```bash
# Ensure tests pass
npm test

# Check git status
git status

# Ensure up to date
git pull origin main

# Count lines in target file
wc -l path/to/file.ts
```

---

### 2. Impact Analysis

- [ ] Identified all files that import from target file
- [ ] Documented current import statements
- [ ] Checked for circular dependencies
- [ ] Identified external packages/libraries used
- [ ] Verified no dynamic imports that might be missed

**Commands**:
```bash
# Find all files importing target
grep -r "from.*items" app/ lib/ components/

# Find dynamic imports
grep -r "import(" app/ lib/ components/

# Check for circular dependencies
npx madge --circular src/
```

---

### 3. Refactoring Plan

- [ ] Identified distinct concerns in file (types, data, logic, etc.)
- [ ] Planned new file structure
- [ ] Sketched out which code goes in which file
- [ ] Verified no circular dependencies will be created
- [ ] Designed barrel file (index.ts) for public API
- [ ] Planned import path updates

**Template**:
```markdown
## Refactoring Plan: lib/items.ts

Current: 758 lines, multiple concerns

New Structure:
- lib/items/types.ts (~45 lines) - Type definitions
- lib/items/data.ts (~450 lines) - Item data array
- lib/items/queries.ts (~80 lines) - Query functions
- lib/items/filters.ts (~60 lines) - Filter functions
- lib/items/breeding.ts (~30 lines) - Breeding logic
- lib/items/utils.ts (~30 lines) - Utility functions
- lib/items/index.ts (~20 lines) - Public API barrel

Dependency Graph:
types.ts (no deps)
  ↑
data.ts (depends on types)
  ↑
utils.ts (depends on types)
  ↑
queries.ts (depends on types, data)
  ↑
filters.ts (depends on types, data, utils)
  ↑
breeding.ts (depends on types, queries)
  ↑
index.ts (re-exports all)

No circular dependencies ✓
```

---

### 4. Safety Checks

- [ ] No breaking changes to public API (unless intentional)
- [ ] Export signatures will remain the same
- [ ] TypeScript types are fully defined
- [ ] No hardcoded paths that will break
- [ ] Build process will not be affected

---

### 5. Test Coverage

- [ ] Existing test files identified
- [ ] Test coverage measured before refactoring
- [ ] Plan for updating test imports
- [ ] Plan for adding new tests (if needed)

**Commands**:
```bash
# Check test coverage
npm run test -- --coverage

# Find related test files
find . -name "*items*.test.ts" -o -name "*items*.spec.ts"
```

---

## During Refactoring

### 6. Incremental Extraction

- [ ] Create new directory structure first
- [ ] Extract one concern at a time (start with types)
- [ ] Run tests after each extraction
- [ ] Commit after each successful extraction
- [ ] Keep original file until fully extracted

**Process**:
```bash
# Step 1: Create directory
mkdir lib/items

# Step 2: Extract types
# Create lib/items/types.ts
# Copy type definitions
# Test: npm test

# Step 3: Extract data
# Create lib/items/data.ts
# Import types from ./types
# Test: npm test

# Step 4: Continue for each concern...

# Step 5: Create barrel file
# Create lib/items/index.ts
# Re-export public API

# Step 6: Delete original file
# git rm lib/items.ts
```

---

### 7. Import Updates

- [ ] Updated all absolute imports
- [ ] Updated all relative imports
- [ ] Verified IDE auto-import suggestions work
- [ ] Updated import statements in test files
- [ ] Updated import statements in documentation

**Find and Replace Pattern**:
```typescript
// Before
import { Item, getItemBySlug } from '@/lib/items';

// After (if barrel file is used)
import { Item, getItemBySlug } from '@/lib/items';
// No change needed ✓

// OR (if not using barrel)
import { Item } from '@/lib/items/types';
import { getItemBySlug } from '@/lib/items/queries';
```

---

### 8. Verification

- [ ] All tests pass after refactoring
- [ ] TypeScript compilation succeeds with no errors
- [ ] ESLint passes with no new warnings
- [ ] Application builds successfully
- [ ] Application runs without errors
- [ ] No console errors or warnings
- [ ] Import paths are clean and consistent

**Commands**:
```bash
# Run all verification
npm run type-check    # TypeScript compilation
npm run lint          # ESLint
npm run build         # Production build
npm test              # All tests
npm run dev           # Start dev server and manually test
```

---

### 9. Code Review Preparation

- [ ] Created clear commit message(s)
- [ ] Documented refactoring in PR description
- [ ] Highlighted any breaking changes
- [ ] Listed files that import from refactored module
- [ ] Provided before/after file structure
- [ ] Added screenshots if UI is affected

**Commit Message Template**:
```
refactor: split lib/items.ts into modular files

BREAKING CHANGE: None - public API unchanged via barrel file

Changes:
- Split 758-line monolithic file into 7 focused modules
- Created lib/items/ directory with:
  - types.ts (type definitions)
  - data.ts (item data array)
  - queries.ts (query functions)
  - filters.ts (filter functions)
  - breeding.ts (breeding logic)
  - utils.ts (utility functions)
  - index.ts (public API barrel)

Benefits:
- Enables parallel development (agents can work on different files)
- Improved testability (each module can be tested independently)
- Better organization (clear separation of concerns)
- No import changes required (barrel file maintains API)

Testing:
- All existing tests pass
- No new tests added (behavior unchanged)
- TypeScript compilation succeeds
- Application builds and runs correctly
```

---

### 10. Post-Refactoring

- [ ] Merged refactoring PR
- [ ] Updated documentation/wiki
- [ ] Informed team of changes
- [ ] Monitored for any issues in production
- [ ] Measured improvement metrics (file size, conflict rate, etc.)

---

## Red Flags - Don't Proceed If:

- ❌ Tests are failing before you start
- ❌ You don't understand the current code
- ❌ There are significant merge conflicts to resolve first
- ❌ You're not sure about circular dependency impacts
- ❌ Major deadline is imminent (refactoring can wait)
- ❌ Multiple other PRs are touching the same file
- ❌ No time to properly test the changes

---

## Quick Start Checklist (Minimal)

For small, low-risk refactorings:

- [ ] Tests passing ✓
- [ ] Backup created (git commit or branch)
- [ ] New file structure created
- [ ] Code moved incrementally
- [ ] Tests still passing ✓
- [ ] Imports updated
- [ ] Final verification ✓

---

## Example Walkthrough

### Refactoring lib/items.ts

```bash
# 1. Pre-flight
git status                  # Clean working directory
npm test                    # All tests pass
wc -l lib/items.ts        # 758 lines - needs splitting

# 2. Create branch
git checkout -b refactor-items-module

# 3. Create directory
mkdir lib/items

# 4. Extract types (first, no dependencies)
# Create lib/items/types.ts with type definitions
npm test                    # Verify tests pass

# 5. Extract data
# Create lib/items/data.ts with item array
npm test                    # Verify tests pass

# 6. Extract utils
# Create lib/items/utils.ts with utility functions
npm test                    # Verify tests pass

# 7. Extract queries
# Create lib/items/queries.ts with query functions
npm test                    # Verify tests pass

# 8. Extract filters
# Create lib/items/filters.ts with filter functions
npm test                    # Verify tests pass

# 9. Extract breeding
# Create lib/items/breeding.ts with breeding logic
npm test                    # Verify tests pass

# 10. Create barrel file
# Create lib/items/index.ts re-exporting all public API
npm test                    # Verify tests pass

# 11. Update imports to use barrel
# Change: import { X } from '@/lib/items' (should still work!)
npm test                    # Verify tests pass

# 12. Delete original file
git rm lib/items.ts
npm test                    # Verify tests STILL pass

# 13. Final verification
npm run type-check          # TypeScript OK
npm run lint                # ESLint OK
npm run build               # Build succeeds
npm run dev                 # App runs correctly

# 14. Commit
git add lib/items/
git commit -m "refactor: split lib/items.ts into modular files"

# 15. Push and create PR
git push origin refactor-items-module
gh pr create --title "Refactor: Modularize items library" --body "..."
```

---

## Metrics to Track

After refactoring, measure improvement:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Largest file size | 758 lines | 450 lines | 41% smaller |
| Avg file size | 758 lines | 95 lines | 87% smaller |
| Files touching items | 1 file | 7 files | 7x more granular |
| Estimated conflict rate | 65% | 10% | 85% reduction |
| Test coverage | 80% | 80% | Maintained |

---

*"Measure twice, refactor once."*

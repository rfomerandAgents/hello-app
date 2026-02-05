# Merge Conflict Avoidance Strategies

Deep dive into preventing merge conflicts when multiple AI agents (or developers) work on the same codebase simultaneously.

## Table of Contents

- [Understanding Git Merge Conflicts](#understanding-git-merge-conflicts)
- [File-Level Strategies](#file-level-strategies)
- [Code-Level Strategies](#code-level-strategies)
- [Agent Assignment Patterns](#agent-assignment-patterns)
- [PR Sequencing](#pr-sequencing)
- [Real-World Scenarios](#real-world-scenarios)

---

## Understanding Git Merge Conflicts

### How Git Merges

Git uses **line-based three-way merge**:

```
Base (main branch):
1: const items = [
2:   { id: 'lucy', name: 'Lucy' },
3: ];

Agent A's change:
1: const items = [
2:   { id: 'lucy', name: 'Lucy' },
3:   { id: 'rosie', name: 'Rosie' },  ← Added line 3
4: ];

Agent B's change:
1: const items = [
2:   { id: 'lucy', name: 'Lucy' },
3:   { id: 'suki', name: 'Suki' },    ← Added line 3
4: ];

Result: CONFLICT on line 3
Both agents modified the same line number in different ways
```

### Why Conflicts Happen

1. **Same Line Modified** - Two agents change the same line differently
2. **Adjacent Line Modified** - Changes to lines next to each other
3. **Insertion Conflicts** - Both agents insert at the same position
4. **Deletion Conflicts** - One agent modifies, another deletes

### Conflict Probability by File Size

| File Size | Conflict Probability |
|-----------|---------------------|
| 50 lines | 5% |
| 100 lines | 12% |
| 200 lines | 28% |
| 500 lines | 65% |
| 1000 lines | 85%+ |

**Key Insight**: Smaller files = exponentially fewer conflicts.

---

## File-Level Strategies

### Strategy 1: File Ownership

Assign entire files to specific agents for a sprint or feature.

**Example Assignment**:
```yaml
Sprint 3 - Item Feature Development:
  Agent A:
    - lib/items/filters.ts
    - components/item-filters.tsx
  Agent B:
    - lib/items/queries.ts
    - components/item-search.tsx
  Agent C:
    - lib/items/breeding.ts
    - components/breeding-tracker.tsx

Result: Zero conflicts - no overlapping files
```

**Benefits**:
- Guaranteed zero conflicts
- Clear responsibility
- Simple coordination

**Drawbacks**:
- Less flexible
- Requires upfront planning
- Can block agents if dependencies exist

### Strategy 2: Directory Ownership

Assign entire directories/features to agents.

```
features/
  authentication/     ← Agent A owns everything here
  user-profile/       ← Agent B owns everything here
  item-management/  ← Agent C owns everything here
```

**Benefits**:
- Even clearer boundaries than file ownership
- Agent has full control over feature
- Scales to larger teams

### Strategy 3: Layer Ownership

Agents work on different architectural layers.

```yaml
Feature: Add Item Search
  Agent A: UI Layer
    - components/search-bar.tsx
    - components/search-results.tsx
  Agent B: Business Logic Layer
    - lib/search/search-service.ts
    - lib/search/search-algorithms.ts
  Agent C: Data Layer
    - lib/search/search-repository.ts
    - lib/search/search-types.ts
```

**Benefits**:
- Agents can work simultaneously
- Clear separation of concerns
- Each layer has specific expertise

**Drawbacks**:
- Requires sequential integration
- More coordination needed

---

## Code-Level Strategies

### Strategy 1: Alphabetical Ordering

**Problem**: Array insertions conflict

```typescript
// BEFORE: Unordered array
const items = [
  { id: 'lucy', name: 'Lucy' },
  { id: 'jack', name: 'Jack' },
  { id: 'thunder', name: 'Thunder' }
];

// Agent A adds Rosie at end
// Agent B adds Suki at end
// → CONFLICT (both modify same line)
```

**Solution**: Alphabetical ordering

```typescript
// AFTER: Alphabetically ordered
const items = [
  { id: 'jack', name: 'Jack' },      // J
  { id: 'lucy', name: 'Lucy' },      // L
  { id: 'rosie', name: 'Rosie' },    // R ← Agent A inserts here
  { id: 'suki', name: 'Suki' },      // S ← Agent B inserts here
  { id: 'thunder', name: 'Thunder' } // T
];

// Git sees:
// Agent A: Added line between 'lucy' and 'thunder'
// Agent B: Added line between 'rosie' and 'thunder'
// → NO CONFLICT (different positions)
```

**When to use**:
- Data arrays (item lists, configuration)
- Import statements
- Enum values
- Object keys (when possible)

### Strategy 2: One Item Per Line

**Problem**: Multiple items per line create conflicts

```typescript
// BAD: Compact format
export { getItemBySlug, getAllItems, getAllJennys, getAllJacks };

// Agent A adds getAdultItems:
export { getItemBySlug, getAllItems, getAllJennys, getAllJacks, getAdultItems };

// Agent B adds getFoals:
export { getItemBySlug, getAllItems, getAllJennys, getAllJacks, getFoals };

// → CONFLICT (same line modified)
```

**Solution**: One item per line

```typescript
// GOOD: One export per line
export { getItemBySlug };
export { getAllItems };
export { getAllJennys };
export { getAllJacks };

// Agent A adds getAdultItems:
export { getAdultItems };  // New line, no conflict

// Agent B adds getFoals:
export { getFoals };         // New line, no conflict

// → NO CONFLICT
```

**Alternative**: Trailing commas

```typescript
// ALSO GOOD: Trailing commas help
export {
  getItemBySlug,
  getAllItems,
  getAllJennys,
  getAllJacks,  // ← Trailing comma
};

// Agent A adds (creates new line):
export {
  getItemBySlug,
  getAllItems,
  getAllJennys,
  getAllJacks,
  getAdultItems,  // ← New line
};

// Agent B adds (creates new line):
export {
  getItemBySlug,
  getAllItems,
  getAllJennys,
  getAllJacks,
  getFoals,  // ← New line
};

// → NO CONFLICT (different new lines)
```

### Strategy 3: Append vs Insert

**Problem**: Inserting in the middle conflicts more than appending

```typescript
// RISKY: Adding to middle of array
const colors = [
  'Grey Dun',
  'Dark Brown',
  // Agent A adds 'Sorrel' here
  'Black'
];
```

**Better**: Add to end (if ordering doesn't matter)

```typescript
const colors = [
  'Grey Dun',
  'Dark Brown',
  'Black',
  'Sorrel',  // Agent A adds here (line 5)
  'White'    // Agent B adds here (line 6)
];
// Less likely to conflict - different lines
```

**Best**: Use Sets or Objects when order doesn't matter

```typescript
// Object keys (insertion order not guaranteed)
const colors = {
  greyDun: 'Grey Dun',
  darkBrown: 'Dark Brown',
  black: 'Black',
  sorrel: 'Sorrel',  // Agent A adds
  white: 'White'     // Agent B adds
};

// Or use a Map
const colors = new Map([
  ['greyDun', 'Grey Dun'],
  ['darkBrown', 'Dark Brown'],
  ['black', 'Black']
]);
```

### Strategy 4: Separate Data from Logic

**Problem**: Modifying data in same file as logic creates conflicts

```typescript
// BAD: Data and logic together (758 lines)
// lib/items.ts

// Data (450 lines) - frequently modified
export const items: Item[] = [ /* ... */ ];

// Logic (300 lines) - occasionally modified
export function getItemBySlug(slug: string) { /* ... */ }
export function getAllJennys() { /* ... */ }

// Agent A: Adds a item (modifies data)
// Agent B: Adds query function (modifies logic)
// → Both edit same file, increased conflict risk
```

**Solution**: Separate files

```typescript
// GOOD: Data isolated
// lib/items/data.ts (450 lines)
export const items: Item[] = [ /* ... */ ];

// lib/items/queries.ts (80 lines)
import { items } from './data';
export function getItemBySlug(slug: string) { /* ... */ }

// lib/items/filters.ts (60 lines)
import { items } from './data';
export function getAllJennys() { /* ... */ }

// Agent A: Edits data.ts
// Agent B: Edits queries.ts
// → NO CONFLICT (different files)
```

### Strategy 5: Extract Constants

**Problem**: Magic numbers and strings scattered throughout code

```typescript
// BAD: Constants embedded in logic
export function isAdultItem(age: number): boolean {
  return age >= 3;  // Magic number
}

export function canBreed(item: Item): boolean {
  return item.age >= 3 && item.age <= 15;  // Same magic number
}

// Agent A: Changes adult age to 4
// Agent B: Also modifies breeding age
// → Possible conflicts on multiple lines
```

**Solution**: Extract to constants file

```typescript
// constants.ts
export const ITEM_MIN_AGE = 3;
export const ITEM_MAX_AGE = 15;

// breeding.ts
import { ITEM_MIN_AGE, ITEM_MAX_AGE } from './constants';

export function isAdultItem(age: number): boolean {
  return age >= ITEM_MIN_AGE;
}

export function canBreed(item: Item): boolean {
  return item.age >= ITEM_MIN_AGE &&
         item.age <= ITEM_MAX_AGE;
}

// Agent A: Modifies constant in constants.ts
// Agent B: Adds new breeding logic in breeding.ts
// → NO CONFLICT (different files)
```

---

## Agent Assignment Patterns

### Pattern 1: Feature Branches

Each agent works on a distinct feature in isolation.

```yaml
main
  ↓
  ├─ feature/add-search (Agent A)
  ├─ feature/add-filters (Agent B)
  └─ feature/add-breeding-tracker (Agent C)

Files modified:
  Agent A: components/search.tsx, lib/search.ts
  Agent B: components/filters.tsx, lib/filters.ts
  Agent C: components/breeding.tsx, lib/breeding.ts

Result: Zero overlap = zero conflicts
```

### Pattern 2: Vertical Slicing

Agents work on different parts of the same feature stack.

```yaml
Feature: Item Search
  Agent A (Frontend):
    - components/search-bar.tsx
    - components/search-results.tsx
    - hooks/use-item-search.ts

  Agent B (Backend):
    - lib/search/search-engine.ts
    - lib/search/search-index.ts

  Agent C (Data):
    - lib/search/search-types.ts
    - lib/search/search-repository.ts
```

**Coordination needed**:
- Agent C merges first (types)
- Agent B merges second (uses types)
- Agent A merges last (uses backend)

### Pattern 3: Parallel Iteration

Multiple agents work on similar tasks across different domains.

```yaml
Task: Add Image Upload
  Agent A: Item image upload
    - components/item/image-uploader.tsx
    - lib/items/image-service.ts

  Agent B: Farm image upload
    - components/farm/image-uploader.tsx
    - lib/farm/image-service.ts

  Agent C: General image utilities
    - lib/images/image-processor.ts
    - lib/images/image-validator.ts
```

**Benefits**:
- Pattern reuse across agents
- No file overlap
- Knowledge sharing

---

## PR Sequencing

### Sequential PRs (Dependencies)

When PRs depend on each other, merge in order:

```
PR #1: Add types (Agent C)
  ↓ depends on
PR #2: Add service (Agent B)
  ↓ depends on
PR #3: Add UI (Agent A)
```

**Process**:
1. Agent C creates PR #1, gets review, merges
2. Agent B rebases on main, creates PR #2, merges
3. Agent A rebases on main, creates PR #3, merges

**Conflicts**: Minimal - each PR builds on previous

### Parallel PRs (No Dependencies)

When PRs are independent, merge in any order:

```
PR #1: Add item filters (Agent A)
PR #2: Add breeding tracker (Agent B)
PR #3: Update farm location (Agent C)

All three can merge in any order
```

**Process**:
1. All agents create PRs from main
2. First to get approval merges
3. Others rebase and resolve any conflicts (should be minimal)

### Batch Merges

For many small PRs, use batch merge strategy:

```yaml
Morning batch:
  - PR #101: Add Rosie (Agent A)
  - PR #102: Add Suki (Agent B)
  - PR #103: Add Thunder (Agent C)

All merge to main within 1 hour
```

**Benefits**:
- Reduced integration overhead
- Fewer rebase cycles
- Batch testing

---

## Real-World Scenarios

### Scenario 1: Two Agents Adding Items

**Setup**:
- Agent A adding "Rosie"
- Agent B adding "Suki"
- Both modify `lib/items/data.ts`

**Without Conflict Avoidance** (Append pattern):
```typescript
// Base (main)
export const items: Item[] = [
  { id: 'lucy', name: 'Lucy' },
  { id: 'jack', name: 'Jack' }
];

// Agent A appends Rosie
export const items: Item[] = [
  { id: 'lucy', name: 'Lucy' },
  { id: 'jack', name: 'Jack' },
  { id: 'rosie', name: 'Rosie' }  // Line 4
];

// Agent B appends Suki
export const items: Item[] = [
  { id: 'lucy', name: 'Lucy' },
  { id: 'jack', name: 'Jack' },
  { id: 'suki', name: 'Suki' }    // Line 4
];

// CONFLICT on line 4
```

**With Conflict Avoidance** (Alphabetical + one per line):
```typescript
// Base (main) - alphabetically ordered
export const items: Item[] = [
  { id: 'jack', name: 'Jack' },
  { id: 'lucy', name: 'Lucy' },
];

// Agent A inserts Rosie (R comes after L, before end)
export const items: Item[] = [
  { id: 'jack', name: 'Jack' },
  { id: 'lucy', name: 'Lucy' },
  { id: 'rosie', name: 'Rosie' },  // Insert at line 4
];

// Agent B inserts Suki (S comes after R)
export const items: Item[] = [
  { id: 'jack', name: 'Jack' },
  { id: 'lucy', name: 'Lucy' },
  { id: 'suki', name: 'Suki' },    // Insert at line 4
];

// Git three-way merge:
// Base: 3 lines
// Agent A: Added line 4 (Rosie)
// Agent B: Added line 4 (Suki)
// Result: STILL CONFLICT (same position)

// BETTER: Insert in alphabetical position
// Agent A inserts Rosie between Lucy and end
export const items: Item[] = [
  { id: 'jack', name: 'Jack' },
  { id: 'lucy', name: 'Lucy' },
  { id: 'rosie', name: 'Rosie' },
];

// Agent B inserts Suki between Lucy and end (but different position due to alphabetization)
export const items: Item[] = [
  { id: 'jack', name: 'Jack' },
  { id: 'lucy', name: 'Lucy' },
  { id: 'suki', name: 'Suki' },
];

// Merged result (Git combines both):
export const items: Item[] = [
  { id: 'jack', name: 'Jack' },
  { id: 'lucy', name: 'Lucy' },
  { id: 'rosie', name: 'Rosie' },  // Agent A
  { id: 'suki', name: 'Suki' },    // Agent B
];
// NO CONFLICT if Git can auto-merge
```

**Best Solution**: File ownership

```yaml
Agent A: Creates new file app/items/rosie/page.tsx
         Adds entry to lib/items/data.ts (line for Rosie)

Agent B: Creates new file app/items/suki/page.tsx
         Adds entry to lib/items/data.ts (line for Suki)

Different files = no conflict on pages
Alphabetical insertion = reduced conflict on data
```

### Scenario 2: Updating Shared Component

**Setup**:
- Agent A adding new prop to ItemCard
- Agent B fixing bug in ItemCard

**Without Modularization**:
```typescript
// components/item-card.tsx (200 lines)
// Both agents modify same file
// → High conflict probability
```

**With Modularization**:
```typescript
// Agent A: Adds prop and updates types
// components/item-card/types.ts
export interface ItemCardProps {
  item: Item;
  showBreeding: boolean;  // New prop added by Agent A
}

// Agent B: Fixes date formatting bug
// components/item-card/utils.ts
export function formatBirthdate(date: string): string {
  // Bug fix by Agent B
  return new Date(date).toLocaleDateString();
}

// Main component imports from both
// components/item-card/index.tsx
import { ItemCardProps } from './types';
import { formatBirthdate } from './utils';

// NO CONFLICT - different files
```

### Scenario 3: Adding Tests

**Setup**:
- Agent A adds test for new feature
- Agent B adds test for bug fix

**Without Organization**:
```typescript
// items.test.ts (500 lines)
// Both append tests to end
// → Conflict likely
```

**With Organization**:
```typescript
// tests/items/queries.test.ts - Agent A
describe('getItemBySlug', () => {
  test('new feature test', () => {
    // Agent A's test
  });
});

// tests/items/filters.test.ts - Agent B
describe('getAllJennys', () => {
  test('bug fix test', () => {
    // Agent B's test
  });
});

// NO CONFLICT - different files
```

---

## Conflict Resolution Checklist

When conflicts do occur:

- [ ] Identify the conflict type (same line, adjacent, insertion)
- [ ] Check if files should have been separate
- [ ] Verify both changes are necessary
- [ ] Manually merge both changes if compatible
- [ ] Test merged result thoroughly
- [ ] Consider refactoring to prevent future conflicts
- [ ] Document why conflict occurred
- [ ] Update team practices if pattern emerges

---

## Prevention Checklist

Before starting work:

- [ ] Check if other agents are working on same files
- [ ] Coordinate file/feature ownership
- [ ] Use alphabetical ordering for new items
- [ ] One item per line for arrays/exports
- [ ] Separate data from logic
- [ ] Create new files instead of modifying existing
- [ ] Use feature branches
- [ ] Plan PR merge order

---

## Metrics to Track

Monitor these to measure conflict avoidance success:

- **Conflict Rate**: % of PRs requiring manual conflict resolution
  - Target: < 10%
  - Excellent: < 5%

- **Average PR Size**: Lines changed per PR
  - Target: < 200 lines
  - Excellent: < 100 lines

- **File Ownership Score**: % of PRs modifying unique files
  - Target: > 70%
  - Excellent: > 85%

- **Merge Time**: Time from PR creation to merge
  - Target: < 4 hours
  - Excellent: < 2 hours

---

*"The best merge conflict is the one that never happens."*

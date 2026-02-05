---
name: ai-agent-optimized-javascript
description: Expert JavaScript/TypeScript refactoring skill for modularizing codebases to enable parallel AI agent development and concurrent PR workflows. Use when refactoring large files into smaller modules, establishing file size guidelines, creating barrel exports, or organizing code to minimize merge conflicts between multiple agents.
---

# AI Agent Optimized JavaScript

Expert guidance for refactoring JavaScript/TypeScript codebases into modular structures that enable parallel development by multiple AI agents with minimal merge conflicts.

## Engineering Philosophy

**"Small files enable parallel work. Parallel work enables velocity."**

### Core Principles

1. **Single Responsibility File** - Each file should have one primary export. Small, focused files reduce merge conflicts when multiple agents work simultaneously.

2. **Merge-Friendly Boundaries** - Separate functions and components into individual files. When Agent A modifies ComponentA.tsx and Agent B modifies ComponentB.tsx simultaneously, there are zero conflicts.

3. **Index File Pattern** - Use barrel files (index.ts) to maintain clean imports while enabling internal modularization. Public API stays stable even as internals refactor.

4. **Optimal File Sizes** - Target 50-200 lines per file. Files over 200 lines should be evaluated for splitting. Files over 400 lines must be split.

5. **Data Isolation** - Separate data from logic. Multiple agents can safely modify business logic while data remains stable, and vice versa.

### Why Monolithic Files Cause Problems

When multiple agents (or developers) work on the same monolithic file:
- **Line-based merging fails** - Git merges at the line level. Two agents adding different exports to the same file = conflict.
- **Context switching overhead** - Large files require more cognitive load to understand what changed.
- **False conflicts** - Changes to unrelated parts of the same file still trigger merge conflicts.
- **Serial development** - Team must coordinate who edits which files, eliminating parallel work benefits.

**Example:**
```typescript
// BAD: app/lib/items.ts (758 lines)
// - Contains types, data, query functions, filter functions, breeding logic
// - Any change requires touching this file
// - Multiple PRs = guaranteed conflicts

// GOOD: Modular structure enables parallel work
// Agent A: Updates lib/items/types.ts (0 conflicts)
// Agent B: Adds filter to lib/items/filters.ts (0 conflicts)
// Agent C: Adds item to lib/items/data.ts (0 conflicts)
// All three PRs merge cleanly
```

## File Structure Patterns

### Directory Organization

**Prefer flat structures over deep nesting** for small to medium projects. Deep nesting makes imports verbose and creates artificial boundaries.

```typescript
// BAD: Over-engineered nesting
lib/
  items/
    domain/
      entities/
        item.ts
      value-objects/
        breed.ts
    application/
      use-cases/
        get-item.ts
    infrastructure/
      repositories/
        item-repository.ts

// GOOD: Flat, pragmatic structure
lib/items/
  types.ts          // ~45 lines - Interfaces and type definitions
  data.ts           // ~450 lines - Item data array (stable, rarely modified)
  queries.ts        // ~80 lines - getItemBySlug, getAllItems
  filters.ts        // ~60 lines - getAllJennys, getAllJacks, getFoals
  breeding.ts       // ~30 lines - isCurrentlyBred, getBreedingStatus
  index.ts          // ~20 lines - Public API re-exports
```

### Component-Per-File Pattern

For React components, avoid component folders for small components. Use folders only when a component has significant supporting files.

```typescript
// BAD: Unnecessary folder for simple component
components/Button/
  Button.tsx        // 50 lines
  index.ts          // Just re-exports Button
  Button.test.tsx

// GOOD: Flat structure for simple components
components/
  Button.tsx
  Button.test.tsx

// GOOD: Folder for complex components with subcomponents
components/ItemBiography/
  index.tsx           // Main component (~150 lines)
  DetailsSection.tsx // Sub-component (~80 lines)
  useToggle.ts        // Custom hook (~30 lines)
  formatDate.ts       // Utility (~20 lines)
```

### Data and Types Separation

Separate type definitions from data, and both from business logic. Different change frequencies require different files.

```typescript
// types.ts - Changes when domain model evolves
export interface Item {
  id: string;
  name: string;
  breed: string;
  // ...
}

// data.ts - Changes when adding/updating items
export const items: Item[] = [
  { id: "lucy", name: "Lucy", breed: "Jenny" },
  { id: "jack", name: "Jack", breed: "Jack" },
  // ... 50 more items
];

// queries.ts - Changes when adding query capabilities
export function getItemBySlug(slug: string): Item | undefined {
  return items.find(d => d.id === slug);
}

// filters.ts - Changes when adding filter capabilities
export function getAllJennys(): Item[] {
  return items.filter(d => d.breed === "Jenny");
}
```

## Refactoring Decision Matrix

### When to Split a File

| Threshold | Action | Rationale |
|-----------|--------|-----------|
| < 100 lines | Keep as-is | File is already focused and manageable |
| 100-200 lines | Evaluate cohesion | Split if file has multiple unrelated concerns |
| 200-400 lines | Consider splitting | Look for natural boundaries (types, utils, components) |
| > 400 lines | Must split | High conflict risk, reduced maintainability |

### Cohesion Rules

Split when a file contains **multiple unrelated exports**:

```typescript
// BAD: Poor cohesion - utilities, types, and components mixed
export interface Item { /* ... */ }
export function formatDate(date: Date): string { /* ... */ }
export function ItemCard({ item }: Props) { /* ... */ }

// GOOD: High cohesion - each file has single responsibility
// types.ts
export interface Item { /* ... */ }

// utils/formatDate.ts
export function formatDate(date: Date): string { /* ... */ }

// components/ItemCard.tsx
export function ItemCard({ item }: Props) { /* ... */ }
```

### Frequency Rules

**Split frequently-modified code from stable code** to reduce unnecessary diffs:

```typescript
// data.ts - Modified frequently (new items added weekly)
export const items: Item[] = [ /* ... */ ];

// queries.ts - Modified infrequently (query logic stable)
export function getItemBySlug(slug: string) { /* ... */ }

// Benefit: Adding items doesn't trigger review of query logic
```

### Interface Boundaries

**Separate type definitions from implementations**:

```typescript
// interfaces/item-repository.ts
export interface ItemRepository {
  findBySlug(slug: string): Promise<Item | undefined>;
  findAll(): Promise<Item[]>;
}

// implementations/in-memory-item-repository.ts
export class InMemoryItemRepository implements ItemRepository {
  // Implementation details
}

// Benefit: Multiple agents can work on different implementations
```

## Component Modularization Patterns

### Extract Custom Hooks

Move React hooks into separate files for reusability and testability:

```typescript
// BEFORE: components/ItemBiography.tsx (360 lines)
function ItemBiography({ item }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);
  const toggle = () => setIsExpanded(!isExpanded);

  // ... 350 more lines
}

// AFTER: Extracted hook
// components/ItemBiography/useToggle.ts (~30 lines)
export function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);
  const toggle = useCallback(() => setValue(v => !v), []);
  return [value, toggle] as const;
}

// components/ItemBiography/index.tsx (~150 lines)
function ItemBiography({ item }: Props) {
  const [isExpanded, toggleExpanded] = useToggle(false);
  // ... component logic
}
```

### Extract Utility Functions

Domain utilities should live in separate files:

```typescript
// BEFORE: Mixed in component
function ItemBiography({ item }: Props) {
  const formatDateWithoutTimezone = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return <div>{formatDateWithoutTimezone(item.birthdate)}</div>;
}

// AFTER: Extracted utility
// utils/formatDate.ts (~20 lines)
export function formatDateWithoutTimezone(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// components/ItemBiography/index.tsx
import { formatDateWithoutTimezone } from '@/utils/formatDate';

function ItemBiography({ item }: Props) {
  return <div>{formatDateWithoutTimezone(item.birthdate)}</div>;
}
```

### Extract Sub-Components

Break large components into smaller, focused pieces:

```typescript
// BEFORE: components/ItemBiography.tsx (360 lines)
function ItemBiography({ item }: Props) {
  return (
    <div>
      {/* 100 lines of details rendering */}
      {/* 80 lines of characteristics */}
      {/* 60 lines of timeline */}
    </div>
  );
}

// AFTER: Modular components
// components/ItemBiography/index.tsx (~80 lines)
export default function ItemBiography({ item }: Props) {
  return (
    <div>
      <DetailsSection item={item} />
      <CharacteristicsSection item={item} />
      <TimelineSection item={item} />
    </div>
  );
}

// components/ItemBiography/DetailsSection.tsx (~100 lines)
export function DetailsSection({ item }: Props) {
  // Focused on details rendering
}

// Benefit: Three agents can work on three sections simultaneously
```

## Import/Export Best Practices

### Prefer Named Exports Over Default

Named exports improve discoverability and enable better refactoring:

```typescript
// BAD: Default exports hide what's available
// components/Button.tsx
export default function Button() { /* ... */ }

// GOOD: Named exports show exactly what's available
// components/Button.tsx
export function Button() { /* ... */ }
export function IconButton() { /* ... */ }
export type ButtonProps = { /* ... */ };
```

### Use Barrel Files for Public APIs

Barrel files (index.ts) create stable public interfaces while enabling internal refactoring:

```typescript
// lib/items/index.ts - Public API
export * from './types';
export * from './queries';
export * from './filters';
export * from './breeding';
// Note: data.ts NOT exported - internal implementation detail

// Usage - Clean imports
import { Item, getItemBySlug, getAllJennys } from '@/lib/items';

// Benefit: Internal file structure can change without breaking imports
```

### Layer Your Imports

Keep internal imports relative, public imports from barrel files:

```typescript
// lib/items/queries.ts - Internal file
import { Item } from './types';        // Relative - internal
import { items } from './data';        // Relative - internal

// components/ItemCard.tsx - External consumer
import { Item, getItemBySlug } from '@/lib/items';  // Via barrel
```

### Avoid Circular Dependencies

Maintain a clear dependency hierarchy:

```typescript
// GOOD: Layered architecture prevents circles
types.ts           // Layer 0 - No dependencies
  ↑
data.ts            // Layer 1 - Depends on types
  ↑
queries.ts         // Layer 2 - Depends on data and types
  ↑
filters.ts         // Layer 2 - Depends on data and types
  ↑
index.ts           // Layer 3 - Re-exports all

// BAD: Circular dependency
// queries.ts imports from filters.ts
// filters.ts imports from queries.ts
// Result: Import errors, undefined values
```

## Merge Conflict Avoidance

### The Array Modification Problem

**Problem**: When multiple agents add items to an array, Git cannot auto-merge:

```typescript
// data.ts - BEFORE (Agent A and Agent B both branch from here)
export const items: Item[] = [
  { id: "lucy", name: "Lucy" },
  { id: "jack", name: "Jack" },
];

// Agent A adds Rosie
export const items: Item[] = [
  { id: "lucy", name: "Lucy" },
  { id: "jack", name: "Jack" },
  { id: "rosie", name: "Rosie" },  // Added
];

// Agent B adds Suki
export const items: Item[] = [
  { id: "lucy", name: "Lucy" },
  { id: "jack", name: "Jack" },
  { id: "suki", name: "Suki" },    // Added
];

// Result: MERGE CONFLICT when both PRs try to merge
```

**Solutions:**

1. **Alphabetical Ordering** - Reduces conflicts by creating predictable positions:
```typescript
export const items: Item[] = [
  { id: "jack", name: "Jack" },    // J
  { id: "lucy", name: "Lucy" },    // L
  { id: "rosie", name: "Rosie" },  // R - Agent A inserts here
  { id: "suki", name: "Suki" },    // S - Agent B inserts here
  // Less likely to conflict - different positions
];
```

2. **One Export Per Line** - Makes diffs clearer:
```typescript
// BAD: Compact format
export { getItemBySlug, getAllItems, getAllJennys, getAllJacks };

// GOOD: One per line
export { getItemBySlug };
export { getAllItems };
export { getAllJennys };
export { getAllJacks };
// Agents can add exports with lower conflict probability
```

3. **File Assignment Strategy** - Assign files to specific agents:
```typescript
// Planning Phase:
// Agent A: Modify lib/items/filters.ts only
// Agent B: Modify lib/items/queries.ts only
// Agent C: Modify lib/items/breeding.ts only
// Result: Zero conflicts guaranteed
```

### Barrel Files Reduce Dependencies

Barrel files isolate changes:

```typescript
// WITHOUT barrel file - Direct imports create tight coupling
// components/ItemCard.tsx
import { Item } from '@/lib/items/types';
import { getItemBySlug } from '@/lib/items/queries';
// If queries.ts is refactored, this import might break

// WITH barrel file - Loose coupling
// components/ItemCard.tsx
import { Item, getItemBySlug } from '@/lib/items';
// Internal refactoring doesn't affect consumers
```

### Document Agent File Ownership

Use comments or task assignment to coordinate:

```yaml
# PR #123 - Add Rosie Biography
Assigned to: Agent A
Files modified:
  - lib/items/data.ts (add Rosie entry)
  - app/items/rosie/page.tsx (create page)

# PR #124 - Add Search Functionality
Assigned to: Agent B
Files modified:
  - lib/items/queries.ts (add search function)
  - components/ItemSearch.tsx (create component)

# Result: No overlapping files = no conflicts
```

## Codebase Analysis Workflow

Follow this systematic approach when analyzing a codebase for modularization:

### 1. Run File Size Analysis

```bash
# Use the provided script
bash .claude/skills/ai-agent-optimized-javascript/scripts/analyze-file-sizes.sh app/

# Output shows largest files first:
# 758 app/lib/items.ts
# 360 app/components/ItemBiography.tsx
# 245 app/lib/utils.ts
```

### 2. Identify Files >200 Lines

Flag files exceeding the recommended threshold:
- Files 200-400 lines: Evaluate for splitting
- Files >400 lines: Must split

### 3. Analyze Export Count Per File

```bash
# Count exports in a file
grep -c "^export" app/lib/items.ts
# If result > 10, likely needs splitting
```

### 4. Map Modification Frequency

```bash
# See how often file is modified
git log --oneline app/lib/items.ts | wc -l

# If frequently modified + large = high conflict risk
```

### 5. Propose Split Strategy

Create a refactoring plan:

```markdown
## lib/items.ts Refactoring Plan

Current: 758 lines, 25+ exports, modified in 40+ commits

Proposed structure:
- lib/items/types.ts (~45 lines) - Interfaces
- lib/items/data.ts (~450 lines) - Item array
- lib/items/queries.ts (~80 lines) - Find functions
- lib/items/filters.ts (~60 lines) - Filter functions
- lib/items/breeding.ts (~30 lines) - Breeding logic
- lib/items/index.ts (~20 lines) - Re-exports

Benefits:
- 6 smaller files vs 1 large file
- Agents can work on different concerns in parallel
- Data changes isolated from logic changes
```

### 6. Execute Refactoring with Tests

```bash
# 1. Ensure tests pass before refactoring
npm test

# 2. Create new file structure
mkdir lib/items

# 3. Move code incrementally, testing after each move
# 4. Update imports across codebase
# 5. Run tests to verify behavior unchanged
npm test

# 6. Commit with clear message
git commit -m "refactor: split lib/items.ts into modular files"
```

## Anti-Patterns to Avoid

### The God File

**Problem**: Single file handling multiple responsibilities

```typescript
// BAD: app/lib/items.ts
// - Type definitions
// - Data storage
// - Query functions
// - Filter functions
// - Breeding logic
// - Validation functions
// - Utility functions
// Result: 758 lines, merge conflict magnet
```

**Fix**: Apply Single Responsibility File principle

### The Barrel Barrel

**Problem**: Nested barrel files creating confusion

```typescript
// BAD:
lib/items/index.ts
  exports from queries/index.ts
    exports from queries/slug/index.ts
      exports from queries/slug/get-by-slug.ts

// GOOD: Maximum 2 levels
lib/items/index.ts
  exports from queries.ts
```

### The Import Maze

**Problem**: Inconsistent import patterns

```typescript
// BAD: Mixing styles
import { Item } from '@/lib/items/types';
import { getItemBySlug } from '@/lib/items';
import data from '@/lib/items/data';

// GOOD: Consistent barrel imports
import { Item, getItemBySlug } from '@/lib/items';
```

### The Premature Abstraction

**Problem**: Creating complex module structure before needed

```typescript
// BAD: Over-engineering for 3 functions
lib/items/
  domain/
    repositories/
      interfaces/
        i-item-repository.ts
      implementations/
        item-repository.ts

// GOOD: Start simple, refactor when needed
lib/items/
  queries.ts  // When this grows > 200 lines, then split
```

## Success Metrics

A well-modularized codebase should achieve:

- **Average file size**: 50-150 lines (excluding data files)
- **Merge conflict rate**: < 5% of PRs when multiple agents work
- **PR velocity**: Multiple PRs can merge same day without coordination
- **Import clarity**: Any file's dependencies are obvious from imports
- **Refactoring ease**: Moving code doesn't break multiple files

## Quick Reference

### File Size Guidelines

| File Type | Target Lines | Max Lines | Notes |
|-----------|--------------|-----------|-------|
| Types | 20-50 | 100 | Pure interface definitions |
| Utilities | 30-100 | 150 | Focus on single domain |
| Components | 50-200 | 300 | Extract hooks and sub-components |
| Data files | 100-500 | 1000 | Okay to be larger if rarely modified |
| Page files | 50-150 | 250 | Should be thin, delegate to components |

### When to Split Checklist

- [ ] File exceeds 200 lines
- [ ] File has 10+ exports
- [ ] File modified in 20+ commits
- [ ] File contains unrelated concerns
- [ ] Multiple agents need to modify file
- [ ] Team experiences frequent merge conflicts

### Barrel File Template

```typescript
// lib/[domain]/index.ts
// Public API - export only what consumers need

// Types
export type { EntityName, EntityProps } from './types';

// Core functions
export { getEntity, getAllEntities } from './queries';
export { filterEntities } from './filters';

// Internal files not exported:
// - data.ts (implementation detail)
// - utils.ts (internal helpers)
```

## Additional Resources

See the `references/` directory for comprehensive guides:
- `modular-patterns.md` - Detailed patterns for different architectures
- `file-size-guidelines.md` - In-depth file sizing recommendations
- `export-patterns.md` - Complete export/import pattern catalog
- `conflict-avoidance.md` - Advanced merge conflict prevention strategies

See the `assets/` directory for practical examples:
- `before-after-examples.md` - Real-world refactoring examples
- `checklist.md` - Pre-refactoring checklist

---

*"The best code for parallel development is code that doesn't conflict. The best way to avoid conflicts is small, focused files."*

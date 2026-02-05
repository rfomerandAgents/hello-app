# File Size Guidelines

Comprehensive guide to optimal file sizes for different file types in JavaScript/TypeScript projects.

## Table of Contents

- [Core Philosophy](#core-philosophy)
- [File Type Guidelines](#file-type-guidelines)
- [Measuring File Size](#measuring-file-size)
- [Exception Cases](#exception-cases)
- [Size vs Complexity](#size-vs-complexity)

---

## Core Philosophy

**"A file should be small enough to understand in one mental context, but large enough to contain a complete thought."**

### Why File Size Matters

1. **Cognitive Load**: Humans can hold ~7 items in working memory. A 500-line file has dozens of concepts.

2. **Merge Conflicts**: Larger files = more surface area for conflicts. 200-line files conflict 5x less than 1000-line files.

3. **Review Efficiency**: PRs with 50-150 line changes get reviewed faster and more thoroughly than 500+ line changes.

4. **Test Granularity**: Small files encourage focused tests. Large files lead to incomplete test coverage.

5. **Parallel Work**: Multiple agents can work on 10 small files simultaneously. One large file forces serialization.

### The 200-Line Rule

**200 lines is the inflection point** where files transition from "comfortable" to "complex":

| Lines | Status | Action |
|-------|--------|--------|
| 0-100 | Optimal | Keep as-is |
| 101-200 | Comfortable | Monitor for growth |
| 201-400 | Warning | Evaluate for splitting |
| 401+ | Critical | Must split |

---

## File Type Guidelines

### Type Definitions (types.ts, interfaces.ts)

**Target**: 20-50 lines
**Maximum**: 100 lines
**Purpose**: Interface and type definitions only

**Example - Good Size** (~45 lines):
```typescript
// lib/items/types.ts
export interface Item {
  id: string;
  name: string;
  breed: 'Jenny' | 'Jack' | 'Gelding';
  birthdate: string;
  color: string;
  markings: string[];
  parentA?: string;
  parentB?: string;
  currentlyBred: boolean;
  arrivalDate: string;
}

export interface Details {
  itemId: string;
  generation: number;
  ancestors: Ancestor[];
}

export interface Ancestor {
  id: string;
  name: string;
  relationship: 'parentA' | 'parentB';
}

export type ItemBreed = 'Jenny' | 'Jack' | 'Gelding';
export type ItemColor = 'Grey Dun' | 'Dark Brown' | 'Sorrel' | 'Black';

export interface ItemFilters {
  breed?: ItemBreed;
  color?: ItemColor;
  minAge?: number;
  maxAge?: number;
}
```

**When to Split**:
- More than 10 interfaces → Split by domain area
- Types from different domains → Separate files

```typescript
// Too many types in one file - SPLIT:
// lib/items/types.ts →
//   lib/items/item-types.ts (Item, ItemBreed, etc.)
//   lib/items/details-types.ts (Details, Ancestor, etc.)
//   lib/items/filter-types.ts (ItemFilters, SearchOptions, etc.)
```

---

### Utility Functions (utils.ts, helpers.ts)

**Target**: 30-100 lines
**Maximum**: 150 lines
**Purpose**: Pure functions with single domain focus

**Example - Good Size** (~60 lines):
```typescript
// lib/utils/date-utils.ts
export function formatDateWithoutTimezone(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

export function calculateAge(birthdate: string): number {
  const birth = new Date(birthdate);
  const now = new Date();
  const diffMs = now.getTime() - birth.getTime();
  const ageYears = diffMs / (1000 * 60 * 60 * 24 * 365.25);
  return Math.floor(ageYears);
}

export function isAdult(birthdate: string, adultAge: number = 3): boolean {
  return calculateAge(birthdate) >= adultAge;
}

export function formatDateRange(start: string, end?: string): string {
  const startFormatted = formatDateWithoutTimezone(start);
  if (!end) return `Since ${startFormatted}`;
  const endFormatted = formatDateWithoutTimezone(end);
  return `${startFormatted} - ${endFormatted}`;
}
```

**When to Split**:
- More than 8-10 utility functions → Split by sub-domain
- Utilities from different domains → Separate files

```typescript
// Before: lib/utils.ts (300 lines)
// All utilities mixed together

// After: Split by domain
// lib/utils/date-utils.ts (~60 lines)
// lib/utils/string-utils.ts (~40 lines)
// lib/utils/array-utils.ts (~50 lines)
// lib/utils/validation-utils.ts (~70 lines)
```

---

### React Components (*.tsx)

**Target**: 50-200 lines
**Maximum**: 300 lines
**Purpose**: UI component with render logic

**Example - Good Size** (~120 lines):
```typescript
// components/item-card.tsx
import { Item } from '@/lib/items/types';
import { formatDateWithoutTimezone } from '@/lib/utils/date-utils';
import { useItemImage } from '@/hooks/use-item-image';

interface ItemCardProps {
  item: Item;
  onSelect?: (id: string) => void;
}

export function ItemCard({ item, onSelect }: ItemCardProps) {
  const { imageUrl, isLoading } = useItemImage(item.id);

  const handleClick = () => {
    onSelect?.(item.id);
  };

  return (
    <div className="item-card" onClick={handleClick}>
      {isLoading ? (
        <div className="skeleton" />
      ) : (
        <img src={imageUrl} alt={item.name} />
      )}

      <div className="content">
        <h3>{item.name}</h3>
        <p className="breed">{item.breed}</p>
        <p className="birthdate">
          Born {formatDateWithoutTimezone(item.birthdate)}
        </p>

        {item.currentlyBred && (
          <div className="badge">Currently Bred</div>
        )}
      </div>
    </div>
  );
}
```

**When to Split**:
- Component exceeds 200 lines → Extract sub-components or hooks
- Contains custom hooks → Move to separate file
- Contains utility functions → Move to utils/
- Multiple sub-components → Create component directory

```typescript
// Before: components/item-biography.tsx (360 lines)

// After: Split into directory
// components/item-biography/
//   index.tsx (~150 lines) - Main component
//   details-section.tsx (~80 lines) - Sub-component
//   characteristics-section.tsx (~60 lines) - Sub-component
//   use-toggle.ts (~30 lines) - Custom hook
//   format-date.ts (~20 lines) - Utility
```

---

### Data Files (data.ts, constants.ts)

**Target**: 100-500 lines
**Maximum**: 1000 lines
**Purpose**: Static data arrays or constant definitions

**Exception**: Data files can be larger because:
- Rarely modified (stable)
- Line-by-line structure (easy to merge)
- Often auto-generated
- Low cognitive complexity

**Example - Acceptable Size** (~450 lines):
```typescript
// lib/items/data.ts
import { Item } from './types';

export const items: Item[] = [
  {
    id: 'lucy',
    name: 'Lucy',
    breed: 'Jenny',
    birthdate: '2015-05-12',
    color: 'Grey Dun',
    markings: ['White muzzle', 'Cross on back'],
    parentA: 'thunder',
    parentB: 'bella',
    currentlyBred: false,
    arrivalDate: '2018-06-01'
  },
  // ... 50 more item entries
  // Each entry ~8-10 lines
  // Total: ~450 lines
];
```

**When to Split**:
- More than 100 entries → Consider database
- Multiple data types → Separate files
- Data from different domains → Split by domain

```typescript
// lib/items/data.ts (800 lines) → Split by type
//   lib/items/categorys-data.ts (~300 lines)
//   lib/items/jacks-data.ts (~250 lines)
//   lib/items/geldings-data.ts (~200 lines)
```

---

### Service/API Files (services.ts, api.ts)

**Target**: 80-150 lines
**Maximum**: 250 lines
**Purpose**: API calls or business logic

**Example - Good Size** (~100 lines):
```typescript
// lib/services/item-service.ts
import { Item, ItemFilters } from '@/lib/items/types';

export class ItemService {
  private baseUrl = '/api/items';

  async getAll(): Promise<Item[]> {
    const response = await fetch(this.baseUrl);
    if (!response.ok) throw new Error('Failed to fetch items');
    return response.json();
  }

  async getById(id: string): Promise<Item | null> {
    const response = await fetch(`${this.baseUrl}/${id}`);
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Failed to fetch item ${id}`);
    return response.json();
  }

  async create(item: Omit<Item, 'id'>): Promise<Item> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    if (!response.ok) throw new Error('Failed to create item');
    return response.json();
  }

  async update(id: string, updates: Partial<Item>): Promise<Item> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error(`Failed to update item ${id}`);
    return response.json();
  }

  async search(filters: ItemFilters): Promise<Item[]> {
    const params = new URLSearchParams(filters as any);
    const response = await fetch(`${this.baseUrl}/search?${params}`);
    if (!response.ok) throw new Error('Failed to search items');
    return response.json();
  }
}

export const itemService = new ItemService();
```

**When to Split**:
- More than 8-10 methods → Split by responsibility
- Multiple concerns → Separate services

```typescript
// Before: lib/services/item-service.ts (400 lines)
// CRUD, search, breeding, health all mixed

// After: Split by concern
// lib/services/item-crud-service.ts (~100 lines)
// lib/services/item-search-service.ts (~80 lines)
// lib/services/breeding-service.ts (~120 lines)
// lib/services/health-service.ts (~100 lines)
```

---

### Page Files (Next.js page.tsx, route.tsx)

**Target**: 50-150 lines
**Maximum**: 250 lines
**Purpose**: Route handler with minimal logic

**Philosophy**: Pages should be thin. Heavy lifting belongs in components, hooks, or services.

**Example - Good Size** (~80 lines):
```typescript
// app/items/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { getItemBySlug } from '@/lib/items/queries';
import { ItemBiography } from '@/components/item-biography';
import { Breadcrumbs } from '@/components/breadcrumbs';

interface ItemPageProps {
  params: { slug: string };
}

export async function generateMetadata({ params }: ItemPageProps) {
  const item = await getItemBySlug(params.slug);
  if (!item) return { title: 'Item Not Found' };

  return {
    title: `${item.name} - ${item.breed}`,
    description: `Meet ${item.name}, a ${item.color} ${item.breed} at {{PROJECT_NAME}}.`
  };
}

export async function generateStaticParams() {
  const items = await getAllItems();
  return items.map(d => ({ slug: d.id }));
}

export default async function ItemPage({ params }: ItemPageProps) {
  const item = await getItemBySlug(params.slug);

  if (!item) {
    notFound();
  }

  return (
    <div className="container">
      <Breadcrumbs
        items={[
          { label: 'Home', href: '/' },
          { label: 'Items', href: '/items' },
          { label: item.name, href: `/items/${item.id}` }
        ]}
      />

      <ItemBiography item={item} />
    </div>
  );
}
```

**When to Split**:
- Page exceeds 150 lines → Extract components
- Complex data fetching → Move to server actions
- Client interactivity → Extract to 'use client' components

---

### Hook Files (use-*.ts)

**Target**: 20-80 lines
**Maximum**: 120 lines
**Purpose**: Single custom React hook

**Example - Good Size** (~45 lines):
```typescript
// hooks/use-item-search.ts
import { useState, useEffect } from 'react';
import { Item } from '@/lib/items/types';
import { searchItems } from '@/lib/items/queries';

export function useItemSearch(initialQuery: string = '') {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }

    const searchAsync = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const items = await searchItems(query);
        setResults(items);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Search failed'));
      } finally {
        setIsLoading(false);
      }
    };

    const timeoutId = setTimeout(searchAsync, 300); // Debounce
    return () => clearTimeout(timeoutId);
  }, [query]);

  return { query, setQuery, results, isLoading, error };
}
```

**When to Split**:
- Hook exceeds 80 lines → Extract sub-hooks
- Multiple pieces of state → Separate hooks

---

### Test Files (*.test.ts, *.spec.ts)

**Target**: Matches source file size (1:1 ratio)
**Maximum**: 300 lines
**Purpose**: Comprehensive test coverage

**Philosophy**: Test files can be as large as the code they test, but not larger.

**Example** (~80 lines tests ~60 line utils file):
```typescript
// lib/utils/date-utils.test.ts
import { formatDateWithoutTimezone, calculateAge, isAdult } from './date-utils';

describe('formatDateWithoutTimezone', () => {
  test('formats date correctly', () => {
    expect(formatDateWithoutTimezone('2020-05-12')).toBe('May 12, 2020');
  });

  test('handles invalid date', () => {
    expect(() => formatDateWithoutTimezone('invalid')).toThrow();
  });
});

describe('calculateAge', () => {
  test('calculates age correctly', () => {
    // Mock current date as 2024-01-01
    jest.useFakeTimers().setSystemTime(new Date('2024-01-01'));

    expect(calculateAge('2020-01-01')).toBe(4);
    expect(calculateAge('2021-06-15')).toBe(2);

    jest.useRealTimers();
  });
});

describe('isAdult', () => {
  test('returns true for adult items', () => {
    jest.useFakeTimers().setSystemTime(new Date('2024-01-01'));
    expect(isAdult('2020-01-01', 3)).toBe(true);
    jest.useRealTimers();
  });

  test('returns false for young items', () => {
    jest.useFakeTimers().setSystemTime(new Date('2024-01-01'));
    expect(isAdult('2023-01-01', 3)).toBe(false);
    jest.useRealTimers();
  });
});
```

---

## Measuring File Size

### Effective Lines vs Total Lines

Not all lines are equal. Exclude from counts:

- Blank lines
- Import statements
- Comments (but not JSDoc)
- Closing braces on their own line

**Example**:
```typescript
// Total lines: 45
// Effective lines: ~25

import { useState } from 'react';      // Import - doesn't count
import { Item } from './types';      // Import - doesn't count
                                       // Blank - doesn't count
// Component for displaying item     // Comment - doesn't count
export function ItemCard({ item }: Props) {  // Counts
  const [expanded, setExpanded] = useState(false); // Counts
                                       // Blank - doesn't count
  return (                             // Counts
    <div>                              // Counts
      {item.name}                    // Counts
    </div>                             // Counts (debatable)
  );                                   // Counts (debatable)
}                                      // Counts (debatable)
```

**Script to count effective lines**:
```bash
# Count excluding imports, blanks, and comments
grep -v "^import\|^//\|^$" file.ts | wc -l
```

---

## Exception Cases

### When Larger Files Are Acceptable

1. **Auto-Generated Code**
   - TypeScript types generated from GraphQL schemas
   - API clients generated from OpenAPI specs
   - Database migration files

2. **Data Files**
   - Large constant arrays (item data, country lists)
   - Configuration objects with many keys
   - Translation files with 100+ strings

3. **Complex Components**
   - Data visualization components (D3.js charts)
   - Rich text editors
   - Complex forms with extensive validation

4. **Migration Code**
   - Database seed files
   - One-time data transformation scripts

**Rule**: Exception files should:
- Be clearly labeled (e.g., `items.data.ts` not `items.ts`)
- Have a comment explaining why they're large
- Be reviewed less frequently (stable)

---

## Size vs Complexity

**File size ≠ File complexity**

A 100-line file with deep nesting and complex logic is worse than a 200-line file with simple, linear logic.

### Complexity Metrics

**Low Complexity** (okay to be larger):
```typescript
// 200 lines, but simple object definitions
export const itemData = [
  { id: 1, name: 'Lucy', breed: 'Jenny' },
  { id: 2, name: 'Jack', breed: 'Jack' },
  // ... 50 more entries
];
```

**High Complexity** (must be smaller):
```typescript
// Only 80 lines, but high cyclomatic complexity
export function calculateBreedingEligibility(
  item: Item,
  rules: BreedingRules
): EligibilityResult {
  if (item.breed === 'Jenny') {
    if (item.age < 3) return 'too-young';
    if (item.age > 15) return 'too-old';
    if (item.currentlyBred) {
      if (monthsSinceBreeding(item) < 11) return 'recently-bred';
      // ... 10 more nested conditions
    }
  }
  // ... more complex logic
}
```

**Fix**: Split high-complexity functions into smaller, testable units.

---

## Quick Reference Table

| File Type | Target Lines | Max Lines | Split Trigger |
|-----------|--------------|-----------|---------------|
| Types | 20-50 | 100 | >10 interfaces |
| Utils | 30-100 | 150 | >8 functions |
| Components | 50-200 | 300 | Sub-components or hooks |
| Data | 100-500 | 1000 | >100 entries |
| Services | 80-150 | 250 | >8 methods |
| Pages | 50-150 | 250 | Complex logic |
| Hooks | 20-80 | 120 | Multiple state pieces |
| Tests | 1:1 with source | 300 | Too many test cases |

---

## Validation Commands

```bash
# Find large files
find src -name "*.ts" -o -name "*.tsx" | xargs wc -l | sort -rn | head -20

# Find files over 200 lines
find src -name "*.ts" -o -name "*.tsx" | xargs wc -l | awk '$1 > 200'

# Count effective lines (excluding imports and blanks)
grep -v "^import\|^$" src/file.ts | wc -l
```

---

*"The perfect file size is the smallest size that maintains cohesion."*

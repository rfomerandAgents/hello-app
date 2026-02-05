# Before/After Refactoring Examples

Real-world examples demonstrating the transformation from monolithic files to modular, agent-friendly structures.

## Table of Contents

- [Example 1: Data and Logic Split](#example-1-data-and-logic-split)
- [Example 2: Component Extraction](#example-2-component-extraction)
- [Example 3: Utility Functions Extraction](#example-3-utility-functions-extraction)
- [Example 4: API Service Modularization](#example-4-api-service-modularization)
- [Example 5: Hook Extraction](#example-5-hook-extraction)

---

## Example 1: Data and Logic Split

### Before: Monolithic lib/items.ts (758 lines)

**Problem**: Single file containing types, data, and all business logic. Any change to the domain requires editing this file, creating a bottleneck for parallel development.

```typescript
// lib/items.ts (758 lines total)

// Types (50 lines)
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
  location: string;
  description: string;
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

// Data array (450 lines)
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
    arrivalDate: '2018-06-01',
    location: 'Main Pasture',
    description: 'Sweet and gentle category...'
  },
  // ... 50+ more item entries
];

// Query functions (80 lines)
export function getItemBySlug(slug: string): Item | undefined {
  return items.find(d => d.id === slug);
}

export function getAllItems(): Item[] {
  return items;
}

export function getItemCount(): number {
  return items.length;
}

export function getItemsByLocation(location: string): Item[] {
  return items.filter(d => d.location === location);
}

// Filter functions (60 lines)
export function getAllJennys(): Item[] {
  return items.filter(d => d.breed === 'Jenny');
}

export function getAllJacks(): Item[] {
  return items.filter(d => d.breed === 'Jack');
}

export function getFoals(): Item[] {
  const now = new Date();
  return items.filter(d => {
    const birth = new Date(d.birthdate);
    const ageMonths = (now.getTime() - birth.getTime()) / (1000 * 60 * 60 * 24 * 30);
    return ageMonths < 12;
  });
}

export function getAdultItems(): Item[] {
  const now = new Date();
  return items.filter(d => {
    const birth = new Date(d.birthdate);
    const ageYears = (now.getTime() - birth.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
    return ageYears >= 3;
  });
}

// Breeding functions (30 lines)
export function isCurrentlyBred(itemId: string): boolean {
  const item = getItemBySlug(itemId);
  return item?.currentlyBred ?? false;
}

export function getBreedingStatus(itemId: string): string {
  const item = getItemBySlug(itemId);
  if (!item) return 'unknown';
  if (item.breed !== 'Jenny') return 'not-applicable';
  if (item.currentlyBred) return 'bred';
  return 'open';
}

// Details functions (40 lines)
export function buildDetails(itemId: string, generations: number = 3): Details {
  const ancestors: Ancestor[] = [];
  const item = getItemBySlug(itemId);

  if (!item) {
    return { itemId, generation: 0, ancestors: [] };
  }

  // Recursive details building logic...
  // ... more code ...

  return { itemId, generation: generations, ancestors };
}

// Age calculation utilities (30 lines)
export function calculateAge(birthdate: string): number {
  const birth = new Date(birthdate);
  const now = new Date();
  const diffMs = now.getTime() - birth.getTime();
  const ageYears = diffMs / (1000 * 60 * 60 * 24 * 365.25);
  return Math.floor(ageYears);
}

// More utility functions...
```

**Issues**:
- 758 lines - too large for comfortable editing
- Mixing concerns: types, data, queries, filters, breeding, details
- Multiple agents need to edit this file simultaneously = conflicts
- Modified in 40+ commits - high churn

---

### After: Modular Structure

```
lib/items/
  types.ts          (~45 lines)
  data.ts           (~450 lines)
  queries.ts        (~80 lines)
  filters.ts        (~60 lines)
  breeding.ts       (~30 lines)
  details.ts       (~40 lines)
  utils.ts          (~30 lines)
  index.ts          (~20 lines)
```

**lib/items/types.ts** (~45 lines):
```typescript
// Types only - changes when domain model evolves
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
  location: string;
  description: string;
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
export type BreedingStatus = 'bred' | 'open' | 'not-applicable' | 'unknown';
```

**lib/items/data.ts** (~450 lines):
```typescript
// Data only - changes when adding/updating items
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
    arrivalDate: '2018-06-01',
    location: 'Main Pasture',
    description: 'Sweet and gentle category...'
  },
  // ... 50+ more item entries (alphabetically sorted)
];
```

**lib/items/queries.ts** (~80 lines):
```typescript
// Query functions only - changes when adding query capabilities
import { Item } from './types';
import { items } from './data';

export function getItemBySlug(slug: string): Item | undefined {
  return items.find(d => d.id === slug);
}

export function getAllItems(): Item[] {
  return items;
}

export function getItemCount(): number {
  return items.length;
}

export function getItemsByLocation(location: string): Item[] {
  return items.filter(d => d.location === location);
}
```

**lib/items/filters.ts** (~60 lines):
```typescript
// Filter functions only - changes when adding filter capabilities
import { Item } from './types';
import { items } from './data';
import { calculateAge } from './utils';

export function getAllJennys(): Item[] {
  return items.filter(d => d.breed === 'Jenny');
}

export function getAllJacks(): Item[] {
  return items.filter(d => d.breed === 'Jack');
}

export function getFoals(): Item[] {
  return items.filter(d => calculateAge(d.birthdate) < 1);
}

export function getAdultItems(): Item[] {
  return items.filter(d => calculateAge(d.birthdate) >= 3);
}
```

**lib/items/breeding.ts** (~30 lines):
```typescript
// Breeding logic only - changes when breeding rules change
import { BreedingStatus } from './types';
import { getItemBySlug } from './queries';

export function isCurrentlyBred(itemId: string): boolean {
  const item = getItemBySlug(itemId);
  return item?.currentlyBred ?? false;
}

export function getBreedingStatus(itemId: string): BreedingStatus {
  const item = getItemBySlug(itemId);
  if (!item) return 'unknown';
  if (item.breed !== 'Jenny') return 'not-applicable';
  if (item.currentlyBred) return 'bred';
  return 'open';
}
```

**lib/items/details.ts** (~40 lines):
```typescript
// Details logic only
import { Details, Ancestor } from './types';
import { getItemBySlug } from './queries';

export function buildDetails(itemId: string, generations: number = 3): Details {
  const ancestors: Ancestor[] = [];
  const item = getItemBySlug(itemId);

  if (!item) {
    return { itemId, generation: 0, ancestors: [] };
  }

  // Recursive details building logic...

  return { itemId, generation: generations, ancestors };
}
```

**lib/items/utils.ts** (~30 lines):
```typescript
// Utility functions only
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
```

**lib/items/index.ts** (~20 lines):
```typescript
// Public API - barrel file
export type { Item, ItemBreed, Details, Ancestor, BreedingStatus } from './types';

export { getItemBySlug, getAllItems, getItemCount, getItemsByLocation } from './queries';
export { getAllJennys, getAllJacks, getFoals, getAdultItems } from './filters';
export { isCurrentlyBred, getBreedingStatus } from './breeding';
export { buildDetails } from './details';
export { calculateAge, isAdult } from './utils';

// Note: data.ts is NOT exported - internal implementation detail
```

**Benefits**:
- 8 focused files instead of 1 monolithic file
- Agents can work in parallel:
  - Agent A: Add new item (edits data.ts)
  - Agent B: Add search function (edits queries.ts)
  - Agent C: Add filter (edits filters.ts)
  - Zero conflicts!
- Clear separation of concerns
- Easier to test (mock data separately from logic)
- Public API remains stable via barrel file

---

## Example 2: Component Extraction

### Before: Monolithic components/ItemBiography.tsx (360 lines)

```typescript
// components/ItemBiography.tsx (360 lines)
'use client';

import { useState, useCallback } from 'react';
import { Item } from '@/lib/items/types';

interface ItemBiographyProps {
  item: Item;
}

export default function ItemBiography({ item }: ItemBiographyProps) {
  const [isDetailsExpanded, setIsDetailsExpanded] = useState(false);
  const [isTimelineExpanded, setIsTimelineExpanded] = useState(false);

  // Utility function embedded
  const formatDateWithoutTimezone = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Custom hook logic embedded
  const toggleDetails = useCallback(() => {
    setIsDetailsExpanded(prev => !prev);
  }, []);

  const toggleTimeline = useCallback(() => {
    setIsTimelineExpanded(prev => !prev);
  }, []);

  return (
    <div className="item-biography">
      {/* Header section - 40 lines */}
      <header>
        <h1>{item.name}</h1>
        <p className="breed">{item.breed}</p>
        <p className="birthdate">Born {formatDateWithoutTimezone(item.birthdate)}</p>
        {/* ... more header content */}
      </header>

      {/* Characteristics section - 60 lines */}
      <section className="characteristics">
        <h2>Characteristics</h2>
        <dl>
          <dt>Color</dt>
          <dd>{item.color}</dd>
          <dt>Markings</dt>
          <dd>{item.markings.join(', ')}</dd>
          {/* ... more characteristics */}
        </dl>
      </section>

      {/* Details section - 100 lines */}
      <section className="details">
        <div className="section-header" onClick={toggleDetails}>
          <h2>Details</h2>
          <button>{isDetailsExpanded ? '−' : '+'}</button>
        </div>

        {isDetailsExpanded && (
          <div className="details-tree">
            {/* Complex details rendering - 80 lines */}
            {item.parentA && (
              <div className="parent">
                <h3>Sire: {item.parentA}</h3>
                {/* Recursive details display... */}
              </div>
            )}
            {item.parentB && (
              <div className="parent">
                <h3>Dam: {item.parentB}</h3>
                {/* Recursive details display... */}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Timeline section - 80 lines */}
      <section className="timeline">
        <div className="section-header" onClick={toggleTimeline}>
          <h2>Timeline</h2>
          <button>{isTimelineExpanded ? '−' : '+'}</button>
        </div>

        {isTimelineExpanded && (
          <div className="timeline-events">
            {/* Timeline rendering - 60 lines */}
            <div className="event">
              <span className="date">{formatDateWithoutTimezone(item.birthdate)}</span>
              <span className="description">Born</span>
            </div>
            {/* ... more timeline events */}
          </div>
        )}
      </section>

      {/* Footer - 20 lines */}
      <footer>
        <p className="description">{item.description}</p>
      </footer>
    </div>
  );
}
```

**Issues**:
- 360 lines - too large for comfortable review
- Multiple concerns mixed: main component, sub-components, hooks, utilities
- Hard to test individual pieces
- Multiple agents can't work on different sections simultaneously

---

### After: Modular Component Structure

```
components/ItemBiography/
  index.tsx                  (~80 lines)
  ItemHeader.tsx           (~40 lines)
  CharacteristicsSection.tsx (~60 lines)
  DetailsSection.tsx        (~100 lines)
  TimelineSection.tsx        (~80 lines)
  useToggle.ts               (~30 lines)
  formatDate.ts              (~20 lines)
  types.ts                   (~15 lines)
```

**components/ItemBiography/types.ts** (~15 lines):
```typescript
import { Item } from '@/lib/items/types';

export interface ItemBiographyProps {
  item: Item;
}

export interface SectionProps {
  item: Item;
}
```

**components/ItemBiography/useToggle.ts** (~30 lines):
```typescript
import { useState, useCallback } from 'react';

export function useToggle(initialValue: boolean = false) {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue(prev => !prev);
  }, []);

  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse } as const;
}
```

**components/ItemBiography/formatDate.ts** (~20 lines):
```typescript
export function formatDateWithoutTimezone(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}
```

**components/ItemBiography/ItemHeader.tsx** (~40 lines):
```typescript
import { SectionProps } from './types';
import { formatDateWithoutTimezone } from './formatDate';

export function ItemHeader({ item }: SectionProps) {
  return (
    <header className="item-header">
      <h1>{item.name}</h1>
      <p className="breed">{item.breed}</p>
      <p className="birthdate">
        Born {formatDateWithoutTimezone(item.birthdate)}
      </p>
      {item.currentlyBred && (
        <div className="badge">Currently Bred</div>
      )}
    </header>
  );
}
```

**components/ItemBiography/CharacteristicsSection.tsx** (~60 lines):
```typescript
import { SectionProps } from './types';

export function CharacteristicsSection({ item }: SectionProps) {
  return (
    <section className="characteristics">
      <h2>Characteristics</h2>
      <dl>
        <dt>Color</dt>
        <dd>{item.color}</dd>

        <dt>Markings</dt>
        <dd>{item.markings.join(', ')}</dd>

        <dt>Location</dt>
        <dd>{item.location}</dd>
      </dl>
    </section>
  );
}
```

**components/ItemBiography/DetailsSection.tsx** (~100 lines):
```typescript
'use client';

import { SectionProps } from './types';
import { useToggle } from './useToggle';

export function DetailsSection({ item }: SectionProps) {
  const { value: isExpanded, toggle } = useToggle(false);

  return (
    <section className="details">
      <div className="section-header" onClick={toggle}>
        <h2>Details</h2>
        <button>{isExpanded ? '−' : '+'}</button>
      </div>

      {isExpanded && (
        <div className="details-tree">
          {item.parentA && (
            <div className="parent">
              <h3>Sire: {item.parentA}</h3>
            </div>
          )}
          {item.parentB && (
            <div className="parent">
              <h3>Dam: {item.parentB}</h3>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
```

**components/ItemBiography/TimelineSection.tsx** (~80 lines):
```typescript
'use client';

import { SectionProps } from './types';
import { useToggle } from './useToggle';
import { formatDateWithoutTimezone } from './formatDate';

export function TimelineSection({ item }: SectionProps) {
  const { value: isExpanded, toggle } = useToggle(false);

  return (
    <section className="timeline">
      <div className="section-header" onClick={toggle}>
        <h2>Timeline</h2>
        <button>{isExpanded ? '−' : '+'}</button>
      </div>

      {isExpanded && (
        <div className="timeline-events">
          <div className="event">
            <span className="date">
              {formatDateWithoutTimezone(item.birthdate)}
            </span>
            <span className="description">Born</span>
          </div>
          <div className="event">
            <span className="date">
              {formatDateWithoutTimezone(item.arrivalDate)}
            </span>
            <span className="description">Arrived at {{PROJECT_NAME}}</span>
          </div>
        </div>
      )}
    </section>
  );
}
```

**components/ItemBiography/index.tsx** (~80 lines):
```typescript
import { ItemBiographyProps } from './types';
import { ItemHeader } from './ItemHeader';
import { CharacteristicsSection } from './CharacteristicsSection';
import { DetailsSection } from './DetailsSection';
import { TimelineSection } from './TimelineSection';

export default function ItemBiography({ item }: ItemBiographyProps) {
  return (
    <div className="item-biography">
      <ItemHeader item={item} />
      <CharacteristicsSection item={item} />
      <DetailsSection item={item} />
      <TimelineSection item={item} />

      <footer>
        <p className="description">{item.description}</p>
      </footer>
    </div>
  );
}
```

**Benefits**:
- 8 focused files instead of 1 monolithic component
- Parallel development:
  - Agent A: Update DetailsSection.tsx
  - Agent B: Update TimelineSection.tsx
  - Agent C: Update CharacteristicsSection.tsx
  - Zero conflicts!
- Easier to test each section independently
- Reusable hooks and utilities (useToggle, formatDate)
- Main component is now just composition

---

## Example 3: Utility Functions Extraction

### Before: Scattered Utilities

```typescript
// Multiple files with embedded utilities

// components/ItemCard.tsx
function formatDate(date: string) {
  return new Date(date).toLocaleDateString();
}

// components/ItemList.tsx
function formatDate(date: string) {  // Duplicated!
  return new Date(date).toLocaleDateString();
}

// pages/items/[slug]/page.tsx
function calculateAge(birthdate: string) {
  const birth = new Date(birthdate);
  const now = new Date();
  return Math.floor((now.getTime() - birth.getTime()) / (1000 * 60 * 60 * 24 * 365.25));
}
```

**Issues**:
- Duplicated code across files
- Inconsistent implementations
- Hard to update (must find all copies)

---

### After: Centralized Utilities

```
lib/utils/
  date-utils.ts
  string-utils.ts
  array-utils.ts
  index.ts
```

**lib/utils/date-utils.ts**:
```typescript
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
```

**Usage**:
```typescript
// components/ItemCard.tsx
import { formatDateWithoutTimezone } from '@/lib/utils/date-utils';

export function ItemCard({ item }: Props) {
  return <div>{formatDateWithoutTimezone(item.birthdate)}</div>;
}

// components/ItemList.tsx
import { formatDateWithoutTimezone, calculateAge } from '@/lib/utils/date-utils';

export function ItemList({ items }: Props) {
  return items.map(d => (
    <div key={d.id}>
      {d.name} - Age {calculateAge(d.birthdate)}
    </div>
  ));
}
```

**Benefits**:
- DRY (Don't Repeat Yourself)
- Single source of truth
- Easy to test utilities in isolation
- Consistent behavior across app

---

## Summary: Migration Path

For any large file, follow this process:

1. **Analyze**: Identify distinct concerns (types, data, queries, UI, etc.)
2. **Plan**: Create file structure matching concerns
3. **Extract**: Move code incrementally, one concern at a time
4. **Test**: Verify behavior unchanged after each extraction
5. **Update Imports**: Fix all import statements
6. **Create Barrel**: Add index.ts for clean public API
7. **Verify**: Ensure all tests pass
8. **Commit**: Single commit with clear refactoring message

**Result**: Modular, agent-friendly codebase ready for parallel development!

# Export Patterns for JavaScript/TypeScript

Comprehensive guide to import/export patterns that minimize merge conflicts and enable parallel development.

## Table of Contents

- [Named vs Default Exports](#named-vs-default-exports)
- [Barrel File Patterns](#barrel-file-patterns)
- [Tree-Shaking Considerations](#tree-shaking-considerations)
- [Circular Dependency Prevention](#circular-dependency-prevention)
- [Re-export Strategies](#re-export-strategies)

---

## Named vs Default Exports

### Prefer Named Exports

**Why**: Named exports provide better developer experience and enable safer refactoring.

**Named Exports** (Recommended):
```typescript
// components/button.tsx
export function Button(props: ButtonProps) {
  return <button {...props} />;
}

export function IconButton(props: IconButtonProps) {
  return <button className="icon-btn" {...props} />;
}

export type ButtonProps = {
  variant: 'primary' | 'secondary';
  onClick: () => void;
};
```

**Usage**:
```typescript
// Explicit imports - IDE knows what's available
import { Button, IconButton, ButtonProps } from '@/components/button';

// Easier to refactor - find all references
// Easier to tree-shake - bundler knows what's used
```

**Default Exports** (Use Sparingly):
```typescript
// components/button.tsx
export default function Button(props: ButtonProps) {
  return <button {...props} />;
}

// Problem: Can be imported with any name
import Btn from '@/components/button';      // Works
import MyButton from '@/components/button'; // Also works
import Whatever from '@/components/button'; // Still works!

// Hard to find references across codebase
```

### When to Use Default Exports

Default exports are acceptable for:

1. **Next.js Pages** (Required by framework):
```typescript
// app/items/page.tsx
export default function ItemsPage() {
  return <div>Items</div>;
}
```

2. **Single-Purpose Components** (Convention):
```typescript
// components/logo.tsx
export default function Logo() {
  return <img src="/logo.svg" alt="Logo" />;
}

// But still export types as named exports
export type LogoProps = { size: number };
```

3. **Lazy-Loaded Components**:
```typescript
// Lazy loading works better with default exports
const ItemBiography = lazy(() => import('@/components/item-biography'));
```

### Conversion Strategy

If you have default exports, gradually convert to named:

```typescript
// Before (default export)
export default function Button(props: ButtonProps) {
  return <button {...props} />;
}

// Step 1: Add named export alongside default
export function Button(props: ButtonProps) {
  return <button {...props} />;
}
export default Button;

// Step 2: Update all imports to use named export
// import Button from './button'; → import { Button } from './button';

// Step 3: Remove default export
export function Button(props: ButtonProps) {
  return <button {...props} />;
}
```

---

## Barrel File Patterns

Barrel files (`index.ts`) aggregate exports from multiple files, creating a clean public API.

### Basic Barrel Pattern

```typescript
// lib/items/index.ts
export * from './types';
export * from './queries';
export * from './filters';
export * from './breeding';
```

**Usage**:
```typescript
// Instead of:
import { Item } from '@/lib/items/types';
import { getItemBySlug } from '@/lib/items/queries';
import { getAllJennys } from '@/lib/items/filters';

// Use:
import { Item, getItemBySlug, getAllJennys } from '@/lib/items';
```

### Selective Re-exports

Don't export everything - hide internal implementation:

```typescript
// lib/items/index.ts

// Public API - types
export type { Item, ItemBreed, ItemFilters } from './types';

// Public API - queries
export { getItemBySlug, getAllItems } from './queries';

// Public API - filters
export { getAllJennys, getAllJacks, getFoals } from './filters';

// NOT exported - internal implementation
// export { items } from './data';  ← Data array is private
// export { validateItem } from './validation';  ← Internal utility
```

**Benefits**:
- Clear public vs private API
- Can refactor internals without breaking consumers
- Reduces surface area for breaking changes

### Named Re-exports

For clarity, explicitly name what you're exporting:

```typescript
// Verbose but clear
export { getItemBySlug } from './queries';
export { getAllItems } from './queries';
export { getAllJennys } from './filters';
export { getAllJacks } from './filters';

// vs Wildcard (less clear)
export * from './queries';
export * from './filters';
```

**Tradeoff**:
- Named: More maintenance, but explicit
- Wildcard: Less maintenance, but can accidentally export

### Avoiding Barrel File Pitfalls

**Pitfall 1: Performance**

Barrel files can slow down builds if misused:

```typescript
// BAD: Everything in one giant barrel
// lib/index.ts
export * from './items';
export * from './horses';
export * from './goats';
export * from './sheep';
// ... 50 more exports

// Consumer only needs one function:
import { getItemBySlug } from '@/lib';
// But bundler might include everything from lib/
```

**Fix**: Use granular barrels:

```typescript
// GOOD: Specific barrels
import { getItemBySlug } from '@/lib/items';
// Only includes item-related code
```

**Pitfall 2: Circular Dependencies**

Barrels can create circular dependencies:

```typescript
// lib/items/queries.ts
import { formatItemData } from '@/lib/items';  // Imports from barrel
// ↑ Circular! queries.ts exports to barrel, then imports from it

// FIX: Import from specific file
import { formatItemData } from './utils';
```

**Rule**: Internal files should NEVER import from their own barrel.

### Barrel File Convention

```typescript
// lib/items/index.ts

// ===== Public API =====
// Types
export type {
  Item,
  ItemBreed,
  ItemColor,
  ItemFilters
} from './types';

// Query Functions
export {
  getItemBySlug,
  getAllItems,
  getItemCount
} from './queries';

// Filter Functions
export {
  getAllJennys,
  getAllJacks,
  getFoals
} from './filters';

// Utility Functions
export {
  calculateAge,
  isAdult
} from './utils';

// ===== Internal Only (NOT exported) =====
// - data.ts (raw item array)
// - validation.ts (internal validation helpers)
```

---

## Tree-Shaking Considerations

Tree-shaking removes unused code from bundles. Export patterns affect tree-shaking effectiveness.

### Tree-Shakable Exports

**Good** (Shakable):
```typescript
// utils.ts
export function formatDate(date: Date): string {
  return date.toISOString();
}

export function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

// Consumer only imports formatDate
import { formatDate } from './utils';
// Bundle ONLY includes formatDate, not formatCurrency ✓
```

**Bad** (Not Shakable):
```typescript
// utils.ts
const utils = {
  formatDate(date: Date): string {
    return date.toISOString();
  },
  formatCurrency(amount: number): string {
    return `$${amount.toFixed(2)}`;
  }
};

export default utils;

// Consumer only uses formatDate
import utils from './utils';
utils.formatDate(new Date());
// Bundle includes ENTIRE utils object ✗
```

### Side-Effect Free Code

Mark modules as side-effect free for better tree-shaking:

```json
// package.json
{
  "sideEffects": false
}

// Or specify files with side-effects
{
  "sideEffects": [
    "**/*.css",
    "src/polyfills.ts"
  ]
}
```

### Re-export and Tree-Shaking

Wildcard re-exports can hurt tree-shaking:

```typescript
// BAD: Wildcard re-export
export * from './module-a';
export * from './module-b';
export * from './module-c';
// Bundler must analyze all three modules

// BETTER: Named re-exports
export { functionA } from './module-a';
export { functionB } from './module-b';
// Bundler only needs to analyze what's explicitly exported
```

**Modern bundlers** (webpack 5, Rollup, esbuild) handle this better, but named exports are still safer.

---

## Circular Dependency Prevention

Circular dependencies cause import errors and undefined values. Prevent them with clear layering.

### What is a Circular Dependency?

```typescript
// file-a.ts
import { funcB } from './file-b';
export function funcA() {
  return funcB();
}

// file-b.ts
import { funcA } from './file-a';  // ← Circular!
export function funcB() {
  return funcA();
}

// Result: Runtime error or undefined function
```

### Layered Architecture

Organize files in layers. Lower layers never import from higher layers.

```
Layer 0: types.ts
  ↑
Layer 1: constants.ts, utils.ts
  ↑
Layer 2: data.ts
  ↑
Layer 3: queries.ts, filters.ts
  ↑
Layer 4: services.ts
  ↑
Layer 5: components.tsx
  ↑
Layer 6: pages.tsx
```

**Example**:
```typescript
// Layer 0: types.ts
export interface Item {
  id: string;
  name: string;
}

// Layer 1: utils.ts
import { Item } from './types';  // ✓ Layer 1 can import Layer 0
export function formatItemName(item: Item): string {
  return item.name.toUpperCase();
}

// Layer 2: data.ts
import { Item } from './types';  // ✓ Layer 2 can import Layer 0
export const items: Item[] = [ /* ... */ ];

// Layer 3: queries.ts
import { Item } from './types';       // ✓ Layer 3 can import Layer 0
import { items } from './data';       // ✓ Layer 3 can import Layer 2
import { formatItemName } from './utils';  // ✓ Layer 3 can import Layer 1

export function getItemBySlug(slug: string): Item | undefined {
  const item = items.find(d => d.id === slug);
  if (item) {
    console.log(formatItemName(item));
  }
  return item;
}

// Layer 4: components.tsx
import { Item } from './types';           // ✓ Layer 4 can import Layer 0
import { getItemBySlug } from './queries'; // ✓ Layer 4 can import Layer 3

export function ItemCard({ slug }: Props) {
  const item = getItemBySlug(slug);
  return <div>{item?.name}</div>;
}
```

### Detecting Circular Dependencies

**ESLint Plugin**:
```bash
npm install --save-dev eslint-plugin-import

# .eslintrc.json
{
  "plugins": ["import"],
  "rules": {
    "import/no-cycle": "error"
  }
}
```

**Manual Detection**:
```bash
# Using madge
npm install --save-dev madge
npx madge --circular src/

# Output shows circular dependencies:
# src/queries.ts -> src/utils.ts -> src/queries.ts
```

### Breaking Circular Dependencies

**Strategy 1: Extract Shared Code**

```typescript
// BEFORE: Circular
// user.ts
import { formatDate } from './post';
export function formatUser(user) {
  return formatDate(user.createdAt);
}

// post.ts
import { formatUser } from './user';
export function formatDate(date) { /* ... */ }

// AFTER: Extracted
// utils/format.ts
export function formatDate(date) { /* ... */ }

// user.ts
import { formatDate } from './utils/format';

// post.ts
import { formatDate } from './utils/format';
```

**Strategy 2: Dependency Injection**

```typescript
// BEFORE: Circular dependency via direct import
// item-service.ts
import { logEvent } from './logger';
export function getItem(id: string) {
  logEvent('get-item', id);
  // ...
}

// logger.ts
import { getItem } from './item-service';  // Circular!
export function logEvent(event: string, id: string) {
  const item = getItem(id);  // Wants to log item name
}

// AFTER: Dependency injection
// item-service.ts
export function getItem(id: string, logger?: Logger) {
  logger?.logEvent('get-item', id);
  // ...
}

// logger.ts (no import of item-service)
export function logEvent(event: string, id: string) {
  // Just logs event, doesn't fetch item
}
```

---

## Re-export Strategies

### Internal vs External Re-exports

**Internal** (within same module):
```typescript
// lib/items/index.ts
export { getItemBySlug } from './queries';
export { getAllJennys } from './filters';
```

**External** (from dependencies):
```typescript
// lib/index.ts
// Re-export common utilities from lodash
export { debounce, throttle } from 'lodash';
```

**When to re-export externally**:
- Creating a facade over third-party libraries
- Want to swap implementations later
- Reduce direct dependencies across codebase

### Type-Only Re-exports

For TypeScript types, use `export type` to avoid runtime overhead:

```typescript
// Good for types
export type { Item, ItemBreed } from './types';

// Avoids including type definition code in bundle
// Only exports the type information
```

### Grouped Re-exports

Organize re-exports by category:

```typescript
// lib/items/index.ts

// ===== TYPES =====
export type {
  Item,
  ItemBreed,
  ItemColor
} from './types';

export type {
  ItemFilters,
  SearchOptions
} from './search-types';

// ===== QUERY FUNCTIONS =====
export {
  getItemBySlug,
  getAllItems
} from './queries';

// ===== FILTER FUNCTIONS =====
export {
  getAllJennys,
  getAllJacks
} from './filters';

// ===== UTILITIES =====
export {
  formatItemName,
  calculateAge
} from './utils';
```

### Conditional Re-exports

Re-export based on environment:

```typescript
// lib/api/index.ts
export { ApiClient } from './client';

// Only export mock in development
if (process.env.NODE_ENV === 'development') {
  export { MockApiClient } from './mock-client';
}
```

---

## Best Practices Summary

### Do's ✓

1. **Prefer named exports** over default exports
2. **Use barrel files** to create clean public APIs
3. **Hide implementation details** - don't export everything
4. **Layer your dependencies** to prevent circular imports
5. **Use `export type`** for TypeScript types
6. **Be explicit** with named re-exports when clarity matters
7. **Document public APIs** in barrel files with comments

### Don'ts ✗

1. **Don't create barrel barrels** (nested layers of barrels)
2. **Don't import from your own barrel** within the module
3. **Don't use wildcard re-exports** for large modules
4. **Don't create circular dependencies** between files
5. **Don't export mutable objects** (prefer functions or constants)
6. **Don't mix default and named exports** in the same file
7. **Don't create mega-barrels** that re-export entire library

---

## Quick Reference

### Named Export
```typescript
// utils.ts
export function formatDate(date: Date): string {
  return date.toISOString();
}

// Usage
import { formatDate } from './utils';
```

### Default Export
```typescript
// button.tsx
export default function Button(props: Props) {
  return <button {...props} />;
}

// Usage
import Button from './button';
```

### Barrel File
```typescript
// lib/items/index.ts
export * from './types';
export { getItemBySlug, getAllItems } from './queries';

// Usage
import { Item, getItemBySlug } from '@/lib/items';
```

### Type-Only Export
```typescript
// types.ts
export type { Item, ItemBreed };

// Usage
import type { Item } from './types';
```

### Conditional Re-export
```typescript
// index.ts
export { prodFunction } from './prod';
if (process.env.NODE_ENV === 'development') {
  export { devFunction } from './dev';
}
```

---

## Validation

Check your export patterns:

```bash
# Find files with default exports
grep -r "export default" src/

# Find potential circular dependencies
npx madge --circular src/

# Check for unused exports
npx ts-prune
```

---

*"Explicit exports create explicit dependencies. Explicit dependencies prevent conflicts."*

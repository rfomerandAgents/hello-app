# TypeScript Testing Patterns

## Overview

TypeScript adds type safety to JavaScript, and testing TypeScript code requires patterns that leverage types while maintaining test clarity. This guide covers testing pure functions, type guards, and utility functions in TypeScript.

## Core Testing Pattern: AAA (Arrange, Act, Assert)

The AAA pattern is the foundation of clear, maintainable tests:

```typescript
describe('functionName', () => {
  it('should do something when condition is met', () => {
    // Arrange - Set up test data and dependencies
    const input = { id: 1, name: 'Test' };
    const expected = { id: 1, name: 'Test', processed: true };

    // Act - Execute the function under test
    const result = functionName(input);

    // Assert - Verify the outcome
    expect(result).toEqual(expected);
  });
});
```

### Why AAA?

1. **Readability** - Clear structure for anyone reading the test
2. **Maintainability** - Easy to update when requirements change
3. **Debugging** - Quickly identify which phase failed
4. **Consistency** - Team follows the same pattern

## Testing Pure Functions

Pure functions are the easiest to test (no side effects, deterministic output).

### Example: Testing `getOffspring` from lineage.ts

```typescript
// Source function
export function getOffspring(itemSlug: string): Item[] {
  return items.filter(
    (item) =>
      (item.parentB === itemSlug || item.parentA === itemSlug) &&
      item.category !== 'sold'
  );
}

// Test file: lib/lineage.test.ts
import { describe, it, expect, vi } from 'vitest';
import { getOffspring } from './lineage';

// Mock the items module
vi.mock('./items', () => ({
  items: [
    {
      id: 1,
      slug: 'mother-item',
      name: 'Mother',
      category: 'category',
    },
    {
      id: 2,
      slug: 'baby-item',
      name: 'Baby',
      parentB: 'mother-item',
      category: 'child',
    },
    {
      id: 3,
      slug: 'sold-baby',
      name: 'Sold Baby',
      parentB: 'mother-item',
      category: 'sold',
    },
  ],
}));

describe('getOffspring', () => {
  describe('when item is a parentB (mother)', () => {
    it('returns offspring where item is the mother', () => {
      // Arrange
      const parentSlug = 'mother-item';

      // Act
      const result = getOffspring(parentSlug);

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0].slug).toBe('baby-item');
    });

    it('excludes sold offspring', () => {
      // Arrange
      const parentSlug = 'mother-item';

      // Act
      const result = getOffspring(parentSlug);

      // Assert
      expect(result.every(d => d.category !== 'sold')).toBe(true);
      expect(result.map(d => d.slug)).not.toContain('sold-baby');
    });
  });

  describe('when item has no offspring', () => {
    it('returns empty array', () => {
      // Arrange
      const childlessSlug = 'baby-item';

      // Act
      const result = getOffspring(childlessSlug);

      // Assert
      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });
  });

  describe('edge cases', () => {
    it('returns empty array for non-existent slug', () => {
      // Arrange
      const invalidSlug = 'does-not-exist';

      // Act
      const result = getOffspring(invalidSlug);

      // Assert
      expect(result).toEqual([]);
    });

    it('returns empty array for empty string', () => {
      // Arrange
      const emptySlug = '';

      // Act
      const result = getOffspring(emptySlug);

      // Assert
      expect(result).toEqual([]);
    });
  });
});
```

## Type-Safe Test Data

### Factory Functions

Create reusable, type-safe test data builders:

```typescript
// test-utils/factories.ts
import { Item, ItemBiography } from '@/lib/items';

/**
 * Create a test item with sensible defaults
 * Override any fields as needed
 */
export const createTestItem = (overrides: Partial<Item> = {}): Item => ({
  id: 1,
  name: 'Test Item',
  slug: 'test-item',
  imageSrc: '/test.jpg',
  alt: 'Test item image',
  type: 'category',
  category: 'category',
  biography: {
    bio: 'Test biography text',
  },
  ...overrides,
});

/**
 * Create a category with breeding status
 */
export const createBredJenny = (overrides: Partial<Item> = {}): Item =>
  createTestItem({
    type: 'category',
    category: 'category',
    breedingStatus: {
      bredTo: 'test-jack',
      expectedYear: 2026,
    },
    ...overrides,
  });

/**
 * Create a jack item
 */
export const createJack = (overrides: Partial<Item> = {}): Item =>
  createTestItem({
    type: 'jack',
    category: 'jack',
    ...overrides,
  });

/**
 * Create a child with parents
 */
export const createFoal = (overrides: Partial<Item> = {}): Item =>
  createTestItem({
    category: 'child',
    parentB: 'mother-slug',
    parentA: 'father-slug',
    ...overrides,
  });
```

### Using Factories in Tests

```typescript
import { createTestItem, createBredJenny } from '@/test-utils/factories';

describe('hasBreedingStatus', () => {
  it('returns true for bred category', () => {
    // Arrange - Factory creates type-safe item
    const category = createBredJenny({ name: 'Pink Lady' });

    // Act
    const result = hasBreedingStatus(category);

    // Assert
    expect(result).toBe(true);
  });

  it('returns false for item without breeding status', () => {
    // Arrange - Override breeding status to undefined
    const category = createTestItem({
      type: 'category',
      breedingStatus: undefined,
    });

    // Act
    const result = hasBreedingStatus(category);

    // Assert
    expect(result).toBe(false);
  });
});
```

### Benefits of Factory Functions

1. **Type safety** - TypeScript ensures all required fields are present
2. **DRY** - No duplicated test data setup
3. **Maintainability** - Update one place when types change
4. **Readability** - Express intent clearly (`createBredJenny()`)
5. **Flexibility** - Override only what matters for the test

## Parameterized Tests (Test Tables)

Test multiple inputs efficiently with `test.each`:

```typescript
describe('getParentCount', () => {
  it.each([
    { parentB: undefined, parentA: undefined, expected: 0 },
    { parentB: 'mother', parentA: undefined, expected: 1 },
    { parentB: undefined, parentA: 'father', expected: 1 },
    { parentB: 'mother', parentA: 'father', expected: 2 },
  ])('returns $expected when parentB=$parentB and parentA=$parentA', ({ parentB, parentA, expected }) => {
    // Arrange
    const item = createTestItem({ parentB, parentA });

    // Act
    const result = getParentCount(item);

    // Assert
    expect(result).toBe(expected);
  });
});
```

### Alternative Syntax

```typescript
describe('isCurrentlyBred', () => {
  const testCases: Array<[string, Item, boolean]> = [
    ['bred category', createBredJenny(), true],
    ['non-bred category', createTestItem({ type: 'category' }), false],
    ['jack item', createJack(), false],
  ];

  test.each(testCases)('%s: returns %s', (description, item, expected) => {
    expect(isCurrentlyBred(item)).toBe(expected);
  });
});
```

## Testing Type Guards

Type guards are functions that narrow TypeScript types at runtime.

```typescript
// Example type guard
export function isJenny(item: Item): item is Item & { type: 'category' } {
  return item.type === 'category';
}

// Testing type guards
describe('isJenny', () => {
  it('returns true for category items', () => {
    // Arrange
    const category = createTestItem({ type: 'category' });

    // Act
    const result = isJenny(category);

    // Assert
    expect(result).toBe(true);

    // TypeScript now knows category.type is 'category'
    if (result) {
      type AssertJennyType = typeof category.type; // 'category'
    }
  });

  it('returns false for jack items', () => {
    // Arrange
    const jack = createTestItem({ type: 'jack' });

    // Act
    const result = isJenny(jack);

    // Assert
    expect(result).toBe(false);
  });
});
```

## Testing Functions with Optional Parameters

```typescript
// Function with optional parameters
export function formatItemName(
  item: Item,
  includeAge: boolean = false
): string {
  if (includeAge && item.biography.age) {
    return `${item.name} (${item.biography.age})`;
  }
  return item.name;
}

// Tests
describe('formatItemName', () => {
  const item = createTestItem({
    name: 'Pink Lady',
    biography: { bio: 'Test', age: '6 years old' },
  });

  it('returns name only when includeAge is false', () => {
    expect(formatItemName(item, false)).toBe('Pink Lady');
  });

  it('returns name only when includeAge is omitted (default)', () => {
    expect(formatItemName(item)).toBe('Pink Lady');
  });

  it('returns name with age when includeAge is true', () => {
    expect(formatItemName(item, true)).toBe('Pink Lady (6 years old)');
  });

  it('returns name only when includeAge is true but age is missing', () => {
    const itemNoAge = createTestItem({
      name: 'Rain',
      biography: { bio: 'Test', age: undefined },
    });

    expect(formatItemName(itemNoAge, true)).toBe('Rain');
  });
});
```

## Testing Array Transformations

Common pattern in this codebase (filter, map, reduce):

```typescript
// Function that transforms arrays
export function getItemsByCategory(category: Item['category']): string[] {
  return items
    .filter(d => d.category === category)
    .map(d => d.name);
}

// Tests
describe('getItemsByCategory', () => {
  it('returns names of categories', () => {
    // Arrange
    const expectedJennies = ['Pink Lady', 'Rain', 'Spumoni'];

    // Act
    const result = getItemsByCategory('category');

    // Assert
    expect(result).toEqual(expectedJennies);
    expect(result).toHaveLength(expectedJennies.length);
  });

  it('returns empty array for category with no items', () => {
    // Arrange
    const nonExistentCategory = 'unicorn' as Item['category'];

    // Act
    const result = getItemsByCategory(nonExistentCategory);

    // Assert
    expect(result).toEqual([]);
  });

  it('returns names in correct order (as filtered)', () => {
    // Arrange
    const category = 'category';

    // Act
    const result = getItemsByCategory(category);

    // Assert
    // Verify order matches the source array order
    expect(result[0]).toBe('Pink Lady'); // First category in the array
  });
});
```

## Testing Functions with Complex Logic

```typescript
// Function: buildLineageTree (from lineage.ts)
export function buildLineageTree(item: Item): LineageTreeNode {
  const children: LineageTreeNode[] = [];

  // Add parentB if present
  if (item.parentB) {
    const parentB = items.find(d => d.slug === item.parentB);
    if (parentB) {
      children.push({ name: parentB.name, slug: parentB.slug, type: 'parentB' });
    } else {
      children.push({
        name: item.parentB,
        slug: item.parentB,
        type: 'parentB',
        isPlaceholder: true,
      });
    }
  }

  // ... similar for parentA, offspring, siblings

  return {
    name: item.name,
    slug: item.slug,
    type: 'self',
    children: children.length > 0 ? children : undefined,
  };
}

// Tests - Break complex function into scenarios
describe('buildLineageTree', () => {
  describe('root node (self)', () => {
    it('returns item as root with type "self"', () => {
      // Arrange
      const item = createTestItem({ name: 'Pink Lady', slug: 'pink-lady' });

      // Act
      const tree = buildLineageTree(item);

      // Assert
      expect(tree.name).toBe('Pink Lady');
      expect(tree.slug).toBe('pink-lady');
      expect(tree.type).toBe('self');
    });
  });

  describe('parent nodes', () => {
    it('includes parentB when present in dataset', () => {
      // Arrange
      vi.mock('./items', () => ({
        items: [
          { slug: 'mercury', name: 'Mercury' },
          { slug: 'pink-lady', name: 'Pink Lady', parentB: 'mercury' },
        ],
      }));

      const item = createTestItem({ parentB: 'mercury' });

      // Act
      const tree = buildLineageTree(item);

      // Assert
      const parentBNode = tree.children?.find(c => c.type === 'parentB');
      expect(parentBNode).toBeDefined();
      expect(parentBNode?.name).toBe('Mercury');
      expect(parentBNode?.isPlaceholder).toBeUndefined();
    });

    it('includes parentB as placeholder when not in dataset', () => {
      // Arrange
      const item = createTestItem({ parentB: 'unknown-parentB' });

      // Act
      const tree = buildLineageTree(item);

      // Assert
      const parentBNode = tree.children?.find(c => c.type === 'parentB');
      expect(parentBNode).toBeDefined();
      expect(parentBNode?.name).toBe('unknown-parentB');
      expect(parentBNode?.isPlaceholder).toBe(true);
    });

    it('does not include parentB when undefined', () => {
      // Arrange
      const item = createTestItem({ parentB: undefined });

      // Act
      const tree = buildLineageTree(item);

      // Assert
      const parentBNode = tree.children?.find(c => c.type === 'parentB');
      expect(parentBNode).toBeUndefined();
    });
  });

  describe('offspring nodes', () => {
    it('includes offspring in children', () => {
      // Arrange - Mock with parent-child relationship
      vi.mock('./items', () => ({
        items: [
          { slug: 'mother', name: 'Mother' },
          { slug: 'baby', name: 'Baby', parentB: 'mother', category: 'child' },
        ],
      }));

      const item = createTestItem({ slug: 'mother' });

      // Act
      const tree = buildLineageTree(item);

      // Assert
      const offspringNode = tree.children?.find(c => c.type === 'offspring');
      expect(offspringNode).toBeDefined();
      expect(offspringNode?.name).toBe('Baby');
    });
  });

  describe('children array', () => {
    it('sets children to undefined when no relationships exist', () => {
      // Arrange
      const loner = createTestItem({
        parentB: undefined,
        parentA: undefined,
        // No offspring or siblings
      });

      // Act
      const tree = buildLineageTree(loner);

      // Assert
      expect(tree.children).toBeUndefined();
    });

    it('includes children array when relationships exist', () => {
      // Arrange
      const item = createTestItem({ parentB: 'mercury' });

      // Act
      const tree = buildLineageTree(item);

      // Assert
      expect(tree.children).toBeDefined();
      expect(Array.isArray(tree.children)).toBe(true);
    });
  });
});
```

## Testing Boolean Functions

```typescript
// Function: hasOffspring
export function hasOffspring(itemSlug: string): boolean {
  return getOffspring(itemSlug).length > 0;
}

// Tests
describe('hasOffspring', () => {
  it('returns true when item has offspring', () => {
    // Arrange
    vi.mock('./items', () => ({
      items: [
        { slug: 'mother', name: 'Mother' },
        { slug: 'baby', name: 'Baby', parentB: 'mother', category: 'child' },
      ],
    }));

    // Act
    const result = hasOffspring('mother');

    // Assert
    expect(result).toBe(true);
  });

  it('returns false when item has no offspring', () => {
    // Arrange
    vi.mock('./items', () => ({
      items: [{ slug: 'loner', name: 'Loner' }],
    }));

    // Act
    const result = hasOffspring('loner');

    // Assert
    expect(result).toBe(false);
  });

  it('returns false for non-existent item', () => {
    // Act
    const result = hasOffspring('does-not-exist');

    // Assert
    expect(result).toBe(false);
  });
});
```

## Mocking Module Dependencies

### Mocking the items array

```typescript
import { vi } from 'vitest';

// Mock entire module
vi.mock('./items', () => ({
  items: [
    { id: 1, slug: 'test-1', name: 'Test 1' },
    { id: 2, slug: 'test-2', name: 'Test 2' },
  ],
}));

// Mock with actual module + overrides
vi.mock('./items', async () => {
  const actual = await vi.importActual('./items');
  return {
    ...actual,
    items: [/* test data */],
  };
});
```

### Mocking specific functions

```typescript
import { vi } from 'vitest';
import * as lineageModule from './lineage';

// Spy on function
const getOffspringSpy = vi.spyOn(lineageModule, 'getOffspring');
getOffspringSpy.mockReturnValue([/* test data */]);

// Verify calls
expect(getOffspringSpy).toHaveBeenCalledWith('pink-lady');
expect(getOffspringSpy).toHaveBeenCalledTimes(1);

// Restore original
getOffspringSpy.mockRestore();
```

## Assertion Best Practices

### Use Specific Matchers

```typescript
// ❌ Generic: Hard to understand failures
expect(result === expected).toBe(true);

// ✅ Specific: Clear failure messages
expect(result).toBe(expected);
expect(result).toEqual(expected); // Deep equality
expect(result).toStrictEqual(expected); // Strict deep equality
```

### Array/Object Assertions

```typescript
// Array length
expect(result).toHaveLength(3);

// Array contains
expect(result).toContain('Pink Lady');
expect(result).toContainEqual({ id: 1, name: 'Test' });

// Object shape
expect(result).toMatchObject({ name: 'Pink Lady', type: 'category' });

// Object keys
expect(result).toHaveProperty('name');
expect(result).toHaveProperty('breedingStatus.bredTo', 'santiago');
```

### Boolean Assertions

```typescript
// Truthy/Falsy
expect(result).toBeTruthy();
expect(result).toBeFalsy();

// Specific boolean
expect(result).toBe(true);
expect(result).toBe(false);

// Defined/Undefined
expect(result).toBeDefined();
expect(result).toBeUndefined();
expect(result).toBeNull();
```

## Edge Case Testing Checklist

For every function, test:

- [ ] **Null input** - `null`
- [ ] **Undefined input** - `undefined`
- [ ] **Empty string** - `""`
- [ ] **Empty array** - `[]`
- [ ] **Empty object** - `{}`
- [ ] **Zero** - `0`
- [ ] **Negative numbers** - `-1`
- [ ] **Very large numbers** - `Number.MAX_SAFE_INTEGER`
- [ ] **Invalid enum values** - Type casting edge cases
- [ ] **Boundary values** - First/last array elements, min/max dates

```typescript
describe('edge cases', () => {
  it.each([
    ['null', null],
    ['undefined', undefined],
    ['empty string', ''],
  ])('handles %s input', (description, input) => {
    // Test function behavior with edge case input
    const result = someFunction(input as any);
    expect(result).toEqual(expectedEdgeCaseOutput);
  });
});
```

## Test Organization

### Group by Functionality

```typescript
describe('lineage utilities', () => {
  describe('getOffspring', () => {
    describe('happy path', () => {
      it('returns offspring for parentB', () => {});
      it('returns offspring for parentA', () => {});
    });

    describe('edge cases', () => {
      it('handles non-existent slug', () => {});
      it('handles empty string', () => {});
    });
  });

  describe('getSiblings', () => {
    // Similar structure
  });
});
```

### Use Descriptive Test Names

```typescript
// ❌ BAD: Vague
it('works', () => {});
it('test 1', () => {});

// ✅ GOOD: Descriptive
it('returns offspring where item is the parentB', () => {});
it('excludes sold items from results', () => {});
it('returns empty array for non-existent slug', () => {});
```

## Summary: TypeScript Testing Patterns

1. **AAA Pattern** - Arrange, Act, Assert for clarity
2. **Factory Functions** - Type-safe test data builders
3. **Parameterized Tests** - Test multiple inputs efficiently
4. **Mock Dependencies** - Isolate units under test
5. **Edge Cases** - Test null, undefined, empty values
6. **Specific Matchers** - Use toEqual, toHaveLength, toContain
7. **Descriptive Names** - Test names explain expected behavior
8. **Organize Tests** - Group by functionality and scenario

## Resources

- [Vitest API Reference](https://vitest.dev/api/)
- [Jest Matchers](https://jestjs.io/docs/expect) (Vitest compatible)
- [TypeScript Testing Best Practices](https://basarat.gitbook.io/typescript/intro-1/testing)

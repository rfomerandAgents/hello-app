# Test Organization and File Structure

## Overview

Well-organized tests are easier to maintain, faster to run, and simpler to understand. This guide covers file naming conventions, directory structure, test grouping patterns, and setup/teardown strategies.

## File Naming Conventions

### Test File Names

**Pattern:** `{source-file}.test.{ts|tsx}`

```
src/
├── lib/
│   ├── lineage.ts
│   └── lineage.test.ts          # Test file next to source
├── components/
│   ├── ItemBiography.tsx
│   └── ItemBiography.test.tsx  # Component test
└── utils/
    ├── formatters.ts
    └── formatters.test.ts
```

**Alternatives (less common):**

- `{source-file}.spec.{ts|tsx}` - Jest convention
- `__tests__/{source-file}.test.{ts|tsx}` - Separate directory

**Recommendation for this codebase:** Co-locate tests with source files using `.test.ts(x)` extension.

### Why Co-location?

1. **Easy to find** - Test is right next to the code it tests
2. **Import paths** - Simpler relative imports
3. **Refactoring** - Moving/renaming files keeps tests together
4. **Context** - See test coverage when browsing code

## Directory Structure

### Recommended Structure for {{PROJECT_NAME}}

```
app/
├── lib/
│   ├── items.ts
│   ├── items.test.ts
│   ├── lineage.ts
│   └── lineage.test.ts
├── components/
│   ├── ItemBiography.tsx
│   ├── ItemBiography.test.tsx
│   ├── LineageTree.tsx
│   ├── LineageTree.test.tsx
│   ├── BunInOven.tsx
│   └── BunInOven.test.tsx
├── test-utils/
│   ├── factories.ts              # Test data factories
│   ├── test-helpers.ts           # Shared test utilities
│   └── mocks/
│       ├── items.ts            # Mock data
│       └── next-router.ts        # Next.js mocks
├── vitest.config.ts              # Vitest configuration
└── vitest.setup.ts               # Global test setup
```

### Test Utilities Directory

Shared test code goes in `test-utils/`:

```typescript
// test-utils/factories.ts
export const createTestItem = (overrides = {}) => ({ /* ... */ });

// test-utils/test-helpers.ts
export const renderWithProviders = (component) => { /* ... */ };

// test-utils/mocks/items.ts
export const mockItems = [ /* test data */ ];
```

### Why Separate test-utils?

- Avoid circular dependencies
- Share across multiple test files
- Keep test files focused on assertions
- Easy to find reusable test code

## Test Grouping with describe Blocks

### Pattern: Nested Describe Blocks

Organize tests hierarchically:

```typescript
describe('FunctionOrComponent', () => {
  describe('Feature 1', () => {
    describe('Scenario A', () => {
      it('behaves this way', () => {});
    });

    describe('Scenario B', () => {
      it('behaves that way', () => {});
    });
  });

  describe('Feature 2', () => {
    // ...
  });
});
```

### Real Example: lineage.test.ts

```typescript
describe('lineage utilities', () => {
  // Top-level: Module name

  describe('getOffspring', () => {
    // Second-level: Function name

    describe('when item is a parentB', () => {
      // Third-level: Scenario

      it('returns offspring where item is the mother', () => {
        // Specific behavior
      });

      it('excludes sold offspring', () => {});
    });

    describe('when item is a parentA', () => {
      it('returns offspring where item is the father', () => {});
    });

    describe('edge cases', () => {
      it('returns empty array for non-existent slug', () => {});
      it('returns empty array for empty string', () => {});
    });
  });

  describe('getSiblings', () => {
    // Similar structure for next function
  });
});
```

### Benefits of Grouping

1. **Readable output** - Test reports show hierarchical structure
2. **Focused failures** - Quickly identify which scenario broke
3. **Shared setup** - Use beforeEach within describe blocks
4. **Logical organization** - Group related tests together

### Output Example

```
✓ lineage utilities (8 tests)
  ✓ getOffspring (5 tests)
    ✓ when item is a parentB (2 tests)
      ✓ returns offspring where item is the mother
      ✓ excludes sold offspring
    ✓ when item is a parentA (1 test)
      ✓ returns offspring where item is the father
    ✓ edge cases (2 tests)
      ✓ returns empty array for non-existent slug
      ✓ returns empty array for empty string
  ✓ getSiblings (3 tests)
    ...
```

## Test Naming Conventions

### Pattern: "should [expected behavior] when [condition]"

```typescript
describe('hasOffspring', () => {
  it('should return true when item has offspring', () => {});
  it('should return false when item has no offspring', () => {});
  it('should return false when slug does not exist', () => {});
});
```

### Alternative Pattern (less verbose, more natural)

```typescript
describe('hasOffspring', () => {
  it('returns true when item has offspring', () => {});
  it('returns false when item has no offspring', () => {});
  it('returns false when slug does not exist', () => {});
});
```

**Recommendation:** Use the simpler pattern (without "should") for this codebase.

### Describe Block Naming

```typescript
// ✅ GOOD: Clear context
describe('ItemBiography', () => {
  describe('Bun in Oven section', () => {
    describe('when category is bred', () => {
      it('renders breeding information', () => {});
    });

    describe('when category is not bred', () => {
      it('does not render section', () => {});
    });
  });
});

// ❌ BAD: Vague
describe('ItemBiography', () => {
  describe('test1', () => {
    it('works', () => {});
  });
});
```

## Setup and Teardown Patterns

### beforeEach and afterEach

Run code before/after each test:

```typescript
describe('ItemRepository', () => {
  let repository: ItemRepository;

  beforeEach(() => {
    // Runs before EACH test
    repository = new ItemRepository();
  });

  afterEach(() => {
    // Runs after EACH test
    repository.cleanup();
  });

  it('fetches items', () => {
    // repository is fresh for this test
    const items = repository.getAll();
    expect(items).toHaveLength(10);
  });

  it('filters by category', () => {
    // repository is fresh again
    const categories = repository.filterByCategory('category');
    expect(categories.every(d => d.category === 'category')).toBe(true);
  });
});
```

### beforeAll and afterAll

Run once before/after all tests in a describe block:

```typescript
describe('Database integration tests', () => {
  beforeAll(async () => {
    // Runs ONCE before all tests
    await database.connect();
  });

  afterAll(async () => {
    // Runs ONCE after all tests
    await database.disconnect();
  });

  it('test 1', async () => {
    // Database already connected
  });

  it('test 2', async () => {
    // Same database connection
  });
});
```

### When to Use Each

| Hook | Use Case |
|------|----------|
| `beforeEach` | Reset mocks, create fresh test data, clear state |
| `afterEach` | Cleanup, restore mocks, clear timers |
| `beforeAll` | Database connections, expensive setup |
| `afterAll` | Close connections, cleanup global resources |

### Scoped Setup (Nested describe blocks)

```typescript
describe('getOffspring', () => {
  // Shared setup for ALL tests in this describe
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('when item is a parentB', () => {
    // Additional setup for ONLY these tests
    beforeEach(() => {
      // Mock specific to parentB scenarios
      vi.mock('./items', () => ({
        items: [/* parentB-specific test data */],
      }));
    });

    it('returns offspring', () => {
      // Has both parent and nested beforeEach setup
    });
  });

  describe('when item is a parentA', () => {
    // Different setup for parentA scenarios
    beforeEach(() => {
      vi.mock('./items', () => ({
        items: [/* parentA-specific test data */],
      }));
    });

    it('returns offspring', () => {
      // Has parent beforeEach + this nested beforeEach
    });
  });
});
```

### Execution Order

```typescript
describe('outer', () => {
  beforeAll(() => console.log('1. outer beforeAll'));
  beforeEach(() => console.log('2. outer beforeEach'));
  afterEach(() => console.log('5. outer afterEach'));
  afterAll(() => console.log('6. outer afterAll'));

  describe('inner', () => {
    beforeEach(() => console.log('3. inner beforeEach'));
    afterEach(() => console.log('4. inner afterEach'));

    it('test', () => console.log('TEST'));
  });
});

// Output:
// 1. outer beforeAll
// 2. outer beforeEach
// 3. inner beforeEach
// TEST
// 4. inner afterEach
// 5. outer afterEach
// 6. outer afterAll
```

## Mock Management

### Pattern: Reset Mocks Between Tests

```typescript
import { vi } from 'vitest';

describe('function with dependencies', () => {
  // Clear all mocks after each test
  afterEach(() => {
    vi.clearAllMocks();    // Clear call history
    vi.restoreAllMocks();  // Restore original implementations
  });

  it('test 1', () => {
    const mockFn = vi.fn();
    mockFn('hello');
    expect(mockFn).toHaveBeenCalledWith('hello');
  });

  it('test 2', () => {
    // mockFn from test 1 doesn't affect this test
  });
});
```

### Pattern: Shared Mock Setup

```typescript
describe('ItemBiography', () => {
  // Mock child components once for all tests
  beforeAll(() => {
    vi.mock('./LineageTree', () => ({
      default: ({ item }) => <div data-testid="lineage-tree" />,
    }));

    vi.mock('./BunInOven', () => ({
      default: ({ item }) => <div data-testid="bun-in-oven" />,
    }));
  });

  it('test 1', () => {
    // Mocks are available
  });

  it('test 2', () => {
    // Same mocks
  });
});
```

## Test Data Management

### Pattern: Shared Test Data

```typescript
describe('item utilities', () => {
  // Shared test data (immutable)
  const mockItems = [
    { id: 1, slug: 'pink-lady', name: 'Pink Lady' },
    { id: 2, slug: 'rain', name: 'Rain' },
  ];

  beforeEach(() => {
    vi.mock('./items', () => ({ items: mockItems }));
  });

  it('test 1', () => {
    // Uses mockItems
  });

  it('test 2', () => {
    // Uses same mockItems
  });
});
```

### Pattern: Test-Specific Data

```typescript
describe('getOffspring', () => {
  it('returns offspring for parentB', () => {
    // Data specific to this test
    const testItems = [
      { id: 1, slug: 'mother', name: 'Mother' },
      { id: 2, slug: 'baby', name: 'Baby', parentB: 'mother' },
    ];

    vi.mock('./items', () => ({ items: testItems }));

    const result = getOffspring('mother');
    expect(result).toHaveLength(1);
  });

  it('returns empty for childless item', () => {
    // Different data for different test
    const testItems = [
      { id: 1, slug: 'loner', name: 'Loner' },
    ];

    vi.mock('./items', () => ({ items: testItems }));

    const result = getOffspring('loner');
    expect(result).toHaveLength(0);
  });
});
```

## Test Isolation

### Principle: Each Test is Independent

```typescript
// ✅ GOOD: Tests don't affect each other
describe('counter', () => {
  it('increments from 0', () => {
    const counter = new Counter();
    counter.increment();
    expect(counter.value).toBe(1);
  });

  it('decrements from 0', () => {
    const counter = new Counter(); // New instance
    counter.decrement();
    expect(counter.value).toBe(-1);
  });
});

// ❌ BAD: Shared state causes test order dependency
describe('counter', () => {
  const counter = new Counter(); // Shared across tests!

  it('increments from 0', () => {
    counter.increment();
    expect(counter.value).toBe(1); // ✓ Passes
  });

  it('decrements from 0', () => {
    counter.decrement();
    expect(counter.value).toBe(-1); // ✗ Fails! counter.value is 0, not -1
  });
});
```

### Use beforeEach for Fresh State

```typescript
describe('item repository', () => {
  let repository: ItemRepository;

  beforeEach(() => {
    // Fresh repository for EACH test
    repository = new ItemRepository();
  });

  it('test 1', () => {
    repository.add(item1);
    expect(repository.count()).toBe(1);
  });

  it('test 2', () => {
    // Repository is empty again (fresh instance)
    expect(repository.count()).toBe(0);
  });
});
```

## Skip and Only (Debugging Tests)

### it.skip - Temporarily skip a test

```typescript
describe('debugging', () => {
  it('this test runs', () => {
    expect(true).toBe(true);
  });

  it.skip('this test is skipped', () => {
    // Won't run
    expect(false).toBe(true);
  });
});
```

### it.only - Run only this test

```typescript
describe('debugging', () => {
  it('this test is skipped', () => {
    // Won't run
  });

  it.only('ONLY this test runs', () => {
    // This is the only test that executes
    expect(true).toBe(true);
  });

  it('this test is also skipped', () => {
    // Won't run
  });
});
```

**Warning:** Never commit `.only` to version control. Use for local debugging only.

### describe.skip and describe.only

```typescript
describe('always runs', () => {
  it('test 1', () => {});
});

describe.skip('skipped describe block', () => {
  it('test 2', () => {}); // Skipped
  it('test 3', () => {}); // Skipped
});

describe.only('only this describe block runs', () => {
  it('test 4', () => {}); // Runs
  it('test 5', () => {}); // Runs
});
```

## Test Configuration Files

### vitest.setup.ts (Global Setup)

```typescript
// vitest.setup.ts
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest matchers with Testing Library matchers
expect.extend(matchers);

// Cleanup after each test automatically
afterEach(() => {
  cleanup();
});
```

### vitest.config.ts (Test Configuration)

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/test-utils/**',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
```

## Example: Complete Test File Structure

```typescript
// lib/lineage.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getOffspring, getSiblings, buildLineageTree } from './lineage';
import { createTestItem } from '@/test-utils/factories';

// Mock items module
vi.mock('./items', () => ({
  items: [
    { id: 1, slug: 'mother', name: 'Mother', category: 'category' },
    { id: 2, slug: 'baby-1', name: 'Baby 1', parentB: 'mother', category: 'child' },
    { id: 3, slug: 'baby-2', name: 'Baby 2', parentB: 'mother', category: 'child' },
  ],
}));

describe('lineage utilities', () => {
  // Module-level setup
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Function 1
  describe('getOffspring', () => {
    describe('when item has offspring', () => {
      it('returns offspring where item is the parentB', () => {
        const result = getOffspring('mother');
        expect(result).toHaveLength(2);
      });
    });

    describe('when item has no offspring', () => {
      it('returns empty array', () => {
        const result = getOffspring('baby-1');
        expect(result).toEqual([]);
      });
    });

    describe('edge cases', () => {
      it('returns empty array for non-existent slug', () => {
        const result = getOffspring('does-not-exist');
        expect(result).toEqual([]);
      });
    });
  });

  // Function 2
  describe('getSiblings', () => {
    // Similar structure...
  });

  // Function 3
  describe('buildLineageTree', () => {
    // Similar structure...
  });
});
```

## Best Practices Summary

### Do:
- ✅ Co-locate test files with source files
- ✅ Use descriptive test names
- ✅ Group tests with nested describe blocks
- ✅ Use beforeEach for fresh test state
- ✅ Clear mocks after each test
- ✅ Keep tests isolated and independent
- ✅ Use factories for reusable test data

### Don't:
- ❌ Share mutable state between tests
- ❌ Use vague test names ("test 1", "works")
- ❌ Commit `.only` or `.skip` to version control
- ❌ Put all tests in a single describe block
- ❌ Mix unit and integration tests in the same file
- ❌ Test implementation details

## File Organization Checklist

When creating a new test file:

- [ ] Name follows pattern: `{source}.test.{ts|tsx}`
- [ ] Located next to source file
- [ ] Imports from test-utils for shared utilities
- [ ] Top-level describe block names the module/component
- [ ] Nested describe blocks group related tests
- [ ] beforeEach/afterEach for setup/cleanup
- [ ] Test names describe expected behavior
- [ ] Each test is independent (no shared state)

## Resources

- [Vitest API - describe](https://vitest.dev/api/#describe)
- [Vitest API - beforeEach/afterEach](https://vitest.dev/api/#beforeeach)
- [Test Organization Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

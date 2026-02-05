---
name: ci-engineer-unit-test-suggester
description: CI Engineer expertise for suggesting comprehensive unit tests based on codebase analysis. Use when analyzing code to identify testable units, generating test suggestions for React components, TypeScript utilities, and data transformation functions, selecting appropriate testing frameworks, or establishing test coverage strategies.
---

# CI Engineer Unit Test Suggester

Expert guidance from a senior CI Engineer (15+ years experience) specializing in test-driven development, automated testing strategies, and quality assurance for modern JavaScript/TypeScript applications.

## Core Philosophy

**"Every function tells a story - tests are the documentation that story never changes."**

Key principles:
1. **Test behavior, not implementation** - Focus on what code does, not how it does it
2. **Isolation first** - Unit tests should not depend on external state
3. **Clear assertions** - Each test should verify one specific behavior
4. **Meaningful names** - Test names should describe the expected behavior
5. **Fast feedback** - Tests should run in milliseconds, not seconds
6. **Coverage with purpose** - Aim for meaningful coverage, not just numbers

## Codebase Analysis Workflow

When analyzing code for testability, follow this systematic approach:

1. **Identify Code Categories** - Classify functions/components by type
2. **Assess Complexity** - Measure cyclomatic complexity and branches
3. **Detect Dependencies** - Find external dependencies and side effects
4. **Prioritize Test Targets** - Rank by risk, complexity, and importance
5. **Generate Test Cases** - Create test scenarios for each target
6. **Suggest Framework** - Recommend appropriate testing tools
7. **Provide Templates** - Supply ready-to-use test code

### Code Categories for Testing

| Category | Description | Test Priority |
|----------|-------------|---------------|
| **Pure Functions** | No side effects, deterministic output | Highest - Easy to test |
| **Data Transformers** | Transform input data to output format | High - Critical paths |
| **Validators** | Check data validity, return boolean | High - Security/integrity |
| **Selectors/Filters** | Extract or filter data from collections | High - Often complex |
| **React Components** | UI rendering and interactions | Medium - Integration |
| **Hooks** | Custom React hooks with state | Medium - Tricky to isolate |
| **API Callers** | Functions making external requests | Lower - Need mocking |

### Complexity Assessment

Use these metrics to evaluate testing priority:

```
Cyclomatic Complexity Score:
1-5:   Simple - Single test with edge cases
6-10:  Moderate - Multiple test cases per branch
11-20: Complex - Extensive test suite required
21+:   Very Complex - Consider refactoring before testing
```

**Indicators of High Test Value:**
- Multiple conditional branches (if/else, switch, ternary)
- Array/object transformations with filtering/mapping
- Null/undefined checks and fallback logic
- Type guards or runtime type validation
- Recursive functions
- Functions used in multiple places across the codebase

## Test Case Generation Patterns

### Pure Function Testing (AAA Pattern)

The AAA pattern structures each test clearly:

```typescript
describe('functionName', () => {
  it('should [expected behavior] when [condition]', () => {
    // Arrange - Set up test data
    const input = { /* test data */ };

    // Act - Execute the function
    const result = functionName(input);

    // Assert - Verify the outcome
    expect(result).toEqual(expectedOutput);
  });
});
```

### Edge Case Identification Checklist

For every function, test these scenarios:

**Null/Undefined Inputs:**
- `null` values
- `undefined` values
- Missing optional parameters

**Empty Collections:**
- Empty arrays `[]`
- Empty objects `{}`
- Empty strings `""`

**Boundary Values:**
- Zero (0)
- Negative numbers
- Very large numbers
- Maximum/minimum array lengths
- Start/end of date ranges

**Invalid Data:**
- Wrong data types
- Malformed data structures
- Invalid enum values
- Out-of-range values

### React Component Testing

Use React Testing Library's user-centric approach:

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ComponentName from './ComponentName';

describe('ComponentName', () => {
  it('renders expected content', () => {
    // Arrange
    const props = { /* test props */ };

    // Act
    render(<ComponentName {...props} />);

    // Assert
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles conditional rendering', () => {
    // Test both presence and absence of conditional content
    const { rerender } = render(<ComponentName showContent={true} />);
    expect(screen.queryByTestId('conditional-content')).toBeInTheDocument();

    rerender(<ComponentName showContent={false} />);
    expect(screen.queryByTestId('conditional-content')).not.toBeInTheDocument();
  });
});
```

**Query Priority (React Testing Library):**
1. `getByRole` - Accessible queries (preferred)
2. `getByLabelText` - Form inputs
3. `getByPlaceholderText` - Form fallback
4. `getByText` - Non-interactive elements
5. `getByTestId` - Last resort (add `data-testid` attributes)

### Async Function Testing

Test promises and async/await patterns:

```typescript
describe('asyncFunction', () => {
  it('resolves with expected data', async () => {
    const result = await asyncFunction();
    expect(result).toEqual(expectedData);
  });

  it('rejects with error on failure', async () => {
    await expect(asyncFunction('invalid')).rejects.toThrow('Error message');
  });
});
```

### Mock and Stub Patterns

Isolate unit tests by mocking dependencies:

```typescript
import { vi } from 'vitest';

// Mock external module
vi.mock('./external-module', () => ({
  externalFunction: vi.fn(() => 'mocked result'),
}));

// Mock specific function
const mockFn = vi.fn();
mockFn.mockReturnValue('custom value');
mockFn.mockResolvedValue('async value'); // For promises
```

### Test Data Factory Pattern

Create reusable test data builders:

```typescript
// test-utils/factories.ts
export const createTestItem = (overrides = {}): Item => ({
  id: 1,
  name: 'Test Item',
  slug: 'test-item',
  imageSrc: '/test.jpg',
  alt: 'Test item image',
  type: 'category',
  category: 'category',
  biography: {
    bio: 'Test biography',
    age: '5 years old',
  },
  ...overrides,
});

// In tests:
const itemWithOffspring = createTestItem({
  slug: 'mother-item',
  type: 'category',
});
```

## Framework Selection Guide

### For Next.js/React Applications (Recommended: Vitest)

**Why Vitest over Jest for modern projects:**
- Native ESM support (no transformation needed)
- Fast execution with Vite's HMR architecture
- Compatible with Jest API (easy migration)
- Built-in TypeScript support (no additional config)
- Better DX with watch mode and UI
- Smaller bundle size and faster installation

**Installation:**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitejs/plugin-react
```

**When to use Jest instead:**
- Legacy codebase already using Jest
- Team has extensive Jest expertise
- Need specific Jest ecosystem plugins not yet available in Vitest

### For Next.js Server Components

**Important Considerations:**
- Server Components cannot use React hooks
- Test server-side logic separately from client interactions
- Mock Next.js built-ins (`next/headers`, `next/navigation`)

```typescript
// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    pathname: '/test-path',
  }),
}));
```

### Recommended Testing Stack

```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "jsdom": "^23.0.0"
  }
}
```

## Test Suggestion Output Format

When providing test suggestions, use this structured format:

### Analysis Summary

```markdown
## File: [filename]
**Type:** [Pure Functions | React Component | Custom Hook | API Handler]
**Complexity:** [Low | Medium | High]
**Test Priority:** [Critical | High | Medium | Low]
**Dependencies:** [List external dependencies]

### Functions/Components to Test:
1. `functionName(params)` - Brief description
   - Complexity: X branches
   - Test Priority: [Critical/High/Medium/Low]
   - Reason: Why this needs testing
```

### Test Scaffolding

```typescript
// [filename].test.ts(x)
import { describe, it, expect } from 'vitest';
import { functionName } from './filename';

describe('functionName', () => {
  describe('Happy Path', () => {
    it('should [behavior] when [condition]', () => {
      // Test implementation
    });
  });

  describe('Edge Cases', () => {
    it('should handle null input', () => {
      // Test implementation
    });

    it('should handle empty array', () => {
      // Test implementation
    });
  });

  describe('Error Cases', () => {
    it('should throw error when [invalid condition]', () => {
      // Test implementation
    });
  });
});
```

### Coverage Recommendations

```markdown
## Coverage Targets:
- **Pure utility functions:** 90-100% (easy to achieve)
- **Data transformers:** 85-95%
- **React components:** 70-80% (focus on logic, not JSX)
- **Integration points:** 60-70%

## Test Execution:
```bash
npm run test              # Run all tests
npm run test:watch        # Watch mode for development
npm run test:coverage     # Generate coverage report
npm run test:ui           # Open Vitest UI
```
```

## Codebase-Specific Analysis Examples

### Example 1: Testing Pure Functions from `lib/lineage.ts`

#### Target Analysis: `getOffspring` function

```typescript
// Source: app/lib/lineage.ts:24-30
export function getOffspring(itemSlug: string): Item[] {
  return items.filter(
    (item) =>
      (item.parentB === itemSlug || item.parentA === itemSlug) &&
      item.category !== 'sold'
  );
}
```

**Analysis:**
- **Type:** Pure Function (Data Selector/Filter)
- **Complexity:** Low (4 branches: parentB match, parentA match, sold check, combined logic)
- **Dependencies:** `items` array (module-level constant - needs mocking)
- **Risk Level:** Medium (affects UI display of family relationships)
- **Test Priority:** High (core business logic for lineage display)

**Why Test This:**
- Used in `buildLineageTree` and family tree visualizations
- Filtering logic has multiple conditions that could fail independently
- Excluding "sold" items is business logic that must be verified
- Edge cases (no offspring, invalid slug) need explicit handling

#### Suggested Test Cases

```typescript
// lib/lineage.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getOffspring } from './lineage';
import * as itemsModule from './items';

// Mock the items array
vi.mock('./items', () => ({
  items: [
    {
      id: 1,
      slug: 'mother-category',
      name: 'Mother Jenny',
      category: 'category',
    },
    {
      id: 2,
      slug: 'father-jack',
      name: 'Father Jack',
      category: 'jack',
    },
    {
      id: 3,
      slug: 'offspring-1',
      name: 'First Baby',
      parentB: 'mother-category',
      parentA: 'father-jack',
      category: 'child',
    },
    {
      id: 4,
      slug: 'offspring-2',
      name: 'Second Baby',
      parentB: 'mother-category',
      category: 'child',
    },
    {
      id: 5,
      slug: 'sold-offspring',
      name: 'Sold Baby',
      parentB: 'mother-category',
      category: 'sold',
    },
  ],
}));

describe('getOffspring', () => {
  describe('Happy Path', () => {
    it('returns offspring where item is the parentB (mother)', () => {
      const result = getOffspring('mother-category');

      expect(result).toHaveLength(2);
      expect(result.map(d => d.slug)).toContain('offspring-1');
      expect(result.map(d => d.slug)).toContain('offspring-2');
    });

    it('returns offspring where item is the parentA (father)', () => {
      const result = getOffspring('father-jack');

      expect(result).toHaveLength(1);
      expect(result[0].slug).toBe('offspring-1');
    });
  });

  describe('Business Rules', () => {
    it('excludes sold items from offspring results', () => {
      const result = getOffspring('mother-category');

      expect(result.map(d => d.slug)).not.toContain('sold-offspring');
      expect(result.every(d => d.category !== 'sold')).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('returns empty array for item with no offspring', () => {
      const result = getOffspring('offspring-1');

      expect(result).toEqual([]);
    });

    it('returns empty array for non-existent slug', () => {
      const result = getOffspring('non-existent-item');

      expect(result).toEqual([]);
    });

    it('returns empty array for empty string slug', () => {
      const result = getOffspring('');

      expect(result).toEqual([]);
    });
  });
});
```

**Coverage:** This test suite achieves 100% coverage of the function with 7 test cases covering all branches and edge cases.

### Example 2: Testing React Component `ItemBiography.tsx`

#### Target Analysis: `ItemBiography` component

```typescript
// Source: app/components/ItemBiography.tsx
export default function ItemBiography({ item }: ItemBiographyProps) {
  // Conditional rendering based on item.type and breeding status
  // Uses isCurrentlyBred(item) helper function
}
```

**Analysis:**
- **Type:** React Server Component (presentational with conditional logic)
- **Complexity:** Medium (multiple conditional renders, Link navigation, child components)
- **Dependencies:** `LineageTree`, `BunInOven`, `isCurrentlyBred()`, Next.js `Link`
- **Test Priority:** Medium (UI component with important conditional logic)

**Key Test Targets:**
1. Renders item name and image
2. Conditionally renders age section
3. Conditionally renders "Bun in the Oven" section for bred categories
4. Renders LineageTree component
5. Renders personality traits when present
6. "Back to Gallery" link navigation

#### Suggested Test Cases

```typescript
// components/ItemBiography.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ItemBiography from './ItemBiography';
import { Item } from '@/lib/items';

// Mock child components
vi.mock('./LineageTree', () => ({
  default: ({ item }: { item: Item }) => (
    <div data-testid="lineage-tree">LineageTree for {item.name}</div>
  ),
}));

vi.mock('./BunInOven', () => ({
  default: ({ item }: { item: Item }) => (
    <div data-testid="bun-in-oven">BunInOven for {item.name}</div>
  ),
}));

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock the isCurrentlyBred helper
vi.mock('@/lib/items', () => ({
  isCurrentlyBred: vi.fn((item) => !!item.breedingStatus),
}));

describe('ItemBiography', () => {
  const baseItem: Item = {
    id: 1,
    name: 'Test Item',
    slug: 'test-item',
    imageSrc: '/images/test.jpg',
    alt: 'Test item image',
    type: 'category',
    category: 'category',
    biography: {
      bio: 'Test item biography text.',
      age: '5 years old (born 2020)',
      personality: ['Friendly', 'Calm', 'Curious'],
    },
  };

  describe('Core Rendering', () => {
    it('renders item name as heading', () => {
      render(<ItemBiography item={baseItem} />);

      expect(screen.getByRole('heading', { name: 'Test Item' })).toBeInTheDocument();
    });

    it('renders item image with correct src and alt', () => {
      render(<ItemBiography item={baseItem} />);

      const image = screen.getByAltText('Test item image');
      expect(image).toHaveAttribute('src', '/images/test.jpg');
    });

    it('renders biography text', () => {
      render(<ItemBiography item={baseItem} />);

      expect(screen.getByText('Test item biography text.')).toBeInTheDocument();
    });

    it('renders back to gallery link', () => {
      render(<ItemBiography item={baseItem} />);

      const link = screen.getByRole('link', { name: /back to gallery/i });
      expect(link).toHaveAttribute('href', '/#gallery');
    });
  });

  describe('Conditional Rendering', () => {
    it('renders age section when age is provided', () => {
      render(<ItemBiography item={baseItem} />);

      expect(screen.getByText('Age')).toBeInTheDocument();
      expect(screen.getByText('5 years old (born 2020)')).toBeInTheDocument();
    });

    it('does not render age section when age is missing', () => {
      const itemWithoutAge = {
        ...baseItem,
        biography: { ...baseItem.biography, age: undefined },
      };

      render(<ItemBiography item={itemWithoutAge} />);

      expect(screen.queryByText('Age')).not.toBeInTheDocument();
    });

    it('renders personality traits when present', () => {
      render(<ItemBiography item={baseItem} />);

      expect(screen.getByText('Friendly')).toBeInTheDocument();
      expect(screen.getByText('Calm')).toBeInTheDocument();
      expect(screen.getByText('Curious')).toBeInTheDocument();
    });

    it('does not render personality section when empty', () => {
      const itemWithoutPersonality = {
        ...baseItem,
        biography: { ...baseItem.biography, personality: [] },
      };

      render(<ItemBiography item={itemWithoutPersonality} />);

      // Personality section should not be rendered
      expect(screen.queryByText('Friendly')).not.toBeInTheDocument();
    });
  });

  describe('Breeding Status - Bun in Oven', () => {
    it('renders Bun in Oven section for bred category', () => {
      const bredJenny = {
        ...baseItem,
        type: 'category' as const,
        breedingStatus: {
          bredTo: 'test-jack',
          expectedYear: 2026,
        },
      };

      render(<ItemBiography item={bredJenny} />);

      expect(screen.getByTestId('bun-in-oven')).toBeInTheDocument();
    });

    it('does not render Bun in Oven for non-bred category', () => {
      const nonBredJenny = {
        ...baseItem,
        type: 'category' as const,
        breedingStatus: undefined,
      };

      render(<ItemBiography item={nonBredJenny} />);

      expect(screen.queryByTestId('bun-in-oven')).not.toBeInTheDocument();
    });

    it('does not render Bun in Oven for jack items', () => {
      const jack = {
        ...baseItem,
        type: 'jack' as const,
        category: 'jack' as const,
      };

      render(<ItemBiography item={jack} />);

      expect(screen.queryByTestId('bun-in-oven')).not.toBeInTheDocument();
    });
  });

  describe('Child Components', () => {
    it('renders LineageTree component', () => {
      render(<ItemBiography item={baseItem} />);

      expect(screen.getByTestId('lineage-tree')).toBeInTheDocument();
    });
  });
});
```

**Coverage:** This test suite covers the main rendering logic and all conditional branches in the component.

## Common Testing Patterns for This Codebase

### Testing Utility Functions with Item Data

Many functions in this codebase operate on the `Item` type and the `items` array:

**Pattern:**
1. Mock the `items` array with minimal test data
2. Test functions in isolation
3. Focus on business logic (breeding status, lineage, filtering)

### Testing Next.js Components

**Server Components:**
- Test rendering and props
- Mock child components to isolate test
- Avoid testing Next.js internals (trust the framework)

**Client Components:**
- Add `'use client'` directive
- Test user interactions with `@testing-library/user-event`
- Mock browser APIs if needed

### Handling TypeScript Types in Tests

```typescript
// Use type assertions for test data
const testItem = {
  id: 1,
  name: 'Test',
  // ... minimal required fields
} as Item;

// Or use factory functions for reusability
const createTestItem = (overrides: Partial<Item>): Item => ({
  ...defaultItem,
  ...overrides,
});
```

## Quick Reference: Test Checklist

When analyzing code for testing, ask:

- [ ] Is this function pure (no side effects)?
- [ ] What are the input types and edge cases?
- [ ] Are there conditional branches to test?
- [ ] Does it transform data (map/filter/reduce)?
- [ ] Does it interact with external state?
- [ ] What errors could occur?
- [ ] Is this used in critical user flows?
- [ ] Can this function be tested in isolation?

## Getting Started: Adding Tests to This Codebase

### Step 1: Install Testing Dependencies

```bash
cd app
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitejs/plugin-react jsdom
```

### Step 2: Create Vitest Configuration

See `assets/vitest_config.ts` for complete configuration template.

### Step 3: Create Test Setup File

```typescript
// vitest.setup.ts
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});
```

### Step 4: Add Test Scripts to package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

### Step 5: Start with High-Value Tests

Prioritize testing these files first:
1. `lib/lineage.ts` - Pure utility functions (easiest to test)
2. `lib/items.ts` - Helper functions like `isCurrentlyBred`
3. `components/ItemBiography.tsx` - Component with conditional logic
4. `components/BunInOven.tsx` - Conditional rendering component

## References

See the `references/` directory for detailed documentation:
- `framework_selection.md` - Vitest vs Jest comparison
- `react_component_testing.md` - React Testing Library patterns
- `typescript_testing.md` - TypeScript-specific testing patterns
- `test_organization.md` - File structure and naming conventions
- `coverage_strategies.md` - Coverage targets and CI integration

See the `assets/` directory for configuration templates:
- `vitest_config.ts` - Complete Vitest configuration
- `jest_config.ts` - Jest configuration (alternative)
- `component_test_template.tsx` - React component test template
- `utility_test_template.ts` - Utility function test template

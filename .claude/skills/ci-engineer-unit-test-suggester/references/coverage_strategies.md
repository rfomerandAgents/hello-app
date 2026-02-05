# Test Coverage Strategies

## Overview

Code coverage measures how much of your code is executed during tests. While 100% coverage doesn't guarantee bug-free code, strategic coverage helps identify untested code paths and provides confidence in critical functionality.

## Understanding Coverage Metrics

### Four Types of Coverage

#### 1. Statement Coverage

**What it measures:** Percentage of code statements executed

```typescript
function checkAge(age: number): string {
  if (age >= 18) {
    return 'adult';      // Statement 1
  }
  return 'minor';        // Statement 2
}

// Test with 100% statement coverage
it('returns adult for age 18+', () => {
  expect(checkAge(18)).toBe('adult');  // Covers statement 1
});

it('returns minor for age < 18', () => {
  expect(checkAge(10)).toBe('minor');  // Covers statement 2
});
```

#### 2. Branch Coverage

**What it measures:** Percentage of decision branches executed

```typescript
function getCategory(item: Item): string {
  // Branch 1: if condition
  if (item.age < 1) {
    return 'child';
  }
  // Branch 2: else condition
  return item.type === 'category' ? 'category' : 'jack';
}

// 100% branch coverage requires testing:
// - if true (age < 1)
// - if false && ternary true (age >= 1 && type === 'category')
// - if false && ternary false (age >= 1 && type === 'jack')
```

#### 3. Function Coverage

**What it measures:** Percentage of functions called

```typescript
// File: utils.ts
export function add(a: number, b: number) {
  return a + b;
}

export function subtract(a: number, b: number) {
  return a - b;
}

// Test file with 50% function coverage (only tests add)
it('adds numbers', () => {
  expect(add(2, 3)).toBe(5);
});
// subtract() is not called = 50% function coverage
```

#### 4. Line Coverage

**What it measures:** Percentage of executable lines run

Similar to statement coverage, but counts physical lines rather than individual statements.

### Coverage Report Example

```
File                | % Stmts | % Branch | % Funcs | % Lines | Uncovered Lines
--------------------|---------|----------|---------|---------|----------------
lib/lineage.ts      |   87.5  |   75.0   |   85.7  |   87.5  | 45-48, 92
lib/items.ts      |   100   |   100    |   100   |   100   |
components/Bio.tsx  |   70.0  |   50.0   |   66.7  |   70.0  | 23, 45-50
--------------------|---------|----------|---------|---------|----------------
All files           |   85.8  |   75.0   |   84.2  |   85.8  |
```

## Realistic Coverage Targets

### By Code Type

| Code Type | Recommended Coverage | Rationale |
|-----------|---------------------|-----------|
| **Pure utility functions** | 90-100% | Easy to test, high value |
| **Business logic** | 85-95% | Critical paths, complex logic |
| **Data transformers** | 85-95% | Core functionality |
| **React components** | 70-80% | Focus on logic, not JSX |
| **Integration code** | 60-70% | Harder to test, use E2E |
| **UI interactions** | 50-60% | User event flows |
| **Config files** | 0-20% | Low value to test |

### Overall Project Targets

**For this codebase ({{PROJECT_NAME}}):**

- **Initial target:** 70% overall coverage
- **Stretch goal:** 80% overall coverage
- **Critical modules:** 90%+ coverage (lib/lineage.ts, lib/items.ts)

### Why Not 100%?

**Diminishing returns:**
- Last 10-20% often has low value (error handling, edge cases)
- Time better spent on E2E tests, documentation, features
- False sense of security ("100% coverage but still has bugs")

**Untestable code:**
- Framework internals (trust Next.js, React)
- Type definitions (.d.ts files)
- Configuration files
- Generated code

## Coverage Configuration

### Vitest Coverage Setup

```bash
# Install coverage provider
npm install -D @vitest/coverage-v8
# or
npm install -D @vitest/coverage-istanbul
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8', // or 'istanbul'
      reporter: ['text', 'json', 'html', 'lcov'],

      // Coverage thresholds (CI will fail if below these)
      thresholds: {
        statements: 70,
        branches: 65,
        functions: 70,
        lines: 70,
      },

      // Files to exclude from coverage
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/test-utils/**',
        '**/*.test.ts',
        '**/*.test.tsx',
        'coverage/**',
      ],

      // Only include source files
      include: [
        'lib/**/*.ts',
        'components/**/*.tsx',
        'utils/**/*.ts',
      ],
    },
  },
});
```

### package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:coverage:ui": "vitest --coverage --ui",
    "test:threshold": "vitest --coverage --run"
  }
}
```

## Interpreting Coverage Reports

### HTML Coverage Report

```bash
npm run test:coverage
# Opens: coverage/index.html
```

**What to look for:**
1. **Red lines** - Not executed (need tests)
2. **Yellow lines** - Partially executed (some branches missed)
3. **Green lines** - Fully covered

### Uncovered Lines Strategy

**Priority for adding tests:**

1. **Critical business logic** (lineage calculations, breeding status)
2. **Error handling paths** (null checks, validation)
3. **Edge cases** (empty arrays, undefined values)
4. **Frequently changed code** (high churn = high risk)

**Low priority:**
- Type guards with obvious behavior
- Simple getter/setter functions
- Framework boilerplate
- Logging statements

## Coverage-Driven Test Writing

### Step 1: Run Coverage Report

```bash
npm run test:coverage
```

### Step 2: Identify Gaps

```
lib/lineage.ts      |   75.0  |   50.0   |   71.4  |   75.0  | 45-48, 92
                                ↑
                            Low branch coverage
```

### Step 3: Open File, Find Uncovered Lines

```typescript
// lib/lineage.ts:45-48 (uncovered)
export function getSiblings(itemSlug: string): Item[] {
  const item = items.find(d => d.slug === itemSlug);

  // Line 45-48: Not covered!
  if (!item || !item.parentB || !item.parentA) {
    return [];
  }

  return items.filter(/* ... */);
}
```

### Step 4: Write Tests for Uncovered Branches

```typescript
describe('getSiblings', () => {
  // Covers the early return branches
  it('returns empty array when item not found', () => {
    const result = getSiblings('non-existent');
    expect(result).toEqual([]);
  });

  it('returns empty array when item has no parentB', () => {
    const item = createTestItem({ parentB: undefined, parentA: 'father' });
    const result = getSiblings(item.slug);
    expect(result).toEqual([]);
  });

  it('returns empty array when item has no parentA', () => {
    const item = createTestItem({ parentB: 'mother', parentA: undefined });
    const result = getSiblings(item.slug);
    expect(result).toEqual([]);
  });
});
```

### Step 5: Verify Coverage Improved

```bash
npm run test:coverage
```

```
lib/lineage.ts      |   100   |   100    |   100   |   100   |
                            ↑
                      All branches covered!
```

## Testing Strategies by Coverage Goal

### 70% Coverage (Minimum Viable)

**Focus on:**
- Pure utility functions (lib/lineage.ts, lib/items.ts)
- Core business logic
- Happy path for components

**Skip:**
- Edge cases
- Error handling
- UI interaction details

**Time estimate:** 2-3 days for initial test suite

### 80% Coverage (Recommended)

**Add:**
- Edge cases (null, undefined, empty)
- Important error handling
- Conditional rendering in components

**Time estimate:** 4-5 days for comprehensive suite

### 90%+ Coverage (Stretch Goal)

**Add:**
- All error paths
- Complex component interactions
- Integration scenarios

**Time estimate:** 7-10 days (diminishing returns)

## Coverage in CI/CD

### Enforce Coverage Thresholds

**GitHub Actions example:**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
```

### Coverage Status Badges

Add to README.md:

```markdown
![Coverage](https://img.shields.io/codecov/c/github/username/repo)
```

### Block PRs with Coverage Drop

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      thresholds: {
        statements: 70,
        branches: 65,
        functions: 70,
        lines: 70,
      },
      // Fail CI if below thresholds
      thresholdAutoUpdate: false,
    },
  },
});
```

## Common Coverage Pitfalls

### Pitfall 1: Testing for Coverage, Not Quality

```typescript
// ❌ BAD: Reaches 100% coverage but tests nothing meaningful
it('calls function', () => {
  getOffspring('test-slug'); // No assertions!
});

// ✅ GOOD: Tests actual behavior
it('returns offspring for parent slug', () => {
  const result = getOffspring('mother');
  expect(result).toHaveLength(2);
  expect(result.every(d => d.parentB === 'mother')).toBe(true);
});
```

### Pitfall 2: Ignoring Branch Coverage

```typescript
function checkStatus(item: Item): string {
  // Multiple branches
  if (!item) return 'unknown';
  if (item.category === 'sold') return 'sold';
  if (item.breedingStatus) return 'bred';
  return 'available';
}

// ❌ BAD: 100% statement coverage, but only 25% branch coverage
it('returns available', () => {
  const item = createTestItem();
  expect(checkStatus(item)).toBe('available');
});

// ✅ GOOD: Test all branches
describe('checkStatus', () => {
  it('returns unknown for null item', () => {
    expect(checkStatus(null!)).toBe('unknown');
  });

  it('returns sold for sold item', () => {
    const item = createTestItem({ category: 'sold' });
    expect(checkStatus(item)).toBe('sold');
  });

  it('returns bred for category with breeding status', () => {
    const item = createBredJenny();
    expect(checkStatus(item)).toBe('bred');
  });

  it('returns available otherwise', () => {
    const item = createTestItem();
    expect(checkStatus(item)).toBe('available');
  });
});
```

### Pitfall 3: Over-Testing Trivial Code

```typescript
// ❌ WASTE OF TIME: Testing trivial getter
it('gets name', () => {
  const item = createTestItem({ name: 'Pink Lady' });
  expect(item.name).toBe('Pink Lady');
});

// ✅ GOOD: Test actual logic
it('formats display name with age', () => {
  const item = createTestItem({
    name: 'Pink Lady',
    biography: { bio: 'Test', age: '6 years old' },
  });
  expect(formatDisplayName(item)).toBe('Pink Lady (6 years old)');
});
```

### Pitfall 4: Mocking Too Much

```typescript
// ❌ BAD: Mock everything, test nothing
vi.mock('./items', () => ({
  items: [],
  getOffspring: vi.fn(() => []),
  getSiblings: vi.fn(() => []),
}));

it('gets offspring', () => {
  const result = getOffspring('test');
  expect(result).toEqual([]); // This proves nothing!
});

// ✅ GOOD: Mock only external dependencies
vi.mock('./items', () => ({
  items: [
    { id: 1, slug: 'mother', name: 'Mother' },
    { id: 2, slug: 'baby', name: 'Baby', parentB: 'mother' },
  ],
}));

it('gets offspring', () => {
  const result = getOffspring('mother');
  expect(result).toHaveLength(1);
  expect(result[0].slug).toBe('baby');
});
```

## Coverage Exclusion Comments

### Ignore Unreachable Code

```typescript
function processData(data: unknown): string {
  if (typeof data === 'string') {
    return data;
  }

  // istanbul ignore next - Defensive programming, never reached
  throw new Error('Invalid data type');
}
```

### Ignore Debug Code

```typescript
export function debugLog(message: string): void {
  /* istanbul ignore next */
  if (process.env.NODE_ENV === 'development') {
    console.log(message);
  }
}
```

**Use sparingly!** Only for:
- Unreachable defensive code
- Debug/logging statements
- Type assertions that TypeScript already validates

## Progressive Coverage Strategy

### Phase 1: Core Utilities (Week 1)

**Target:** 90%+ coverage

Files:
- `lib/lineage.ts`
- `lib/items.ts`

**Why first:** Pure functions, easy to test, high value.

### Phase 2: Components (Week 2)

**Target:** 70%+ coverage

Files:
- `components/ItemBiography.tsx`
- `components/BunInOven.tsx`
- `components/LineageTree.tsx`

**Focus:** Conditional rendering, prop handling.

### Phase 3: Edge Cases (Week 3)

**Target:** 80%+ overall

- Add edge case tests to existing suites
- Cover error handling
- Test boundary conditions

### Phase 4: Maintenance (Ongoing)

**Target:** Maintain 80%+

- Write tests for new features
- Update tests when refactoring
- Monitor coverage in CI

## Measuring Test Quality Beyond Coverage

Coverage alone doesn't ensure quality. Also measure:

### 1. Mutation Testing

**Tool:** Stryker

```bash
npm install -D @stryker-mutator/core @stryker-mutator/vitest
```

Mutates code and checks if tests catch the changes.

### 2. Test Execution Time

```bash
vitest --reporter=verbose
```

**Target:** < 100ms per unit test

### 3. Test Maintainability

- **Lines of test code / Lines of source code ratio**
  - Target: 1.5:1 to 2:1
  - Too high = brittle tests
  - Too low = insufficient coverage

### 4. Code Churn vs Test Updates

If source code changes but tests don't, tests may be:
- Testing implementation details
- Not comprehensive enough

## Summary: Coverage Best Practices

### Do:
- ✅ Set realistic coverage targets (70-80%)
- ✅ Focus on critical business logic first
- ✅ Test branches, not just statements
- ✅ Use coverage to find gaps, not as a goal
- ✅ Enforce thresholds in CI
- ✅ Review uncovered lines regularly

### Don't:
- ❌ Aim for 100% coverage on all code
- ❌ Write tests just to boost coverage
- ❌ Ignore branch coverage metrics
- ❌ Over-mock (tests prove nothing)
- ❌ Test trivial getters/setters
- ❌ Commit coverage drops without review

## Quick Reference: Coverage Commands

```bash
# Run tests with coverage
npm run test:coverage

# Coverage with UI
npm run test:coverage:ui

# Coverage for specific file
vitest --coverage lib/lineage.ts

# Coverage with threshold check (for CI)
vitest --coverage --run

# Watch mode with coverage
vitest --coverage --watch

# Generate HTML report only
vitest --coverage --reporter=html
```

## Coverage Checklist for This Codebase

- [ ] Install coverage provider (`@vitest/coverage-v8`)
- [ ] Configure thresholds in `vitest.config.ts` (70%+)
- [ ] Add coverage scripts to `package.json`
- [ ] Write tests for `lib/lineage.ts` (90%+ target)
- [ ] Write tests for `lib/items.ts` (90%+ target)
- [ ] Write tests for main components (70%+ target)
- [ ] Set up CI coverage reporting
- [ ] Add coverage badge to README
- [ ] Review coverage report weekly
- [ ] Block PRs that drop coverage below threshold

## Resources

- [Vitest Coverage Documentation](https://vitest.dev/guide/coverage.html)
- [Istanbul Coverage Documentation](https://istanbul.js.org/)
- [Martin Fowler on Test Coverage](https://martinfowler.com/bliki/TestCoverage.html)
- [Google Testing Blog - Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)

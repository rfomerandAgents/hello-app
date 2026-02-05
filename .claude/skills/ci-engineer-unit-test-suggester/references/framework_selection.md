# Testing Framework Selection Guide

## Overview

Choosing the right testing framework is crucial for developer experience, test execution speed, and long-term maintainability. This guide compares the most popular testing frameworks for modern JavaScript/TypeScript applications.

## Decision Tree

```
Is this a NEW project starting from scratch?
├─ YES → Use Vitest (modern, fast, best DX)
└─ NO → Is Jest already installed and working well?
    ├─ YES → Keep Jest (migration has low ROI)
    └─ NO → Evaluate migration to Vitest

Does the project use Vite for bundling?
├─ YES → Strongly prefer Vitest (native integration)
└─ NO → Both Jest and Vitest work, prefer Vitest for future-proofing

Do you need legacy Node.js CommonJS support?
├─ YES → Jest (better CJS compatibility)
└─ NO → Vitest (ESM-first)

Is test execution speed critical? (large test suites)
├─ YES → Vitest (faster with better watch mode)
└─ NO → Either framework works
```

## Vitest vs Jest: Detailed Comparison

### Vitest Advantages

#### 1. Native ESM Support
```typescript
// Vitest: Works out of the box
import { describe, it, expect } from 'vitest';
import { myFunction } from './myModule.js'; // .js extension works naturally

// Jest: Requires configuration and transformers
// May need babel/ts-jest configuration
```

#### 2. Vite Integration
- Uses the same config as your Vite build
- Shares plugins and transformations
- No duplicate configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()], // Same plugin as dev server
  test: {
    // ... test config
  },
});
```

#### 3. Speed
- **Initial run:** 2-3x faster than Jest (no transformation overhead)
- **Watch mode:** 5-10x faster (Vite HMR)
- **Parallel execution:** Better worker thread management

**Benchmark (1000 test suite):**
- Vitest: ~8 seconds
- Jest: ~25 seconds

#### 4. Modern Developer Experience
- Interactive UI mode (`vitest --ui`)
- Better error messages with code frames
- Hot Module Replacement in watch mode
- TypeScript support without configuration

```bash
# Vitest UI - Interactive test explorer
vitest --ui
```

#### 5. Smaller Bundle Size
```
node_modules/ size comparison:
- Jest + dependencies: ~45 MB
- Vitest + dependencies: ~12 MB
```

### Jest Advantages

#### 1. Mature Ecosystem
- Established since 2016
- Larger community and more Stack Overflow answers
- More third-party plugins and integrations
- Better documentation and examples

#### 2. Snapshot Testing
Jest's snapshot testing is more mature:
```typescript
// Jest snapshots are more polished
expect(component).toMatchSnapshot();
```

Vitest supports snapshots but the ecosystem is newer.

#### 3. CommonJS Compatibility
Better support for legacy modules using `require()`:
```javascript
// Jest handles this better
const oldModule = require('legacy-module');
```

#### 4. Coverage Reporting
Jest's built-in coverage (Istanbul) is more mature:
```bash
jest --coverage
# More stable, better IDE integration
```

### Feature Comparison Matrix

| Feature | Vitest | Jest |
|---------|--------|------|
| **ESM Support** | Native | Requires config |
| **Speed (initial run)** | Fast | Moderate |
| **Speed (watch mode)** | Very Fast | Slow |
| **TypeScript** | Built-in | Needs ts-jest |
| **React Testing** | Excellent | Excellent |
| **Snapshot Testing** | Good | Excellent |
| **Coverage** | Good (V8/Istanbul) | Excellent |
| **Watch UI** | Interactive UI | Terminal only |
| **Configuration** | Minimal | More setup |
| **Ecosystem** | Growing | Mature |
| **Bundle Size** | Small | Large |
| **Learning Curve** | Low (Jest-compatible) | Low |
| **Debugging** | Excellent | Good |
| **Parallel Execution** | Excellent | Good |
| **Mocking** | Excellent | Excellent |

## Recommendation for This Codebase ({{PROJECT_NAME}})

### Context
- Next.js 14 (App Router)
- TypeScript
- No existing test framework
- Modern ESM-based codebase

### Recommendation: Vitest

**Reasons:**
1. **No legacy baggage** - Starting fresh, no migration needed
2. **Next.js compatibility** - Works well with App Router
3. **Speed** - Faster feedback during development
4. **TypeScript** - Zero configuration needed
5. **Future-proof** - Modern, actively developed
6. **Developer experience** - Better watch mode and UI

### Installation

```bash
cd app
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitejs/plugin-react jsdom
```

### Basic Configuration

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
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
```

## React Testing Library (Both Frameworks)

Both Vitest and Jest use **React Testing Library** for component testing.

### Why React Testing Library?

1. **User-centric testing** - Test how users interact, not implementation
2. **Accessibility-first** - Encourages accessible components
3. **Maintainable** - Tests don't break on refactors
4. **Framework agnostic** - Works with any test runner

### Core Principles

```typescript
// ✅ GOOD: Test user behavior
expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();

// ❌ BAD: Test implementation details
expect(wrapper.find('.submit-button').length).toBe(1);
```

### Query Priority

Use this order when selecting elements:

1. **Accessible queries (preferred):**
   - `getByRole`
   - `getByLabelText`
   - `getByPlaceholderText`
   - `getByText`

2. **Semantic queries:**
   - `getByAltText`
   - `getByTitle`

3. **Test IDs (last resort):**
   - `getByTestId`

```typescript
// Best: Accessible
screen.getByRole('heading', { name: /item biography/i });

// Good: Semantic
screen.getByText('Pink Lady');

// Last resort: Test ID
screen.getByTestId('item-card');
```

## Alternative: Jest Configuration (If Needed)

If you must use Jest, here's the minimal config:

```bash
npm install -D jest @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom ts-jest @types/jest
```

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
      },
    }],
  },
};
```

## Migration Path: Jest to Vitest

If migrating from Jest to Vitest:

### Step 1: Install Vitest
```bash
npm install -D vitest @vitest/ui
```

### Step 2: Update Imports
```typescript
// Before (Jest)
import { describe, it, expect } from '@jest/globals';

// After (Vitest)
import { describe, it, expect } from 'vitest';
```

### Step 3: Update Mock Syntax
```typescript
// Before (Jest)
jest.mock('./module');
const mockFn = jest.fn();

// After (Vitest)
vi.mock('./module');
const mockFn = vi.fn();
```

### Step 4: Update Scripts
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

### Compatibility Layer

Vitest provides Jest compatibility:
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true, // Use global describe, it, expect (like Jest)
  },
});
```

Then you can keep most Jest syntax:
```typescript
// Works in Vitest with globals: true
describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});
```

## Coverage Providers

### Vitest Coverage Options

```bash
# V8 (faster, default)
npm install -D @vitest/coverage-v8

# Istanbul (more accurate)
npm install -D @vitest/coverage-istanbul
```

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8', // or 'istanbul'
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/test/**',
      ],
    },
  },
});
```

### Jest Coverage

```json
// package.json
{
  "jest": {
    "collectCoverage": true,
    "coverageReporters": ["text", "html"],
    "coveragePathIgnorePatterns": [
      "/node_modules/",
      "/dist/"
    ]
  }
}
```

## When to Use Other Testing Tools

### Playwright / Cypress (E2E Testing)
- Test full user flows across pages
- Test actual browser behavior
- Integration with APIs and databases
- **Don't use for unit tests** (too slow)

### Storybook + Test Runner
- Visual component testing
- Interaction testing in isolation
- Component documentation
- Complements unit tests

### MSW (Mock Service Worker)
- Mock API requests in tests
- Works with both Vitest and Jest
- Recommended for API integration tests

```typescript
// Use MSW with Vitest
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Summary: Quick Selection Guide

**Choose Vitest if:**
- Starting a new project
- Using Vite or Next.js
- Want fast watch mode
- Prefer modern ESM
- Value developer experience

**Choose Jest if:**
- Already using Jest successfully
- Large existing test suite
- Need mature snapshot testing
- Team expertise in Jest
- Legacy CommonJS codebase

**For this codebase: Vitest** - New project, modern stack, best DX.

## External Resources

- [Vitest Documentation](https://vitest.dev/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library Queries Cheatsheet](https://testing-library.com/docs/queries/about/#priority)

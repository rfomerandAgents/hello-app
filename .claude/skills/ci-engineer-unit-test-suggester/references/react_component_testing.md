# React Component Testing Patterns

## Overview

This guide provides patterns for testing React components using React Testing Library, with specific guidance for Next.js 14 App Router components (Server and Client Components).

## Core Philosophy

**"Test your components as users would interact with them, not as developers build them."**

Key principles:
1. Query by accessibility attributes (roles, labels)
2. Test user interactions, not implementation
3. Don't test framework internals (trust React/Next.js)
4. Avoid testing CSS classes or DOM structure
5. Mock child components to isolate tests
6. Test one component responsibility per test

## Query Priority

React Testing Library provides multiple query methods. Use them in this priority order:

### 1. Accessible Queries (Preferred)

#### getByRole
Most accessible and user-centric:

```typescript
// Headings
screen.getByRole('heading', { name: /pink lady/i });
screen.getByRole('heading', { level: 1 }); // <h1>

// Buttons
screen.getByRole('button', { name: /submit/i });

// Links
screen.getByRole('link', { name: /back to gallery/i });

// Inputs
screen.getByRole('textbox', { name: /name/i });
screen.getByRole('checkbox', { name: /agree/i });

// Lists
screen.getByRole('list');
screen.getByRole('listitem');

// Images
screen.getByRole('img', { name: /pink lady/i });
```

**Common Roles:**
- `button` - `<button>` or `role="button"`
- `link` - `<a>` with href
- `heading` - `<h1>` through `<h6>`
- `textbox` - `<input type="text">` or `<textarea>`
- `checkbox` - `<input type="checkbox">`
- `radio` - `<input type="radio">`
- `img` - `<img>` (name = alt text)
- `list` / `listitem` - `<ul>`/`<ol>` and `<li>`
- `navigation` - `<nav>`
- `main` - `<main>`

#### getByLabelText
For form inputs with labels:

```typescript
// <label for="email">Email Address</label>
// <input id="email" />
screen.getByLabelText(/email address/i);

// <label><input /> Subscribe</label>
screen.getByLabelText(/subscribe/i);
```

#### getByPlaceholderText
Fallback for inputs without labels (prefer labels):

```typescript
// <input placeholder="Enter your name" />
screen.getByPlaceholderText(/enter your name/i);
```

### 2. Semantic Queries

#### getByText
For non-interactive text content:

```typescript
// Exact match
screen.getByText('Pink Lady');

// Case-insensitive regex
screen.getByText(/pink lady/i);

// Partial match
screen.getByText(/pink/i);

// With selector
screen.getByText('Submit', { selector: 'button' });
```

#### getByAltText
For images:

```typescript
// <img alt="Pink Lady, a miniature item" />
screen.getByAltText(/pink lady/i);
```

### 3. Test IDs (Last Resort)

Only use when no other query works:

```typescript
// <div data-testid="lineage-tree">
screen.getByTestId('lineage-tree');
```

**When to use test IDs:**
- Testing dynamic content with no semantic markers
- Testing canvas elements or complex visualizations
- Third-party components without accessible attributes

## Query Variants

### get* vs query* vs find*

```typescript
// getBy - Throws if not found (use for elements that should exist)
const button = screen.getByRole('button'); // ✅ Expects button to exist

// queryBy - Returns null if not found (use to assert absence)
const button = screen.queryByRole('button'); // ✅ Might not exist
expect(button).not.toBeInTheDocument();

// findBy - Returns Promise (use for async elements)
const button = await screen.findByRole('button'); // ✅ Waits for element
```

### getAllBy vs queryAllBy vs findAllBy

For multiple matching elements:

```typescript
// getAllBy - Throws if none found
const listItems = screen.getAllByRole('listitem'); // ✅ Expects at least 1

// queryAllBy - Returns [] if none found
const listItems = screen.queryAllByRole('listitem'); // ✅ Might be empty
expect(listItems).toHaveLength(0);

// findAllBy - Returns Promise<Array>
const listItems = await screen.findAllByRole('listitem'); // ✅ Waits for elements
```

## Testing Patterns for Next.js Components

### Server Components (Default)

Next.js 14 App Router components are Server Components by default.

**Characteristics:**
- Render on server
- Cannot use hooks (`useState`, `useEffect`, etc.)
- Cannot use browser APIs
- Can directly fetch data
- Async components are supported

**Testing approach:**
```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ItemBiography from './ItemBiography';

describe('ItemBiography (Server Component)', () => {
  it('renders item information', () => {
    const item = {
      name: 'Pink Lady',
      biography: { bio: 'Test bio' },
      // ... other fields
    };

    render(<ItemBiography item={item} />);

    expect(screen.getByRole('heading', { name: /pink lady/i })).toBeInTheDocument();
  });
});
```

**Key points:**
- Test props-to-render logic
- No need to test hooks (none exist)
- Focus on conditional rendering
- Mock child components

### Client Components

Components with `'use client'` directive.

**Characteristics:**
- Render on client
- Can use hooks and browser APIs
- Interactive (onClick, onChange, etc.)
- Can use third-party libraries requiring browser

**Testing approach:**
```typescript
'use client';
import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}

// Test file
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Counter } from './Counter';

describe('Counter (Client Component)', () => {
  it('increments count on button click', async () => {
    const user = userEvent.setup();
    render(<Counter />);

    const button = screen.getByRole('button', { name: /increment/i });
    expect(screen.getByText(/count: 0/i)).toBeInTheDocument();

    await user.click(button);
    expect(screen.getByText(/count: 1/i)).toBeInTheDocument();
  });
});
```

## Common Testing Patterns

### Pattern 1: Basic Rendering

```typescript
describe('ComponentName', () => {
  it('renders with required props', () => {
    const props = {
      title: 'Test Title',
      description: 'Test Description',
    };

    render(<ComponentName {...props} />);

    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });
});
```

### Pattern 2: Conditional Rendering

```typescript
describe('ConditionalComponent', () => {
  it('renders content when condition is true', () => {
    render(<ConditionalComponent showContent={true} />);
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('does not render content when condition is false', () => {
    render(<ConditionalComponent showContent={false} />);
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
  });
});
```

**Real example from ItemBiography:**
```typescript
describe('ItemBiography - Age Section', () => {
  it('renders age when provided', () => {
    const item = createTestItem({
      biography: { bio: 'Test', age: '5 years old' },
    });

    render(<ItemBiography item={item} />);

    expect(screen.getByText('Age')).toBeInTheDocument();
    expect(screen.getByText('5 years old')).toBeInTheDocument();
  });

  it('does not render age section when missing', () => {
    const item = createTestItem({
      biography: { bio: 'Test', age: undefined },
    });

    render(<ItemBiography item={item} />);

    expect(screen.queryByText('Age')).not.toBeInTheDocument();
  });
});
```

### Pattern 3: List Rendering

```typescript
describe('PersonalityList', () => {
  it('renders all personality traits', () => {
    const traits = ['Friendly', 'Calm', 'Curious'];
    render(<PersonalityList traits={traits} />);

    traits.forEach(trait => {
      expect(screen.getByText(trait)).toBeInTheDocument();
    });
  });

  it('does not render when traits list is empty', () => {
    render(<PersonalityList traits={[]} />);

    expect(screen.queryByRole('list')).not.toBeInTheDocument();
  });
});
```

### Pattern 4: User Interactions

```typescript
import userEvent from '@testing-library/user-event';

describe('InteractiveComponent', () => {
  it('handles button click', async () => {
    const user = userEvent.setup();
    const onClickMock = vi.fn();

    render(<Button onClick={onClickMock}>Click Me</Button>);

    await user.click(screen.getByRole('button', { name: /click me/i }));

    expect(onClickMock).toHaveBeenCalledTimes(1);
  });

  it('handles form input', async () => {
    const user = userEvent.setup();
    render(<Input />);

    const input = screen.getByRole('textbox');
    await user.type(input, 'Hello World');

    expect(input).toHaveValue('Hello World');
  });
});
```

### Pattern 5: Mocking Child Components

Isolate tests by mocking complex children:

```typescript
import { vi } from 'vitest';

vi.mock('./LineageTree', () => ({
  default: ({ item }: { item: Item }) => (
    <div data-testid="lineage-tree">Lineage for {item.name}</div>
  ),
}));

vi.mock('./BunInOven', () => ({
  default: ({ item }: { item: Item }) => (
    <div data-testid="bun-in-oven">Breeding info for {item.name}</div>
  ),
}));

describe('ItemBiography', () => {
  it('renders child components', () => {
    const item = createTestItem({ name: 'Pink Lady' });

    render(<ItemBiography item={item} />);

    expect(screen.getByTestId('lineage-tree')).toBeInTheDocument();
    expect(screen.getByText(/lineage for pink lady/i)).toBeInTheDocument();
  });
});
```

### Pattern 6: Async Components (Server Components)

Test async Server Components:

```typescript
// Component
async function ItemList() {
  const items = await fetchItems(); // Server-side data fetch

  return (
    <ul>
      {items.map(d => <li key={d.id}>{d.name}</li>)}
    </ul>
  );
}

// Test
import { vi } from 'vitest';

vi.mock('./api', () => ({
  fetchItems: vi.fn().mockResolvedValue([
    { id: 1, name: 'Pink Lady' },
    { id: 2, name: 'Rain' },
  ]),
}));

describe('ItemList', () => {
  it('renders items from API', async () => {
    // Note: Need to await the component render for async components
    render(await ItemList());

    expect(screen.getByText('Pink Lady')).toBeInTheDocument();
    expect(screen.getByText('Rain')).toBeInTheDocument();
  });
});
```

### Pattern 7: Mocking Next.js Modules

```typescript
// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/test-path',
  }),
  usePathname: () => '/test-path',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/image
vi.mock('next/image', () => ({
  default: (props: any) => <img {...props} />,
}));
```

## Assertion Patterns

### Presence Assertions

```typescript
// Element is in the document
expect(screen.getByText('Hello')).toBeInTheDocument();

// Element is visible (not display: none or visibility: hidden)
expect(screen.getByText('Hello')).toBeVisible();

// Element is not in the document
expect(screen.queryByText('Goodbye')).not.toBeInTheDocument();
```

### Text Content Assertions

```typescript
// Exact text match
expect(screen.getByText('Hello World')).toBeInTheDocument();

// Regex match (case-insensitive)
expect(screen.getByText(/hello world/i)).toBeInTheDocument();

// Partial match
expect(screen.getByText(/hello/i)).toBeInTheDocument();

// Check text content
const element = screen.getByRole('heading');
expect(element).toHaveTextContent('Hello World');
```

### Attribute Assertions

```typescript
const link = screen.getByRole('link', { name: /back/i });

// Check href attribute
expect(link).toHaveAttribute('href', '/#gallery');

// Check class
expect(link).toHaveClass('text-farm-green');

// Check src (images)
const img = screen.getByRole('img');
expect(img).toHaveAttribute('src', '/images/pinklady.jpg');
```

### Form Assertions

```typescript
// Input value
const input = screen.getByRole('textbox');
expect(input).toHaveValue('test value');

// Checkbox/radio checked state
const checkbox = screen.getByRole('checkbox');
expect(checkbox).toBeChecked();
expect(checkbox).not.toBeChecked();

// Disabled state
expect(screen.getByRole('button')).toBeDisabled();
expect(screen.getByRole('button')).toBeEnabled();
```

### Collection Assertions

```typescript
// Count elements
const listItems = screen.getAllByRole('listitem');
expect(listItems).toHaveLength(3);

// All elements match condition
const traits = screen.getAllByRole('listitem');
expect(traits.every(el => el.textContent)).toBeTruthy();
```

## Testing Item Biography Component (Complete Example)

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

vi.mock('@/lib/items', async () => {
  const actual = await vi.importActual('@/lib/items');
  return {
    ...actual,
    isCurrentlyBred: vi.fn((item) => !!item.breedingStatus),
  };
});

// Test data factory
const createTestItem = (overrides: Partial<Item> = {}): Item => ({
  id: 1,
  name: 'Test Item',
  slug: 'test-item',
  imageSrc: '/images/test.jpg',
  alt: 'Test item image',
  type: 'category',
  category: 'category',
  biography: {
    bio: 'Test item biography.',
    age: '5 years old (born 2020)',
    personality: ['Friendly', 'Calm'],
  },
  ...overrides,
});

describe('ItemBiography', () => {
  describe('Core Elements', () => {
    it('renders item name as main heading', () => {
      const item = createTestItem({ name: 'Pink Lady' });
      render(<ItemBiography item={item} />);

      expect(screen.getByRole('heading', { name: 'Pink Lady', level: 1 }))
        .toBeInTheDocument();
    });

    it('renders item image with correct attributes', () => {
      const item = createTestItem({
        imageSrc: '/images/pinklady.jpg',
        alt: 'Pink Lady, a miniature item',
      });

      render(<ItemBiography item={item} />);

      const image = screen.getByAltText('Pink Lady, a miniature item');
      expect(image).toHaveAttribute('src', '/images/pinklady.jpg');
    });

    it('renders biography text', () => {
      const item = createTestItem({
        biography: { bio: 'This is a special item.' },
      });

      render(<ItemBiography item={item} />);

      expect(screen.getByText('This is a special item.')).toBeInTheDocument();
    });

    it('renders back to gallery link', () => {
      const item = createTestItem();
      render(<ItemBiography item={item} />);

      const link = screen.getByRole('link', { name: /back to gallery/i });
      expect(link).toHaveAttribute('href', '/#gallery');
    });
  });

  describe('Conditional Sections', () => {
    describe('Age Section', () => {
      it('renders age when provided', () => {
        const item = createTestItem({
          biography: { bio: 'Test', age: '5 years old' },
        });

        render(<ItemBiography item={item} />);

        expect(screen.getByText('Age')).toBeInTheDocument();
        expect(screen.getByText('5 years old')).toBeInTheDocument();
      });

      it('does not render age section when missing', () => {
        const item = createTestItem({
          biography: { bio: 'Test', age: undefined },
        });

        render(<ItemBiography item={item} />);

        expect(screen.queryByText('Age')).not.toBeInTheDocument();
      });
    });

    describe('Personality Traits', () => {
      it('renders all personality traits as list items', () => {
        const item = createTestItem({
          biography: {
            bio: 'Test',
            personality: ['Friendly', 'Calm', 'Curious'],
          },
        });

        render(<ItemBiography item={item} />);

        expect(screen.getByText('Friendly')).toBeInTheDocument();
        expect(screen.getByText('Calm')).toBeInTheDocument();
        expect(screen.getByText('Curious')).toBeInTheDocument();
      });

      it('does not render personality section when empty', () => {
        const item = createTestItem({
          biography: { bio: 'Test', personality: [] },
        });

        render(<ItemBiography item={item} />);

        const allText = screen.queryByText(/friendly|calm|curious/i);
        expect(allText).not.toBeInTheDocument();
      });
    });

    describe('Bun in Oven Section', () => {
      it('renders for bred category', () => {
        const item = createTestItem({
          type: 'category',
          breedingStatus: { bredTo: 'santiago', expectedYear: 2026 },
        });

        render(<ItemBiography item={item} />);

        expect(screen.getByTestId('bun-in-oven')).toBeInTheDocument();
      });

      it('does not render for non-bred category', () => {
        const item = createTestItem({
          type: 'category',
          breedingStatus: undefined,
        });

        render(<ItemBiography item={item} />);

        expect(screen.queryByTestId('bun-in-oven')).not.toBeInTheDocument();
      });

      it('does not render for jack items', () => {
        const item = createTestItem({
          type: 'jack',
          category: 'jack',
        });

        render(<ItemBiography item={item} />);

        expect(screen.queryByTestId('bun-in-oven')).not.toBeInTheDocument();
      });
    });
  });

  describe('Child Components', () => {
    it('renders LineageTree component', () => {
      const item = createTestItem({ name: 'Pink Lady' });
      render(<ItemBiography item={item} />);

      expect(screen.getByTestId('lineage-tree')).toBeInTheDocument();
      expect(screen.getByText(/lineagetree for pink lady/i)).toBeInTheDocument();
    });
  });
});
```

## Common Pitfalls and Solutions

### Pitfall 1: Testing Implementation Details

```typescript
// ❌ BAD: Tests CSS classes
expect(component.find('.card-title')).toExist();

// ✅ GOOD: Tests accessible content
expect(screen.getByRole('heading', { name: /title/i })).toBeInTheDocument();
```

### Pitfall 2: Not Waiting for Async Updates

```typescript
// ❌ BAD: No waiting
user.click(button);
expect(screen.getByText('Clicked')).toBeInTheDocument(); // Fails!

// ✅ GOOD: Await user events
await user.click(button);
expect(screen.getByText('Clicked')).toBeInTheDocument();
```

### Pitfall 3: Using getBy for Optional Elements

```typescript
// ❌ BAD: Throws error if not found
expect(screen.getByText('Optional')).not.toBeInTheDocument(); // Error!

// ✅ GOOD: Use queryBy for absence checks
expect(screen.queryByText('Optional')).not.toBeInTheDocument();
```

### Pitfall 4: Overly Specific Queries

```typescript
// ❌ BAD: Brittle to text changes
screen.getByText('Submit the form now!');

// ✅ GOOD: Flexible regex
screen.getByRole('button', { name: /submit/i });
```

## Summary Checklist

When testing React components:

- [ ] Use accessible queries (getByRole, getByLabelText)
- [ ] Test user behavior, not implementation
- [ ] Mock child components for isolation
- [ ] Use queryBy for absence assertions
- [ ] Await async user interactions
- [ ] Test conditional rendering branches
- [ ] Use test data factories for consistency
- [ ] Mock Next.js built-ins when needed
- [ ] Focus on critical user flows
- [ ] Keep tests simple and readable

## Resources

- [React Testing Library Cheatsheet](https://testing-library.com/docs/react-testing-library/cheatsheet)
- [Common Mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Which Query Should I Use?](https://testing-library.com/docs/queries/about#priority)

# Modular Patterns for JavaScript/TypeScript

Comprehensive patterns for organizing code to enable parallel agent development.

## Table of Contents

- [Feature-Based Organization](#feature-based-organization)
- [Domain-Driven Organization](#domain-driven-organization)
- [Layered Architecture](#layered-architecture)
- [Hybrid Approaches](#hybrid-approaches)
- [React/Next.js Specific Patterns](#reactnextjs-specific-patterns)

---

## Feature-Based Organization

**When to use**: Applications with distinct features that operate independently.

**Structure**:
```
src/
  features/
    authentication/
      types.ts
      auth-service.ts
      login-form.tsx
      signup-form.tsx
      index.ts
    user-profile/
      types.ts
      profile-service.ts
      profile-card.tsx
      edit-profile.tsx
      index.ts
    item-management/
      types.ts
      item-service.ts
      item-list.tsx
      item-detail.tsx
      index.ts
```

**Benefits**:
- Clear ownership boundaries (Agent A owns authentication, Agent B owns profile)
- Easy to locate all code related to a feature
- Features can be developed in complete isolation
- Can evolve into micro-frontends if needed

**Drawbacks**:
- Cross-feature code sharing requires careful planning
- Risk of duplicating utilities across features

**Agent Assignment Strategy**:
```yaml
Sprint 1:
  - Agent A: features/authentication/* (Complete feature)
  - Agent B: features/user-profile/* (Complete feature)
  - Agent C: features/item-management/* (Complete feature)
# Zero conflicts - each agent owns a directory
```

---

## Domain-Driven Organization

**When to use**: Complex business domains with rich domain logic.

**Structure**:
```
src/
  domain/
    item/
      entities/
        item.ts           # Domain model
        details.ts
      value-objects/
        breed.ts
        color.ts
      services/
        breeding-service.ts
        health-service.ts
      repositories/
        item-repository.ts
      index.ts
    farm/
      entities/
        farm.ts
      services/
        location-service.ts
      index.ts
```

**Benefits**:
- Mirrors business domain structure
- Clear separation of concerns (entities, services, repositories)
- Rich domain models with behavior
- Supports complex business rules

**Drawbacks**:
- Can become over-engineered for simple CRUD
- Requires team understanding of DDD concepts
- More files and directories to navigate

**Agent Assignment Strategy**:
```yaml
Feature: Add Breeding Tracking
  - Agent A: domain/item/entities/item.ts (Add breeding fields)
  - Agent B: domain/item/services/breeding-service.ts (Implement logic)
  - Agent C: domain/item/repositories/item-repository.ts (Add queries)
# Each agent works on different layer
```

---

## Layered Architecture

**When to use**: Applications with clear separation between UI, business logic, and data.

**Structure**:
```
src/
  presentation/        # Layer 1: UI Components
    components/
      item-card.tsx
      item-list.tsx
    pages/
      items.tsx
  application/         # Layer 2: Application Logic
    use-cases/
      get-item-details.ts
      update-item.ts
    queries/
      item-queries.ts
  domain/              # Layer 3: Business Logic
    models/
      item.ts
    services/
      breeding-service.ts
  infrastructure/      # Layer 4: External Services
    api/
      item-api.ts
    repositories/
      item-repository.ts
```

**Dependencies**: Each layer only depends on layers below it.

```
presentation → application → domain → infrastructure
```

**Benefits**:
- Clear dependency direction
- Easy to test (mock lower layers)
- Can swap infrastructure without affecting domain
- Prevents circular dependencies

**Drawbacks**:
- Can feel bureaucratic for simple operations
- Jumping between layers for single feature
- More boilerplate

**Agent Assignment Strategy**:
```yaml
Feature: Add Item Search
  - Agent A: presentation/pages/search.tsx
  - Agent B: application/use-cases/search-items.ts
  - Agent C: infrastructure/api/search-api.ts
# Sequential PRs (C → B → A) but minimal conflicts
```

---

## Hybrid Approaches

### Screaming Architecture

**Concept**: Project structure should scream what the application does, not what framework it uses.

```
src/
  item-breeding/     # Business capability, not "controllers"
    types.ts
    breeding-rules.ts
    breeding-calculator.ts
    breeding-ui.tsx
  item-health/
    types.ts
    health-checker.ts
    vaccination-tracker.ts
    health-dashboard.tsx
  item-registry/
    types.ts
    registry-service.ts
    registry-ui.tsx
```

**Benefits**:
- Business capabilities are immediately obvious
- Non-technical stakeholders can understand structure
- Aligns with business conversations

### Colocation by Feature

**Concept**: Keep everything related to a feature together, including tests and styles.

```
src/
  item-profile/
    item-profile.tsx        # Component
    item-profile.test.tsx   # Tests
    item-profile.module.css # Styles
    item-profile.types.ts   # Types
    use-item-data.ts        # Hook
    index.ts                  # Barrel
```

**Benefits**:
- Delete feature = delete directory
- All context in one place
- Easy to see complete feature scope

### Ports and Adapters (Hexagonal)

**Concept**: Business logic at center, external concerns at edges.

```
src/
  core/                # Business logic (no external dependencies)
    item/
      types.ts
      breeding-logic.ts
      health-rules.ts
  ports/               # Interfaces for external services
    item-repository.ts
    notification-service.ts
  adapters/            # Implementations of ports
    rest-item-repository.ts
    graphql-item-repository.ts
    email-notification-service.ts
  ui/                  # Presentation layer
    components/
    pages/
```

**Benefits**:
- Core logic completely isolated from infrastructure
- Easy to swap implementations (REST → GraphQL)
- Testable without mocks (use in-memory adapters)

---

## React/Next.js Specific Patterns

### Next.js App Router Structure

**Pattern**: Combine file-system routing with modular organization.

```
app/
  (marketing)/         # Route group (not in URL)
    page.tsx           # Homepage
    about/
      page.tsx
  (app)/               # Route group
    items/
      page.tsx         # /items
      [slug]/
        page.tsx       # /items/[slug]
      _components/     # Private components (not routes)
        item-grid.tsx
        item-filters.tsx
  api/                 # API routes
    items/
      route.ts         # /api/items

lib/                   # Shared business logic
  items/
    types.ts
    queries.ts
    filters.ts
    index.ts

components/            # Shared UI components
  ui/
    button.tsx
    card.tsx
  item/
    item-card.tsx
    item-list.tsx
```

**Agent Assignment**:
```yaml
Feature: Add Item Breeding Pages
  - Agent A: app/(app)/breeding/page.tsx + _components/*
  - Agent B: lib/breeding/* (business logic)
  - Agent C: components/breeding/* (shared components)
```

### Component Composition Pattern

**Pattern**: Build complex UIs from small, focused components.

```typescript
// Bad: Monolithic component
function ItemProfile({ item }: Props) {
  return (
    <div>
      {/* 50 lines of header */}
      {/* 80 lines of details */}
      {/* 60 lines of characteristics */}
      {/* 40 lines of timeline */}
    </div>
  );
}

// Good: Composed components
function ItemProfile({ item }: Props) {
  return (
    <div>
      <ItemHeader item={item} />
      <ItemDetails item={item} />
      <ItemCharacteristics item={item} />
      <ItemTimeline item={item} />
    </div>
  );
}

// Each sub-component in separate file:
// item-header.tsx
// item-details.tsx
// item-characteristics.tsx
// item-timeline.tsx
```

**Agent Assignment**: One agent per sub-component = parallel work.

### Custom Hooks Pattern

**Pattern**: Extract stateful logic into reusable hooks.

```typescript
// hooks/use-item-search.ts
export function useItemSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Item[]>([]);

  useEffect(() => {
    // Search logic
  }, [query]);

  return { query, setQuery, results };
}

// hooks/use-item-filters.ts
export function useItemFilters() {
  const [filters, setFilters] = useState<Filters>({});
  const [filtered, setFiltered] = useState<Item[]>([]);

  // Filter logic

  return { filters, setFilters, filtered };
}

// Component just composes hooks
function ItemBrowser() {
  const search = useItemSearch();
  const filters = useItemFilters();

  return (/* UI */);
}
```

**Benefits for Agents**:
- Agent A: Modify search logic in use-item-search.ts
- Agent B: Modify filter logic in use-item-filters.ts
- No conflicts

### Server/Client Component Split

**Pattern**: Separate data fetching (server) from interactivity (client).

```typescript
// app/items/[slug]/page.tsx (Server Component)
export default async function ItemPage({ params }: Props) {
  const item = await getItemBySlug(params.slug);
  return <ItemDetail item={item} />;
}

// components/item-detail.tsx (Client Component)
'use client';

export function ItemDetail({ item }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);
  // Interactive UI
}
```

**Agent Assignment**:
- Agent A: Server components (data fetching)
- Agent B: Client components (interactivity)
- Different concerns, different files

---

## Pattern Selection Decision Tree

```
Start: Need to organize code?
│
├─ Is this a new project?
│  ├─ Yes → Start with Feature-Based (simplest)
│  └─ No → Continue
│
├─ Do you have complex business rules?
│  ├─ Yes → Domain-Driven Organization
│  └─ No → Continue
│
├─ Do you need to swap infrastructure (DB, API)?
│  ├─ Yes → Layered or Ports & Adapters
│  └─ No → Continue
│
├─ Is your team distributed (multiple agents)?
│  ├─ Yes → Feature-Based (clearest boundaries)
│  └─ No → Continue
│
└─ Default → Hybrid: Features + Colocation
```

---

## Migration Strategies

### From Monolithic to Modular

**Step 1**: Identify features
```bash
# Analyze current structure
find src -name "*.tsx" -o -name "*.ts" | head -20

# Group by feature/domain
# Example: All item-related files, all auth-related files
```

**Step 2**: Create feature directories
```bash
mkdir -p src/features/{items,auth,profile}
```

**Step 3**: Move files incrementally
```bash
# Move one feature at a time
git mv src/components/ItemCard.tsx src/features/items/
git mv src/lib/item-queries.ts src/features/items/

# Test after each move
npm test

# Commit when feature is complete
git commit -m "refactor: move item feature to features/ directory"
```

**Step 4**: Update imports
```typescript
// Before
import { ItemCard } from '@/components/ItemCard';

// After
import { ItemCard } from '@/features/items';
```

**Step 5**: Add barrel files
```typescript
// src/features/items/index.ts
export { ItemCard } from './item-card';
export { ItemList } from './item-list';
export { useItemData } from './use-item-data';
```

### From Feature-Based to Domain-Driven

When complexity grows, evolve feature modules into domain modules:

```
Before (Feature-Based):
features/
  items/
    item-list.tsx
    item-detail.tsx
    item-queries.ts

After (Domain-Driven):
domain/
  item/
    entities/
      item.ts
    services/
      item-service.ts
    repositories/
      item-repository.ts
presentation/
  items/
    item-list.tsx
    item-detail.tsx
```

**When to migrate**:
- Feature modules exceed 15 files
- Complex business logic mixed with UI
- Need to share domain logic across features

---

## Anti-Patterns

### 1. Generic Folders

**Bad**:
```
src/
  components/  (100 components)
  utils/       (50 utilities)
  types/       (30 type files)
  hooks/       (40 hooks)
```

**Problem**: No clear ownership, everything is "shared".

**Fix**: Group by feature/domain first, then by type.

### 2. Deep Nesting

**Bad**:
```
src/
  features/
    items/
      domain/
        models/
          entities/
            item/
              item.entity.ts
```

**Problem**: Verbose imports, artificial boundaries.

**Fix**: Maximum 3 levels deep.

### 3. Circular Dependencies

**Bad**:
```typescript
// item-service.ts
import { formatItemName } from './item-utils';

// item-utils.ts
import { getItem } from './item-service';  // Circular!
```

**Problem**: Import errors, undefined values.

**Fix**: Create dependency layers (types → utils → services).

---

## Validation Checklist

After organizing code, verify:

- [ ] No file exceeds 300 lines (excluding data files)
- [ ] Each directory has a clear purpose
- [ ] No circular dependencies
- [ ] All directories have index.ts barrel files
- [ ] Related files are colocated
- [ ] Agent can work on one feature without touching others
- [ ] Import paths are consistent
- [ ] Tests are colocated with code

---

## Additional Resources

- [Feature-Sliced Design](https://feature-sliced.design/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Next.js Project Structure](https://nextjs.org/docs/app/building-your-application/routing/colocation)

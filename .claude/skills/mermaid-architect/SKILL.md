---
name: mermaid-architect
description: Expert Mermaid diagram creation for all diagram types including flowcharts, sequence diagrams, class diagrams, state diagrams, ER diagrams, Gantt charts, and more. Use when creating visual diagrams, system architecture, process flows, database schemas, timelines, or any technical documentation requiring clear visual representation. Provides best practices for diagram structure, readability, styling, and advanced patterns.
---

# Mermaid Architect

Expert guidance for creating professional, readable, and well-structured Mermaid diagrams across all diagram types.

## Core Principles

### Clarity Over Complexity
- Keep diagrams focused on a single purpose or level of abstraction
- Break complex systems into multiple related diagrams rather than one overwhelming diagram
- Use clear, descriptive labels that communicate purpose without reading implementation details
- Limit nodes per diagram: flowcharts 15-20 nodes, sequence diagrams 8-10 participants, class diagrams 10-12 classes

### Consistent Naming Conventions
- Use camelCase for IDs: `userService`, `paymentGateway`
- Use Title Case for display labels: "User Service", "Payment Gateway"
- Be consistent within a diagram family (use same naming for related diagrams)
- Avoid special characters in IDs that might break parsing

### Progressive Disclosure
- Start with high-level overview diagrams
- Create detailed diagrams for complex subsystems
- Link diagrams hierarchically when documenting complex systems
- Use subgraphs to group related components without overwhelming the main view

## Diagram Type Selection Guide

**Flowcharts** - Process flows, decision trees, algorithm logic
- Best for: Business processes, workflow automation, decision logic
- When to use: Showing sequential steps with branching conditions

**Sequence Diagrams** - Interaction over time, API calls, message passing
- Best for: System interactions, API documentation, protocol flows
- When to use: Showing how components communicate in temporal order

**Class Diagrams** - Object relationships, system structure, data models
- Best for: OOP design, system architecture, data modeling
- When to use: Showing static structure and relationships between entities

**State Diagrams** - State machines, lifecycle management
- Best for: Object lifecycles, UI states, workflow states
- When to use: Showing how an entity transitions between states

**Entity Relationship Diagrams** - Database schemas, data relationships
- Best for: Database design, data modeling
- When to use: Showing tables, columns, and relationships in databases

**Gantt Charts** - Project timelines, schedules, milestones
- Best for: Project planning, roadmaps, delivery schedules
- When to use: Showing tasks, dependencies, and timelines

**Git Graphs** - Branch strategies, commit history
- Best for: Development workflows, release processes
- When to use: Visualizing Git branching and merging strategies

**User Journey** - Customer experience, user flows
- Best for: UX design, customer journey mapping
- When to use: Showing user interactions across multiple touchpoints

## Flowchart Best Practices

### Basic Structure
```mermaid
flowchart TD
    Start([Start]) --> Input[/User Input/]
    Input --> Process[Process Data]
    Process --> Decision{Valid?}
    Decision -->|Yes| Success[Update Database]
    Decision -->|No| Error[Show Error]
    Success --> End([End])
    Error --> End
```

### Shape Conventions
- `([Terminal])` - Start/End points
- `[Process]` - Standard processing step
- `{Decision}` - Conditional branching
- `[/Input/]` - Input/Output operations
- `[(Database)]` - Database operations
- `[[Subroutine]]` - Subprocess or module call

### Organization Patterns
```mermaid
flowchart TD
    subgraph "Authentication Layer"
        A[Login Request] --> B{Credentials Valid?}
        B -->|Yes| C[Generate Token]
        B -->|No| D[Return Error]
    end
    
    subgraph "Business Logic Layer"
        C --> E[Access Resource]
        E --> F[Process Request]
    end
    
    F --> G[Return Response]
```

### Styling for Emphasis
```mermaid
flowchart LR
    A[Normal Step] --> B[Another Step]
    B --> C[Critical Path]
    B --> D[Alternative Path]
    
    classDef critical fill:#f96,stroke:#333,stroke-width:3px
    classDef alternative fill:#bbf,stroke:#333,stroke-width:1px
    class C critical
    class D alternative
```

## Sequence Diagram Best Practices

### Clear Participant Organization
```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant API
    participant Database
    
    User->>Frontend: Click Submit
    Frontend->>API: POST /api/data
    activate API
    API->>Database: INSERT query
    activate Database
    Database-->>API: Success
    deactivate Database
    API-->>Frontend: 201 Created
    deactivate API
    Frontend-->>User: Show Success
```

### Critical Features
- Use `activate`/`deactivate` to show processing lifelines
- Use `actor` for human participants, `participant` for systems
- Use solid arrows (`->>`) for requests, dashed (`-->>`) for responses
- Use `Note` to add context: `Note over API,Database: Transaction starts here`
- Use `alt`/`else` for conditional flows, `opt` for optional steps, `loop` for iterations

### Complex Interactions
```mermaid
sequenceDiagram
    participant Client
    participant LB as Load Balancer
    participant S1 as Server 1
    participant S2 as Server 2
    participant Cache
    participant DB as Database
    
    Client->>LB: Request
    LB->>S1: Forward Request
    
    alt Cache Hit
        S1->>Cache: Check Cache
        Cache-->>S1: Return Data
    else Cache Miss
        S1->>Cache: Check Cache
        Cache-->>S1: Not Found
        S1->>DB: Query Database
        DB-->>S1: Return Data
        S1->>Cache: Update Cache
    end
    
    S1-->>LB: Response
    LB-->>Client: Response
```

## Class Diagram Best Practices

### Relationship Types
```mermaid
classDiagram
    class User {
        +String username
        +String email
        -String passwordHash
        +login() bool
        +logout() void
    }
    
    class Profile {
        +String bio
        +String avatar
        +updateProfile() void
    }
    
    class Post {
        +String title
        +String content
        +Date published
        +publish() void
    }
    
    User "1" -- "1" Profile : has
    User "1" -- "*" Post : creates
```

### Visibility and Relationships
- Use `+` for public, `-` for private, `#` for protected
- Use `--|>` for inheritance (generalization)
- Use `--*` for composition (strong ownership)
- Use `--o` for aggregation (weak ownership)
- Use `-->` for dependency
- Use `--` for association
- Specify cardinality: `"1"`, `"*"`, `"0..1"`, `"1..*"`

### Organized Architecture
```mermaid
classDiagram
    namespace Domain {
        class User {
            <<entity>>
        }
        class Order {
            <<aggregate root>>
        }
    }
    
    namespace Infrastructure {
        class UserRepository {
            <<interface>>
        }
        class SqlUserRepository {
            <<implementation>>
        }
    }
    
    Domain.User --> Infrastructure.UserRepository : uses
    Infrastructure.SqlUserRepository ..|> Infrastructure.UserRepository : implements
```

## State Diagram Best Practices

### Clear State Transitions
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review : Submit
    Review --> Approved : Approve
    Review --> Rejected : Reject
    Review --> Draft : Request Changes
    Approved --> Published : Publish
    Published --> Archived : Archive
    Rejected --> Draft : Revise
    Archived --> [*]
    
    note right of Review
        Reviewers can approve,
        reject, or request changes
    end note
```

### Complex State Machines
```mermaid
stateDiagram-v2
    [*] --> Idle
    
    state "Processing" as Processing {
        [*] --> Validating
        Validating --> Executing : Valid
        Validating --> [*] : Invalid
        Executing --> Completing
        Completing --> [*]
    }
    
    Idle --> Processing : Start
    Processing --> Idle : Complete
    Processing --> Error : Failure
    Error --> Idle : Reset
```

## Entity Relationship Diagram Best Practices

### Database Schema Representation
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        int id PK
        string email UK
        string name
        datetime created_at
    }
    
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        int id PK
        int customer_id FK
        datetime order_date
        decimal total
        string status
    }
    
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
    PRODUCT {
        int id PK
        string sku UK
        string name
        decimal price
        int stock_quantity
    }
    
    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
    }
```

### Cardinality Notation
- `||--||` : One to exactly one
- `||--o{` : One to zero or more
- `||--|{` : One to one or more
- `}o--o{` : Zero or more to zero or more

### Key Indicators
- `PK` : Primary Key
- `FK` : Foreign Key
- `UK` : Unique Key

## Gantt Chart Best Practices

### Project Planning
```mermaid
gantt
    title Development Roadmap Q1 2025
    dateFormat YYYY-MM-DD
    section Planning
    Requirements Gathering    :done, req, 2025-01-01, 2025-01-15
    Architecture Design       :active, arch, 2025-01-10, 2025-01-25
    
    section Development
    Backend API              :dev1, 2025-01-20, 30d
    Frontend UI              :dev2, after dev1, 25d
    Integration Testing      :test, after dev2, 10d
    
    section Deployment
    Staging Deploy           :after test, 5d
    Production Deploy        :milestone, after test, 0d
```

### Status and Dependencies
- Use `:done` for completed tasks
- Use `:active` for current tasks
- Use `:crit` for critical path items
- Use `after taskId` for dependencies
- Use `:milestone` for zero-duration milestones

## Advanced Styling Techniques

### Theme and Direction
```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#ff6b6b','primaryTextColor':'#fff','primaryBorderColor':'#c92a2a','lineColor':'#495057','secondaryColor':'#51cf66','tertiaryColor':'#fff'}}}%%
flowchart LR
    A[Start] --> B[Process]
    B --> C[End]
```

### Custom Classes
```mermaid
flowchart TD
    A[Input] --> B{Valid?}
    B -->|Yes| C[Process]
    B -->|No| D[Error]
    
    classDef errorStyle fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef successStyle fill:#51cf66,stroke:#2f9e44,color:#fff
    classDef processStyle fill:#339af0,stroke:#1971c2,color:#fff
    
    class D errorStyle
    class C successStyle
    class A,B processStyle
```

## Anti-Patterns to Avoid

### Overcomplicated Diagrams
**Bad:**
```mermaid
flowchart TD
    A --> B & C & D & E
    B --> F & G & H
    C --> I & J & K
    D --> L & M & N
    E --> O & P & Q
```

**Good:** Break into multiple focused diagrams or use subgraphs

### Ambiguous Labels
**Bad:** `A[Proc]`, `B[Do Thing]`, `C[Check]`
**Good:** `A[Validate User Input]`, `B[Calculate Total Price]`, `C[Verify Payment Method]`

### Inconsistent Styling
**Bad:** Mixing arrow styles arbitrarily, random colors
**Good:** Consistent arrow usage, purposeful color coding (errors red, success green)

### Missing Context
**Bad:** Diagram with no title, unexplained abbreviations
**Good:** Clear title, legend for colors/shapes, notes for complex logic

## Advanced Patterns

For complex scenarios including:
- Multi-layer architecture diagrams
- Microservices interaction patterns
- Real-time collaboration flows
- CI/CD pipeline visualization
- Event-driven architecture
- CQRS and Event Sourcing patterns

See `references/advanced_patterns.md` for detailed examples and best practices.

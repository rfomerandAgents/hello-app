# Advanced Mermaid Patterns

This reference provides complex, real-world patterns for advanced Mermaid diagram scenarios.

## Microservices Architecture

### Service Mesh Communication
```mermaid
flowchart TB
    subgraph "External"
        Client[Client Application]
        LB[Load Balancer]
    end
    
    subgraph "Service Mesh"
        subgraph "User Service"
            US[User Service]
            USP[Sidecar Proxy]
        end
        
        subgraph "Order Service"
            OS[Order Service]
            OSP[Sidecar Proxy]
        end
        
        subgraph "Payment Service"
            PS[Payment Service]
            PSP[Sidecar Proxy]
        end
        
        subgraph "Notification Service"
            NS[Notification Service]
            NSP[Sidecar Proxy]
        end
        
        CP[Control Plane]
    end
    
    subgraph "Data Layer"
        UDB[(User DB)]
        ODB[(Order DB)]
        PDB[(Payment DB)]
        MQ[Message Queue]
    end
    
    Client --> LB
    LB --> USP
    USP <--> US
    US --> UDB
    
    USP <-.mTLS.-> OSP
    OSP <--> OS
    OS --> ODB
    
    OSP <-.mTLS.-> PSP
    PSP <--> PS
    PS --> PDB
    
    OSP -.event.-> MQ
    MQ -.event.-> NSP
    NSP <--> NS
    
    CP -.config.-> USP & OSP & PSP & NSP
    
    classDef service fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef proxy fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef data fill:#51cf66,stroke:#2f9e44,color:#fff
    classDef control fill:#ffd43b,stroke:#fab005,color:#333
    
    class US,OS,PS,NS service
    class USP,OSP,PSP,NSP proxy
    class UDB,ODB,PDB,MQ data
    class CP control
```

## Event-Driven Architecture

### CQRS with Event Sourcing
```mermaid
flowchart TB
    subgraph "Command Side"
        CMD[Command Handler]
        AGG[Aggregate]
        ES[(Event Store)]
    end
    
    subgraph "Event Bus"
        EB[Event Bus]
    end
    
    subgraph "Query Side"
        EP1[Event Processor 1]
        EP2[Event Processor 2]
        RDB1[(Read Model 1)]
        RDB2[(Read Model 2)]
        QH[Query Handler]
    end
    
    Client[Client] -->|Command| CMD
    CMD --> AGG
    AGG -->|Events| ES
    ES -->|Publish Events| EB
    
    EB -->|Subscribe| EP1
    EB -->|Subscribe| EP2
    
    EP1 -->|Update| RDB1
    EP2 -->|Update| RDB2
    
    Client -->|Query| QH
    QH -->|Read| RDB1
    QH -->|Read| RDB2
    
    classDef command fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef event fill:#ffd43b,stroke:#fab005,color:#333
    classDef query fill:#4dabf7,stroke:#1971c2,color:#fff
    
    class CMD,AGG command
    class ES,EB event
    class EP1,EP2,RDB1,RDB2,QH query
```

### Saga Pattern for Distributed Transactions
```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant OS as Order Service
    participant PS as Payment Service
    participant IS as Inventory Service
    participant SS as Shipping Service
    
    Note over O: Start Order Saga
    O->>OS: Create Order
    activate OS
    OS-->>O: Order Created (OrderId: 123)
    deactivate OS
    
    O->>PS: Reserve Payment
    activate PS
    PS-->>O: Payment Reserved
    deactivate PS
    
    O->>IS: Reserve Inventory
    activate IS
    IS-->>O: Inventory Reserved
    deactivate IS
    
    O->>SS: Schedule Shipping
    activate SS
    SS--xO: Shipping Failed
    deactivate SS
    
    Note over O: Compensation Started
    O->>IS: Release Inventory
    activate IS
    IS-->>O: Inventory Released
    deactivate IS
    
    O->>PS: Refund Payment
    activate PS
    PS-->>O: Payment Refunded
    deactivate PS
    
    O->>OS: Cancel Order
    activate OS
    OS-->>O: Order Cancelled
    deactivate OS
    
    Note over O: Saga Failed - Compensated
```

## CI/CD Pipeline Visualization

### Complete DevOps Pipeline
```mermaid
flowchart LR
    subgraph "Source Control"
        GH[GitHub]
        PR[Pull Request]
    end
    
    subgraph "CI Pipeline"
        direction TB
        Lint[Linting]
        Test[Unit Tests]
        Build[Build]
        Scan[Security Scan]
        Int[Integration Tests]
    end
    
    subgraph "Artifact Management"
        Reg[Container Registry]
        Art[Artifact Store]
    end
    
    subgraph "CD Pipeline"
        direction TB
        Dev[Dev Deploy]
        Stage[Staging Deploy]
        Prod[Production Deploy]
    end
    
    subgraph "Monitoring"
        direction TB
        Mon[Monitoring]
        Log[Logging]
        Alert[Alerting]
    end
    
    GH --> PR
    PR -->|Merge| Lint
    Lint --> Test
    Test --> Build
    Build --> Scan
    Scan --> Int
    Int --> Reg
    Int --> Art
    
    Reg --> Dev
    Dev -->|Promote| Stage
    Stage -->|Approve| Prod
    
    Dev & Stage & Prod --> Mon
    Mon --> Log
    Log --> Alert
    
    classDef source fill:#ffd43b,stroke:#fab005
    classDef ci fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef artifact fill:#51cf66,stroke:#2f9e44,color:#fff
    classDef cd fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef monitor fill:#cc5de8,stroke:#9c36b5,color:#fff
    
    class GH,PR source
    class Lint,Test,Build,Scan,Int ci
    class Reg,Art artifact
    class Dev,Stage,Prod cd
    class Mon,Log,Alert monitor
```

## Complex State Machines

### Order Processing Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Created
    
    Created --> PaymentPending : Submit Order
    
    state PaymentPending {
        [*] --> AwaitingPayment
        AwaitingPayment --> ProcessingPayment : Payment Initiated
        ProcessingPayment --> PaymentConfirmed : Success
        ProcessingPayment --> PaymentFailed : Failure
        PaymentFailed --> AwaitingPayment : Retry
    }
    
    PaymentPending --> Cancelled : Cancel
    PaymentPending --> Processing : Payment Confirmed
    
    state Processing {
        [*] --> InventoryCheck
        InventoryCheck --> InStock : Available
        InventoryCheck --> OutOfStock : Unavailable
        InStock --> Preparing
        OutOfStock --> [*] : Cancel Order
        Preparing --> ReadyToShip
    }
    
    Processing --> Cancelled : Inventory Unavailable
    Processing --> Shipping : Ready to Ship
    
    state Shipping {
        [*] --> PickedUp
        PickedUp --> InTransit
        InTransit --> OutForDelivery
        OutForDelivery --> Delivered
        OutForDelivery --> DeliveryFailed
        DeliveryFailed --> OutForDelivery : Retry
    }
    
    Shipping --> Delivered : Success
    Shipping --> ReturnInitiated : Return Request
    
    state Returns {
        [*] --> ReturnRequested
        ReturnRequested --> ReturnApproved
        ReturnApproved --> ReturnInTransit
        ReturnInTransit --> ReturnReceived
        ReturnReceived --> Refunded
    }
    
    Delivered --> Returns : Customer Return
    Returns --> Completed : Refund Processed
    
    Delivered --> Completed : Happy Path
    Cancelled --> [*]
    Completed --> [*]
```

## Multi-Layer Architecture

### Hexagonal Architecture (Ports and Adapters)
```mermaid
flowchart TB
    subgraph "External Actors"
        UI[Web UI]
        API[REST API]
        CLI[CLI Tool]
        Scheduler[Scheduled Jobs]
    end
    
    subgraph "Application Layer"
        direction LR
        subgraph "Inbound Ports"
            IPS[Service Port]
            IPQ[Query Port]
        end
        
        subgraph "Application Core"
            UC[Use Cases]
            DM[Domain Model]
            BL[Business Logic]
        end
        
        subgraph "Outbound Ports"
            OPP[Persistence Port]
            OPM[Messaging Port]
            OPE[External Service Port]
        end
    end
    
    subgraph "Infrastructure Adapters"
        PG[(PostgreSQL)]
        REDIS[(Redis Cache)]
        KAFKA[Kafka]
        EMAIL[Email Service]
        PAYMENT[Payment Gateway]
    end
    
    UI --> IPS
    API --> IPS
    CLI --> IPS
    Scheduler --> IPS
    
    IPS --> UC
    IPQ --> UC
    UC --> DM
    DM --> BL
    
    BL --> OPP
    BL --> OPM
    BL --> OPE
    
    OPP --> PG
    OPP --> REDIS
    OPM --> KAFKA
    OPE --> EMAIL
    OPE --> PAYMENT
    
    classDef external fill:#ffd43b,stroke:#fab005
    classDef port fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef core fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef infra fill:#51cf66,stroke:#2f9e44,color:#fff
    
    class UI,API,CLI,Scheduler external
    class IPS,IPQ,OPP,OPM,OPE port
    class UC,DM,BL core
    class PG,REDIS,KAFKA,EMAIL,PAYMENT infra
```

## Real-Time Collaboration System

### WebSocket Communication Flow
```mermaid
sequenceDiagram
    participant U1 as User 1 Browser
    participant U2 as User 2 Browser
    participant LB as Load Balancer
    participant WS1 as WebSocket Server 1
    participant WS2 as WebSocket Server 2
    participant Redis as Redis Pub/Sub
    participant DB as Database
    
    Note over U1,DB: Initial Connection
    U1->>LB: Connect WebSocket
    LB->>WS1: Route Connection
    WS1->>Redis: SUBSCRIBE document:123
    WS1->>DB: Load Document
    DB-->>WS1: Document Data
    WS1-->>U1: Document Content
    
    Note over U1,DB: User 2 Joins
    U2->>LB: Connect WebSocket
    LB->>WS2: Route Connection
    WS2->>Redis: SUBSCRIBE document:123
    WS2->>DB: Load Document
    DB-->>WS2: Document Data
    WS2-->>U2: Document Content
    
    Note over U1,DB: Collaborative Edit
    U1->>WS1: Edit Operation
    WS1->>Redis: PUBLISH edit to document:123
    Redis-->>WS1: Broadcast
    Redis-->>WS2: Broadcast
    WS2-->>U2: Update from User 1
    WS1->>DB: Persist Change
    
    Note over U1,DB: Cursor Position
    U2->>WS2: Cursor Move
    WS2->>Redis: PUBLISH cursor to document:123
    Redis-->>WS1: Broadcast
    WS1-->>U1: User 2 Cursor Position
    
    Note over U1,DB: Presence
    loop Every 30 seconds
        U1->>WS1: Heartbeat
        U2->>WS2: Heartbeat
        WS1->>Redis: Update Presence
        WS2->>Redis: Update Presence
    end
```

## Data Flow Architecture

### ETL Pipeline with Error Handling
```mermaid
flowchart TB
    subgraph "Source Systems"
        S1[CRM System]
        S2[ERP System]
        S3[Web Analytics]
        S4[IoT Sensors]
    end
    
    subgraph "Extraction Layer"
        E1[API Extractor]
        E2[Database Extractor]
        E3[File Extractor]
        E4[Stream Extractor]
    end
    
    subgraph "Staging Area"
        RAW[(Raw Data Lake)]
    end
    
    subgraph "Transformation Layer"
        V[Validation]
        C[Cleansing]
        N[Normalization]
        E[Enrichment]
        A[Aggregation]
    end
    
    subgraph "Quality Checks"
        Q1{Schema Valid?}
        Q2{Data Quality OK?}
        Q3{Business Rules OK?}
    end
    
    subgraph "Error Handling"
        DLQ[Dead Letter Queue]
        ERR[(Error Log)]
        ALERT[Alert System]
    end
    
    subgraph "Load Layer"
        DW[(Data Warehouse)]
        OLAP[(OLAP Cubes)]
        CACHE[(Cache Layer)]
    end
    
    S1 --> E1
    S2 --> E2
    S3 --> E3
    S4 --> E4
    
    E1 & E2 & E3 & E4 --> RAW
    RAW --> V
    
    V --> Q1
    Q1 -->|Yes| C
    Q1 -->|No| DLQ
    
    C --> Q2
    Q2 -->|Yes| N
    Q2 -->|No| DLQ
    
    N --> E
    E --> A
    
    A --> Q3
    Q3 -->|Yes| DW
    Q3 -->|No| DLQ
    
    DLQ --> ERR
    ERR --> ALERT
    
    DW --> OLAP
    DW --> CACHE
    
    classDef source fill:#ffd43b,stroke:#fab005
    classDef extract fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef transform fill:#51cf66,stroke:#2f9e44,color:#fff
    classDef error fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef load fill:#cc5de8,stroke:#9c36b5,color:#fff
    
    class S1,S2,S3,S4 source
    class E1,E2,E3,E4,RAW extract
    class V,C,N,E,A,Q1,Q2,Q3 transform
    class DLQ,ERR,ALERT error
    class DW,OLAP,CACHE load
```

## Complex Class Hierarchies

### Plugin Architecture
```mermaid
classDiagram
    class IPlugin {
        <<interface>>
        +getName() String
        +getVersion() String
        +initialize() void
        +execute() Result
        +cleanup() void
    }
    
    class AbstractPlugin {
        <<abstract>>
        #config Configuration
        #logger Logger
        +getName() String
        +getVersion() String
        #validateConfig() bool
    }
    
    class PluginManager {
        -plugins Map~String,IPlugin~
        -registry PluginRegistry
        +registerPlugin(plugin) void
        +unregisterPlugin(name) void
        +executePlugin(name) Result
        +listPlugins() List~IPlugin~
    }
    
    class DataSourcePlugin {
        -connectionPool ConnectionPool
        +connect() Connection
        +disconnect() void
        +query(sql) ResultSet
    }
    
    class TransformPlugin {
        -transformRules List~Rule~
        +addRule(rule) void
        +transform(data) Data
    }
    
    class OutputPlugin {
        -destination Destination
        +write(data) void
        +flush() void
    }
    
    class MySQLPlugin {
        -host String
        -port int
        +connect() Connection
    }
    
    class PostgreSQLPlugin {
        -connectionString String
        +connect() Connection
    }
    
    class JSONTransformPlugin {
        +transform(data) JSON
    }
    
    class XMLTransformPlugin {
        +transform(data) XML
    }
    
    class FileOutputPlugin {
        -filePath String
        +write(data) void
    }
    
    class KafkaOutputPlugin {
        -topic String
        -broker String
        +write(data) void
    }
    
    IPlugin <|.. AbstractPlugin
    AbstractPlugin <|-- DataSourcePlugin
    AbstractPlugin <|-- TransformPlugin
    AbstractPlugin <|-- OutputPlugin
    
    DataSourcePlugin <|-- MySQLPlugin
    DataSourcePlugin <|-- PostgreSQLPlugin
    
    TransformPlugin <|-- JSONTransformPlugin
    TransformPlugin <|-- XMLTransformPlugin
    
    OutputPlugin <|-- FileOutputPlugin
    OutputPlugin <|-- KafkaOutputPlugin
    
    PluginManager "1" --> "*" IPlugin : manages
    
    class Configuration {
        +get(key) Value
        +set(key, value) void
    }
    
    class Logger {
        +info(msg) void
        +error(msg) void
        +debug(msg) void
    }
    
    AbstractPlugin --> Configuration
    AbstractPlugin --> Logger
```

## Deployment Architecture

### Blue-Green Deployment with Canary
```mermaid
flowchart TB
    subgraph "Traffic Management"
        DNS[DNS/CDN]
        LB[Load Balancer]
        Router{Routing Rules}
    end
    
    subgraph "Blue Environment (v1.0)"
        direction LR
        B1[Instance 1]
        B2[Instance 2]
        B3[Instance 3]
        BDB[(Database v1)]
    end
    
    subgraph "Green Environment (v2.0)"
        direction LR
        G1[Instance 1]
        G2[Instance 2]
        G3[Instance 3]
        GDB[(Database v2)]
    end
    
    subgraph "Canary (v2.0)"
        C1[Canary Instance]
    end
    
    subgraph "Monitoring"
        M[Metrics]
        H[Health Checks]
        A[Automated Rollback]
    end
    
    DNS --> LB
    LB --> Router
    
    Router -->|95% traffic| B1 & B2 & B3
    Router -->|5% traffic| C1
    Router -.prepare.-> G1 & G2 & G3
    
    B1 & B2 & B3 --> BDB
    C1 --> GDB
    G1 & G2 & G3 -.-> GDB
    
    C1 --> M
    M --> H
    H -->|Failure| A
    A -.rollback.-> Router
    
    classDef blue fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef green fill:#51cf66,stroke:#2f9e44,color:#fff
    classDef canary fill:#ffd43b,stroke:#fab005
    classDef monitor fill:#ff6b6b,stroke:#c92a2a,color:#fff
    
    class B1,B2,B3,BDB blue
    class G1,G2,G3,GDB green
    class C1 canary
    class M,H,A monitor
```

## User Journey Mapping

### E-Commerce Purchase Flow
```mermaid
journey
    title Customer Purchase Journey
    section Discovery
      Browse Products: 5: Customer
      View Product Details: 4: Customer
      Read Reviews: 3: Customer, ReviewSystem
      Compare Options: 4: Customer
    section Decision
      Add to Cart: 5: Customer
      View Cart: 4: Customer
      Apply Coupon: 3: Customer, PromoSystem
      Calculate Shipping: 3: ShippingService
    section Purchase
      Enter Shipping Info: 2: Customer
      Enter Payment Info: 2: Customer, PaymentGateway
      Review Order: 4: Customer
      Place Order: 5: Customer, OrderSystem
    section Fulfillment
      Receive Confirmation: 5: Customer, EmailService
      Track Shipment: 4: Customer, ShippingService
      Receive Package: 5: Customer
      Leave Review: 3: Customer, ReviewSystem
```

## Timeline and Roadmap

### Product Development Phases
```mermaid
gantt
    title Product Development Roadmap 2025
    dateFormat YYYY-MM-DD
    
    section Research & Planning
    Market Research           :done, r1, 2025-01-01, 30d
    Competitive Analysis      :done, r2, 2025-01-15, 20d
    User Interviews          :active, r3, 2025-02-01, 15d
    Requirements Definition   :r4, after r3, 10d
    
    section Design
    UX Wireframes            :d1, after r4, 15d
    UI Mockups              :d2, after d1, 10d
    Design System           :d3, after d1, 20d
    User Testing            :d4, after d2, 10d
    
    section Development
    Backend API             :crit, dev1, after d3, 45d
    Frontend Core           :crit, dev2, after d3, 40d
    Integration Layer       :dev3, after dev1, 20d
    Admin Dashboard         :dev4, after dev2, 30d
    
    section Testing & QA
    Unit Testing            :test1, after dev1, 15d
    Integration Testing     :test2, after dev3, 15d
    Performance Testing     :test3, after test2, 10d
    Security Audit          :crit, test4, after test3, 5d
    UAT                     :test5, after test4, 10d
    
    section Launch
    Staging Deployment      :milestone, after test5, 0d
    Marketing Campaign      :market, after test5, 20d
    Beta Release           :beta, after test5, 14d
    Production Launch      :milestone, crit, after beta, 0d
    Post-Launch Support    :support, after beta, 30d
```

## Best Practices Summary

1. **Limit Complexity**: Keep diagrams focused on one aspect of the system
2. **Use Subgraphs**: Group related components for better organization
3. **Consistent Styling**: Apply color coding purposefully (errors red, success green)
4. **Clear Labels**: Use descriptive, business-friendly terminology
5. **Progressive Disclosure**: Start high-level, provide detailed sub-diagrams as needed
6. **Document Assumptions**: Use notes to clarify complex logic or decisions
7. **Version Control**: Include diagram version/date for documentation purposes
8. **Accessibility**: Ensure color choices work for colorblind users
9. **Maintenance**: Keep diagrams updated as systems evolve
10. **Tool Integration**: Link diagrams to live documentation and code

# Pivota — System Architecture

> **Product:** Pivota Data Navigator  
> **Tagline:** *Find where your data lives*

---

## 1. Architecture Overview

Pivota is an AI-powered metadata navigation platform that connects to multiple external database systems, extracts metadata without importing business records, builds a centralized metadata catalog, discovers relationships, generates semantic metadata, indexes metadata in a vector database, and uses hybrid retrieval with an LLM to answer natural-language data-location questions.

The architecture is organized into the following major layers:

```text
┌──────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│ Dashboard | Data Sources | Catalog | Search | AI | Data Map │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS / REST
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     API / APPLICATION LAYER                  │
│ Auth | Users | Sources | Catalog | Search | AI | Audit      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
┌────────────────────┐ ┌───────────────┐ ┌───────────────────┐
│ METADATA SERVICES  │ │ AI / RETRIEVAL│ │ BACKGROUND JOBS   │
│ Discovery          │ │ Query Analyze  │ │ Sync              │
│ Catalog            │ │ Hybrid Search  │ │ Embedding         │
│ Relationships      │ │ Reranking      │ │ Metadata Refresh  │
│ Semantic Metadata  │ │ LLM            │ │ Notifications     │
└─────────┬──────────┘ └───────┬───────┘ └─────────┬─────────┘
          │                    │                   │
          ▼                    ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                          │
│ PostgreSQL | Vector DB | Redis | Object / Log Storage       │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 EXTERNAL DATA SOURCE LAYER                  │
│ PostgreSQL | MySQL | SQL Server | Oracle | Future Providers│
└──────────────────────────────────────────────────────────────┘
```

---

# 2. Architectural Goals

The system architecture should satisfy these goals:

1. Support multiple database providers.
2. Store metadata instead of business records.
3. Keep organizations securely isolated.
4. Make metadata searchable.
5. Support semantic retrieval.
6. Provide explainable AI responses.
7. Run metadata synchronization asynchronously.
8. Allow new database providers to be added easily.
9. Support horizontal scaling.
10. Provide strong observability and auditability.
11. Separate application storage from external source data.
12. Prevent unauthorized access to connected databases.

---

# 3. High-Level Architecture

Pivota follows a layered architecture.

```text
                         USERS
                           │
                           ▼
                 ┌───────────────────┐
                 │ React Web Client  │
                 └─────────┬─────────┘
                           │
                         HTTPS
                           │
                           ▼
                 ┌───────────────────┐
                 │ API Gateway /     │
                 │ Reverse Proxy     │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ FastAPI Backend   │
                 └─────────┬─────────┘
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
       ▼                   ▼                    ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Auth & RBAC │     │ Metadata     │     │ AI / Search  │
│ Service     │     │ Services     │     │ Services     │
└─────────────┘     └──────┬───────┘     └──────┬───────┘
                           │                    │
                           ▼                    ▼
                    ┌────────────┐       ┌─────────────┐
                    │ PostgreSQL │       │ Vector DB   │
                    │ App DB     │       │             │
                    └────────────┘       └─────────────┘
                           ▲                    ▲
                           │                    │
                    ┌──────┴───────┐     ┌──────┴──────┐
                    │ Worker Queue │     │ Embedding   │
                    │ / Redis      │     │ Service     │
                    └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌───────────────┐
                    │ DB Connectors │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         PostgreSQL       MySQL       SQL Server
```

---

# 4. Major Architectural Layers

## 4.1 Presentation Layer

The presentation layer is the user-facing React application.

### Main modules

```text
Dashboard
Data Sources
Data Map
Catalog
Search
Ask Pivota AI
Data Insights
Alerts
Audit Logs
Settings
```

### Responsibilities

- User interaction
- Authentication UI
- Data source configuration
- Metadata browsing
- Search interface
- AI chat interface
- Data visualization
- Notifications
- Error and loading states

The frontend communicates with the backend through HTTPS APIs.

---

# 5. API / Application Layer

The application layer is implemented using FastAPI.

It acts as the central entry point for frontend requests.

### Responsibilities

- Authentication
- Authorization
- Request validation
- Business logic orchestration
- API responses
- Data source management
- Catalog operations
- Search operations
- AI requests
- Audit logging

### API structure

```text
/api/v1
    /auth
    /organizations
    /users
    /roles
    /providers
    /data-sources
    /credentials
    /catalog
    /databases
    /schemas
    /tables
    /columns
    /relationships
    /sync-jobs
    /search
    /ai
    /insights
    /alerts
    /audit-logs
    /settings
```

---

# 6. Authentication & Authorization Layer

Pivota requires secure authentication and organization-level authorization.

### Authentication flow

```text
User
 ↓
Login
 ↓
Credential Verification
 ↓
Access Token
 ↓
Frontend
 ↓
Authenticated API Requests
```

### Authorization

Pivota uses role-based access control.

Example roles:

```text
Organization Admin
Data Manager
Analyst
Viewer
```

Every protected resource should be evaluated against:

```text
User
 ↓
Organization
 ↓
Role
 ↓
Permission
 ↓
Resource
```

---

# 7. Organization / Multi-Tenant Architecture

Pivota is designed as a multi-tenant application.

Each organization has isolated:

- Users
- Roles
- Data sources
- Credentials
- Metadata
- Search results
- Vector documents
- Audit logs
- AI context

### Isolation model

```text
                    PIVOTA
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     Organization A Organization B Organization C
          │           │           │
       Metadata    Metadata    Metadata
       Vectors     Vectors     Vectors
       Users       Users       Users
```

Every application-level metadata and vector record should contain an organization identifier or equivalent tenant boundary.

---

# 8. Data Source Management Layer

The Data Source service manages connections to external databases.

### Workflow

```text
User
 ↓
Select Provider
 ↓
Enter Connection Details
 ↓
Configure Credential
 ↓
Configure SSL/TLS
 ↓
Test Connection
 ↓
Register Data Source
```

### Responsibilities

- Create data source
- Update data source
- Delete data source
- Test connection
- Get connection status
- Start metadata synchronization
- Manage connection configuration

---

# 9. Provider / Connector Architecture

A connector abstraction prevents Pivota from becoming dependent on a single database vendor.

### Common connector interface

```text
connect()
disconnect()
test_connection()

get_databases()
get_schemas(database)
get_tables(schema)
get_columns(table)

get_primary_keys(table)
get_foreign_keys(table)
get_indexes(table)
get_constraints(table)
```

### Architecture

```text
                  Connector Interface
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   PostgreSQL        MySQL          SQL Server
   Connector         Connector       Connector
          │              │              │
          ▼              ▼              ▼
     PostgreSQL        MySQL        SQL Server
```

### Benefit

Adding another provider should require implementing the connector interface rather than changing the entire metadata system.

---

# 10. Metadata Extraction Architecture

Metadata extraction is one of Pivota's core services.

### Extraction pipeline

```text
Data Source
    ↓
Connection
    ↓
Database Discovery
    ↓
Schema Discovery
    ↓
Table Discovery
    ↓
Column Discovery
    ↓
Key Discovery
    ↓
Relationship Discovery
    ↓
Metadata Persistence
```

### Metadata extracted

- Database name
- Schema name
- Table name
- Column name
- Data type
- Nullable
- Primary key
- Foreign key
- Constraints
- Index information
- Comments where available
- Estimated row count where appropriate

### Core rule

> Pivota's metadata discovery process should not copy business records into Pivota.

---

# 11. Metadata Storage Architecture

Pivota uses a relational database for structured metadata.

### Recommended database

**PostgreSQL**

### Logical structure

```text
Organization
   │
   ├── Users
   ├── Roles
   ├── Data Sources
   │      │
   │      ├── Credentials
   │      ├── Sync Jobs
   │      └── Databases
   │             └── Schemas
   │                    └── Tables
   │                           └── Columns
   │
   └── Audit Logs
```

The relational database acts as the source of truth for Pivota's structured metadata.

---

# 12. Relationship Discovery Architecture

Relationship discovery identifies connections between metadata objects.

### Primary source

Actual foreign-key constraints from the source database.

### Optional inference

Pivota can later infer relationships using:

- Naming similarity
- Data type compatibility
- Primary-key patterns
- Foreign-key patterns
- Semantic similarity

### Flow

```text
Source Database
      ↓
Foreign Key Metadata
      ↓
Relationship Extraction
      ↓
Relationship Validation
      ↓
Relationship Storage
      ↓
Data Map
      ↓
Retrieval Context
```

---

# 13. Semantic Metadata Layer

Technical metadata is transformed into business-friendly descriptions.

### Example

```text
Column:
cust_id

Semantic Metadata:
"Unique identifier used to identify a customer."
```

### Generated information

- Description
- Business terms
- Synonyms
- Keywords
- Entity meaning
- Context

### Flow

```text
Raw Metadata
     ↓
Prompt / Semantic Generation
     ↓
LLM
     ↓
Semantic Metadata
     ↓
PostgreSQL
     ↓
Embedding Pipeline
```

---

# 14. Embedding Architecture

Pivota converts metadata into vector representations.

### Pipeline

```text
Catalog Metadata
      ↓
Semantic Metadata
      ↓
Document Builder
      ↓
Embedding Model
      ↓
Vector
      ↓
Vector Database
```

### Example document

```text
Entity: Column

Provider: PostgreSQL
Data Source: Production
Database: ecommerce
Schema: public
Table: orders
Column: total_amount

Description:
Monetary amount associated with an order.

Related concepts:
revenue, sales, order value, transaction amount
```

This document is converted into an embedding.

---

# 15. Vector Database Architecture

The vector database provides semantic retrieval.

### Recommended options

- Qdrant
- pgvector

The initial implementation can use either depending on infrastructure requirements.

### Vector record

A vector document should contain:

```text
Vector ID
Organization ID
Entity Type
Entity ID
Embedding
Content
Metadata
Embedding Model
Created At
Updated At
```

### Important metadata filters

```text
organization_id
entity_type
provider
data_source
database
schema
table
```

This prevents retrieval from crossing organization boundaries.

---

# 16. Search Architecture

Pivota should use hybrid search rather than relying only on vector similarity.

### Hybrid search

```text
                  User Query
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    Keyword Search          Vector Search
          │                       │
          └───────────┬───────────┘
                      ▼
                Candidate Set
                      ↓
                  Reranking
                      ↓
                Final Results
```

### Search components

- Keyword search
- Semantic vector search
- Metadata filtering
- Relationship-aware retrieval
- Reranking
- Permission filtering

---

# 17. Retrieval Layer

The retrieval layer is responsible for selecting the best metadata context for the LLM.

### Flow

```text
User Query
    ↓
Query Understanding
    ↓
Query Expansion
    ↓
Hybrid Retrieval
    ↓
Candidate Results
    ↓
Relationship Expansion
    ↓
Reranking
    ↓
Context Selection
```

### Example

Query:

> "Where is customer revenue stored?"

Possible retrieved objects:

```text
customers.customer_id
orders.customer_id
orders.total_amount
order_items.order_id
```

The retrieval layer determines which objects are most relevant.

---

# 18. Ask Pivota AI Architecture

Ask Pivota AI is the natural-language interface to the metadata intelligence layer.

### Complete flow

```text
                 User Question
                       ↓
               Query Understanding
                       ↓
                 Query Expansion
                       ↓
               Hybrid Retrieval
                       ↓
                  Reranking
                       ↓
               Context Builder
                       ↓
                 Prompt Builder
                       ↓
                     LLM
                       ↓
             Grounded Response
                       ↓
              Catalog References
```

### AI responsibilities

The LLM should:

- Understand user intent.
- Identify important concepts.
- Interpret synonyms.
- Analyze retrieved metadata.
- Explain the result.
- Provide relevant data locations.
- Explain relationships.
- Avoid unsupported claims.

The LLM should not invent database objects that do not exist in the retrieved catalog.

---

# 19. Background Job Architecture

Long-running operations should run asynchronously.

### Examples

- Metadata synchronization
- Metadata extraction
- Relationship discovery
- Semantic metadata generation
- Embedding generation
- Vector indexing
- Large-scale re-indexing

### Architecture

```text
API
 ↓
Create Job
 ↓
Redis / Queue
 ↓
Worker
 ↓
Connector / AI / Vector Service
 ↓
Update Job Status
 ↓
Frontend
```

### Job states

```text
QUEUED
  ↓
RUNNING
  ↓
COMPLETED

RUNNING
  ↓
FAILED
  ↓
RETRY
```

---

# 20. Synchronization Architecture

Pivota should keep its metadata catalog synchronized with source databases.

### Full synchronization

```text
Source Database
      ↓
Extract Metadata
      ↓
Compare Existing Metadata
      ↓
Insert / Update / Remove
      ↓
Update Catalog
      ↓
Regenerate Changed Semantic Metadata
      ↓
Update Vector Documents
```

### Future incremental synchronization

Only changed metadata objects should be processed.

This reduces:

- Database load
- Processing time
- Embedding cost
- Vector indexing cost

---

# 21. Cache Architecture

Redis can be used for:

- Job queues
- Temporary state
- Session-related data where appropriate
- Rate limiting
- Frequently accessed catalog cache
- Search result caching
- AI response caching where safe

Example:

```text
Frontend
   ↓
FastAPI
   ↓
Redis Cache
   ├── HIT → Response
   └── MISS
        ↓
    PostgreSQL / Vector DB
```

---

# 22. Audit Architecture

Important user and system actions should be recorded.

### Example events

```text
LOGIN
CREATE_DATA_SOURCE
TEST_CONNECTION
START_SYNC
COMPLETE_SYNC
FAIL_SYNC
SEARCH
ASK_AI
UPDATE_ROLE
DELETE_DATA_SOURCE
UPDATE_SETTINGS
```

### Flow

```text
User Action
     ↓
API
     ↓
Business Service
     ↓
Audit Event
     ↓
Audit Log Storage
```

---

# 23. Security Architecture

Security should be applied at every layer.

```text
┌──────────────────────────────┐
│ Authentication               │
├──────────────────────────────┤
│ Authorization / RBAC         │
├──────────────────────────────┤
│ Organization Isolation       │
├──────────────────────────────┤
│ API Validation               │
├──────────────────────────────┤
│ Credential Encryption        │
├──────────────────────────────┤
│ TLS / SSL                    │
├──────────────────────────────┤
│ Least Privilege              │
├──────────────────────────────┤
│ Audit Logging                │
├──────────────────────────────┤
│ AI Retrieval Authorization   │
└──────────────────────────────┘
```

### External database access

Prefer read-only database credentials for metadata discovery.

Pivota should request only the permissions required to inspect metadata.

---

# 24. Credential Architecture

Credentials are sensitive and should not be treated as ordinary application metadata.

### Recommended flow

```text
User
 ↓
Credential Input
 ↓
Encryption / Secret Manager
 ↓
Encrypted Secret Reference
 ↓
Data Source
 ↓
Connector
 ↓
External Database
```

### Database should store

```text
Credential ID
Authentication Type
Secret Reference
Expiration
Status
```

Avoid storing plaintext passwords.

---

# 25. API Communication

Frontend-to-backend communication should use HTTPS.

```text
React
  │
  │ HTTPS
  ▼
Reverse Proxy
  │
  │ HTTP / internal network
  ▼
FastAPI
```

Backend-to-external-database communication should use secure connections where supported.

---

# 26. Deployment Architecture

A production deployment can be structured as:

```text
                         Internet
                            │
                            ▼
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
           Frontend CDN          API Server
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
               PostgreSQL       Redis         Vector DB
                    │              │              │
                    │              ▼              │
                    │          Workers            │
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
                            DB Connectors
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
             PostgreSQL          MySQL          SQL Server
```

---

# 27. Recommended Technology Stack

| Layer | Recommended Technology |
|---|---|
| Frontend | React + TypeScript |
| Styling | Tailwind CSS |
| Backend | FastAPI |
| API Schema | OpenAPI |
| Main Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Queue / Cache | Redis |
| Workers | Celery / RQ |
| Vector DB | Qdrant / pgvector |
| Embedding | Embedding model abstraction |
| LLM | Provider abstraction |
| Authentication | JWT / OAuth2 |
| Containers | Docker |
| Reverse Proxy | Nginx / Traefik |
| Testing | Pytest + frontend test framework |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana / equivalent |

---

# 28. Backend Module Architecture

Recommended backend organization:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── organizations.py
│   │       ├── users.py
│   │       ├── roles.py
│   │       ├── providers.py
│   │       ├── data_sources.py
│   │       ├── catalog.py
│   │       ├── search.py
│   │       ├── ai.py
│   │       ├── insights.py
│   │       ├── alerts.py
│   │       └── audit_logs.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── connectors/
│   ├── retrieval/
│   ├── ai/
│   ├── vector/
│   ├── workers/
│   ├── security/
│   ├── core/
│   └── utils/
│
└── tests/
```

---

# 29. Frontend Architecture

```text
frontend/
│
├── src/
│   ├── components/
│   ├── layouts/
│   ├── pages/
│   │   ├── Dashboard/
│   │   ├── DataSources/
│   │   ├── DataMap/
│   │   ├── Catalog/
│   │   ├── Search/
│   │   ├── AskPivotaAI/
│   │   ├── Insights/
│   │   ├── Alerts/
│   │   ├── AuditLogs/
│   │   └── Settings/
│   │
│   ├── services/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   ├── routes/
│   └── utils/
│
└── tests/
```

---

# 30. Core Data Flow

## Data ingestion flow

```text
External DB
    ↓
Connector
    ↓
Metadata Extraction
    ↓
Metadata Validation
    ↓
PostgreSQL Catalog
    ↓
Relationship Discovery
    ↓
Semantic Metadata
    ↓
Embedding Generation
    ↓
Vector DB
```

---

# 31. User Search Flow

```text
User
 ↓
Search UI
 ↓
Search API
 ↓
Query Processing
 ↓
Keyword + Vector Retrieval
 ↓
Reranking
 ↓
Metadata Results
 ↓
Catalog UI
```

---

# 32. Ask Pivota AI Flow

```text
User
 ↓
Ask Pivota AI
 ↓
LLM Query Understanding
 ↓
Hybrid Retrieval
 ↓
Relationship Context
 ↓
Reranking
 ↓
Context Builder
 ↓
LLM
 ↓
Grounded Answer
 ↓
Catalog / Data Map
```

---

# 33. Complete End-to-End Architecture

```text
                            USER
                              │
                              ▼
                    ┌──────────────────┐
                    │   PIVOTA WEB UI  │
                    │                  │
                    │ Dashboard        │
                    │ Data Sources     │
                    │ Catalog          │
                    │ Search           │
                    │ Ask Pivota AI    │
                    │ Data Map         │
                    └────────┬─────────┘
                             │ HTTPS
                             ▼
                    ┌──────────────────┐
                    │   FASTAPI API    │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
          ▼                  ▼                   ▼
   ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
   │ Auth / RBAC │    │ Metadata     │    │ AI / Search  │
   └─────────────┘    │ Services     │    │ Services     │
                      └──────┬───────┘    └──────┬───────┘
                             │                   │
               ┌─────────────┼───────┐           │
               │             │       │           │
               ▼             ▼       ▼           ▼
         ┌──────────┐  ┌────────┐ ┌───────┐ ┌──────────┐
         │ Catalog  │  │ Sync   │ │Semantic│ │Retrieval │
         │ Service  │  │Worker  │ │Service │ │ / Rerank │
         └────┬─────┘  └────┬───┘ └───┬───┘ └────┬─────┘
              │             │         │           │
              ▼             ▼         ▼           ▼
         ┌────────────────────┐  ┌──────────────┐
         │ PostgreSQL         │  │ Vector DB    │
         │ Application DB     │  │              │
         └─────────┬──────────┘  └──────┬───────┘
                   │                    │
                   │              ┌─────▼──────┐
                   │              │ Embedding  │
                   │              │ Model      │
                   │              └────────────┘
                   │
                   ▼
             ┌───────────┐
             │ Connector │
             │ Framework │
             └─────┬─────┘
                   │
       ┌───────────┼───────────────┐
       ▼           ▼               ▼
 PostgreSQL      MySQL         SQL Server
       │           │               │
       └───────────┴───────────────┘
                   │
             Metadata Only
```

---

# 34. Critical Architectural Rule

Pivota should maintain a clear separation between:

### Source Data

Actual business records remain inside the organization's databases.

### Pivota Metadata

Pivota stores information describing where that data exists.

```text
SOURCE DATABASE
────────────────────────
Customer records
Order records
Transaction records
Employee records
        │
        │ metadata discovery
        ▼
PIVOTA
────────────────────────
Database
Schema
Table
Column
Relationship
Description
Semantic Metadata
Embeddings
```

This distinction is fundamental to Pivota's architecture.

---

# 35. Architecture Evolution

## MVP

```text
React
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
PostgreSQL / MySQL Connectors
```

Add:

```text
Redis
 ↓
Workers
```

Then:

```text
Semantic Layer
 ↓
Vector DB
 ↓
Retrieval
 ↓
LLM
```

---

# 36. Scalability Strategy

As Pivota grows:

### API

Scale FastAPI horizontally.

```text
Load Balancer
    ├── API 1
    ├── API 2
    └── API 3
```

### Workers

Scale workers independently.

```text
Queue
 ├── Worker 1
 ├── Worker 2
 ├── Worker 3
 └── Worker N
```

### Vector database

Scale according to vector volume and query traffic.

### Metadata database

Use:

- Proper indexing
- Connection pooling
- Read replicas where necessary
- Partitioning if required at large scale

---

# 37. Reliability Strategy

Pivota should use:

- Retries for transient connection failures.
- Job state tracking.
- Idempotent metadata synchronization.
- Transaction boundaries.
- Connection timeouts.
- Circuit breakers where appropriate.
- Health checks.
- Backup and restore procedures.
- Failure notifications.

Metadata synchronization should be safe to retry without creating duplicate catalog objects.

---

# 38. Observability

The system should expose metrics for:

### API

- Request count
- Response latency
- Error rate

### Sync

- Jobs completed
- Jobs failed
- Metadata objects discovered
- Sync duration

### Search

- Query count
- Search latency
- Retrieval results

### AI

- LLM latency
- Token usage
- Retrieval latency
- AI error rate

### Vector DB

- Search latency
- Index size
- Query failures

---

# 39. Architecture Decision Summary

| Decision | Choice |
|---|---|
| Architecture | Layered + modular services |
| Frontend | React |
| Backend | FastAPI |
| Main DB | PostgreSQL |
| Metadata model | Relational |
| Queue | Redis |
| Background jobs | Worker-based |
| Connectors | Provider abstraction |
| Semantic layer | LLM-based |
| Retrieval | Hybrid |
| Vector DB | Qdrant / pgvector |
| AI | LLM abstraction |
| Authentication | JWT / OAuth2 |
| Authorization | RBAC |
| Deployment | Docker |
| Observability | Metrics + logs + tracing |

---

# 40. Final Architecture Principle

Pivota should be built around a simple architectural idea:

```text
CONNECT
   ↓
DISCOVER
   ↓
CATALOG
   ↓
UNDERSTAND
   ↓
INDEX
   ↓
RETRIEVE
   ↓
EXPLAIN
   ↓
NAVIGATE
```

The system does not primarily move organizational data.

It builds an intelligent map **about the data**.

That metadata map becomes the foundation for catalog browsing, semantic search, relationship exploration, and Ask Pivota AI.

> **Pivota = An intelligent navigation layer over distributed organizational data.**

# Pivota — Backend Architecture

> **Product:** Pivota Data Navigator  
> **Tagline:** *Find where your data lives*

---

## 1. Backend Architecture Overview

The Pivota backend is the central orchestration and intelligence layer responsible for:

- Managing organizations and users
- Managing roles and permissions
- Registering external data sources
- Securely managing connection credentials
- Connecting to supported database providers
- Discovering database metadata
- Building the metadata catalog
- Discovering table relationships
- Generating semantic metadata
- Creating and indexing embeddings
- Performing metadata retrieval
- Powering Search
- Powering Ask Pivota AI
- Running background synchronization jobs
- Managing alerts
- Recording audit events
- Enforcing tenant isolation and security

The backend **does not import or store source database records** as part of the core metadata ingestion process.

The primary information stored by Pivota is:

```text
Provider
   ↓
Data Source
   ↓
Database
   ↓
Schema
   ↓
Table
   ↓
Column
   ↓
Relationship
   ↓
Semantic Metadata
   ↓
Vector Document
```

---

# 2. Backend Architecture Goals

The backend should be:

1. Modular
2. Secure
3. Multi-tenant
4. Provider-independent
5. Scalable
6. Observable
7. Fault tolerant
8. API-first
9. Async-job capable
10. AI-ready
11. Metadata-centric
12. Easy to extend with new database providers

---

# 3. Recommended Backend Technology Stack

| Layer | Recommended Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| ORM | SQLAlchemy |
| Database Migration | Alembic |
| Application Database | PostgreSQL |
| Validation | Pydantic |
| Authentication | JWT / OAuth-compatible authentication |
| Password Hashing | Argon2id / bcrypt |
| Cache | Redis |
| Background Jobs | Celery / RQ / Arq |
| Vector Database | Qdrant / pgvector |
| Embeddings | Configurable embedding model |
| LLM | Configurable provider |
| HTTP Client | httpx |
| Database Drivers | SQLAlchemy dialects / native drivers |
| Logging | Python logging / structured logging |
| Testing | Pytest |
| API Documentation | OpenAPI / Swagger |
| Containerization | Docker |

The exact infrastructure can change without changing the logical backend architecture.

---

# 4. High-Level Backend Architecture

```text
                         ┌─────────────────────┐
                         │     Pivota Web UI   │
                         └──────────┬──────────┘
                                    │ HTTPS
                                    ▼
                         ┌─────────────────────┐
                         │    API Gateway /    │
                         │   FastAPI Backend   │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌────────────┐     ┌────────────┐     ┌────────────┐
          │ Auth & RBAC│     │ Catalog    │     │ Search / AI│
          └────────────┘     └────────────┘     └────────────┘
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Application /       │
                         │ Domain Services     │
                         └──────────┬──────────┘
                                    │
            ┌───────────────────────┼────────────────────────┐
            │                       │                        │
            ▼                       ▼                        ▼
     ┌──────────────┐       ┌──────────────┐        ┌──────────────┐
     │ PostgreSQL   │       │ Redis        │        │ Vector DB    │
     │ App Database │       │ Cache / Jobs │        │ Embeddings   │
     └──────────────┘       └──────────────┘        └──────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │ Worker Services │
                           └────────┬────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │ Connector Layer │
                           └────────┬────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
           PostgreSQL             MySQL              SQL Server
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    ▼
                           External Data Sources
```

---

# 5. Backend Layers

The backend should follow a layered architecture:

```text
API Layer
   ↓
Application / Service Layer
   ↓
Domain Layer
   ↓
Repository Layer
   ↓
Infrastructure Layer
```

### API Layer

Responsible for:

- HTTP endpoints
- Request validation
- Authentication dependencies
- Authorization checks
- Response serialization
- HTTP status codes

### Application Layer

Responsible for:

- Use cases
- Workflow orchestration
- Transaction coordination
- Calling domain services
- Calling external infrastructure

### Domain Layer

Responsible for:

- Business rules
- Metadata concepts
- Relationship rules
- Search behavior
- Synchronization states
- Permission rules

### Repository Layer

Responsible for:

- Database queries
- Persistence
- Transaction boundaries

### Infrastructure Layer

Responsible for:

- Database drivers
- Vector DB clients
- Redis
- LLM providers
- Embedding providers
- External integrations

---

# 6. Recommended Backend Project Structure

```text
backend/
│
├── app/
│   │
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── organizations.py
│   │   │   ├── users.py
│   │   │   ├── roles.py
│   │   │   ├── providers.py
│   │   │   ├── data_sources.py
│   │   │   ├── credentials.py
│   │   │   ├── catalog.py
│   │   │   ├── relationships.py
│   │   │   ├── sync.py
│   │   │   ├── search.py
│   │   │   ├── ai.py
│   │   │   ├── insights.py
│   │   │   ├── alerts.py
│   │   │   ├── audit_logs.py
│   │   │   └── settings.py
│   │
│   ├── core/
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── middleware.py
│   │
│   ├── models/
│   │   ├── organization.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── provider.py
│   │   ├── data_source.py
│   │   ├── credential.py
│   │   ├── database.py
│   │   ├── schema.py
│   │   ├── table.py
│   │   ├── column.py
│   │   ├── relationship.py
│   │   ├── sync_job.py
│   │   ├── audit_log.py
│   │   ├── semantic_metadata.py
│   │   └── vector_document.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── organization.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── data_source.py
│   │   ├── catalog.py
│   │   ├── search.py
│   │   ├── ai.py
│   │   └── common.py
│   │
│   ├── repositories/
│   │   ├── organization.py
│   │   ├── user.py
│   │   ├── data_source.py
│   │   ├── catalog.py
│   │   ├── relationship.py
│   │   ├── sync_job.py
│   │   └── audit_log.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── organization_service.py
│   │   ├── data_source_service.py
│   │   ├── credential_service.py
│   │   ├── metadata_service.py
│   │   ├── relationship_service.py
│   │   ├── semantic_service.py
│   │   ├── embedding_service.py
│   │   ├── search_service.py
│   │   ├── retrieval_service.py
│   │   ├── ai_service.py
│   │   ├── sync_service.py
│   │   ├── alert_service.py
│   │   └── audit_service.py
│   │
│   ├── connectors/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── mysql.py
│   │   ├── postgresql.py
│   │   ├── sqlserver.py
│   │   └── oracle.py
│   │
│   ├── workers/
│   │   ├── worker.py
│   │   ├── sync_tasks.py
│   │   ├── embedding_tasks.py
│   │   └── cleanup_tasks.py
│   │
│   ├── vector/
│   │   ├── client.py
│   │   ├── collections.py
│   │   ├── indexing.py
│   │   └── search.py
│   │
│   ├── llm/
│   │   ├── provider.py
│   │   ├── openai.py
│   │   ├── local.py
│   │   └── prompts.py
│   │
│   ├── embeddings/
│   │   ├── provider.py
│   │   └── service.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── migrations/
│   │
│   └── utils/
│       ├── crypto.py
│       ├── pagination.py
│       ├── identifiers.py
│       └── validators.py
│
├── tests/
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env
```

---

# 7. Core Backend Modules

Pivota backend consists of the following major modules:

```text
1. Authentication
2. Organization Management
3. User Management
4. Role & Permission Management
5. Data Provider Management
6. Data Source Management
7. Credential Management
8. Metadata Ingestion
9. Catalog Management
10. Relationship Discovery
11. Semantic Metadata
12. Vector Indexing
13. Search & Retrieval
14. Ask Pivota AI
15. Synchronization
16. Data Insights
17. Alerts
18. Audit Logging
19. System Configuration
```

---

# 8. Authentication Module

Responsible for:

- Login
- Logout
- Token generation
- Token validation
- Session management
- Password handling
- Refresh token management
- Account status checks

Flow:

```text
User
 ↓
POST /auth/login
 ↓
Validate Credentials
 ↓
Generate Access Token
 ↓
Generate Refresh Token
 ↓
Return Authentication Response
```

Authentication should be implemented independently from business modules.

---

# 9. Authorization and RBAC

Pivota uses role-based access control.

```text
Organization
      │
      ├── Users
      │
      └── Roles
             │
             └── Permissions
```

Permission examples:

```text
organization.read
organization.manage

users.read
users.manage

roles.read
roles.manage

data_sources.read
data_sources.create
data_sources.update
data_sources.delete

catalog.read
catalog.manage

search.execute
ai.ask

sync.read
sync.execute

audit.read
settings.manage
```

Authorization must be enforced in backend endpoints and services.

---

# 10. Multi-Tenant Architecture

Every organization is an isolated tenant.

```text
Organization A
 ├── Users
 ├── Data Sources
 ├── Catalog
 ├── Vector Documents
 └── Audit Logs

Organization B
 ├── Users
 ├── Data Sources
 ├── Catalog
 ├── Vector Documents
 └── Audit Logs
```

Every tenant-owned entity should carry an organization context directly or through a validated relationship.

The backend must never allow:

```text
Organization A
        ↓
access
        ↓
Organization B data
```

---

# 11. Data Provider Module

A Data Provider represents a database technology.

Examples:

```text
MySQL
PostgreSQL
Microsoft SQL Server
Oracle
MongoDB
```

Provider configuration can contain:

```text
Provider Name
Provider Type
Version
Supported Features
Driver
Status
```

Provider registry:

```text
Provider Registry
      │
      ├── MySQL Connector
      ├── PostgreSQL Connector
      ├── SQL Server Connector
      └── Oracle Connector
```

---

# 12. Connector Architecture

Connectors abstract database-specific behavior.

### Base interface

Conceptually:

```python
class BaseConnector:

    def test_connection():
        pass

    def connect():
        pass

    def close():
        pass

    def list_databases():
        pass

    def list_schemas():
        pass

    def list_tables():
        pass

    def list_columns():
        pass

    def list_relationships():
        pass
```

Each provider implements the same logical contract.

This allows the rest of Pivota to remain provider-independent.

---

# 13. Data Source Module

A Data Source represents an actual external database/server connection.

Responsibilities:

- Create data source
- Update data source
- Delete data source
- Test connection
- Manage connection settings
- Start metadata discovery
- Trigger synchronization
- Monitor health

Flow:

```text
Create Data Source
       ↓
Validate Provider
       ↓
Validate Configuration
       ↓
Validate Credential
       ↓
Test Connection
       ↓
Register Data Source
```

---

# 14. Credential Module

Credentials must be treated as highly sensitive infrastructure data.

Possible authentication types:

```text
Username + Password
API Key
Access Token
Certificate
Cloud IAM
Secret Reference
```

Recommended architecture:

```text
Pivota
   ↓
Credential Service
   ↓
Encryption / Secret Manager
   ↓
Encrypted Secret
```

The application database should preferably store a reference to the secret rather than plaintext credentials.

Example:

```text
secretReference:
    secret/data-source/8f31...
```

---

# 15. Connection Security

Supported security configuration may include:

```text
SSL/TLS Required
Certificate Validation
CA Certificate
Connection Timeout
Allowed Network Policy
Host Validation
Port Validation
```

For V1, connection policies should be explicit and restrictive.

The backend should prevent unsafe outbound connection behavior according to the configured network policy.

---

# 16. Metadata Ingestion Module

This is one of the core Pivota modules.

The ingestion process:

```text
Data Source
     ↓
Connector
     ↓
Database Discovery
     ↓
Schema Discovery
     ↓
Table Discovery
     ↓
Column Discovery
     ↓
Relationship Discovery
     ↓
Semantic Metadata
     ↓
Vector Indexing
     ↓
Catalog Ready
```

No source records are required for normal metadata ingestion.

---

# 17. Metadata Discovery

The connector extracts metadata such as:

### Database

```text
Database Name
Database Type
Version
```

### Schema

```text
Schema Name
Description if available
```

### Table

```text
Table Name
Object Type
Description if available
Estimated Row Count
```

### Column

```text
Column Name
Data Type
Nullable
Ordinal Position
Primary Key
Foreign Key
Default
Description
```

---

# 18. System Schema Handling

Each provider has its own system schemas.

The ingestion configuration should support:

```text
Include System Schemas
Exclude System Schemas
```

By default, Pivota should focus on application/business metadata rather than internal database implementation metadata.

---

# 19. Relationship Discovery

Relationships can be discovered through:

1. Native foreign keys
2. Database metadata
3. Column matching
4. Naming conventions
5. Semantic analysis

Example:

```text
orders.customer_id
        │
        │ FK
        ▼
customers.customer_id
```

The backend should record:

```text
Source Column
Target Column
Relationship Type
Discovery Method
Confidence
Status
```

Potential statuses:

```text
Discovered
Validated
Approved
Rejected
```

---

# 20. Semantic Metadata Module

Raw database metadata is technical.

Pivota converts it into understandable semantic information.

Example:

```text
Column:
cust_id
```

Semantic interpretation:

```text
Customer identifier used to uniquely identify a customer.
```

Generated information may include:

```text
Description
Business Terms
Synonyms
Entity Meaning
Data Domain
```

Semantic metadata can be generated by an LLM but should remain editable and traceable.

---

# 21. Semantic Generation Flow

```text
Raw Metadata
     ↓
Metadata Context Builder
     ↓
LLM Prompt
     ↓
LLM
     ↓
Structured Semantic Output
     ↓
Validation
     ↓
Store Semantic Metadata
```

The LLM should not directly modify the production catalog without validation.

---

# 22. Embedding Module

Semantic metadata is converted into vector embeddings.

Example document:

```text
Table: orders

Description:
Stores customer purchase orders.

Columns:
order_id
customer_id
order_date
total_amount

Business terms:
purchase
order
customer transaction
revenue
```

Then:

```text
Text
 ↓
Embedding Model
 ↓
Vector
 ↓
Vector Database
```

---

# 23. Vector Document Architecture

Each vector document should contain enough metadata to locate the original catalog object.

Example:

```text
VectorDocument
├── organizationId
├── entityType
├── entityId
├── content
├── embedding
├── embeddingModel
└── metadata
```

Possible entity types:

```text
database
schema
table
column
relationship
semantic_metadata
```

---

# 24. Vector Database Isolation

Vector search must respect organization boundaries.

Recommended conceptual filter:

```text
organization_id = current_organization_id
```

The backend should never perform unrestricted vector retrieval across tenants.

---

# 25. Search Architecture

Pivota Search should support hybrid retrieval.

```text
User Query
     │
     ├───────────────┐
     ▼               ▼
Keyword Search   Vector Search
     │               │
     └───────┬───────┘
             ▼
       Result Fusion
             ↓
       Ranking / Rerank
             ↓
       Final Results
```

This is more robust than relying only on semantic similarity.

---

# 26. Retrieval Layer

The retrieval service determines where relevant data lives.

Input:

```text
"Where is customer revenue stored?"
```

Retrieval pipeline:

```text
User Query
   ↓
Query Normalization
   ↓
Intent Detection
   ↓
Keyword Retrieval
   ↓
Vector Retrieval
   ↓
Metadata Filtering
   ↓
Relationship Expansion
   ↓
Result Ranking
   ↓
Relevant Data Objects
```

Output:

```text
Data Source
Database
Schema
Table
Column
Relationship
Relevance Score
```

---

# 27. Ask Pivota AI Architecture

Ask Pivota AI sits above the retrieval layer.

```text
User Question
      ↓
AI API
      ↓
Query Understanding
      ↓
Retrieval Service
      ↓
Relevant Metadata
      ↓
Context Builder
      ↓
LLM
      ↓
Answer + References
```

The LLM should use retrieved metadata rather than blindly answering from general knowledge.

---

# 28. Ask Pivota AI Response

A response should contain:

```text
Answer
Relevant Objects
Locations
Relationships
Confidence
References
```

Example:

```text
Customer revenue is primarily represented by:

Table:
orders

Column:
total_amount

Location:
Production
→ ecommerce
→ public
→ orders.total_amount

Related:
customers.customer_id
orders.customer_id
```

---

# 29. AI Guardrails

The AI layer should:

- Restrict retrieval to authorized tenant data.
- Avoid exposing credentials.
- Avoid inventing database objects.
- Prefer retrieved catalog information.
- Indicate uncertainty when confidence is low.
- Provide references to catalog objects.
- Avoid executing arbitrary source-database queries in the metadata navigation workflow.

---

# 30. Synchronization Module

Synchronization keeps the Pivota catalog aligned with source metadata.

Types:

```text
Initial Sync
Manual Sync
Scheduled Sync
Incremental Metadata Sync
Full Metadata Sync
```

Flow:

```text
Sync Request
    ↓
Create Sync Job
    ↓
Worker Queue
    ↓
Connector
    ↓
Discover Metadata
    ↓
Compare Existing Catalog
    ↓
Insert / Update / Remove Metadata
    ↓
Generate Semantic Metadata
    ↓
Update Embeddings
    ↓
Complete Job
```

---

# 31. Sync Job State Machine

```text
Pending
   ↓
Queued
   ↓
Running
   ↓
 ┌───────────────┐
 ▼               ▼
Completed       Failed
   │               │
   ▼               ▼
Indexed        Error Recorded
```

Possible job fields:

```text
Job ID
Data Source ID
Job Type
Status
Started At
Completed At
Entities Discovered
Entities Updated
Entities Removed
Error Message
```

---

# 32. Background Worker Architecture

Long-running operations should not block API requests.

Examples:

```text
Metadata Sync
Semantic Generation
Embedding Generation
Vector Indexing
Cleanup
Scheduled Health Checks
```

Architecture:

```text
FastAPI
   ↓
Create Job
   ↓
Redis / Queue
   ↓
Worker
   ↓
Execute Task
   ↓
Update Job
```

---

# 33. Redis Usage

Redis can be used for:

- Job queues
- Caching
- Rate limiting
- Temporary state
- Distributed locks
- Short-lived AI/session state

Redis should not become the primary persistent catalog database.

---

# 34. Application Database

PostgreSQL is recommended for the Pivota application database.

It stores:

```text
Organizations
Users
Roles
Providers
Data Sources
Credentials / Secret References
Databases
Schemas
Tables
Columns
Relationships
Semantic Metadata
Sync Jobs
Audit Logs
```

The application database stores Pivota's metadata, not the source database's business records.

---

# 35. Database Transaction Strategy

Transactions should be used for logically atomic operations.

Example:

```text
Create Data Source
       ↓
Create Credential Reference
       ↓
Create Initial Sync Job
       ↓
Commit
```

If a critical database operation fails:

```text
Rollback
```

Long-running metadata synchronization should use smaller transactional units rather than one massive transaction.

---

# 36. Repository Pattern

Services should not contain large amounts of raw SQL.

Use:

```text
Service
   ↓
Repository
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

Example:

```text
CatalogService
      ↓
CatalogRepository
      ↓
SQLAlchemy Query
      ↓
PostgreSQL
```

This improves testability and separation of concerns.

---

# 37. Service Layer

The service layer implements business workflows.

Examples:

```text
DataSourceService
MetadataService
SyncService
RelationshipService
SearchService
RetrievalService
AIService
CredentialService
AuditService
```

A service can coordinate multiple repositories and infrastructure providers.

---

# 38. API Layer

FastAPI endpoints should remain thin.

Example conceptual flow:

```text
HTTP Request
     ↓
Router
     ↓
Authentication
     ↓
Authorization
     ↓
Pydantic Validation
     ↓
Service
     ↓
Repository / Infrastructure
     ↓
Response Schema
     ↓
HTTP Response
```

Avoid putting complex business logic directly inside route functions.

---

# 39. API Versioning

Use versioned APIs:

```text
/api/v1/auth
/api/v1/data-sources
/api/v1/catalog
/api/v1/search
/api/v1/ai
```

Future versions can coexist:

```text
/api/v1
/api/v2
```

This prevents breaking existing frontend clients.

---

# 40. API Response Architecture

Use consistent response structures.

Success:

```json
{
  "data": {},
  "message": "Success"
}
```

Collection:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

Error:

```json
{
  "error": {
    "code": "DATA_SOURCE_CONNECTION_FAILED",
    "message": "Unable to connect to the data source."
  }
}
```

Never return secrets or internal stack traces.

---

# 41. Pagination

Large resources must be paginated.

Candidates:

```text
Data Sources
Databases
Schemas
Tables
Columns
Search Results
Audit Logs
Alerts
Users
```

The API should support:

```text
page
page_size
sort
order
```

Cursor pagination can be introduced for very large datasets.

---

# 42. Filtering and Sorting

Catalog APIs should support filtering by:

```text
Provider
Data Source
Database
Schema
Object Type
Status
Environment
```

Example:

```text
GET /api/v1/catalog/tables
    ?data_source_id=...
    &schema_id=...
    &search=customer
    &page=1
    &page_size=25
```

---

# 43. Audit Logging

Important actions should generate audit events.

Examples:

```text
LOGIN
LOGOUT
DATA_SOURCE_CREATED
DATA_SOURCE_UPDATED
DATA_SOURCE_DELETED
CONNECTION_TESTED
SYNC_STARTED
SYNC_COMPLETED
SYNC_FAILED
SEARCH_EXECUTED
AI_QUERY_EXECUTED
USER_CREATED
ROLE_UPDATED
SETTINGS_CHANGED
```

Audit records should contain enough context for traceability without storing sensitive secrets.

---

# 44. Alert Module

Alerts can be generated by backend services.

Examples:

```text
Connection Failure
Sync Failure
Metadata Drift
Credential Expiration
Low Retrieval Confidence
System Failure
```

Flow:

```text
Event
 ↓
Alert Rule
 ↓
Create Alert
 ↓
Persist
 ↓
Notify UI
```

---

# 45. Metadata Drift Detection

Pivota can compare current metadata with previous metadata.

Example:

```text
Previous:
orders.total_amount

Current:
orders.total_amount removed
```

System detects:

```text
Column Removed
```

Other changes:

```text
Column Added
Column Type Changed
Table Added
Table Removed
Relationship Added
Relationship Removed
```

These events can trigger alerts.

---

# 46. Caching Strategy

Cache suitable read-heavy information:

```text
Provider definitions
Catalog summaries
Frequently accessed metadata
Search suggestions
Organization configuration
```

Do not cache secrets.

Cache invalidation should happen after relevant mutations.

---

# 47. Rate Limiting

Rate limiting should protect:

```text
Authentication
Search
Ask Pivota AI
Data Source Testing
Expensive metadata operations
```

Example conceptual policy:

```text
Normal API
    → moderate limit

AI API
    → stricter limit

Login
    → strict limit
```

Limits should be configurable per organization or deployment tier.

---

# 48. Outbound Network Security

Because Pivota connects to external databases, outbound connections are a critical security boundary.

The backend should validate:

```text
Hostname
IP
Port
Protocol
TLS
Network Policy
Allowed Destination
```

Avoid blindly allowing arbitrary internal/private network destinations.

A configurable policy can support:

```text
Public-only
Approved private networks
Custom allow-list
```

---

# 49. Credential Lifecycle

Credential handling:

```text
Create
 ↓
Validate
 ↓
Encrypt / Store Reference
 ↓
Use
 ↓
Rotate
 ↓
Expire / Disable
```

The backend should support credential rotation without requiring the data source object to be recreated.

---

# 50. Connection Pooling

External database connections should be managed carefully.

The connector layer should control:

```text
Connection Timeout
Pool Size
Maximum Overflow
Idle Timeout
Retry Policy
```

For metadata extraction, connections should be short-lived whenever possible.

---

# 51. Retry Architecture

Retries should be applied only to recoverable failures.

Examples:

```text
Temporary network failure
Transient database error
Temporary vector DB failure
LLM rate limit
```

Do not blindly retry:

```text
Invalid credentials
Unauthorized access
Invalid host
Invalid configuration
```

Use exponential backoff for appropriate operations.

---

# 52. Observability

The backend should provide:

### Logs

```text
Request
Authentication
Data Source
Sync
Search
AI
Worker
Error
```

### Metrics

```text
API latency
API error rate
Sync duration
Sync failure rate
Search latency
Vector search latency
AI latency
Queue depth
Database connection pool usage
```

### Tracing

Trace major flows:

```text
AI Query
 ↓
Retrieval
 ↓
Vector Search
 ↓
Catalog Lookup
 ↓
LLM
```

---

# 53. Health Checks

Provide:

```text
GET /health
```

For deeper checks:

```text
GET /health/live
GET /health/ready
```

Readiness can verify dependencies such as:

```text
PostgreSQL
Redis
Vector DB
```

External source databases should not necessarily be required for global application readiness.

---

# 54. Configuration Architecture

Use environment variables and configuration classes.

Conceptual configuration:

```text
APP_ENV
DATABASE_URL
REDIS_URL
VECTOR_DB_URL
JWT_SECRET
LLM_PROVIDER
LLM_API_KEY
EMBEDDING_PROVIDER
ENCRYPTION_KEY
CORS_ORIGINS
LOG_LEVEL
```

Secrets should be supplied through secure deployment mechanisms.

---

# 55. Database Migration Architecture

Use Alembic for schema migrations.

Flow:

```text
Model Change
    ↓
Generate Migration
    ↓
Review Migration
    ↓
Apply Migration
    ↓
Verify Database
```

Never modify production database schemas manually without a controlled migration process.

---

# 56. Testing Architecture

## Unit Tests

Test:

```text
Business Rules
Services
Validators
Retrieval Ranking
Metadata Transformation
Permission Logic
```

## Integration Tests

Test:

```text
PostgreSQL
Redis
Vector DB
Connectors
API
```

## End-to-End Tests

Test:

```text
Login
 ↓
Create Data Source
 ↓
Test Connection
 ↓
Sync Metadata
 ↓
Catalog
 ↓
Search
 ↓
Ask Pivota AI
```

---

# 57. Connector Testing

Every connector should have provider-specific tests.

Example:

```text
MySQLConnector
 ├── test_connection
 ├── list_databases
 ├── list_schemas
 ├── list_tables
 ├── list_columns
 └── list_relationships
```

Use mock databases for most automated tests and dedicated integration environments for real provider validation.

---

# 58. AI Testing

AI functionality should be tested at multiple levels.

### Retrieval tests

```text
Question
 ↓
Expected Relevant Tables / Columns
```

### Grounding tests

Ensure generated responses only reference available metadata.

### Regression tests

Maintain representative questions:

```text
Where is customer information?
Where is revenue stored?
Which table contains employee email?
What database contains orders?
```

---

# 59. Backend Deployment Architecture

Recommended production deployment:

```text
                    Internet
                       │
                       ▼
                ┌─────────────┐
                │ Load Balancer│
                └──────┬──────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        FastAPI Instance   FastAPI Instance
              │                 │
              └────────┬────────┘
                       ▼
                 PostgreSQL
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Redis       Vector DB      Workers
                                    │
                                    ▼
                               Connectors
                                    │
                         External Data Sources
```

---

# 60. Container Architecture

Development can use Docker Compose:

```text
docker-compose
│
├── backend
├── postgres
├── redis
├── vector-db
└── worker
```

Production can move each component to managed infrastructure.

---

# 61. Horizontal Scaling

API servers should remain stateless where possible.

```text
             Load Balancer
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    API-1      API-2      API-3
       │          │          │
       └──────────┼──────────┘
                  ▼
              PostgreSQL
```

Authentication state should not depend on a particular API instance.

Background workers can scale independently:

```text
Queue
 ├── Worker 1
 ├── Worker 2
 └── Worker 3
```

---

# 62. Complete Metadata Ingestion Workflow

```text
User
 ↓
Create Data Source
 ↓
Validate Configuration
 ↓
Test Connection
 ↓
Register Source
 ↓
Create Sync Job
 ↓
Queue Job
 ↓
Worker Picks Job
 ↓
Connector Connects
 ↓
Discover Databases
 ↓
Discover Schemas
 ↓
Discover Tables
 ↓
Discover Columns
 ↓
Discover Relationships
 ↓
Store Catalog Metadata
 ↓
Generate Semantic Metadata
 ↓
Generate Embeddings
 ↓
Index Vector Documents
 ↓
Update Sync Job
 ↓
Audit Event
 ↓
Notify Frontend
```

---

# 63. Complete Search Workflow

```text
User Query
    ↓
API
    ↓
Authentication
    ↓
Authorization
    ↓
Query Normalization
    ↓
Keyword Search ───────┐
                      │
Vector Search ────────┤
                      ▼
               Result Fusion
                      ↓
                 Reranking
                      ↓
             Relationship Context
                      ↓
              Relevant Objects
                      ↓
                API Response
                      ↓
                   UI
```

---

# 64. Complete Ask Pivota AI Workflow

```text
User
 ↓
Ask Pivota AI
 ↓
AI API
 ↓
Authentication / Authorization
 ↓
Query Understanding
 ↓
Retrieval Service
 ↓
Hybrid Search
 ↓
Metadata Filtering
 ↓
Relationship Expansion
 ↓
Context Builder
 ↓
LLM
 ↓
Answer Validation
 ↓
Attach Metadata References
 ↓
Audit Event
 ↓
Response
```

---

# 65. Backend Module Dependency

```text
                 API
                  │
       ┌──────────┼───────────┐
       ▼          ▼           ▼
     Auth       Catalog     Search
       │          │           │
       │          ▼           ▼
       │       Metadata    Retrieval
       │          │           │
       │          ▼           ▼
       │      Semantic       AI
       │          │
       │          ▼
       │      Embeddings
       │          │
       │          ▼
       │       Vector DB
       │
       └─────── RBAC

Data Sources
     │
     ▼
Connectors
     │
     ▼
Sync Workers
     │
     ▼
Metadata
```

---

# 66. Backend Development Phases

## Phase 1 — Foundation

Develop:

```text
FastAPI project
Configuration
PostgreSQL
SQLAlchemy
Alembic
Docker
Logging
Exception handling
Health checks
```

## Phase 2 — Identity

Develop:

```text
Authentication
Organizations
Users
Roles
Permissions
Tenant isolation
```

## Phase 3 — Data Sources

Develop:

```text
Provider registry
Connector interface
Data source CRUD
Credential management
Connection testing
Security policies
```

## Phase 4 — Metadata

Develop:

```text
Metadata extraction
Database discovery
Schema discovery
Table discovery
Column discovery
Relationship discovery
Catalog persistence
```

## Phase 5 — Intelligence

Develop:

```text
Semantic metadata
Embedding generation
Vector indexing
Hybrid search
Retrieval
```

## Phase 6 — AI

Develop:

```text
Ask Pivota AI
Context builder
LLM integration
Grounding
References
Streaming
```

## Phase 7 — Operations

Develop:

```text
Background jobs
Sync scheduling
Alerts
Audit logs
Metadata drift
Observability
```

## Phase 8 — Production

Develop:

```text
Testing
Security hardening
Performance
Rate limiting
Deployment
CI/CD
Monitoring
```

---

# 67. Backend Security Checklist

```text
[ ] HTTPS
[ ] Secure authentication
[ ] Password hashing
[ ] Token expiration
[ ] RBAC
[ ] Tenant isolation
[ ] Encrypted credentials
[ ] Secret manager integration
[ ] Outbound network restrictions
[ ] TLS database connections
[ ] Input validation
[ ] SQL injection protection
[ ] Rate limiting
[ ] Audit logging
[ ] Safe error messages
[ ] No secrets in logs
[ ] Dependency scanning
[ ] Container security
```

---

# 68. Backend Performance Checklist

```text
[ ] Database indexes
[ ] Connection pooling
[ ] Pagination
[ ] Redis caching
[ ] Background jobs
[ ] Async I/O where useful
[ ] Vector index optimization
[ ] Search result limits
[ ] Batch embedding generation
[ ] Batch metadata operations
[ ] Lazy relationship loading
[ ] API response compression
```

---

# 69. Backend Reliability Checklist

```text
[ ] Retry policies
[ ] Timeout policies
[ ] Worker retry
[ ] Dead-letter handling
[ ] Transaction boundaries
[ ] Idempotent sync jobs
[ ] Health checks
[ ] Structured logs
[ ] Metrics
[ ] Alerting
[ ] Backup strategy
[ ] Migration strategy
```

---

# 70. Final Backend Architecture

```text
                         PIVOTA BACKEND
                              │
                    ┌─────────┴─────────┐
                    │     FastAPI       │
                    │    API Layer      │
                    └─────────┬─────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
   Auth/RBAC              Catalog              Search / AI
       │                      │                      │
       │                      ▼                      ▼
       │                 Metadata              Retrieval
       │                      │                      │
       │                      ▼                      ▼
       │               Relationships               LLM
       │                      │
       │                      ▼
       │              Semantic Metadata
       │                      │
       │                      ▼
       │                 Embeddings
       │                      │
       └──────────────────────┼──────────────────────┐
                              │                      │
                              ▼                      ▼
                        PostgreSQL                Vector DB
                              │
                         Redis / Queue
                              │
                              ▼
                           Workers
                              │
                              ▼
                         Connectors
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
            MySQL         PostgreSQL        SQL Server
```

---

# 71. Core Architectural Principle

Pivota's backend should maintain a strict separation between:

```text
SOURCE DATA
    ≠
PIVOTA METADATA
```

Pivota primarily discovers and stores:

```text
Where data exists
What the data objects are called
How objects are related
What the objects mean
How users can find them
```

rather than importing the actual business records.

The complete intelligence pipeline is:

```text
DATABASE CONNECTION
        ↓
METADATA DISCOVERY
        ↓
CATALOG
        ↓
SEMANTIC UNDERSTANDING
        ↓
EMBEDDINGS
        ↓
VECTOR INDEX
        ↓
HYBRID RETRIEVAL
        ↓
LLM CONTEXT
        ↓
ASK PIVOTA AI
        ↓
"FIND WHERE YOUR DATA LIVES"
```

> **Pivota's backend is the secure orchestration layer that converts distributed database metadata into a searchable, semantically understandable data map.**

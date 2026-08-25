# Pivota — Frontend Architecture

> **Product:** Pivota Data Navigator  
> **Tagline:** *Find where your data lives*

---

## 1. Frontend Architecture Overview

The Pivota frontend is a modern, modular web application designed to provide a clear interface for managing data sources, exploring metadata, searching across the organization's data landscape, and interacting with Ask Pivota AI.

The frontend should translate the complexity of database infrastructure into a simple user experience.

### Core principle

```text
Complex Data Infrastructure
            ↓
      Pivota Frontend
            ↓
Simple Data Discovery Experience
```

The frontend communicates with the Pivota backend through REST APIs and does not directly connect to external databases.

```text
┌──────────────────────────────┐
│        Pivota Web UI         │
│                              │
│ Dashboard                    │
│ Data Sources                 │
│ Data Map                     │
│ Catalog                      │
│ Search                       │
│ Ask Pivota AI                │
│ Data Insights                │
│ Alerts                       │
│ Audit Logs                   │
│ Settings                     │
└───────────────┬──────────────┘
                │ HTTPS / REST
                ▼
┌──────────────────────────────┐
│       Pivota Backend         │
│           FastAPI            │
└──────────────────────────────┘
```

---

# 2. Frontend Objectives

The frontend should:

1. Provide a consistent Pivota visual identity.
2. Make data discovery fast and intuitive.
3. Hide unnecessary database complexity from normal users.
4. Provide powerful tools for technical users.
5. Support organization-level access control.
6. Clearly communicate synchronization and connection states.
7. Provide explainable AI results.
8. Visualize database relationships effectively.
9. Remain responsive across desktop and tablet screens.
10. Provide reusable components and maintainable code.
11. Handle loading, empty, success, and error states consistently.
12. Provide accessible keyboard and screen-reader interactions where practical.

---

# 3. Recommended Technology Stack

| Area | Technology |
|---|---|
| Framework | React |
| Language | TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Component System | Reusable React components |
| Routing | React Router |
| Server State | TanStack Query |
| Client State | Zustand |
| Forms | React Hook Form |
| Validation | Zod |
| Charts | Recharts / ECharts |
| Graph Visualization | React Flow / Cytoscape |
| Icons | Lucide React |
| API Client | Fetch / Axios |
| Authentication | Token-based authentication |
| Testing | Vitest + React Testing Library |
| E2E Testing | Playwright |
| Linting | ESLint |
| Formatting | Prettier |

The exact library choice can change, but the architecture should preserve separation between UI, state, API, and domain logic.

---

# 4. Frontend Layered Architecture

```text
┌──────────────────────────────────────────────┐
│                UI / Pages                    │
│ Dashboard | Catalog | Search | AI | Settings│
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Feature Components              │
│ DataSource | Catalog | Search | AI | Alerts  │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│             Hooks / State Layer              │
│ TanStack Query | Zustand | Custom Hooks      │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│               API Service Layer              │
│ Auth | Sources | Catalog | Search | AI       │
└──────────────────────┬───────────────────────┘
                       │ HTTPS
                       ▼
              ┌──────────────────┐
              │  FastAPI Backend │
              └──────────────────┘
```

---

# 5. Application Structure

Recommended project structure:

```text
frontend/
│
├── public/
│   ├── favicon.svg
│   └── assets/
│
├── src/
│   │
│   ├── app/
│   │   ├── App.tsx
│   │   ├── routes.tsx
│   │   ├── providers.tsx
│   │   └── config.ts
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   ├── navigation/
│   │   ├── feedback/
│   │   ├── data-display/
│   │   └── forms/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── data-sources/
│   │   ├── data-map/
│   │   ├── catalog/
│   │   ├── search/
│   │   ├── ask-ai/
│   │   ├── insights/
│   │   ├── alerts/
│   │   ├── audit-logs/
│   │   └── settings/
│   │
│   ├── hooks/
│   ├── services/
│   │   ├── api/
│   │   ├── auth/
│   │   └── storage/
│   │
│   ├── stores/
│   ├── types/
│   ├── utils/
│   ├── constants/
│   ├── styles/
│   └── main.tsx
│
├── tests/
├── .env
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

---

# 6. Feature-Based Architecture

Pivota should use feature-oriented organization instead of putting all components into one large directory.

Example:

```text
features/
└── data-sources/
    ├── components/
    │   ├── DataSourceCard.tsx
    │   ├── DataSourceTable.tsx
    │   ├── ConnectionStatus.tsx
    │   └── ConnectionTestResult.tsx
    │
    ├── pages/
    │   ├── DataSourcesPage.tsx
    │   ├── CreateDataSourcePage.tsx
    │   └── DataSourceDetailsPage.tsx
    │
    ├── hooks/
    │   ├── useDataSources.ts
    │   └── useDataSource.ts
    │
    ├── api/
    │   └── dataSourceApi.ts
    │
    ├── schemas/
    │   └── dataSourceSchema.ts
    │
    ├── types.ts
    └── index.ts
```

This keeps related functionality together and makes future development easier.

---

# 7. Global Application Layout

Pivota should use a persistent application shell.

```text
┌───────────────────────────────────────────────────────────┐
│ Pivota Logo      Search...             Notifications User │
├──────────────┬────────────────────────────────────────────┤
│              │                                            │
│ Dashboard    │                                            │
│ Data Sources │               Main Content                 │
│ Data Map     │                                            │
│ Catalog      │                                            │
│ Search       │                                            │
│ Ask Pivota AI│                                            │
│ Insights     │                                            │
│ Alerts       │                                            │
│ Audit Logs   │                                            │
│              │                                            │
│ Settings     │                                            │
└──────────────┴────────────────────────────────────────────┘
```

### Main layout components

```text
AppShell
├── Sidebar
├── TopBar
├── Breadcrumbs
├── PageHeader
├── MainContent
└── GlobalNotifications
```

---

# 8. Navigation Architecture

Primary navigation:

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

### Navigation behavior

- Active page is visually highlighted.
- Navigation supports collapsed sidebar mode.
- Restricted pages are hidden or disabled according to permissions.
- Breadcrumbs provide context for deep catalog pages.
- Search and AI remain easily accessible.

---

# 9. Route Architecture

Recommended routes:

```text
/login

/dashboard

/data-sources
/data-sources/new
/data-sources/:id
/data-sources/:id/edit

/data-map

/catalog
/catalog/databases/:databaseId
/catalog/schemas/:schemaId
/catalog/tables/:tableId
/catalog/columns/:columnId

/search

/ask-pivota-ai

/insights

/alerts

/audit-logs

/settings
/settings/profile
/settings/organization
/settings/users
/settings/roles
/settings/security
```

---

# 10. Route Protection

Routes should be protected according to authentication and permissions.

```text
Request Route
     ↓
Authenticated?
 ┌───┴────┐
No       Yes
 ↓         ↓
Login    Permission Check
             ↓
       ┌─────┴─────┐
     Allow       Deny
       ↓            ↓
     Page       403 / Access
```

Example:

```text
/settings/users
```

may require:

```text
organization.users.manage
```

while:

```text
/catalog
```

may require:

```text
catalog.read
```

---

# 11. Design System

Pivota should use a centralized design system.

### Design system layers

```text
Design Tokens
     ↓
UI Primitives
     ↓
Composite Components
     ↓
Feature Components
     ↓
Pages
```

### UI primitives

- Button
- Input
- Select
- Checkbox
- Switch
- Badge
- Avatar
- Tooltip
- Dialog
- Drawer
- Tabs
- Dropdown
- Table
- Card
- Alert
- Toast
- Skeleton
- Spinner

---

# 12. Pivota Visual Theme

The visual identity should communicate:

- Intelligence
- Data infrastructure
- Precision
- Trust
- Modern engineering
- Exploration

The previously established visual direction can be summarized as:

```text
Dark / Deep Technical Base
          +
Cool Blue / Violet Accent
          +
Soft Glass Surfaces
          +
Subtle Data-Constellation Effects
          +
Clean White Typography
```

The interface should remain professional rather than becoming overly futuristic.

---

# 13. Color System

Use semantic color tokens rather than hard-coding colors throughout components.

Example conceptual palette:

```text
Background
 ├── App Background
 ├── Surface
 ├── Elevated Surface
 └── Overlay

Brand
 ├── Primary
 ├── Secondary
 └── Accent

Text
 ├── Primary
 ├── Secondary
 ├── Muted
 └── Disabled

Status
 ├── Success
 ├── Warning
 ├── Error
 └── Info
```

A representative Pivota theme can use:

```text
Primary:        Blue / Indigo
Secondary:      Violet
Background:     Deep Navy / Near Black
Surface:        Dark Blue-Gray
Primary Text:   White
Secondary Text: Cool Gray
Success:        Green
Warning:        Amber
Error:          Red
```

Exact values should be maintained in design tokens.

---

# 14. Typography

Recommended font hierarchy:

```text
Page Title
  ↓
Section Title
  ↓
Card Title
  ↓
Body
  ↓
Secondary Text
  ↓
Metadata / Caption
```

Recommended font:

```text
Inter
```

or another modern UI sans-serif with strong readability.

Database identifiers can optionally use a monospace font:

```text
JetBrains Mono
```

Example:

```text
orders.customer_id
```

This visually distinguishes technical identifiers from normal business language.

---

# 15. Background and Visual Effects

Pivota can use subtle visual effects without affecting readability.

### Data constellation

The signature visual can represent:

```text
Data Source
     ●
    / \
   ●   ●
  / \   \
 ●   ●   ●
```

These nodes can represent:

- Databases
- Schemas
- Tables
- Columns
- Relationships

### Usage

The constellation effect can appear on:

- Landing page
- Dashboard header
- Data Map
- AI empty state

It should remain subtle in functional pages.

---

# 16. Animation Architecture

Animations should communicate state rather than exist only for decoration.

### Recommended animations

- Page transitions
- Sidebar expansion
- Card hover
- Modal entry
- Toast appearance
- Search result loading
- AI response streaming
- Sync progress
- Data Map node expansion
- Connection testing
- Skeleton loading

### Animation principle

```text
Fast + Subtle + Meaningful
```

Avoid excessive animations on data-heavy screens.

---

# 17. Dashboard Page Architecture

The Dashboard provides an operational overview.

### Components

```text
Dashboard
├── PageHeader
├── OverviewCards
│   ├── Data Sources
│   ├── Databases
│   ├── Tables
│   └── Columns
│
├── SyncStatus
├── DataSourceHealth
├── MetadataGrowthChart
├── RecentActivity
└── QuickActions
```

### Primary actions

- Add data source
- Run synchronization
- Open catalog
- Search metadata
- Ask Pivota AI

---

# 18. Data Sources Page Architecture

The Data Sources page manages external database connections.

### Components

```text
Data Sources
├── PageHeader
├── ProviderFilter
├── EnvironmentFilter
├── Search
├── DataSourceTable / Cards
│   ├── Provider
│   ├── Name
│   ├── Environment
│   ├── Connection Status
│   ├── Last Sync
│   └── Actions
└── Add Data Source
```

### Data source wizard

```text
Step 1 — Provider
        ↓
Step 2 — Connection
        ↓
Step 3 — Credentials
        ↓
Step 4 — Security
        ↓
Step 5 — Test Connection
        ↓
Step 6 — Metadata Scope
        ↓
Step 7 — Review
        ↓
Step 8 — Register
```

---

# 19. Catalog Page Architecture

The Catalog is the structured metadata browser.

### Navigation hierarchy

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
```

### Components

```text
Catalog
├── CatalogSidebar
├── Breadcrumbs
├── Search
├── ObjectList
├── ObjectDetails
├── MetadataSummary
├── RelationshipPanel
└── SemanticDescription
```

---

# 20. Catalog Detail Architecture

A table detail page should provide:

```text
Table Header
├── Name
├── Schema
├── Database
├── Description
└── Status

Tabs
├── Overview
├── Columns
├── Relationships
├── Metadata
└── Activity
```

Column detail can show:

```text
Column Name
Data Type
Nullable
Primary Key
Foreign Key
Description
Business Terms
Synonyms
Related Columns
```

---

# 21. Search Page Architecture

The Search page is the primary metadata discovery interface.

### Components

```text
Search
├── SearchInput
├── Filters
├── SearchMode
│   ├── Keyword
│   ├── Semantic
│   └── Hybrid
├── Results
│   ├── ResultCard
│   ├── RelevanceScore
│   └── Breadcrumb
└── ResultDetails
```

### Example

```text
Query:
"customer revenue"

Results:

orders.total_amount
Customer order monetary amount

customer_revenue.monthly_revenue
Monthly customer revenue

transactions.amount
Transaction amount
```

---

# 22. Ask Pivota AI Page Architecture

Ask Pivota AI is a conversational metadata navigation interface.

### Layout

```text
┌─────────────────────────────────────────────┐
│ Ask Pivota AI                               │
├─────────────────────────────────────────────┤
│                                             │
│ User Question                               │
│                                             │
│ Pivota Response                             │
│                                             │
│ Sources / Metadata References               │
│                                             │
├─────────────────────────────────────────────┤
│ Ask about your data...                 Send │
└─────────────────────────────────────────────┘
```

### Response components

```text
AIResponse
├── Answer
├── Reasoning Summary
├── Relevant Objects
├── Relationship Context
├── Confidence
└── Open in Catalog
```

Do not expose hidden chain-of-thought. The UI should show concise, user-facing explanations and evidence.

---

# 23. Data Map Page Architecture

The Data Map visually represents relationships.

### Graph

```text
Database
   │
   ├── Schema
   │     │
   │     ├── customers
   │     │      │
   │     │      └── customer_id
   │     │
   │     └── orders
   │            │
   │            └── customer_id
   │
   └── products
```

### Controls

- Zoom
- Pan
- Search node
- Filter object type
- Filter provider
- Expand node
- Collapse node
- Show relationships
- Focus selected object
- Open catalog

---

# 24. Data Insights Page Architecture

The Data Insights page provides high-level observations about the metadata landscape.

### Components

```text
Data Insights
├── Metadata Coverage
├── Provider Distribution
├── Database Distribution
├── Table Distribution
├── Relationship Statistics
├── Documentation Coverage
└── Sync Health
```

Example insights:

```text
82% of tables have semantic descriptions.

14 tables have no discovered relationships.

3 data sources have failed their latest sync.
```

---

# 25. Alerts Page Architecture

The Alerts page presents important operational issues.

### Alert categories

```text
Connection
Synchronization
Security
Metadata
System
AI / Retrieval
```

### Alert lifecycle

```text
Detected
   ↓
Open
   ↓
Acknowledged
   ↓
Resolved
```

---

# 26. Audit Logs Page Architecture

Audit Logs provide traceability.

### Components

```text
Audit Logs
├── Date Filter
├── User Filter
├── Action Filter
├── Resource Filter
├── Search
└── AuditTable
```

Example:

```text
User
Action
Resource
Timestamp
IP
Status
```

---

# 27. Settings Architecture

Settings should be organized into sections.

```text
Settings
├── Profile
├── Organization
├── Users
├── Roles & Permissions
├── Security
├── AI Configuration
├── Integrations
└── Preferences
```

Only authorized users should see organization administration sections.

---

# 28. API Client Architecture

The frontend should not call APIs directly from arbitrary components.

Use a centralized API layer.

```text
Component
   ↓
Hook
   ↓
Feature API
   ↓
HTTP Client
   ↓
FastAPI
```

Example:

```text
useDataSources()
       ↓
dataSourceApi.getAll()
       ↓
apiClient.get("/data-sources")
       ↓
FastAPI
```

This provides consistency for:

- Authentication headers
- Error handling
- Request cancellation
- Retries
- Logging
- API versioning

---

# 29. Server State Management

TanStack Query can manage server state.

Use it for:

- Data sources
- Catalog metadata
- Search results
- Sync jobs
- Alerts
- Audit logs
- AI history where appropriate

Example conceptual flow:

```text
Component
   ↓
useQuery()
   ↓
API
   ↓
Cache
   ↓
Component
```

### Benefits

- Caching
- Refetching
- Loading states
- Error states
- Pagination
- Mutation handling
- Cache invalidation

---

# 30. Client State Management

Zustand can manage lightweight global UI state.

Good candidates:

```text
Sidebar state
Theme
Selected organization
Global filters
Data Map preferences
AI UI state
Modal state
```

Do not put all server data into global client state.

---

# 31. Form Architecture

Use React Hook Form + schema validation.

Example:

```text
DataSourceForm
       ↓
React Hook Form
       ↓
Zod Validation
       ↓
API Request
       ↓
FastAPI Validation
```

Validation should exist on both frontend and backend.

Frontend validation improves user experience.

Backend validation provides actual security.

---

# 32. Error Handling

All pages should support:

```text
Loading
Empty
Success
Error
Unauthorized
Forbidden
Not Found
```

Example:

```text
Loading
  ↓
Success ───────→ Empty
  │
  └─────────────→ Error
```

### Error presentation

Use:

- Inline validation
- Toast notifications
- Error banners
- Retry actions
- Dedicated error pages

Errors should be understandable to users.

---

# 33. Loading Architecture

Use skeleton loaders instead of blank screens where possible.

Example:

```text
Table Loading
┌───────────────────────────┐
│ █████████████             │
│ ███████                   │
│ ███████████████           │
│ █████████                 │
└───────────────────────────┘
```

For long operations such as synchronization:

```text
Metadata Sync
██████████████████░░░░ 78%

Tables discovered: 1,240
Columns discovered: 18,431
Current step: Indexing metadata
```

---

# 34. Data Source Connection UX

Connection testing should provide clear state transitions.

```text
Idle
 ↓
Testing
 ↓
 ┌───────────────┐
 ▼               ▼
Success         Failed
 │               │
 ▼               ▼
Connected       Error Details
```

The UI should never expose credentials in logs, errors, or toast messages.

---

# 35. Search UX

Search should feel like a data navigation tool rather than a generic search box.

### Suggested interaction

```text
Type question
      ↓
Search suggestions
      ↓
Execute
      ↓
Semantic + keyword retrieval
      ↓
Results
      ↓
Select object
      ↓
Catalog detail
```

Search suggestions can include:

```text
Where is customer revenue?
Find order information
Show customer-related tables
Find employee email columns
```

---

# 36. AI UX

Ask Pivota AI should make the retrieval process understandable.

A response can show:

```text
Answer
  ↓
Relevant metadata
  ↓
Why it matches
  ↓
Related objects
  ↓
Open in catalog
```

Example:

```text
I found customer revenue information primarily in:

orders.total_amount

Location:
Production → ecommerce → public → orders

Related:
customers.customer_id
orders.customer_id
```

---

# 37. Data Map UX

The Data Map should support progressive exploration.

```text
Initial View
     ↓
Select Database
     ↓
Expand Schema
     ↓
Select Table
     ↓
Show Columns
     ↓
Show Relationships
```

Avoid rendering thousands of nodes at once.

Use:

- Lazy expansion
- Filtering
- Search
- Focus mode
- Relationship limits

---

# 38. Accessibility

The frontend should follow practical accessibility principles.

### Requirements

- Keyboard navigation
- Visible focus states
- Semantic HTML
- Accessible labels
- Sufficient contrast
- Screen-reader-friendly controls
- Error messages associated with fields
- Reduced-motion support
- Accessible tables
- Accessible dialogs

Animations should respect:

```text
prefers-reduced-motion
```

---

# 39. Responsive Architecture

Primary target:

```text
Desktop
```

Secondary target:

```text
Tablet
```

The application should remain usable on smaller screens.

### Responsive behavior

```text
Desktop
Sidebar + Main Content

Tablet
Collapsed Sidebar + Main Content

Small Screen
Compact Navigation + Full-width Content
```

Data-heavy tables can use horizontal scrolling rather than destroying information density.

---

# 40. Performance Architecture

Performance priorities:

1. Fast initial load.
2. Lazy-load large pages.
3. Code split by route.
4. Cache API results.
5. Virtualize large tables.
6. Debounce search input.
7. Paginate catalog results.
8. Avoid rendering huge graph datasets.
9. Optimize charts.
10. Compress static assets.

### Example

```text
Application
   ↓
Route Lazy Loading
   ↓
Feature Bundle
   ↓
Page
```

---

# 41. Security on the Frontend

Frontend security measures include:

- Never store database passwords in local storage.
- Never expose secret values in UI logs.
- Use HTTPS.
- Handle authentication tokens securely.
- Validate permissions on the backend.
- Sanitize rendered content.
- Avoid unsafe HTML rendering.
- Protect sensitive routes.
- Clear session state on logout.
- Avoid exposing internal API errors.

Important:

> Frontend permissions are for UX. Backend permissions are the actual security boundary.

---

# 42. Frontend and Backend Contract

The frontend should consume typed API contracts.

```text
FastAPI
   ↓
OpenAPI
   ↓
Generated / Shared Types
   ↓
TypeScript
   ↓
React
```

Example:

```text
DataSource
{
  id: string
  name: string
  provider: string
  status: DataSourceStatus
  environment: string
  lastSyncAt: string
}
```

This reduces frontend/backend mismatch.

---

# 43. Frontend Data Flow

## Data Source Flow

```text
User
 ↓
Data Source Form
 ↓
Validation
 ↓
API Mutation
 ↓
FastAPI
 ↓
Data Source Created
 ↓
Query Cache Invalidated
 ↓
Data Source List Updated
```

## Catalog Flow

```text
Catalog Page
 ↓
Query Catalog API
 ↓
TanStack Query
 ↓
Render Tree
 ↓
Select Table
 ↓
Query Table Details
 ↓
Render Metadata
```

## Search Flow

```text
Search Input
 ↓
Debounce
 ↓
Search API
 ↓
Hybrid Retrieval
 ↓
Results
 ↓
Select Result
 ↓
Catalog Detail
```

---

# 44. Frontend AI Streaming

If the backend supports streaming AI responses:

```text
User
 ↓
Ask Pivota
 ↓
POST /ai/query
 ↓
Streaming Response
 ↓
Token / Event Stream
 ↓
React State Update
 ↓
Progressive Answer
```

UI:

```text
Pivota AI

I found several relevant data sources...
▌
```

The cursor disappears when streaming completes.

---

# 45. Notifications Architecture

Global notifications can handle:

```text
Success
Warning
Error
Info
```

Examples:

```text
✓ Data source connected successfully.

✓ Metadata synchronization completed.

⚠ 2 tables could not be indexed.

✕ Connection test failed.
```

Long-running operations should additionally have persistent status in the relevant page.

---

# 46. Component Reusability

Common components should be reusable across features.

Example:

```text
DataObjectBadge
StatusBadge
ProviderIcon
MetadataBreadcrumb
RelationshipBadge
ConfidenceIndicator
SyncProgress
EmptyState
SearchInput
FilterBar
DataTable
ConfirmDialog
```

This prevents duplicate UI implementations.

---

# 47. Type Architecture

Types should be grouped by domain.

```text
types/
├── auth.ts
├── organization.ts
├── data-source.ts
├── catalog.ts
├── relationship.ts
├── sync.ts
├── search.ts
├── ai.ts
├── alert.ts
└── audit.ts
```

Avoid using `any` for core domain objects.

---

# 48. Testing Architecture

## Unit Tests

Test:

- Utility functions
- Hooks
- State logic
- Validation
- Data transformation

## Component Tests

Test:

- Forms
- Tables
- Dialogs
- Search
- Catalog navigation
- AI components

## E2E Tests

Test complete workflows:

```text
Login
 ↓
Create Data Source
 ↓
Test Connection
 ↓
Run Sync
 ↓
Open Catalog
 ↓
Search Metadata
 ↓
Ask Pivota AI
 ↓
Open Result
```

---

# 49. Frontend Environment Configuration

Use environment variables for deployment-specific configuration.

Example:

```text
VITE_API_BASE_URL
VITE_APP_ENV
VITE_ENABLE_AI
VITE_ENABLE_DATA_MAP
```

Never put secrets into Vite environment variables.

Anything exposed through a frontend build should be considered public.

---

# 50. Build and Deployment

Development:

```text
npm install
npm run dev
```

Production:

```text
npm run build
```

The generated frontend can be deployed through:

- CDN
- Vercel
- Static hosting
- Nginx
- Cloud storage + CDN

The frontend should communicate with the production FastAPI API through the configured API base URL.

---

# 51. Frontend CI/CD

Recommended pipeline:

```text
Git Push
   ↓
Install Dependencies
   ↓
Lint
   ↓
Type Check
   ↓
Unit Tests
   ↓
Build
   ↓
E2E Tests
   ↓
Deploy
```

Pull requests should run at least:

```text
Lint
Type Check
Tests
Build
```

---

# 52. Frontend Observability

Frontend monitoring should capture:

- JavaScript errors
- API errors
- Route failures
- Performance metrics
- Failed interactions
- Slow API calls

Avoid sending:

- Passwords
- Credentials
- Sensitive database connection details
- Private user data

---

# 53. State Ownership Rules

A clear state ownership model should be followed.

```text
Server Data
    → TanStack Query

Global UI State
    → Zustand

Local Form State
    → React Hook Form

Component-only State
    → useState

URL State
    → Router / query parameters
```

This prevents unnecessary complexity.

---

# 54. Page Development Order

Recommended frontend implementation order:

### Phase 1 — Foundation

```text
Project Setup
Design System
Routing
App Shell
Authentication
API Client
```

### Phase 2 — Core Pages

```text
Dashboard
Data Sources
Catalog
```

### Phase 3 — Discovery

```text
Search
Data Map
```

### Phase 4 — Intelligence

```text
Ask Pivota AI
Data Insights
```

### Phase 5 — Administration

```text
Alerts
Audit Logs
Settings
Users
Roles
```

### Phase 6 — Production Quality

```text
Accessibility
Responsive Design
Performance
Testing
Error Handling
Observability
```

---

# 55. Complete Frontend Architecture

```text
                           USER
                             │
                             ▼
                  ┌────────────────────┐
                  │    React + Vite    │
                  │    Pivota Web App  │
                  └─────────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌─────────────┐
       │  Routes  │   │  Layout  │   │ Design      │
       │          │   │          │   │ System      │
       └────┬─────┘   └──────────┘   └─────────────┘
            │
            ▼
      ┌──────────────────────────────────────────┐
      │                FEATURES                  │
      │                                          │
      │ Dashboard | Sources | Catalog | Search   │
      │ Data Map | Ask AI | Insights | Alerts   │
      │ Audit Logs | Settings                   │
      └──────────────────┬───────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       ┌──────────────┐      ┌──────────────┐
       │ TanStack     │      │ Zustand      │
       │ Query        │      │ UI State     │
       └──────┬───────┘      └──────────────┘
              │
              ▼
       ┌──────────────────┐
       │ Feature Hooks    │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │ API Service      │
       │ / HTTP Client    │
       └────────┬─────────┘
                │ HTTPS
                ▼
       ┌──────────────────┐
       │ FastAPI Backend  │
       └──────────────────┘
```

---

# 56. Final Frontend Architecture Principle

The Pivota frontend should follow this principle:

```text
SIMPLE INTERFACE
       ↓
CLEAR NAVIGATION
       ↓
REUSABLE COMPONENTS
       ↓
DOMAIN-BASED FEATURES
       ↓
TYPED API CONTRACTS
       ↓
RELIABLE STATE MANAGEMENT
       ↓
FAST DATA DISCOVERY
```

The frontend should make a complex distributed data environment feel simple.

A user should not need to understand the internal architecture of PostgreSQL, MySQL, vector databases, embeddings, retrieval pipelines, or LLM orchestration to use Pivota.

They should simply be able to:

```text
Connect
   ↓
Explore
   ↓
Search
   ↓
Ask
   ↓
Understand
   ↓
Navigate
```

> **Pivota's frontend is the visual navigation layer that turns an organization's complex data infrastructure into a simple, intelligent data discovery experience.**

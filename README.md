# Pivota Data Navigator

> **Tagline:** *Find where your data lives.*

Pivota is an AI-powered metadata navigation platform that connects to multiple database systems, extracts schema structures and relationship definitions (without importing actual business records), and builds a centralized metadata catalog. It leverages hybrid retrieval combined with LLMs to let users discover data and answer natural-language questions about where their data lives.

---

## 🚀 Project Overview & Architecture

Pivota is designed with security and scalability at its core, isolating organization metadata and preventing unauthorized access to external databases. The system architecture is organized into four main layers:

```text
┌──────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│ React + Vite + TypeScript (Dashboard, Sources, Wizard, Shell)│
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS / REST (Axios + Auth Interceptors)
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     API / APPLICATION LAYER                  │
│ FastAPI (Auth, Dashboard Stats, Sources CRUD, Sync Jobs)     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
┌────────────────────┐ ┌──────────────┐ ┌───────────────────┐
│ METADATA ENGINE    │ │ SERVICES     │ │ SECURITY & AUDIT  │
│ Discovery Service  │ │ Dashboard    │ │ Secret Manager    │
│ Adapter Registry   │ │ Activity Log │ │ Audit Logging     │
└─────────┬──────────┘ └───────┬──────┘ └─────────┬─────────┘
          │                    │                  │
          ▼                    ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                        │
│ PostgreSQL App DB (SQLAlchemy Models: User, Org, Source, etc)│
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 EXTERNAL DATA SOURCE LAYER                  │
│ PostgreSQL Adapter | MySQL Adapter | MongoDB Adapter         │
└───────────────────────────────┬──────────────────────────────┘
```

For in-depth explanations, refer to the detailed architecture documents:
* 📁 [System Architecture](file:///c:/download/pivotaAI/documentation/Pivota_System_Architecture.md)
* 📁 [Backend Architecture](file:///c:/download/pivotaAI/documentation/Pivota_Backend_Architecture.md)
* 📁 [Frontend Architecture](file:///c:/download/pivotaAI/documentation/Pivota_Frontend_Architecture.md)

---

## 🛠️ Technology Stack

### Backend
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
* **Database & ORM:** [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
* **Settings & Validation:** [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings`
* **Security & Auth:** [PyJWT](https://pyjwt.readthedocs.io/) (JSON Web Tokens), [Bcrypt](https://github.com/pyca/bcrypt/) (password hashing), [Cryptography](https://cryptography.io/) (Fernet AES encryption for credentials)
* **Web Server:** [Uvicorn](https://www.uvicorn.org/)

### Frontend
* **Build Tool & Runtime:** [Vite](https://vite.dev/) + React + TypeScript
* **State Management:** [Zustand](https://github.com/pmndrs/zustand)
* **Data Fetching & Cache:** [React Query / TanStack Query v5](https://tanstack.com/query/latest)
* **Routing:** [React Router v6](https://reactrouter.com/)
* **HTTP Client:** [Axios](https://axios-http.com/) (configured with automatic Bearer Token injection and Token Refresh interceptors)
* **Styling:** Premium Vanilla CSS featuring a glassmorphic design system and dark theme tokens.
* **Icons:** [Lucide React](https://lucide.dev/)

---

## ✨ Features Completed So Far

### 1. Robust Multi-Tenant Authentication & Authorization
* **Registration & Onboarding:** Registration of new Organizations along with the primary Admin account.
* **JWT Access & Refresh Token Flow:** Sign-ins return a short-lived access token and a long-lived refresh token.
* **Token Refresh Interceptor:** The frontend Axios client interceptor automatically intercepts `401 Unauthorized` responses and silently requests a new access token via `/auth/refresh` using the stored refresh token.
* **Protected Routing:** Page routes are wrapped in an auth-check container that verifies user authentication status with the backend (`/auth/me`).

### 2. Interactive Control Dashboard
* **Aggregated Stats:** Displays live summaries of connected data sources, database count, schemas, tables, and columns tracked across the organization.
* **Health Tracker:** Shows connection status (`connected` / `error`), environments (`production` / `staging` / `development`), and connection latencies.
* **Live Audit Activity Feed:** Renders recent administrative actions (login, signup, data source creation, connection tests) mapped with user names and exact timestamps.

### 3. Comprehensive Data Sources Administration
* **Multi-Step Connection Wizard:** An interactive sidebar component (`AddDataSourceWizard.tsx`) that leads users through selecting a database provider, inputting parameters (host, port, auth), setting custom configuration options, testing connections, and final registration.
* **URI Parsing:** Backend support to parse standard connection strings (e.g., `postgresql://user:pass@host:port/db`) and merge connection details automatically.
* **Active Status Toggling:** Allows users to explicitly connect or disconnect data sources.
* **Metadata Synchronization & Discovery:** A service to fetch metadata statistics (databases, schemas, tables, and columns) from the remote host and persist counts to the dashboard.

### 4. Gated Connector & Adapter System
* **Lazy-Loaded Adapter Registry:** Supports dynamic loading of database adapters based on selected provider names.
* **Capabilities Registry:** Reads a capability profile (`capabilities.json`) that dictates what features the adapter supports (e.g., whether the database supports SQL, nested schemas, or relational constraints).
* **Database Adapters:**
  * **PostgreSQL:** Extracts schemas, tables, columns, indexes, primary keys, and foreign keys.
  * **MySQL:** Custom queries to extract databases, tables, columns, constraints, and tablespace details.
  * **MongoDB:** Collection discovery, index lists, and document structure sampling to infer schema keys.

### 5. Backend Cryptography & Audit Logs
* **Secret Manager:** Credentials are encrypted via Fernet AES-256 before storage in Pivota's PostgreSQL instance. Clear text passwords are never stored.
* **Central Audit Service:** Standardized logging helper that writes JSON details of every operational event to an `audit_logs` table for compliance.

---

## 📊 Feature Matrix & Status

| Screen / Feature | Frontend File Path | Backend Endpoint | Status |
| :--- | :--- | :--- | :--- |
| **User Sign-up** | [`SignupPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/SignupPage.tsx) | `/api/v1/auth/signup` | ✅ **Fully Implemented** |
| **User Login** | [`LoginPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/LoginPage.tsx) | `/api/v1/auth/login` | ✅ **Fully Implemented** |
| **Interactive Dashboard** | [`DashboardPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/dashboard/pages/DashboardPage.tsx) | `/api/v1/dashboard` | ✅ **Fully Implemented** |
| **Data Source List** | [`DataSourcesPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/data-sources/pages/DataSourcesPage.tsx) | `/api/v1/data-sources` | ✅ **Fully Implemented** |
| **Add Data Source Wizard** | [`AddDataSourceWizard.tsx`](file:///c:/download/pivotaAI/frontend/src/features/data-sources/components/AddDataSourceWizard.tsx) | `/api/v1/data-sources/test-connection` | ✅ **Fully Implemented** |
| **Connection Testing** | Inline in List & Wizard | `/api/v1/data-sources/{id}/test` | ✅ **Fully Implemented** |
| **Metadata Discovery** | Sync button in List | `/api/v1/data-sources/{id}/discover` | ✅ **Fully Implemented** |
| **Data Map** | [`DataMapPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/data-map/pages/DataMapPage.tsx) | `/api/v1/insights` (Stub) | ⏳ **Coming Soon (Skeleton)** |
| **Catalog** | [`CatalogPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/catalog/pages/CatalogPage.tsx) | `/api/v1/catalog` (Stub) | ⏳ **Coming Soon (Skeleton)** |
| **Search** | [`SearchPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/search/pages/SearchPage.tsx) | `/api/v1/search` (Stub) | ⏳ **Coming Soon (Skeleton)** |
| **Ask Pivota AI** | [`AskAIPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/ask-ai/pages/AskAIPage.tsx) | `/api/v1/ai` (Stub) | ⏳ **Coming Soon (Skeleton)** |
| **Alerts** | [`AlertsPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/alerts/pages/AlertsPage.tsx) | `/api/v1/alerts` (Stub) | ⏳ **Coming Soon (Skeleton)** |
| **Audit Logs Page** | [`AuditLogsPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/audit-logs/pages/AuditLogsPage.tsx) | `/api/v1/audit-logs` (Stub) | ⏳ **Coming Soon (Skeleton)** *(Backend Logging Active)* |
| **Settings** | [`SettingsPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/settings/pages/SettingsPage.tsx) | `/api/v1/settings` (Stub) | ⏳ **Coming Soon (Skeleton)** |

---

## 🗂️ Project Directory Structure

```text
pivotaAI/
├── backend/
│   ├── app/
│   │   ├── adapters/                  # Connection Drivers & Capability Profiles
│   │   │   ├── mongodb/               # MongoDB schema-extraction adapter
│   │   │   ├── mysql/                 # MySQL metadata-extraction adapter
│   │   │   ├── postgresql/            # PostgreSQL metadata-extraction adapter
│   │   │   ├── base.py                # Abstract Base Adapter Class
│   │   │   ├── capabilities.json      # JSON capabilities file for adapters
│   │   │   └── registry.py            # Lazy-loaded adapter registry
│   │   ├── api/
│   │   │   ├── v1/                    # API Endpoints
│   │   │   │   ├── auth.py            # User Auth & Organization signup/login
│   │   │   │   ├── dashboard.py       # Metrics, activity logs & health
│   │   │   │   └── data_sources.py    # Database connection management
│   │   │   └── router.py              # Aggregated API routers
│   │   ├── core/                      # Global Configurations
│   │   │   ├── exceptions.py          # Unified exception handlers
│   │   │   ├── security.py            # AES & Bcrypt security handlers
│   │   │   └── uri_parser.py          # DB connection string parser
│   │   ├── db/                        # Database Sessions
│   │   │   ├── base.py                # Engine & session configurations
│   │   │   └── session.py             # get_db Dependency injection helper
│   │   ├── models/                    # SQLAlchemy Declarative Models
│   │   │   ├── audit_log.py           # Audit events schema
│   │   │   ├── data_source.py         # Registered source schemas
│   │   │   ├── organization.py        # Organization profile schemas
│   │   │   ├── secret.py              # Encrypted password store
│   │   │   └── user.py                # User profiles schemas
│   │   ├── schemas/                   # Pydantic Request & Response schemas
│   │   ├── services/                  # Business Logic Orchestration
│   │   │   ├── audit_service.py       # Logs system interactions
│   │   │   ├── auth_service.py        # Validates logins, issues JWTs
│   │   │   ├── dashboard_service.py   # Computes dashboard analytics
│   │   │   ├── data_source_service.py # Resolves connections & triggers syncs
│   │   │   └── secret_manager.py      # Encrypts passwords for storage
│   │   ├── config.py                  # Pydantic Settings Manager
│   │   ├── dependencies.py            # Token validation & Auth dependency
│   │   └── main.py                    # Application Entry Point & Lifespan Hooks
│   ├── pyproject.toml                 # Backend dependencies setup
│   └── README.md                      # Basic backend guide
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── layout/                # Global Shell, Navigation Sidebar & Topbar
│   │   ├── features/                  # Domain Modules
│   │   │   ├── auth/                  # Login & Signup screens & API client
│   │   │   ├── dashboard/             # Core Control Panel
│   │   │   ├── data-sources/          # Configuration grids & wizard dialogs
│   │   │   └── ...                    # Coming soon module directories
│   │   ├── services/
│   │   │   └── api/                   # Centralized Axios Client
│   │   ├── stores/                    # Zustand Authentication store
│   │   ├── App.tsx                    # Protected Routes & main layout routing
│   │   ├── index.css                  # Custom Vanilla CSS tokens and properties
│   │   └── main.tsx                   # React Entry Point
│   ├── package.json                   # Web Dependencies
│   └── vite.config.ts                 # React development bundle configuration
└── documentation/                     # Technical Architecture Overviews
```

---

## ⚙️ Running Locally

### Prerequisites
* Python 3.10+
* Node.js v18+
* A running PostgreSQL instance (or update the backend connection string to point elsewhere)

### 1. Setting up the Backend
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install package dependencies in editable mode:
   ```bash
   pip install -e .
   ```
4. Copy the environment template and customize connection parameters:
   ```bash
   copy .env.example .env   # On Windows
   cp .env.example .env     # On macOS/Linux
   ```
   *Make sure `DATABASE_URL` is set to your local PostgreSQL instance.*
5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *(On startup, FastAPI will automatically generate all necessary database tables in the configured database).*

### 2. Setting up the Frontend
1. Navigate to the `frontend/` directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the local development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to the local server address (usually `http://localhost:5173`).

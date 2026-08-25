# Pivota Data Navigator & Security Engine

> **Tagline:** *Find where your data lives. Securely.*

Pivota is an enterprise-grade, AI-powered metadata navigation platform that connects to multiple database systems, extracts schema structures and relationship definitions (without importing actual business records), and builds a centralized metadata catalog. It leverages hybrid retrieval combined with LLMs to let users discover data and answer natural-language questions about where their data lives.

This repository features the complete Pivota navigation platform, integrated with an isolated **2FA Authentication service** and a secure **IAM (Identity and Access Management)** policy system for delegated employee access.

---

## 🚀 Project Overview & Architecture

Pivota is designed with tenant isolation and security at its core. The ecosystem is split into four separate local services running concurrently to enforce security boundaries:

```text
       ┌────────────────────────┐         ┌────────────────────────┐
       │     PIVOTA FRONTEND    │         │  AUTH PIVOTA FRONTEND  │
       │    (localhost:3000)    │         │    (localhost:3001)    │
       └───────────┬────────────┘         └───────────┬────────────
                   │                                  │
                   │ HTTP / REST                      │ HTTP / REST
                   ▼                                  ▼
       ┌────────────────────────┐         ┌────────────────────────┐
       │     PIVOTA BACKEND     │◄────────│   AUTH PIVOTA SERVICE  │
       │    (localhost:8080)    │  Shared │    (localhost:8001)    │
       └───────────┬────────────┘  DB     └───────────┬────────────┘
                   │                                  │
                   └─────────────────┬────────────────┘
                                     ▼
                        ┌────────────────────────┐
                        │   POSTGRESQL APP DB    │
                        │        (pivota)        │
                        └────────────────────────┘
```

1. **Pivota Frontend** (`localhost:3000`): The main React application where administrators configure database connections, browse the catalog, view data maps, and manage organization settings.
2. **Pivota Backend** (`localhost:8080`): FastAPI service powering catalog search, adapter metadata discovery, audit logs, and connection wizard logic.
3. **Auth Pivota Frontend** (`localhost:3001`): vite-based React frontend for the isolated 2FA portal.
4. **Auth Pivota Service** (`localhost:8001`): Isolated FastAPI service hosting the TOTP authentication engine and Gmail verification OTP service.

---

## 🛠️ Technology Stack

### Backend Services
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
* **Database & ORM:** [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
* **Security & JWT:** [PyJWT](https://pyjwt.readthedocs.io/) & [python-jose](https://github.com/mpdavis/python-jose)
* **Encryption:** Fernet symmetric encryption (via [Cryptography](https://cryptography.io/)) for database connection credentials.
* **OTP Engine:** HMAC-SHA256 based TOTP tokens rotated every 30 seconds.
* **Email Client:** Python SMTP client using SSL/TLS for secure Gmail OTP and invitation delivery.

### Frontend Client Web Apps
* **Build Tool & Runtime:** [Vite](https://vite.dev/) + React + TypeScript
* **State Management:** [Zustand](https://github.com/pmndrs/zustand)
* **Data Fetching:** [React Query / TanStack Query v5](https://tanstack.com/query/latest)
* **Routing:** [React Router v6](https://reactrouter.com/)
* **HTTP Client:** [Axios](https://axios-http.com/) (configured with automatic Bearer Token injection and Token Refresh interceptors)
* **Styling:** Premium Vanilla CSS featuring a glassmorphic design system and dark theme tokens.

---

## ✨ Features Completed

### 1. Two-Factor Authentication (2FA) System
* **Gmail Email Verification:** Real-time OTP (One-Time Password) generation and delivery to the user's Gmail upon registration request.
* **TOTP Timing Wheel:** Once verified, users get a rotating 6-digit TOTP key updated every 30s. Visualized using a custom SVG circular countdown wheel.
* **Gated Admin Access:** Admin logins are strictly gated by the 2FA screen.

### 2. IAM User Account & Access Policy Management
* **Delegated Permissions:** Admins can invite employees with specific roles (e.g. `Data Analyst`, `Data Engineer`, `Viewer`, `Admin`).
* **Granular Policy Model:** Permissions define access to catalog objects, data maps, query tool previews, database connections, and policy settings.
* **Automated Gmail Invites:** Admin invitations trigger a temporary random credential email to the employee.
* **First-Time Password Reset**: Employee logins require a mandatory password reset flow to activate accounts.
* **2FA Exemption**: Employee/contractor accounts bypass 2FA, enforcing credentials-only login.
* **Dynamic Menu Visibility**: Sidebar menu options (like "Data Sources") are filtered automatically based on the user's IAM policy permissions.

### 3. Connection Wizard & Metadata Adapters
* **Multi-Step Connection Wizard:** Add, test, and register external database connections (PostgreSQL, MySQL, MongoDB).
* **Metadata Sync Jobs**: Extract schema structures (databases, schemas, tables, columns, indexes, relationships) without importing actual records.
* **Gated Protocol Schemes**: Restricts protocols to `postgresql://`, `mysql://`, `mongodb://`, `mongodb+srv://`. All other protocols (like `file://`, `ftp://`) are strictly blocked for security.

---

## 📊 Feature Matrix & Status

| Screen / Feature | Frontend Location | Backend Endpoint | Status |
| :--- | :--- | :--- | :--- |
| **Sign-up (Admin)** | [`SignupPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/SignupPage.tsx) | `/api/v1/auth/signup` | ✅ **Fully Implemented** |
| **Login (Admin)** | [`LoginPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/LoginPage.tsx) | `/api/v1/auth/login` | ✅ **Fully Implemented** |
| **Verify 2FA (Admin)** | [`Verify2FAPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/Verify2FAPage.tsx) | `/api/v1/auth/verify-2fa` | ✅ **Fully Implemented** |
| **IAM User Login** | [`IAMLoginPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/IAMLoginPage.tsx) | `/api/v1/auth/iam/login` | ✅ **Fully Implemented** |
| **Password Reset (First Login)** | [`IAMChangePasswordPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/auth/pages/IAMChangePasswordPage.tsx) | `/api/v1/auth/iam/reset-password` | ✅ **Fully Implemented** |
| **IAM Admin Panel** | [`IAMManagement.tsx`](file:///c:/download/pivotaAI/frontend/src/features/settings/components/IAMManagement.tsx) | `/api/v1/auth/iam/users` | ✅ **Fully Implemented** |
| **Connection Wizard** | [`AddDataSourceWizard.tsx`](file:///c:/download/pivotaAI/frontend/src/features/data-sources/components/AddDataSourceWizard.tsx) | `/api/v1/data-sources` | ✅ **Fully Implemented** |
| **Interactive Dashboard** | [`DashboardPage.tsx`](file:///c:/download/pivotaAI/frontend/src/features/dashboard/pages/DashboardPage.tsx) | `/api/v1/dashboard` | ✅ **Fully Implemented** |

---

## ⚙️ Running Locally

### 1. Setting up the App Database (PostgreSQL)
Pivota requires a local PostgreSQL instance running.
1. Create a database named `pivota`.
2. Ensure you have the database credentials ready (URL example: `postgresql://postgres:password@localhost:5432/pivota`).

### 2. Configure Environment Files (`.env`)
You must configure the SMTP credentials in `.env` files to send verification codes and employee invitations:

**Pivota Backend Env (`backend/.env`):**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/pivota
TOTP_SECRET_KEY=pivota-totp-shared-secret-key-2024
SMTP_EMAIL=your-gmail@gmail.com
SMTP_APP_PASSWORD=your-gmail-app-password
```

**Auth Service Env (`auth-service/.env`):**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/pivota
TOTP_SECRET_KEY=pivota-totp-shared-secret-key-2024
SMTP_EMAIL=your-gmail@gmail.com
SMTP_APP_PASSWORD=your-gmail-app-password
```

---

### 3. Launch the Services

Start all 4 services using separate terminal sessions:

#### Terminal 1: Pivota Backend (API)
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS/Linux
pip install -e .
python -m scripts.recreate_db  # Clears and registers the database schema
uvicorn app.main:app --port 8080 --reload
```

#### Terminal 2: Pivota Frontend (UI)
```bash
cd frontend
npm install
npm run dev
```

#### Terminal 3: Auth Pivota Backend (API)
```bash
cd auth-service
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

#### Terminal 4: Auth Pivota Frontend (UI)
```bash
cd auth-frontend
npm install
npm run dev
```

---

## 🧪 Running Verification Tests
To run the complete test suite (unit and integration tests) on the backend:
```bash
cd backend
.\venv\Scripts\pytest
```
All 29 tests (covering connection adapters, metadata crawlers, security protocols, 2FA, and IAM access controls) should pass.

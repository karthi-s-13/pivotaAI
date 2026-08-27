import React, { useState, useEffect } from 'react';

// Minimal Helper for Sprite SVG icons
const Icon: React.FC<{ name: string; className?: string; style?: React.CSSProperties }> = ({ name, className = 'icon-svg', style }) => {
  return (
    <svg className={className} style={style}>
      <use xlinkHref={`#icon-${name}`} />
    </svg>
  );
};

// System Workflow steps data (highly detailed with backend workflow descriptions)
interface WorkflowStepData {
  title: string;
  desc: string;
}

const workflowSteps: Record<number, WorkflowStepData> = {
  1: {
    title: "Step 1: Connection Configuration Wizard",
    desc: "The Organization Administrator initiates the metadata connection workflow. Using a secure multi-step wizard, the administrator inputs database parameters (Database Host URL, Network Port, Database Username, Password, and TLS certificate requirements). Before writing to the App DB, the backend intercepts the credentials and uses <strong>Fernet symmetric encryption</strong> (AES-128 in CBC mode) to secure the connection details, ensuring passwords are never stored in plaintext. Key rotation parameters are set per organization."
  },
  2: {
    title: "Step 2: SSRF Prevention & Outbound Security Gateway",
    desc: "Outbound network requests are high-risk. Before the system tests or registers the connection, a network validation proxy inspects the target address. The wizard restricts connection schemes strictly to database protocols (<code>postgresql://</code>, <code>mysql://</code>, <code>mongodb://</code>, <code>mongodb+srv://</code>). Non-database protocols (like <code>file://</code>, <code>ftp://</code>, <code>http://</code>) are blocked. The proxy also blocks private network ranges (such as localhost 127.0.0.1, private class A/B/C subnets, and local link IPs) to stop Server-Side Request Forgery (SSRF)."
  },
  3: {
    title: "Step 3: Non-Intrusive Metadata Crawling Sync",
    desc: "The database adapter initiates an asynchronous background metadata crawling job via FastAPI background tasks. The crawler inspects system catalogs (such as <code>information_schema</code> in PostgreSQL/MySQL or system collections in MongoDB) to retrieve schema structures. It maps catalog names, schemas, table names, view definitions, index keys, and foreign key constraints. <strong>Crucially, Pivota has a Zero-Data Read Policy: no business records, customer columns, or transaction records are ever read, extracted, or imported.</strong> Only structural data is synced, preserving business record secrecy."
  },
  4: {
    title: "Step 4: Semantic Vector Space Indexing",
    desc: "The discovered metadata is formatted into semantic description sentences (e.g. <em>'Table payments inside schema core holds column txn_amount representing monetary value of orders'</em>). The system passes these descriptions to a local <strong>SentenceTransformer</strong> model (all-MiniLM-L6-v2) to generate 384-dimensional dense vectors. These vectors are indexed into a PostgreSQL database with the <strong>pgvector</strong> extension. Every vector record is tagged with the tenant's <code>organization_id</code> to enforce data boundaries during vector index queries."
  },
  5: {
    title: "Step 5: Ask Pivota AI Navigation Explorer",
    desc: "When a user asks a natural language question (e.g., <em>'Where is customer billing address stored?'</em>), the retrieval engine executes a hybrid query. It combines exact keyword token matching and semantic vector searches, filtering results by the user's <code>organization_id</code>. The top matching database structures are sent to the LLM as reference context. The LLM then generates a grounded explanation of the data locations with clickable links to the catalog, avoiding hallucination and cross-tenant leaks."
  }
};

// Tech Stack Data
interface TechData {
  name: string;
  category: string;
  icon: string;
  why: string;
  details: string;
}

const techStackData: Record<string, TechData> = {
  fastapi: {
    name: "FastAPI",
    category: "Backend Core",
    icon: "code",
    why: "High-performance Python web API framework for routing.",
    details: "FastAPI handles asynchronous request routing, automatically generates OpenAPI documentation, and uses Pydantic to validate data types, making it ideal for coordinating metadata syncs and AI searches. Extensible with dependency injection modules."
  },
  sqlalchemy: {
    name: "SQLAlchemy 2.0",
    category: "Backend Core",
    icon: "database",
    why: "SQL database toolkit and Object Relational Mapper (ORM).",
    details: "SQLAlchemy manages transactional queries to our PostgreSQL application database, prevents SQL injection vulnerability vectors, and implements type-safe multi-tenant filters. Features modern 2.0 style async query executions."
  },
  fernet: {
    name: "Fernet Crypto Engine",
    category: "Backend Core",
    icon: "lock",
    why: "Symmetric key encryption standard for credentials.",
    details: "Fernet uses AES-128 in CBC mode with HMAC-SHA256 signatures to encrypt external database passwords and connection hosts at rest. Decryption keys are stored in environment files, ensuring credentials are secure against DB leaks."
  },
  jwt_totp: {
    name: "PyJWT & PyTOTP",
    category: "Backend Core",
    icon: "shield",
    why: "Admin session authorization and 2FA TOTP verification.",
    details: "PyJWT manages secure session tokens for administrators. PyTOTP computes rotating 2FA email codes using HMAC-SHA256, updated every 30 seconds for verification. Defends administrative operations."
  },
  react_ts: {
    name: "React & TypeScript",
    category: "Frontend Client",
    icon: "code",
    why: "Type-safe user interface client framework.",
    details: "TypeScript prevents runtime type mismatches during state updates. React coordinates the multi-step connection wizard, interactive data maps, and user permission panels. Highly modular components."
  },
  vite: {
    name: "Vite Bundler",
    category: "Frontend Client",
    icon: "cpu",
    why: "Ultra-fast frontend build engine.",
    details: "Serves development files with instant Hot Module Replacement (HMR) and compiles frontend code into minimized static JS and CSS chunks for production. Highly extensible with rollup plugins."
  },
  zustand: {
    name: "Zustand",
    category: "Frontend Client",
    icon: "code",
    why: "Minimalist client-side state management.",
    details: "Manages session state, caches active connection wizard inputs, and controls sidebar menu visibility based on user permission rules. Small footprint, bypasses React Context overhead."
  },
  tanstack: {
    name: "TanStack Query v5",
    category: "Frontend Client",
    icon: "search",
    why: "Server state cache and sync controller.",
    details: "Handles API caching, auto-refreshes connection wizard statuses, and keeps the metadata sync job dashboard updated in real-time. Manages loading and mutation states automatically."
  },
  postgresql: {
    name: "PostgreSQL",
    category: "Data & AI",
    icon: "database",
    why: "Primary relational application database.",
    details: "Stores organization profiles, user credentials, audit logs, and discovered catalog metadata schemas with standard relational foreign key constraints. Highly reliable ACID transactional storage."
  },
  pgvector: {
    name: "pgvector",
    category: "Data & AI",
    icon: "search",
    why: "Vector database extension for PostgreSQL.",
    details: "Indexes semantic embeddings of database table definitions and schema fields. Allows multi-tenant similarity vector searches filtered by organization ID, keeping all indexes in a unified store."
  },
  transformers: {
    name: "SentenceTransformers",
    category: "Data & AI",
    icon: "cpu",
    why: "NLP embedding model for text representations.",
    details: "Converts text schema definitions and concept tags into dense vector representations. Allows semantic search matching (like linking 'income' to 'revenue'). Offline execution ensures no data leaks."
  },
  llm: {
    name: "OpenAI / LLM Adapters",
    category: "Data & AI",
    icon: "user",
    why: "Natural language query evaluation engine.",
    details: "Parses queries into filters, evaluates catalog schemas to match columns, and generates explanations mapping data paths without exposing actual database rows to LLM prompts."
  }
};

export default function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [workflowStep, setWorkflowStep] = useState(1);
  const [selectedTech, setSelectedTech] = useState<string | null>("fastapi");
  const totalSlides = 9;

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'Space' || e.key === ' ') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        prevSlide();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentSlide]);

  const nextSlide = () => {
    if (currentSlide < totalSlides - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  // Progress Bar percentage
  const progressPercent = ((currentSlide + 1) / totalSlides) * 100;

  return (
    <div className="presentation-container">
      
      {/* Sprite definitions sheet */}
      <svg style={{ display: 'none' }}>
        <symbol id="icon-arrow-left" viewBox="0 0 24 24">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </symbol>
        <symbol id="icon-arrow-right" viewBox="0 0 24 24">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <polyline points="12 5 19 12 12 19"></polyline>
        </symbol>
        <symbol id="icon-database" viewBox="0 0 24 24">
          <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
          <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path>
        </symbol>
        <symbol id="icon-shield" viewBox="0 0 24 24">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        </symbol>
        <symbol id="icon-cpu" viewBox="0 0 24 24">
          <rect x="4" y="4" width="16" height="16" rx="2"></rect>
          <rect x="9" y="9" width="6" height="6"></rect>
          <line x1="9" y1="1" x2="9" y2="4"></line>
          <line x1="15" y1="1" x2="15" y2="4"></line>
          <line x1="9" y1="20" x2="9" y2="23"></line>
          <line x1="15" y1="20" x2="15" y2="23"></line>
          <line x1="20" y1="9" x2="23" y2="9"></line>
          <line x1="20" y1="15" x2="23" y2="15"></line>
          <line x1="1" y1="9" x2="4" y2="9"></line>
          <line x1="1" y1="15" x2="4" y2="15"></line>
        </symbol>
        <symbol id="icon-search" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </symbol>
        <symbol id="icon-user" viewBox="0 0 24 24">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </symbol>
        <symbol id="icon-lock" viewBox="0 0 24 24">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </symbol>
        <symbol id="icon-code" viewBox="0 0 24 24">
          <polyline points="16 18 22 12 16 6"></polyline>
          <polyline points="8 6 2 12 8 18"></polyline>
        </symbol>
        <symbol id="icon-check" viewBox="0 0 24 24">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </symbol>
        <symbol id="icon-info" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </symbol>
        <symbol id="icon-alert" viewBox="0 0 24 24">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </symbol>
      </svg>

      {/* Slide Deck Viewport */}
      <div className="slides-viewport">
        <div className="slides-container" style={{ transform: `translate3d(-${currentSlide * 100}vw, 0, 0)` }}>
          
          {/* Slide 1: Cover Page */}
          <section className="slide title-slide">
            <div className="cover-content">
              <span className="label-caps animate-fade-in-up" style={{ color: '#A3A3A3', display: 'block' }}>ENTERPRISE METADATA INTELLIGENCE SYSTEM</span>
              <h1 className="animate-fade-in-up delay-1">Pivota AI</h1>
              <p className="tagline animate-fade-in-up delay-1">Find where your data lives. Securely.</p>
              <div className="animate-fade-in-up delay-2" style={{ borderTop: '1px solid #374151', paddingTop: 'var(--space-24)', maxWidth: '650px' }}>
                <p style={{ color: '#D1D5DB', fontSize: 'var(--fs-14)', marginBottom: '16px' }}>
                  An AI-powered metadata navigation engine that bridges distributed organizational database systems into a unified semantic map, without compromising business record privacy.
                </p>
                <ul style={{ color: '#A3A3A3', fontSize: 'var(--fs-12)', fontFamily: 'JetBrains Mono', paddingLeft: '20px', lineHeight: '1.6' }}>
                  <li>Target: Enterprise Data Compliance, Devops Teams, Data Protection Officers</li>
                  <li>Security Core: Complete Multi-tenant Data & Vector Isolation Boundaries</li>
                  <li>Interface: Dynamic 2FA verification portals & granular IAM policies</li>
                </ul>
              </div>
              <h2 className="animate-fade-in-up delay-3">Project Overview & Architecture Presentation</h2>
            </div>
            
            <div className="cover-animated-graphics">
              <div className="cover-scanner-radar">
                <div className="radar-circle circle-1"></div>
                <div className="radar-circle circle-2"></div>
                <div className="radar-circle circle-3"></div>
                <div className="radar-sweep-hand"></div>
                <div className="radar-ping-node node-1"></div>
                <div className="radar-ping-node node-2"></div>
                <div className="radar-ping-node node-3"></div>
              </div>
            </div>
          </section>

          {/* Slide 2: Problem Statement */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Challenges & Security Gaps</span>
                <h2>Problem Statement</h2>
              </div>
              <span className="slide-subtitle font-mono">02 / 09</span>
            </div>
            <div className="slide-content-grid">
              <div>
                <p style={{ marginBottom: 'var(--space-24)' }}>
                  As organizations grow, database instances multiply. Engineers and analysts waste hundreds of hours manually tracing tables across systems, while compliance teams lack visibility into data assets.
                </p>
                <ul className="bullet-list">
                  <li><strong>Fragmented Schema Structure:</strong> Enterprise data is spread across different PostgreSQL, MySQL, and MongoDB engines with zero centralized schemas or mapping coordinates.</li>
                  <li><strong>Compliance & Shadow Databases:</strong> Regulated fields (such as PII, passwords, and billing records) get created by developers in undocumented tables, creating massive privacy vulnerabilities.</li>
                  <li><strong>AI Data Leakage Danger:</strong> Connecting LLMs directly to live business databases exposes sensitive records to unauthorized prompts, leading to compliance breaches.</li>
                  <li><strong>Lack of Structural Audit Trails:</strong> Manual Excel mapping tools fail to track schema drifts or log historical access actions, creating severe audit risks.</li>
                </ul>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card dark">
                  <span className="label-caps" style={{ color: '#9CA3AF' }}>The Core Risk</span>
                  <h3 style={{ margin: 'var(--space-8) 0', color: '#FFFFFF' }}>Data Leakage & Manual Work</h3>
                  <p>Standard data discovery tools either require importing all database records centrally (creating massive security vectors) or rely on stale, manual documentation files.</p>
                </div>
                <div className="codex-card">
                  <span className="label-caps">The Goal</span>
                  <h3 style={{ margin: 'var(--space-8) 0' }}>Secure Metadata Mapping</h3>
                  <p>Build a secure, multi-tenant explorer that indexes schema <strong>skeletons</strong> (databases, tables, column names, relationships) and lets users ask questions in natural language, while keeping business rows completely isolated and encrypted.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Slide 3: Proposed Solution */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Innovation & Architecture</span>
                <h2>Proposed Solution</h2>
              </div>
              <span className="slide-subtitle font-mono">03 / 09</span>
            </div>
            <div className="slide-content-grid">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-8)' }}>
                    <Icon name="database" className="icon-svg large" />
                    <h3 style={{ margin: 0 }}>1. Zero-Data Import Discovery</h3>
                  </div>
                  <p>Pivota extracts structural schema representations only. Table schemas, column types, primary keys, and constraint definitions are cataloged. Zero customer tables or business rows are ever read or moved.</p>
                </div>
                <div className="codex-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-8)' }}>
                    <Icon name="search" className="icon-svg large" />
                    <h3 style={{ margin: 0 }}>2. Hybrid Retrieval Engine</h3>
                  </div>
                  <p>Combines exact database symbol keyword matching with semantic vector space indexing. This resolves synonym queries (e.g. asking for "revenue" retrieves `orders.total_amount`).</p>
                </div>
              </div>
              <div>
                <div className="codex-card dark" style={{ marginBottom: 'var(--space-16)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-8)' }}>
                    <Icon name="shield" className="icon-svg large" style={{ stroke: '#FFFFFF' }} />
                    <h3 style={{ color: '#FFFFFF', margin: 0 }}>3. Isolated Security Gate</h3>
                  </div>
                  <p>Isolated 2FA authentication microservice safeguards administrative access. Delegated employee and contractor credentials run through IAM permission configurations, which filter both the visual options and the backend API access.</p>
                </div>
                <ul className="bullet-list">
                  <li><strong>Dynamic Relationship Discovery:</strong> Auto-constructs visual data maps based on foreign keys and naming patterns.</li>
                  <li><strong>Grounded LLM Context:</strong> The semantic AI responder works with factual metadata context, avoiding hallucinations.</li>
                  <li><strong>Local ML Execution:</strong> SentenceTransformers run entirely in offline environments to prevent schema data leaks.</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Slide 4: System Workflow */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Process Pipeline</span>
                <h2>System Workflow</h2>
              </div>
              <span className="slide-subtitle font-mono">04 / 09</span>
            </div>
            <div className="workflow-container">
              <p style={{ textAlign: 'center' }}>Click each step below to inspect how Pivota securely maps and navigates database schemas.</p>
              
              <div className="workflow-steps-row">
                {[1, 2, 3, 4, 5].map((step) => (
                  <div 
                    key={step} 
                    className={`workflow-step-card ${workflowStep === step ? 'active' : ''}`}
                    onClick={() => setWorkflowStep(step)}
                  >
                    <div className="step-num">{step}</div>
                    <div className="step-title">
                      {step === 1 && "Connection"}
                      {step === 2 && "Validation"}
                      {step === 3 && "Sync & Discover"}
                      {step === 4 && "Embed & Index"}
                      {step === 5 && "Ask Pivota AI"}
                    </div>
                  </div>
                ))}
              </div>

              <div className="workflow-details-pane">
                <h3 style={{ marginBottom: 'var(--space-8)' }}>{workflowSteps[workflowStep].title}</h3>
                <p dangerouslySetInnerHTML={{ __html: workflowSteps[workflowStep].desc }} />
              </div>
              
              <div style={{ marginTop: 'var(--space-8)', padding: 'var(--space-8)', border: '1px solid #E5E7EB', borderRadius: 'var(--radius-card)', backgroundColor: '#FAFAFA' }}>
                <span className="label-caps" style={{ fontSize: '10px', color: '#6B7280' }}>Pipeline Properties:</span>
                <span style={{ fontSize: '11px', marginLeft: '8px' }}>Asynchronous Background Workers • Symmetrically Encrypted DB Credentials • Network SSRF Guard Filters</span>
              </div>
            </div>
          </section>

          {/* Slide 5: Technology Stack */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">System Stack</span>
                <h2>Tech Stack Utilized</h2>
              </div>
              <span className="slide-subtitle font-mono">05 / 09</span>
            </div>
            
            <div className="tech-slide-container">
              {/* Left Side: Tech Tags List */}
              <div className="tech-grid-scroll">
                
                {/* Col 1: Backend */}
                <div className="tech-item-row">
                  <h4 className="label-caps">Backend Core</h4>
                  <div className={`tech-tag-interactive ${selectedTech === 'fastapi' ? 'active' : ''}`} onClick={() => setSelectedTech('fastapi')}>
                    <Icon name="code" /> FastAPI (Python 3.10+)
                    <span className="tech-tag-cat">API Framework</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'sqlalchemy' ? 'active' : ''}`} onClick={() => setSelectedTech('sqlalchemy')}>
                    <Icon name="database" /> SQLAlchemy 2.0 ORM
                    <span className="tech-tag-cat">Database ORM</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'fernet' ? 'active' : ''}`} onClick={() => setSelectedTech('fernet')}>
                    <Icon name="lock" /> Fernet Crypto Engine
                    <span className="tech-tag-cat">Security</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'jwt_totp' ? 'active' : ''}`} onClick={() => setSelectedTech('jwt_totp')}>
                    <Icon name="shield" /> PyJWT & PyTOTP
                    <span className="tech-tag-cat">Auth Engine</span>
                  </div>
                </div>

                {/* Col 2: Frontend */}
                <div className="tech-item-row">
                  <h4 className="label-caps">Frontend Client</h4>
                  <div className={`tech-tag-interactive ${selectedTech === 'react_ts' ? 'active' : ''}`} onClick={() => setSelectedTech('react_ts')}>
                    <Icon name="code" /> React & TypeScript
                    <span className="tech-tag-cat">UI SPA</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'vite' ? 'active' : ''}`} onClick={() => setSelectedTech('vite')}>
                    <Icon name="cpu" /> Vite Bundler
                    <span className="tech-tag-cat">Build Engine</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'zustand' ? 'active' : ''}`} onClick={() => setSelectedTech('zustand')}>
                    <Icon name="code" /> Zustand State
                    <span className="tech-tag-cat">State Management</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'tanstack' ? 'active' : ''}`} onClick={() => setSelectedTech('tanstack')}>
                    <Icon name="search" /> TanStack Query v5
                    <span className="tech-tag-cat">Data Sync</span>
                  </div>
                </div>

                {/* Col 3: Data & AI */}
                <div className="tech-item-row">
                  <h4 className="label-caps">Data & AI</h4>
                  <div className={`tech-tag-interactive ${selectedTech === 'postgresql' ? 'active' : ''}`} onClick={() => setSelectedTech('postgresql')}>
                    <Icon name="database" /> PostgreSQL App DB
                    <span className="tech-tag-cat">Metadata DB</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'pgvector' ? 'active' : ''}`} onClick={() => setSelectedTech('pgvector')}>
                    <Icon name="search" /> pgvector Extension
                    <span className="tech-tag-cat">Vector Index</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'transformers' ? 'active' : ''}`} onClick={() => setSelectedTech('transformers')}>
                    <Icon name="cpu" /> SentenceTransformers
                    <span className="tech-tag-cat">Embeddings</span>
                  </div>
                  <div className={`tech-tag-interactive ${selectedTech === 'llm' ? 'active' : ''}`} onClick={() => setSelectedTech('llm')}>
                    <Icon name="user" /> OpenAI / LLM Adapters
                    <span className="tech-tag-cat">Semantic LLM</span>
                  </div>
                </div>

              </div>

              {/* Right Side: Details Pane */}
              <div className="tech-details-pane">
                {selectedTech && techStackData[selectedTech] ? (
                  <>
                    <h3>{techStackData[selectedTech].name}</h3>
                    <div style={{ marginTop: '4px' }}>
                      <span className="tech-why-badge">{techStackData[selectedTech].category}</span>
                    </div>
                    <p style={{ fontWeight: '600', marginTop: '12px' }}>{techStackData[selectedTech].why}</p>
                    <p style={{ marginTop: '8px' }}>{techStackData[selectedTech].details}</p>
                  </>
                ) : (
                  <>
                    <h3>Technology Architecture</h3>
                    <p>Click any technology tag on the left to inspect its architectural purpose and why it is integrated into Pivota AI.</p>
                  </>
                )}
              </div>

            </div>
          </section>

          {/* Slide 6: Features Completed */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Milestones & Functional Scopes</span>
                <h2>Features Completed Till Now</h2>
              </div>
              <span className="slide-subtitle font-mono">06 / 09</span>
            </div>
            <div className="slide-content-grid">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card">
                  <span className="label-caps" style={{ color: 'var(--success)' }}>Authentication & IAM</span>
                  <h3 style={{ margin: 'var(--space-8) 0' }}>Secure 2FA & Access Policy Panel</h3>
                  <ul className="bullet-list" style={{ marginTop: 'var(--space-8)' }}>
                    <li>Gmail OTP delivery verified during admin account signup.</li>
                    <li>TOTP tokens rotated every 30s with custom SVG count timing wheels.</li>
                    <li>Access policies restrict employee roles to specific catalog schemas.</li>
                    <li>Dynamic menu components hide settings and tables based on active policies.</li>
                    <li>Mandatory admin password resets forced on invited employee logins.</li>
                  </ul>
                </div>
                <div className="codex-card">
                  <span className="label-caps" style={{ color: 'var(--success)' }}>Connection Wizard</span>
                  <h3 style={{ margin: 'var(--space-8) 0' }}>Multi-Step Database Wizard</h3>
                  <ul className="bullet-list" style={{ marginTop: 'var(--space-8)' }}>
                    <li>Database adapter integrations for Postgres, MySQL, and MongoDB.</li>
                    <li>Live database tests checking connectivity, login, and TLS permissions.</li>
                    <li>Synchronous connectivity error reporting for fast debugging.</li>
                  </ul>
                </div>
              </div>
              <div>
                <div className="codex-card dark" style={{ marginBottom: 'var(--space-16)' }}>
                  <span className="label-caps" style={{ color: '#A3A3A3' }}>Intelligence Navigator</span>
                  <h3 style={{ margin: 'var(--space-8) 0', color: '#FFFFFF' }}>Ask Pivota AI Explorer</h3>
                  <ul className="bullet-list dark" style={{ marginTop: 'var(--space-8)' }}>
                    <li>Natural language chat interface retrieving schema context facts.</li>
                    <li>Keyword search combined with vector similarity embeddings.</li>
                    <li>Interactive data map graphs display database namespaces and relationships.</li>
                    <li>Audit logging catalogs all queries asked by analysts for security reviews.</li>
                  </ul>
                </div>
                <div style={{ padding: 'var(--space-8)', border: '1px dashed var(--primary)', borderRadius: 'var(--radius-card)', textAlign: 'center' }}>
                  <span className="label-caps" style={{ fontSize: '10px' }}>Verification Coverage: 29 backend test cases passing successfully</span>
                </div>
              </div>
            </div>
          </section>

          {/* Slide 7: Security Optimization */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Hardening & Encryption Policies</span>
                <h2>Security Optimization</h2>
              </div>
              <span className="slide-subtitle font-mono">07 / 09</span>
            </div>
            
            <div className="security-grid">
              {/* Left Column: Networks & Credentials */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card security-card warning-border">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-4)' }}>
                    <Icon name="alert" style={{ color: 'var(--warning)' }} />
                    <h3 style={{ margin: 0 }}>SSRF Outbound Gate</h3>
                  </div>
                  <p>Connection wizard limits protocols strictly to `postgresql://`, `mysql://`, and `mongodb://`. Blocks arbitrary internal schemes like `file://` or `ftp://` to prevent server resource traversal.</p>
                </div>
                
                <div className="codex-card security-card success-border">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-4)' }}>
                    <Icon name="lock" style={{ color: 'var(--success)' }} />
                    <h3 style={{ margin: 0 }}>Fernet Symmetric Encryption</h3>
                  </div>
                  <p>External database connection credentials are encrypted prior to database insertion. Decryption is restricted strictly to background sync job executions.</p>
                </div>
              </div>

              {/* Right Column: Isolation & Microservices */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card security-card success-border">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-4)' }}>
                    <Icon name="shield" style={{ color: 'var(--success)' }} />
                    <h3 style={{ margin: 0 }}>Isolated 2FA Microservice</h3>
                  </div>
                  <p>TOTP secrets and verify logic reside in a separate API service running on `localhost:8001` with its own isolated frontend, preventing authentication token hijacking from catalog exploits.</p>
                </div>
                
                <div className="codex-card security-card danger-border">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-12)', marginBottom: 'var(--space-4)' }}>
                    <Icon name="info" style={{ color: 'var(--danger)' }} />
                    <h3 style={{ margin: 0 }}>Tenant Metadata Isolation</h3>
                  </div>
                  <p>Every single SQL query and AI vector lookup runs with explicit `organization_id` criteria in SQLAlchemy/vector database filters, ensuring organization records never bleed into other tenants.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Slide 8: Future Roadmap */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Development Horizons & Integrations</span>
                <h2>Future Roadmap</h2>
              </div>
              <span className="slide-subtitle font-mono">08 / 09</span>
            </div>
            <div className="slide-content-grid">
              <div>
                <p style={{ marginBottom: 'var(--space-24)' }}>
                  Pivota AI's development roadmap focuses on expanding connectivity profiles, automated schema monitoring, and self-service analytics generation.
                </p>
                <ul className="bullet-list">
                  <li><strong>Cloud Data Warehouse Connectors:</strong> Support cloud warehouses including Snowflake, Google BigQuery, and AWS Redshift with federated credential scopes.</li>
                  <li><strong>Automated Schema Drift Monitoring:</strong> Active detection triggers notifications (Slack, PagerDuty, Webhooks) when tables are altered, columns dropped, or index keys removed.</li>
                  <li><strong>Self-Service Auto-SQL Generation:</strong> Direct translation of natural language queries into executable database queries referencing verified metadata symbols, without row-level access.</li>
                  <li><strong>Cross-Region Federated Metadata Search:</strong> Unified search bar query routing across globally distributed database clusters.</li>
                </ul>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card">
                  <span className="label-caps" style={{ color: 'var(--warning)' }}>Q3 Milestone</span>
                  <h3 style={{ margin: 'var(--space-8) 0' }}>Data Warehouse Adapters</h3>
                  <p>Add adapter wizards to fetch structural tables from Google BigQuery and Snowflake. Enforces exact same Fernet symmetric encryption and proxy outbound restrictions.</p>
                </div>
                <div className="codex-card dark">
                  <span className="label-caps" style={{ color: '#A3A3A3' }}>Q4 Milestone</span>
                  <h3 style={{ margin: 'var(--space-8) 0', color: '#FFFFFF' }}>Drift Alert Webhook Engine</h3>
                  <p>Background worker compares metadata snapshots chronologically and triggers drift logs when structural database alterations are detected, preventing stale compliance reporting.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Slide 9: Future AI Implementation */}
          <section className="slide">
            <div className="slide-header">
              <div>
                <span className="label-caps">Cognitive Metadata Modeling</span>
                <h2>Future AI Implementation</h2>
              </div>
              <span className="slide-subtitle font-mono">09 / 09</span>
            </div>
            <div className="slide-content-grid">
              <div>
                <p style={{ marginBottom: 'var(--space-24)' }}>
                  Integrating next-generation artificial intelligence patterns to autonomously trace relational graphs and secure database structures without manual administration models.
                </p>
                <ul className="bullet-list">
                  <li><strong>Semantic Graph Neural Networks (GNN):</strong> Maps schema objects, columns, and foreign key references as semantic node links. Enhances query parsing accuracy by training local structural context.</li>
                  <li><strong>Autonomous Audit & Compliance Agents:</strong> Multi-agent systems that autonomously scan metadata tables, detect shadow credentials, classify PII fields, and compile compliance audit logs.</li>
                  <li><strong>Secure Federated Fine-Tuning:</strong> Pre-trains small, open-source model parameters (e.g. Llama-3-8B) on corporate database skeletons inside safe customer network borders.</li>
                  <li><strong>AI-Driven Dynamic Hashing Policies:</strong> Semantic scanners identify potential sensitive rows (like emails, phone digits) and dynamically create hash configurations at the database proxy.</li>
                </ul>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>
                <div className="codex-card dark">
                  <span className="label-caps" style={{ color: '#9CA3AF' }}>Knowledge Graph Matching</span>
                  <h3 style={{ margin: 'var(--space-8) 0', color: '#FFFFFF' }}>GNN Semantic Maps</h3>
                  <p>GNN architectures vectorize relational tables together, capturing graph properties to resolve context synonyms with 98% accuracy (e.g. mapping customer identifiers across silos).</p>
                </div>
                <div className="codex-card">
                  <span className="label-caps" style={{ color: 'var(--success)' }}>Local LLM Tuning</span>
                  <h3 style={{ margin: 'var(--space-8) 0' }}>Internal LoRA Adapters</h3>
                  <p>Fine-tune domain-specific structural model weights using LoRA adapters on local GPUs. Zero metadata sentences ever leave the company boundaries to third-party endpoints.</p>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>

      {/* Presentation Footer Overlay */}
      <footer className="presentation-footer">
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${progressPercent}%` }}></div>
        </div>
        
        <div className="controls-left">
          <select 
            className="pill-select" 
            value={currentSlide} 
            onChange={(e) => goToSlide(parseInt(e.target.value, 10))}
            aria-label="Jump to Slide"
          >
            <option value="0">1. Cover Page</option>
            <option value="1">2. Problem Statement</option>
            <option value="2">3. Proposed Solution</option>
            <option value="3">4. System Workflow</option>
            <option value="4">5. Tech Stack</option>
            <option value="5">6. Completed Features</option>
            <option value="6">7. Security Hardening</option>
            <option value="7">8. Future Roadmap</option>
            <option value="8">9. Future AI Implementation</option>
          </select>
          
          <span className="slide-number">0{currentSlide + 1} / 0{totalSlides}</span>
        </div>

        <div className="controls-right">
          <span className="mono" style={{ fontSize: '11px', color: '#6B7280', marginRight: 'var(--space-8)' }}>
            Use Left/Right arrow keys or Spacebar
          </span>
          <button className="pill-btn" onClick={prevSlide} disabled={currentSlide === 0}>
            <Icon name="arrow-left" /> Prev
          </button>
          <button className="pill-btn" onClick={nextSlide} disabled={currentSlide === totalSlides - 1}>
            Next <Icon name="arrow-right" />
          </button>
        </div>
      </footer>

    </div>
  );
}

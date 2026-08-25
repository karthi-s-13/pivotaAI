/**
 * Pivota Data Map — Graph Data Model Types.
 *
 * Defines the normalized node/edge types used throughout the data constellation.
 */

// ─────────────────────────────────────────────
// Node Types
// ─────────────────────────────────────────────

export type NodeType = 'root' | 'provider' | 'database' | 'schema' | 'table' | 'column';

export type NodeStatus = 'idle' | 'loading' | 'ready' | 'error' | 'syncing' | 'disconnected';

export type EdgeType = 'hierarchy' | 'relationship';

export type ObjectType = 'TABLE' | 'VIEW' | 'COLLECTION' | 'MATERIALIZED_VIEW';

// ─────────────────────────────────────────────
// Node Metadata Payloads
// ─────────────────────────────────────────────

export interface RootMetadata {
  label: string;
  subtitle: string;
}

export interface ProviderMetadata {
  provider_type: string;
  environment: string;
  host: string;
  port: number | null;
  database_name: string;
  connection_status: string;
  health_status: string;
  last_tested_at: string | null;
  last_sync_at: string | null;
  databases_count: number;
  tables_count: number;
  columns_count: number;
}

export interface DatabaseMetadata {
  owner: string | null;
  encoding: string | null;
  data_source_id: string;
  data_source_name: string;
}

export interface SchemaMetadata {
  owner: string | null;
  database_id: string;
  database_name: string;
}

export interface TableMetadata {
  type: ObjectType;
  description: string | null;
  row_count_estimate: number;
  schema_id: string;
  schema_name: string;
  database_name: string;
  data_source_name: string;
  column_count: number;
  relationship_count: number;
}

export interface ColumnMetadata {
  ordinal_position: number;
  data_type: string;
  native_type: string | null;
  nullable: boolean;
  default_value: string | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  description: string | null;
}

export type NodeMetadata =
  | RootMetadata
  | ProviderMetadata
  | DatabaseMetadata
  | SchemaMetadata
  | TableMetadata
  | ColumnMetadata;

// ─────────────────────────────────────────────
// Core Graph Node
// ─────────────────────────────────────────────

export interface DataMapNode {
  id: string;
  type: NodeType;
  label: string;
  parentId: string | null;
  /** Computed canvas position */
  x: number;
  y: number;
  /** Whether this node's children are currently shown */
  expanded: boolean;
  /** Whether children have been fetched from the API */
  childrenLoaded: boolean;
  /** Current async state for this node */
  status: NodeStatus;
  /** Type-specific metadata */
  metadata: NodeMetadata;
  /** IDs of direct children */
  childIds: string[];
  /** Whether this node is currently visible (not filtered out) */
  visible: boolean;
  /** Animation entry key — incremented on expansion to trigger entry animation */
  animKey: number;
}

// ─────────────────────────────────────────────
// Core Graph Edge
// ─────────────────────────────────────────────

export interface DataMapEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  /** Column pair label for FK edges e.g. "user_id → id" */
  label?: string;
  fromColumns?: string[];
  toColumns?: string[];
}

// ─────────────────────────────────────────────
// Graph State
// ─────────────────────────────────────────────

export interface DataMapGraph {
  nodes: Record<string, DataMapNode>;
  edges: DataMapEdge[];
}

// ─────────────────────────────────────────────
// Viewport State
// ─────────────────────────────────────────────

export interface ViewportState {
  zoom: number;
  panX: number;
  panY: number;
}

// ─────────────────────────────────────────────
// Filter State
// ─────────────────────────────────────────────

export interface FilterState {
  providerTypes: string[];    // empty = show all
  objectTypes: string[];      // empty = show all
  connectionStatuses: string[]; // empty = show all
  showColumns: boolean;
}

// ─────────────────────────────────────────────
// Search State
// ─────────────────────────────────────────────

export interface SearchState {
  query: string;
  results: SearchResult[];
  loading: boolean;
  highlightedNodeId: string | null;
}

export interface SearchResult {
  nodeId: string | null;
  label: string;
  type: string;
  details: string;
  data_source_name: string;
}

// ─────────────────────────────────────────────
// Context Menu
// ─────────────────────────────────────────────

export interface ContextMenuState {
  nodeId: string | null;
  x: number;
  y: number;
  visible: boolean;
}

// ─────────────────────────────────────────────
// Provider Icon Colors (design system)
// ─────────────────────────────────────────────

export const PROVIDER_COLORS: Record<string, string> = {
  postgresql: '#336791',
  mysql: '#00758f',
  mongodb: '#13aa52',
  mssql: '#cc2927',
  sqlserver: '#cc2927',
  snowflake: '#29b5e8',
  bigquery: '#4285f4',
  redis: '#dc382d',
  sqlite: '#003b57',
  oracle: '#f80000',
  default: '#6366f1',
};

export const PROVIDER_LABELS: Record<string, string> = {
  postgresql: 'PostgreSQL',
  mysql: 'MySQL',
  mongodb: 'MongoDB',
  mssql: 'SQL Server',
  sqlserver: 'SQL Server',
  snowflake: 'Snowflake',
  bigquery: 'BigQuery',
  redis: 'Redis',
  sqlite: 'SQLite',
  oracle: 'Oracle',
};

export function getProviderColor(providerType: string | undefined | null): string {
  if (!providerType) return PROVIDER_COLORS.default;
  return PROVIDER_COLORS[providerType.toLowerCase()] ?? PROVIDER_COLORS.default;
}

export function getProviderLabel(providerType: string | undefined | null): string {
  if (!providerType) return 'Unknown';
  return PROVIDER_LABELS[providerType.toLowerCase()] ?? providerType;
}

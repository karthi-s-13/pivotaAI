/**
 * Pivota Data Map — API Layer.
 *
 * Wraps existing catalog and data-source API clients for
 * the specific needs of the Data Map constellation view.
 */

import apiClient from '../../../services/api/apiClient';
import type {
  DatabaseMetadata,
  SchemaMetadata,
  ObjectSummary,
  ObjectDetail,
  RelationshipMetadata,
  SearchResponse,
} from '../../catalog/api/catalogApi';

// ─────────────────────────────────────────────
// Re-export catalog types the hook needs
// ─────────────────────────────────────────────
export type {
  DatabaseMetadata,
  SchemaMetadata,
  ObjectSummary,
  ObjectDetail,
  RelationshipMetadata,
  SearchResponse,
};

// ─────────────────────────────────────────────
// API Functions
// ─────────────────────────────────────────────

// ─────────────────────────────────────────────
// Normalized flat provider shape used by the data map
// ─────────────────────────────────────────────

export interface ProviderRecord {
  id: string;
  name: string;
  provider_type: string;       // from identity.provider
  environment: string;
  host: string;
  port: number | null;
  database_name: string;
  connection_status: string;   // from health.status
  health_status: string;
  last_tested_at: string | null;
  last_sync_at: string | null;
  databases_count: number;
  tables_count: number;
  columns_count: number;
}

/** Flatten a nested DataSourceResponse into a ProviderRecord. */
function flattenProvider(raw: any): ProviderRecord {
  const identity = raw?.identity ?? {};
  const connectivity = raw?.connectivity ?? {};
  const health = raw?.health ?? {};
  const providerCfg = connectivity?.provider_config ?? {};

  // Backend writes 'healthy' on success (not 'connected') — normalise both to 'connected'
  const rawHealthStatus: string = health.status ?? raw.health_status ?? raw.connection_status ?? 'unknown';
  const normalisedStatus = (rawHealthStatus === 'healthy' || rawHealthStatus === 'connected')
    ? 'connected'
    : rawHealthStatus;

  const metadata = raw?.metadata ?? {};
  
  return {
    id: identity.id ?? raw.id ?? '',
    name: identity.name ?? raw.name ?? 'Unknown',
    provider_type: (identity.provider ?? raw.provider_type ?? '').toLowerCase(),
    environment: identity.environment ?? raw.environment ?? 'development',
    host: connectivity.host ?? raw.host ?? '',
    port: connectivity.port ?? raw.port ?? null,
    database_name: providerCfg.database_name ?? raw.database_name ?? '',
    connection_status: normalisedStatus,
    health_status: normalisedStatus,
    last_tested_at: health.last_check ?? raw.last_tested_at ?? null,
    last_sync_at: raw.last_sync_at ?? null,
    databases_count: metadata.databases?.length ?? raw.databases_count ?? 0,
    tables_count: metadata.objects?.length ?? raw.tables_count ?? 0,
    columns_count: metadata.columns?.length ?? raw.columns_count ?? 0,
  };
}

export const dataMapApi = {
  /** List all connected data source providers (flattened from nested backend response) */
  fetchProviders: async (): Promise<ProviderRecord[]> => {
    const response = await apiClient.get('/data-sources');
    const raw: any[] = response.data;
    return raw.map(flattenProvider);
  },

  /** Fetch databases for a specific data source provider */
  fetchDatabases: async (dataSourceId?: string): Promise<DatabaseMetadata[]> => {
    const response = await apiClient.get('/catalog/databases');
    const all: DatabaseMetadata[] = response.data;
    if (dataSourceId) {
      return all.filter((db) => db.data_source_id === dataSourceId);
    }
    return all;
  },

  /** Fetch schemas for a specific database */
  fetchSchemas: async (databaseId: string): Promise<SchemaMetadata[]> => {
    const response = await apiClient.get('/catalog/schemas', {
      params: { database_id: databaseId },
    });
    return response.data;
  },

  /** Fetch tables/views for a specific schema */
  fetchObjects: async (schemaId: string): Promise<ObjectSummary[]> => {
    const response = await apiClient.get('/catalog/objects', {
      params: { schema_id: schemaId },
    });
    return response.data;
  },

  /** Fetch full object details: columns, indexes, FK relationships */
  fetchObjectDetail: async (objectId: string): Promise<ObjectDetail> => {
    const response = await apiClient.get(`/catalog/objects/${objectId}`);
    return response.data;
  },

  /** Fetch all FK relationships across the organization */
  fetchAllRelationships: async (): Promise<RelationshipMetadata[]> => {
    const response = await apiClient.get('/catalog/relationships');
    return response.data;
  },

  /** Global metadata search */
  search: async (query: string): Promise<SearchResponse> => {
    const response = await apiClient.get('/catalog/search', {
      params: { q: query },
    });
    return response.data;
  },

  /** Trigger metadata re-discovery for a provider */
  refreshProvider: async (sourceId: string): Promise<void> => {
    await apiClient.post(`/data-sources/${sourceId}/discover`);
  },
};

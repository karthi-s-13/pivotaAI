/**
 * Catalog API Client.
 */

import apiClient from '../../../services/api/apiClient';

export interface DatabaseMetadata {
  id: string;
  name: string;
  owner: string | null;
  encoding: string | null;
  created_at: string;
  data_source_id: string;
  data_source_name: string;
}

export interface SchemaMetadata {
  id: string;
  name: string;
  owner: string | null;
  created_at: string;
  database_id: string;
  database_name: string;
}

export interface ObjectSummary {
  id: string;
  name: string;
  type: string;
  description: string | null;
  row_count_estimate: number;
  schema_id: string;
  schema_name: string;
  database_name: string;
  data_source_name: string;
}

export interface ColumnMetadata {
  id: string;
  name: string;
  ordinal_position: number;
  data_type: string;
  native_type: string | null;
  nullable: boolean;
  default_value: string | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  description: string | null;
}

export interface IndexMetadata {
  id: string;
  name: string;
  columns: string[];
  unique: boolean;
  primary: boolean;
  type: string | null;
}

export interface RelationshipMetadata {
  id: string;
  constraint_name: string;
  from_object_id: string;
  from_table_name: string;
  from_columns: string[];
  to_object_id: string;
  to_table_name: string;
  to_columns: string[];
  update_action: string | null;
  delete_action: string | null;
}

export interface ObjectDetail {
  id: string;
  name: string;
  type: string;
  description: string | null;
  row_count_estimate: number;
  schema_id: string;
  schema_name: string;
  database_id: string;
  database_name: string;
  data_source_name: string;
  columns: ColumnMetadata[];
  indexes: IndexMetadata[];
  relationships_outbound: RelationshipMetadata[];
  relationships_inbound: RelationshipMetadata[];
}

export interface SearchMatchItem {
  id: string;
  name: string;
  type: string;
  details: string;
  description: string | null;
  data_source_name: string;
}

export interface SearchResponse {
  query: string;
  results: SearchMatchItem[];
}

export const catalogApi = {
  getDatabases: async (): Promise<DatabaseMetadata[]> => {
    const response = await apiClient.get('/catalog/databases');
    return response.data;
  },

  getSchemas: async (databaseId?: string): Promise<SchemaMetadata[]> => {
    const params = databaseId ? { database_id: databaseId } : {};
    const response = await apiClient.get('/catalog/schemas', { params });
    return response.data;
  },

  getObjects: async (schemaId?: string, databaseId?: string): Promise<ObjectSummary[]> => {
    const params: Record<string, string> = {};
    if (schemaId) params.schema_id = schemaId;
    if (databaseId) params.database_id = databaseId;
    const response = await apiClient.get('/catalog/objects', { params });
    return response.data;
  },

  getObjectDetails: async (objectId: string): Promise<ObjectDetail> => {
    const response = await apiClient.get(`/catalog/objects/${objectId}`);
    return response.data;
  },

  getRelationships: async (): Promise<RelationshipMetadata[]> => {
    const response = await apiClient.get('/catalog/relationships');
    return response.data;
  },

  search: async (query: string): Promise<SearchResponse> => {
    const response = await apiClient.get('/catalog/search', { params: { q: query } });
    return response.data;
  },

  getRecords: async (objectId: string, limit: number = 20, offset: number = 0): Promise<RecordsResponse> => {
    const response = await apiClient.get(`/catalog/objects/${objectId}/records`, { params: { limit, offset } });
    return response.data;
  },

  runQuery: async (databaseId: string, query: string): Promise<QueryResponse> => {
    const response = await apiClient.post(`/catalog/databases/${databaseId}/query`, { query });
    return response.data;
  },
};

export interface RecordsResponse {
  columns: string[];
  rows: Record<string, any>[];
  total_count: number;
}

export interface QueryResponse {
  columns: string[];
  rows: Record<string, any>[];
  error?: string;
}


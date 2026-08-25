/**
 * Data Sources API functions.
 */

import apiClient from '../../../services/api/apiClient';

export interface DataSource {
  id: string;
  name: string;
  description: string | null;
  provider_type: string;
  host: string;
  port: number;
  database_name: string;
  username: string | null;
  ssl_enabled: boolean;
  environment: string;
  status: string;
  connection_status: string;
  connection_error: string | null;
  last_tested_at: string | null;
  last_sync_at: string | null;
  databases_count: number;
  tables_count: number;
  columns_count: number;
  created_by: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
  connection_string: string | null;
  auth_source: string | null;
  replica_set: string | null;
}

export interface CreateDataSourceRequest {
  name: string;
  description?: string;
  provider_type: string;
  host?: string;
  port: number;
  database_name: string;
  username?: string;
  password?: string;
  connection_string?: string;
  auth_source?: string;
  replica_set?: string;
  ssl_enabled: boolean;
  environment: string;
  instance_name?: string;
  authentication_method?: string;
  trust_server_certificate?: boolean;
  // MongoDB-specific
  deployment?: string;           // 'self_hosted' | 'atlas'
  direct_connection?: boolean;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
  server_version: string | null;
  details: Record<string, any> | null;
}

export interface ConnectionTestRequest {
  provider_type: string;
  host?: string;
  port?: number;
  database_name?: string;
  username?: string;
  password?: string;
  connection_string?: string;
  auth_source?: string;
  ssl_enabled: boolean;
  instance_name?: string;
  authentication_method?: string;
  trust_server_certificate?: boolean;
  // MongoDB-specific
  deployment?: string;
  replica_set?: string;
  direct_connection?: boolean;
}

export interface DashboardData {
  stats: {
    data_sources_count: number;
    databases_count: number;
    tables_count: number;
    columns_count: number;
    connected_count: number;
    error_count: number;
  };
  recent_activity: Array<{
    id: string;
    action: string;
    resource_type: string | null;
    resource_id: string | null;
    details: string | null;
    user_name: string | null;
    timestamp: string;
  }>;
  data_source_health: Array<{
    id: string;
    name: string;
    provider_type: string;
    connection_status: string;
    last_tested_at: string | null;
    environment: string;
  }>;
}

export const dataSourceApi = {
  list: async (): Promise<DataSource[]> => {
    const response = await apiClient.get('/data-sources');
    return response.data;
  },

  get: async (id: string): Promise<DataSource> => {
    const response = await apiClient.get(`/data-sources/${id}`);
    return response.data;
  },

  create: async (data: CreateDataSourceRequest): Promise<DataSource> => {
    // Map flat frontend CreateDataSourceRequest to nested backend DataSourceCreate schema
    const nestedPayload = {
      identity: {
        name: data.name,
        provider: data.provider_type,
        environment: data.environment,
      },
      connectivity: {
        host: data.host || undefined,
        port: data.port || undefined,
        connection_mode: 'direct',
        network_mode: 'public',
        provider_config: {
          database_name: data.database_name,
          username: data.username || undefined,
          auth_source: data.auth_source || undefined,
          replica_set: data.replica_set || undefined,
          instance_name: (data as any).instance_name || undefined,
          authentication_method: (data as any).authentication_method || undefined,
          trust_server_certificate: (data as any).trust_server_certificate || undefined,
          deployment: data.deployment || undefined,
          direct_connection: data.direct_connection || undefined,
          ...(data as any).provider_config,
        },
      },
      security: {
        auth_method: (data as any).authentication_method === 'integrated' ? 'none' : (data.username ? 'password' : 'none'),
        tls: data.ssl_enabled,
        password: data.password || undefined,
      },
      description: data.description || undefined,
      connection_string: data.connection_string || undefined,
    };
    const response = await apiClient.post('/data-sources', nestedPayload);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/data-sources/${id}`);
  },

  testConnection: async (id: string): Promise<ConnectionTestResult> => {
    const response = await apiClient.post(`/data-sources/${id}/test`);
    return response.data;
  },

  testConnectionUnsaved: async (data: ConnectionTestRequest): Promise<ConnectionTestResult> => {
    // Map ConnectionTestRequest to backend ConnectionTestRequest schema
    const payload = {
      provider: data.provider_type,
      host: data.host || undefined,
      port: data.port || undefined,
      database_name: data.database_name || undefined,
      username: data.username || undefined,
      password: data.password || undefined,
      connection_string: data.connection_string || undefined,
      ssl_enabled: data.ssl_enabled,
      provider_config: {
        auth_source: data.auth_source || undefined,
        instance_name: (data as any).instance_name || undefined,
        authentication_method: (data as any).authentication_method || undefined,
        trust_server_certificate: (data as any).trust_server_certificate || undefined,
        replica_set: data.replica_set || undefined,
        deployment: data.deployment || undefined,
        direct_connection: data.direct_connection || undefined,
        ...(data as any).provider_config,
      },
    };
    const response = await apiClient.post('/data-sources/test-connection', payload);
    return response.data;
  },

  getDashboard: async (): Promise<DashboardData> => {
    const response = await apiClient.get('/dashboard');
    return response.data;
  },
};

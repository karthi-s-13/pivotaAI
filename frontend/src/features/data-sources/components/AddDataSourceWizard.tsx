/**
 * Add Data Source Wizard.
 *
 * Multi-step wizard: Provider → Connection → Credentials → Security → Test → Review → Save
 */

import { useState } from 'react';
import {
  ArrowLeft, ArrowRight, Database, Check, X,
  Loader2, CheckCircle, XCircle, Wifi, Shield,
  Server, Globe, Lock, RefreshCw, ShieldAlert,
} from 'lucide-react';
import { dataSourceApi } from '../api/dataSourceApi';
import type { CreateDataSourceRequest, ConnectionTestResult } from '../api/dataSourceApi';

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 'provider' | 'connection' | 'credentials' | 'security' | 'test' | 'review';

const STEPS: { key: Step; label: string }[] = [
  { key: 'provider', label: 'Provider' },
  { key: 'connection', label: 'Connection' },
  { key: 'credentials', label: 'Credentials' },
  { key: 'security', label: 'Security' },
  { key: 'test', label: 'Test' },
  { key: 'review', label: 'Review' },
];

export default function AddDataSourceWizard({ onClose, onSuccess }: Props) {
  const [step, setStep] = useState<Step>('provider');
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    name: '',
    description: '',
    provider_type: '',
    host: '',
    port: 5432,
    database_name: 'postgres',
    username: 'postgres',
    password: '',
    connection_string: '',
    auth_source: 'admin',
    replica_set: '',
    ssl_enabled: false,
    environment: 'development' as 'development' | 'staging' | 'production',
    use_connection_string: false,
    instance_name: '',
    authentication_method: 'sql_server',
    trust_server_certificate: false,
    // MongoDB-specific
    deployment: 'self_hosted' as 'self_hosted' | 'atlas',
    direct_connection: false,
    // Supabase-specific
    project_url: '',
    project_ref: '',
    pooler_enabled: false,
    supabase_method: 'project' as 'project' | 'direct',
    include_provider_managed_schemas: false,
    discover_rls: true,
    discover_extensions: true,
    discover_functions: true,
  });

  const update = (field: string, value: any) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const stepIndex = STEPS.findIndex((s) => s.key === step);

  const canProceed = (): boolean => {
    switch (step) {
      case 'provider': return !!form.provider_type;
      case 'connection':
        if (!form.name) return false;
        if (form.use_connection_string) {
          return !!form.connection_string && !!form.database_name;
        }
        if (form.provider_type === 'supabase') {
          if (form.supabase_method === 'project') {
            return (!!form.project_url || !!form.project_ref) && !!form.database_name;
          }
          return !!form.host && !!form.port && !!form.database_name;
        }
        return !!form.host && !!form.port && !!form.database_name;
      case 'credentials':
        if (form.provider_type === 'supabase' && !form.use_connection_string) {
          return !!form.username && !!form.password;
        }
        return true; // optional for others
      case 'security': return true;
      case 'test': return true;
      case 'review': return true;
      default: return false;
    }
  };

  const nextStep = () => {
    const idx = stepIndex;
    if (idx < STEPS.length - 1) setStep(STEPS[idx + 1].key);
  };

  const prevStep = () => {
    const idx = stepIndex;
    if (idx > 0) setStep(STEPS[idx - 1].key);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const provider_config: Record<string, any> = {};
      if (form.provider_type === 'supabase') {
        provider_config.project_url = form.project_url || undefined;
        provider_config.project_ref = form.project_ref || undefined;
        provider_config.pooler_enabled = form.pooler_enabled;
        provider_config.supabase_method = form.supabase_method;
        provider_config.include_provider_managed_schemas = form.include_provider_managed_schemas;
        provider_config.discover_rls = form.discover_rls;
        provider_config.discover_extensions = form.discover_extensions;
        provider_config.discover_functions = form.discover_functions;
      }

      const result = await dataSourceApi.testConnectionUnsaved({
        provider_type: form.provider_type,
        host: form.use_connection_string ? undefined : (form.provider_type === 'supabase' && form.supabase_method === 'project' ? undefined : form.host),
        port: form.port,
        database_name: form.database_name,
        username: form.username || undefined,
        password: form.password || undefined,
        connection_string: form.use_connection_string ? form.connection_string : undefined,
        auth_source: form.auth_source || undefined,
        ssl_enabled: form.ssl_enabled,
        instance_name: form.provider_type === 'sqlserver' ? form.instance_name || undefined : undefined,
        authentication_method: form.provider_type === 'sqlserver' ? form.authentication_method : undefined,
        trust_server_certificate: form.provider_type === 'sqlserver' ? form.trust_server_certificate : undefined,
        // MongoDB-specific
        deployment: form.provider_type === 'mongodb' ? form.deployment : undefined,
        replica_set: form.provider_type === 'mongodb' ? form.replica_set || undefined : undefined,
        direct_connection: form.provider_type === 'mongodb' ? form.direct_connection : undefined,
        // Include custom config
        provider_config: Object.keys(provider_config).length > 0 ? provider_config : undefined,
      } as any);
      setTestResult(result);
    } catch (err: any) {
      const respData = err.response?.data;
      setTestResult({
        success: false,
        message: respData?.error?.message || err.message || 'Connection test failed',
        latency_ms: null,
        server_version: null,
        details: respData?.error || null,
        steps: []
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const provider_config: Record<string, any> = {};
      if (form.provider_type === 'supabase') {
        provider_config.project_url = form.project_url || undefined;
        provider_config.project_ref = form.project_ref || undefined;
        provider_config.pooler_enabled = form.pooler_enabled;
        provider_config.supabase_method = form.supabase_method;
        provider_config.include_provider_managed_schemas = form.include_provider_managed_schemas;
        provider_config.discover_rls = form.discover_rls;
        provider_config.discover_extensions = form.discover_extensions;
        provider_config.discover_functions = form.discover_functions;
      }

      const payload: CreateDataSourceRequest = {
        name: form.name,
        description: form.description || undefined,
        provider_type: form.provider_type,
        host: form.use_connection_string ? undefined : (form.provider_type === 'supabase' && form.supabase_method === 'project' ? undefined : form.host),
        port: form.port,
        database_name: form.database_name,
        username: form.username || undefined,
        password: form.password || undefined,
        connection_string: form.use_connection_string ? form.connection_string : undefined,
        auth_source: form.auth_source || undefined,
        ssl_enabled: form.ssl_enabled,
        environment: form.environment,
        instance_name: form.provider_type === 'sqlserver' ? form.instance_name || undefined : undefined,
        authentication_method: form.provider_type === 'sqlserver' ? form.authentication_method : undefined,
        trust_server_certificate: form.provider_type === 'sqlserver' ? form.trust_server_certificate : undefined,
        // MongoDB-specific
        deployment: form.provider_type === 'mongodb' ? form.deployment : undefined,
        replica_set: form.provider_type === 'mongodb' ? form.replica_set || undefined : undefined,
        direct_connection: form.provider_type === 'mongodb' ? form.direct_connection : undefined,
        // Custom config
        provider_config: Object.keys(provider_config).length > 0 ? provider_config : undefined,
      } as any;
      await dataSourceApi.create(payload);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.error?.message || 'Failed to create data source');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
        <button className="btn-ghost" onClick={onClose} style={{ padding: '8px 12px' }}>
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Add Data Source</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Connect an external database</p>
        </div>
      </div>

      {/* Step Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 32, flexWrap: 'wrap' }}>
        {STEPS.map((s, i) => (
          <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <button
              onClick={() => i <= stepIndex && setStep(s.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 14px',
                borderRadius: 20,
                border: 'none',
                fontSize: '0.78rem',
                fontWeight: i === stepIndex ? 600 : 400,
                cursor: i <= stepIndex ? 'pointer' : 'default',
                background: i === stepIndex ? 'rgba(99,102,241,0.15)' : i < stepIndex ? 'rgba(16,185,129,0.1)' : 'var(--bg-elevated)',
                color: i === stepIndex ? 'var(--brand-primary-light)' : i < stepIndex ? 'var(--status-success)' : 'var(--text-disabled)',
                transition: 'all var(--transition-fast)',
              }}
            >
              {i < stepIndex ? <Check size={12} /> : <span>{i + 1}</span>}
              {s.label}
            </button>
            {i < STEPS.length - 1 && (
              <div style={{ width: 20, height: 1, background: i < stepIndex ? 'var(--status-success)' : 'var(--border-default)' }} />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="glass-card" style={{ padding: '28px', marginBottom: 24 }}>
        {/* Step 1: Provider */}
        {step === 'provider' && (
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Select Provider</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 24 }}>
              Choose the database type you want to connect
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
              {/* PostgreSQL */}
              <button
                onClick={() => { update('provider_type', 'postgresql'); update('port', 5432); }}
                style={{
                  padding: '24px',
                  borderRadius: 14,
                  border: form.provider_type === 'postgresql' ? '2px solid var(--brand-primary)' : '1px solid var(--border-default)',
                  background: form.provider_type === 'postgresql' ? 'rgba(99,102,241,0.08)' : 'var(--bg-elevated)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                  <Database size={24} style={{ color: '#6366f1' }} />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>PostgreSQL</h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Local PostgreSQL database</p>
                <span className="badge badge-info" style={{ marginTop: 10 }}>Local</span>
              </button>

              {/* MySQL */}
              <button
                onClick={() => { update('provider_type', 'mysql'); update('port', 3306); update('use_connection_string', false); }}
                style={{
                  padding: '24px',
                  borderRadius: 14,
                  border: form.provider_type === 'mysql' ? '2px solid var(--brand-primary)' : '1px solid var(--border-default)',
                  background: form.provider_type === 'mysql' ? 'rgba(99,102,241,0.08)' : 'var(--bg-elevated)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(139,92,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                  <Database size={24} style={{ color: '#8b5cf6' }} />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>MySQL</h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Local or Remote MySQL database</p>
                <span className="badge badge-info" style={{ marginTop: 10 }}>Local</span>
              </button>

              {/* SQL Server */}
              <button
                onClick={() => { update('provider_type', 'sqlserver'); update('port', 1433); update('use_connection_string', false); }}
                style={{
                  padding: '24px',
                  borderRadius: 14,
                  border: form.provider_type === 'sqlserver' ? '2px solid var(--brand-primary)' : '1px solid var(--border-default)',
                  background: form.provider_type === 'sqlserver' ? 'rgba(99,102,241,0.08)' : 'var(--bg-elevated)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                  <Database size={24} style={{ color: '#3b82f6' }} />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>SQL Server</h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Enterprise Microsoft SQL Server</p>
                <span className="badge badge-info" style={{ marginTop: 10 }}>Enterprise</span>
              </button>

              {/* MongoDB */}
              <button
                onClick={() => {
                  update('provider_type', 'mongodb');
                  update('port', 27017);
                  update('use_connection_string', true);
                  update('deployment', 'self_hosted');
                }}
                style={{
                  padding: '24px',
                  borderRadius: 14,
                  border: form.provider_type === 'mongodb' ? '2px solid var(--status-success)' : '1px solid var(--border-default)',
                  background: form.provider_type === 'mongodb' ? 'rgba(16,185,129,0.08)' : 'var(--bg-elevated)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(16,185,129,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                  <Globe size={24} style={{ color: '#10b981' }} />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>MongoDB</h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>MongoDB self-hosted or Atlas cloud</p>
                {/* Deployment selector inside card when selected */}
                {form.provider_type === 'mongodb' && (
                  <div style={{ marginTop: 12, display: 'flex', gap: 8 }} onClick={e => e.stopPropagation()}>
                    {(['self_hosted', 'atlas'] as const).map(dep => (
                      <button
                        key={dep}
                        onClick={e => {
                          e.stopPropagation();
                          update('deployment', dep);
                          update('use_connection_string', dep === 'atlas');
                          if (dep === 'atlas') update('ssl_enabled', true);
                        }}
                        style={{
                          padding: '4px 12px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: '0.72rem',
                          fontWeight: form.deployment === dep ? 600 : 400,
                          background: form.deployment === dep ? 'rgba(16,185,129,0.25)' : 'rgba(255,255,255,0.08)',
                          color: form.deployment === dep ? 'var(--status-success)' : 'var(--text-muted)',
                        }}
                      >
                        {dep === 'atlas' ? '☁ Atlas' : '🖥 Self-hosted'}
                      </button>
                    ))}
                  </div>
                )}
                {form.provider_type !== 'mongodb' && (
                  <span className="badge badge-success" style={{ marginTop: 10 }}>NoSQL</span>
                )}
              </button>

              {/* Supabase */}
              <button
                onClick={() => {
                  update('provider_type', 'supabase');
                  update('port', 5432);
                  update('use_connection_string', false);
                  update('ssl_enabled', true);
                  update('supabase_method', 'project');
                  update('database_name', 'postgres');
                  update('username', 'postgres');
                }}
                style={{
                  padding: '24px',
                  borderRadius: 14,
                  border: form.provider_type === 'supabase' ? '2px solid var(--brand-primary)' : '1px solid var(--border-default)',
                  background: form.provider_type === 'supabase' ? 'rgba(99,102,241,0.08)' : 'var(--bg-elevated)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                  <Database size={24} style={{ color: '#6366f1' }} />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>Supabase</h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Managed cloud PostgreSQL database</p>
                <span className="badge badge-success" style={{ marginTop: 10 }}>Cloud</span>
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Connection */}
        {step === 'connection' && (
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Connection Details</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 24 }}>
              Configure the connection to your {form.provider_type === 'postgresql' ? 'PostgreSQL' : form.provider_type === 'mysql' ? 'MySQL' : form.provider_type === 'sqlserver' ? 'SQL Server' : form.provider_type === 'supabase' ? 'Supabase' : 'MongoDB'} database
            </p>

            <div style={{ display: 'grid', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Source Name</label>
                <input className="input-field" value={form.name} onChange={e => update('name', e.target.value)} placeholder={form.provider_type === 'postgresql' ? 'e.g., Production PostgreSQL' : form.provider_type === 'mysql' ? 'e.g., Sales MySQL' : form.provider_type === 'sqlserver' ? 'e.g., Main SQL Server' : form.provider_type === 'supabase' ? 'e.g., Supabase Analytics' : 'e.g., Atlas Production'} />
              </div>

              {(form.provider_type === 'mongodb' || form.provider_type === 'postgresql' || form.provider_type === 'mysql' || form.provider_type === 'sqlserver' || form.provider_type === 'supabase') && (
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Use Connection String (URI)</label>
                  <button
                    type="button"
                    onClick={() => update('use_connection_string', !form.use_connection_string)}
                    style={{
                      width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                      background: form.use_connection_string ? 'var(--brand-primary)' : 'var(--text-disabled)',
                      position: 'relative', transition: 'background 0.2s',
                    }}
                  >
                    <div style={{
                      width: 18, height: 18, borderRadius: '50%', background: 'white',
                      position: 'absolute', top: 3,
                      left: form.use_connection_string ? 23 : 3,
                      transition: 'left 0.2s',
                    }} />
                  </button>
                </div>
              )}

              {form.use_connection_string ? (
                <>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Connection String (URI)</label>
                    <input className="input-field mono" value={form.connection_string} onChange={e => update('connection_string', e.target.value)} placeholder={form.provider_type === 'postgresql' ? 'postgresql://username:password@localhost:5432/database' : form.provider_type === 'mysql' ? 'mysql://username:password@localhost:3306/database' : form.provider_type === 'sqlserver' ? 'mssql+pyodbc://username:password@localhost:1433/database?driver=ODBC+Driver+18+for+SQL+Server' : form.provider_type === 'supabase' ? 'postgresql://postgres.xyz:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres' : 'mongodb+srv://user:pass@cluster.mongodb.net'} style={{ fontSize: '0.82rem' }} />
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-disabled)', marginTop: 4 }}>Paste your database connection URI</p>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Database Name</label>
                    <input className="input-field" value={form.database_name} onChange={e => update('database_name', e.target.value)} placeholder={form.provider_type === 'postgresql' || form.provider_type === 'supabase' ? 'postgres' : form.provider_type === 'mysql' ? 'my_database' : form.provider_type === 'sqlserver' ? 'master' : 'myDatabase'} />
                  </div>
                </>
              ) : form.provider_type === 'supabase' ? (
                <>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Connection Method</label>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <button
                        type="button"
                        onClick={() => { update('supabase_method', 'project'); update('host', ''); }}
                        style={{
                          flex: 1, padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', border: '1px solid var(--border-default)',
                          background: form.supabase_method === 'project' ? 'rgba(99,102,241,0.15)' : 'var(--bg-elevated)',
                          color: form.supabase_method === 'project' ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                          fontWeight: form.supabase_method === 'project' ? 600 : 400,
                        }}
                      >
                        Project URL / Ref ID
                      </button>
                      <button
                        type="button"
                        onClick={() => { update('supabase_method', 'direct'); }}
                        style={{
                          flex: 1, padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', border: '1px solid var(--border-default)',
                          background: form.supabase_method === 'direct' ? 'rgba(99,102,241,0.15)' : 'var(--bg-elevated)',
                          color: form.supabase_method === 'direct' ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                          fontWeight: form.supabase_method === 'direct' ? 600 : 400,
                        }}
                      >
                        Direct Parameters
                      </button>
                    </div>
                  </div>

                  {form.supabase_method === 'project' ? (
                    <div style={{ display: 'grid', gap: 14 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Project URL</label>
                        <input className="input-field" value={form.project_url} onChange={e => {
                          update('project_url', e.target.value);
                          const m = e.target.value.match(/https?:\/\/([^.]+)\.supabase\.(?:co|net|com)/);
                          if (m) update('project_ref', m[1]);
                        }} placeholder="https://xyz.supabase.co" />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Project Reference ID (Optional)</label>
                        <input className="input-field" value={form.project_ref} onChange={e => update('project_ref', e.target.value)} placeholder="xyz" />
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Host</label>
                        <input className="input-field" value={form.host} onChange={e => update('host', e.target.value)} placeholder="db.xyz.supabase.co" />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Port</label>
                        <input className="input-field" type="number" value={form.port} onChange={e => update('port', parseInt(e.target.value) || 0)} />
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px', background: 'var(--bg-elevated)', borderRadius: 12 }}>
                    <div style={{ flex: 1 }}>
                      <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-primary)', fontWeight: 600 }}>Connection Pooler (Port 6543)</span>
                      <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)' }}>Utilize transaction pooler endpoint</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        const nextVal = !form.pooler_enabled;
                        update('pooler_enabled', nextVal);
                        update('port', nextVal ? 6543 : 5432);
                      }}
                      style={{
                        width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                        background: form.pooler_enabled ? 'var(--brand-primary)' : 'var(--text-disabled)',
                        position: 'relative', transition: 'background 0.2s',
                      }}
                    >
                      <div style={{
                        width: 18, height: 18, borderRadius: '50%', background: 'white',
                        position: 'absolute', top: 3,
                        left: form.pooler_enabled ? 23 : 3,
                        transition: 'left 0.2s',
                      }} />
                    </button>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Database Name</label>
                    <input className="input-field" value={form.database_name} onChange={e => update('database_name', e.target.value)} placeholder="postgres" />
                  </div>
                </>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Host</label>
                    <input className="input-field" value={form.host} onChange={e => update('host', e.target.value)} placeholder="localhost" />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Port</label>
                    <input className="input-field" type="number" value={form.port} onChange={e => update('port', parseInt(e.target.value) || 0)} />
                  </div>
                  {form.provider_type === 'sqlserver' && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Instance Name (Optional)</label>
                      <input className="input-field" value={form.instance_name} onChange={e => update('instance_name', e.target.value)} placeholder="SQLEXPRESS" />
                    </div>
                  )}
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Database Name</label>
                    <input className="input-field" value={form.database_name} onChange={e => update('database_name', e.target.value)} placeholder={form.provider_type === 'postgresql' ? 'postgres' : form.provider_type === 'mysql' ? 'my_database' : form.provider_type === 'sqlserver' ? 'master' : 'myDatabase'} />
                  </div>
                </div>
              )}

              {/* MongoDB: Replica Set and Direct Connection (self-hosted manual) */}
              {form.provider_type === 'mongodb' && !form.use_connection_string && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Replica Set Name (Optional)</label>
                    <input className="input-field" value={form.replica_set} onChange={e => update('replica_set', e.target.value)} placeholder="rs0" />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingTop: 22 }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Direct Connection</span>
                    <button
                      type="button"
                      onClick={() => update('direct_connection', !form.direct_connection)}
                      style={{
                        width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                        background: form.direct_connection ? 'var(--brand-primary)' : 'var(--text-disabled)',
                        position: 'relative', transition: 'background 0.2s',
                      }}
                    >
                      <div style={{
                        width: 18, height: 18, borderRadius: '50%', background: 'white',
                        position: 'absolute', top: 3,
                        left: form.direct_connection ? 23 : 3,
                        transition: 'left 0.2s',
                      }} />
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Environment</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {(['development', 'staging', 'production'] as const).map(env => (
                    <button
                      key={env}
                      onClick={() => update('environment', env)}
                      style={{
                        padding: '8px 18px', borderRadius: 8, border: 'none', cursor: 'pointer',
                        background: form.environment === env ? 'rgba(99,102,241,0.15)' : 'var(--bg-elevated)',
                        color: form.environment === env ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                        fontWeight: form.environment === env ? 600 : 400, fontSize: '0.8rem',
                        textTransform: 'capitalize', transition: 'all var(--transition-fast)',
                      }}
                    >
                      {env}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Credentials */}
        {step === 'credentials' && (
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Credentials</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 24 }}>
              {form.use_connection_string ? 'Credentials are included in the connection string. You can skip this step.' : 'Enter the database authentication credentials'}
            </p>
            {!form.use_connection_string && (
              <div style={{ display: 'grid', gap: 16, maxWidth: 400 }}>
                {form.provider_type === 'sqlserver' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Authentication Method</label>
                    <select 
                      className="input-field"
                      value={form.authentication_method}
                      onChange={e => {
                        update('authentication_method', e.target.value);
                        if (e.target.value === 'integrated') {
                          update('username', '');
                          update('password', '');
                        }
                      }}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: 8,
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-default)',
                        color: 'var(--text-primary)',
                      }}
                    >
                      <option value="sql_server">SQL Server Authentication</option>
                      <option value="integrated">Windows / Integrated Authentication</option>
                    </select>
                  </div>
                )}
                {(!form.use_connection_string && (form.provider_type !== 'sqlserver' || form.authentication_method === 'sql_server')) && (
                  <>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Username</label>
                      <input className="input-field" value={form.username} onChange={e => update('username', e.target.value)} placeholder={form.provider_type === 'postgresql' ? 'postgres' : form.provider_type === 'mysql' ? 'root' : 'sa'} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Password</label>
                      <input className="input-field" type="password" value={form.password} onChange={e => update('password', e.target.value)} placeholder="••••••••" />
                    </div>
                  </>
                )}
                {form.provider_type === 'mongodb' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>Auth Source</label>
                    <input className="input-field" value={form.auth_source} onChange={e => update('auth_source', e.target.value)} placeholder="admin" />
                  </div>
                )}
              </div>
            )}
            <div style={{ marginTop: 20, padding: '12px 16px', background: 'var(--status-info-bg)', borderRadius: 10, fontSize: '0.78rem', color: 'var(--status-info)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Lock size={14} /> Credentials are encrypted before storage
            </div>
          </div>
        )}

        {/* Step 4: Security */}
        {step === 'security' && (
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Security</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 24 }}>
              Configure connection security options
            </p>
            <div style={{ display: 'grid', gap: 16, maxWidth: 400 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px', background: 'var(--bg-elevated)', borderRadius: 12 }}>
                <Shield size={20} style={{ color: 'var(--brand-primary)' }} />
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.85rem', fontWeight: 500 }}>SSL/TLS Encryption</p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Encrypt connection to database</p>
                </div>
                <button
                  onClick={() => update('ssl_enabled', !form.ssl_enabled)}
                  style={{
                    width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                    background: form.ssl_enabled ? 'var(--brand-primary)' : 'var(--text-disabled)',
                    position: 'relative', transition: 'background 0.2s',
                  }}
                >
                  <div style={{
                    width: 18, height: 18, borderRadius: '50%', background: 'white',
                    position: 'absolute', top: 3,
                    left: form.ssl_enabled ? 23 : 3,
                    transition: 'left 0.2s',
                  }} />
                </button>
              </div>

              {form.provider_type === 'sqlserver' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px', background: 'var(--bg-elevated)', borderRadius: 12 }}>
                  <ShieldAlert size={20} style={{ color: form.trust_server_certificate ? 'var(--status-warning)' : 'var(--brand-primary)' }} />
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: 500 }}>Trust Server Certificate</p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Trust database self-signed certificates</p>
                  </div>
                  <button
                    onClick={() => update('trust_server_certificate', !form.trust_server_certificate)}
                    style={{
                      width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                      background: form.trust_server_certificate ? 'var(--brand-primary)' : 'var(--text-disabled)',
                      position: 'relative', transition: 'background 0.2s',
                    }}
                  >
                    <div style={{
                      width: 18, height: 18, borderRadius: '50%', background: 'white',
                      position: 'absolute', top: 3,
                      left: form.trust_server_certificate ? 23 : 3,
                      transition: 'left 0.2s',
                    }} />
                  </button>
                </div>
              )}

              {form.provider_type === 'supabase' && (
                <div style={{ marginTop: 20, borderTop: '1px solid var(--border-default)', paddingTop: 20 }}>
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>Metadata Discovery Scope</h3>
                  <div style={{ display: 'grid', gap: 12 }}>
                    {/* Include platform schemas */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <input
                        type="checkbox"
                        id="include_provider_managed_schemas"
                        checked={form.include_provider_managed_schemas}
                        onChange={e => update('include_provider_managed_schemas', e.target.checked)}
                        style={{ width: 16, height: 16, cursor: 'pointer' }}
                      />
                      <label htmlFor="include_provider_managed_schemas" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        Include provider-managed schemas (auth, storage, realtime)
                      </label>
                    </div>

                    {/* Discover RLS */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <input
                        type="checkbox"
                        id="discover_rls"
                        checked={form.discover_rls}
                        onChange={e => update('discover_rls', e.target.checked)}
                        style={{ width: 16, height: 16, cursor: 'pointer' }}
                      />
                      <label htmlFor="discover_rls" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        Discover Row Level Security (RLS) policies
                      </label>
                    </div>

                    {/* Discover Extensions */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <input
                        type="checkbox"
                        id="discover_extensions"
                        checked={form.discover_extensions}
                        onChange={e => update('discover_extensions', e.target.checked)}
                        style={{ width: 16, height: 16, cursor: 'pointer' }}
                      />
                      <label htmlFor="discover_extensions" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        Discover extensions & pgvector columns
                      </label>
                    </div>

                    {/* Discover Functions & Triggers */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <input
                        type="checkbox"
                        id="discover_functions"
                        checked={form.discover_functions}
                        onChange={e => update('discover_functions', e.target.checked)}
                        style={{ width: 16, height: 16, cursor: 'pointer' }}
                      />
                      <label htmlFor="discover_functions" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        Discover functions, triggers, and routines
                      </label>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 5: Test */}
        {step === 'test' && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Test Connection</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 28 }}>
              Verify that Pivota can connect to your database
            </p>

            {!testResult && !testing && (
              <button className="btn-primary" onClick={handleTest} style={{ padding: '14px 32px', fontSize: '0.9rem' }}>
                <Wifi size={18} /> Test Connection
              </button>
            )}

            {testing && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Loader2 size={32} className="animate-spin-slow" style={{ color: 'var(--brand-primary)' }} />
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Connecting to database...</p>
              </div>
            )}

            {testResult && (
              <div style={{ maxWidth: 460, margin: '0 auto', textAlign: 'left' }}>
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 14,
                    padding: 24,
                    borderRadius: 14,
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    marginBottom: 20,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid var(--border-default)', paddingBottom: 14, marginBottom: 6 }}>
                    {testResult.success ? (
                      <CheckCircle size={32} style={{ color: 'var(--status-success)' }} />
                    ) : (
                      <XCircle size={32} style={{ color: 'var(--status-error)' }} />
                    )}
                    <div>
                      <p style={{ fontSize: '1rem', fontWeight: 600, color: testResult.success ? 'var(--status-success)' : 'var(--status-error)' }}>
                        {testResult.success ? 'Connection Successful' : 'Connection Failed'}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {testResult.latency_ms ? `Latency: ${testResult.latency_ms}ms` : ''}
                        {testResult.server_version ? ` • Server: ${testResult.server_version}` : ''}
                      </p>
                    </div>
                  </div>

                  {/* Staged steps checklist */}
                  {testResult.steps && testResult.steps.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>Diagnostics Checklist</p>
                      {testResult.steps.map((s: any) => {
                        const stepLabels: Record<string, string> = {
                          configuration: 'Configuration validation',
                          host_validation: 'SSRF & host safety policy validation',
                          dns: 'DNS Host resolution',
                          network: 'TCP Port connection',
                          tls: 'SSL/TLS security handshakes',
                          authentication: 'Database credentials authentication',
                          database_access: 'Database catalog access',
                          metadata_access: 'Schema metadata SELECT permissions',
                          health: 'System version & health checks'
                        };
                        const label = stepLabels[s.name] || s.name.replace(/_/g, ' ');

                        return (
                          <div key={s.name} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: '0.8rem' }}>
                            <div style={{ marginTop: 2 }}>
                              {s.status === 'success' && <Check size={14} style={{ color: 'var(--status-success)' }} />}
                              {s.status === 'failed' && <X size={14} style={{ color: 'var(--status-error)' }} />}
                              {s.status === 'skipped' && <span style={{ color: 'var(--text-disabled)', fontSize: '0.8rem', fontWeight: 600 }}>—</span>}
                            </div>
                            <div style={{ flex: 1 }}>
                              <span style={{ fontWeight: s.status === 'success' ? 500 : 400, color: s.status === 'success' ? 'var(--text-primary)' : s.status === 'skipped' ? 'var(--text-disabled)' : 'var(--status-error)' }}>
                                {label}
                              </span>
                              {s.message && s.status === 'failed' && (
                                <p style={{ fontSize: '0.72rem', color: 'var(--status-error)', marginTop: 2, lineHeight: 1.3 }}>{s.message}</p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Clean enterprise error troubleshooting */}
                  {!testResult.success && testResult.details && testResult.details.error_code && (
                    <div style={{ marginTop: 10, padding: 14, background: 'rgba(239, 68, 68, 0.04)', border: '1px solid rgba(239, 68, 68, 0.12)', borderRadius: 10 }}>
                      <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--status-error)', marginBottom: 4 }}>
                        {testResult.details.error_title || 'Diagnostic Alert'} ({testResult.details.error_code})
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 8, lineHeight: 1.4 }}>
                        {testResult.message.replace(/^[A-Za-z0-9_ ]+:\s*/, '')}
                      </p>
                      {testResult.details.suggested_action && (
                        <p style={{ fontSize: '0.72rem', color: 'var(--brand-primary-light)', fontWeight: 500, lineHeight: 1.4 }}>
                          <strong>Action Plan:</strong> {testResult.details.suggested_action}
                        </p>
                      )}
                    </div>
                  )}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <button className="btn-ghost" onClick={handleTest} style={{ fontSize: '0.8rem' }}>
                    <RefreshCw size={14} /> Test Again
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 6: Review */}
        {step === 'review' && (
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Review & Save</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 24 }}>
              Confirm your data source configuration
            </p>

            {error && (
              <div style={{ background: 'var(--status-error-bg)', color: 'var(--status-error)', padding: '10px 14px', borderRadius: 10, fontSize: '0.8rem', marginBottom: 18 }}>
                {error}
              </div>
            )}

            <div style={{ display: 'grid', gap: 12, maxWidth: 500 }}>
              {[
                { label: 'Name', value: form.name },
                { label: 'Provider', value: form.provider_type === 'postgresql' ? 'PostgreSQL (Relational)' : form.provider_type === 'mysql' ? 'MySQL (Relational)' : form.provider_type === 'sqlserver' ? 'SQL Server (Enterprise)' : `MongoDB (${form.deployment === 'atlas' ? 'Atlas Cloud' : 'Self-Hosted'})` },
                { label: 'Host', value: form.use_connection_string ? (form.deployment === 'atlas' ? 'Atlas URI' : 'Connection URI') : form.host },
                { label: 'Port', value: form.provider_type === 'mongodb' && form.deployment === 'atlas' ? 'N/A (SRV)' : String(form.port) },
                { label: 'Database', value: form.database_name },
                ...(form.provider_type === 'sqlserver' && form.instance_name ? [{ label: 'Instance', value: form.instance_name }] : []),
                ...(form.provider_type === 'sqlserver' ? [{ label: 'Auth Method', value: form.authentication_method === 'integrated' ? 'Integrated' : 'SQL Server' }] : []),
                ...(form.provider_type === 'mongodb' && form.replica_set ? [{ label: 'Replica Set', value: form.replica_set }] : []),
                ...(form.provider_type === 'mongodb' ? [{ label: 'Auth Source', value: form.auth_source || 'admin' }] : []),
                { label: 'Username', value: form.username || '—' },
                { label: 'SSL', value: form.ssl_enabled ? 'Enabled' : 'Disabled' },
                { label: 'Environment', value: form.environment },
              ].map(row => (
                <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 8 }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{row.label}</span>
                  <span className="mono" style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 500 }}>{row.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button className="btn-ghost" onClick={stepIndex === 0 ? onClose : prevStep}>
          <ArrowLeft size={16} /> {stepIndex === 0 ? 'Cancel' : 'Back'}
        </button>
        <div style={{ display: 'flex', gap: 10 }}>
          {step === 'review' ? (
            <button className="btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? <><Loader2 size={16} className="animate-spin-slow" /> Saving...</> : <><Check size={16} /> Save Data Source</>}
            </button>
          ) : (
            <button className="btn-primary" onClick={nextStep} disabled={!canProceed()}>
              Next <ArrowRight size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

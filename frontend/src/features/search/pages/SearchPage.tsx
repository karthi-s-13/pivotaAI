import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Database, 
  Table, 
  Eye, 
  Columns, 
  Layers, 
  ArrowRight,
  Info,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { catalogApi } from '../../catalog/api/catalogApi';
import type { SearchMatchItem } from '../../catalog/api/catalogApi';

export default function SearchPage() {
  const navigate = useNavigate();

  // Search states
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<SearchMatchItem[]>([]);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'all' | 'database' | 'table' | 'view' | 'column'>('all');

  // Debounced search trigger
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      setLoading(true);
      setError('');
      try {
        const resp = await catalogApi.search(query);
        setResults(resp.results);
      } catch (err: any) {
        setError('Failed to query catalog search. Ensure data source metadata sync has finished.');
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  // Tab filter logic
  const filteredResults = results.filter(item => {
    if (activeTab === 'all') return true;
    return item.type === activeTab;
  });

  // Handle clicking a search result
  const handleItemClick = (item: SearchMatchItem) => {
    // Navigate to catalog with query param. Catalog Page will resolve the database and schema
    navigate(`/catalog?objectId=${item.id}`);
  };

  // Pre-configured quick search examples
  const searchSuggestions = ['users', 'orders', 'transactions', 'customer', 'id'];

  return (
    <div className="animate-fade-in" style={{ maxWidth: 840, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24, padding: '20px 0' }}>
      
      {/* Search Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: 8 }} className="gradient-text">Global Catalog Search</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: 480, margin: '0 auto', lineHeight: 1.5 }}>
          Search for columns, database names, table schemas, views, and index keys across all enterprise sources.
        </p>
      </div>

      {/* Main Search Input */}
      <div style={{ position: 'relative' }}>
        <Search size={20} style={{ position: 'absolute', left: 16, top: 15, color: 'var(--text-muted)' }} />
        <input 
          type="text" 
          placeholder="Search metadata (e.g., column names, datatypes, descriptions...)" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="input-field"
          style={{
            paddingLeft: 48,
            height: 52,
            fontSize: '1rem',
            border: query ? '1px solid var(--brand-primary)' : '1px solid var(--border-default)',
            background: '#ffffff',
            color: 'var(--text-primary)',
          }}
        />
        {loading && (
          <div style={{ position: 'absolute', right: 16, top: 16 }}>
            <Loader2 size={20} className="animate-spin" style={{ color: 'var(--brand-primary)' }} />
          </div>
        )}
      </div>

      {/* Suggested keywords */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Quick Search:</span>
        {searchSuggestions.map(word => (
          <button
            key={word}
            onClick={() => setQuery(word)}
            style={{
              padding: '4px 12px',
              borderRadius: 9999,
              border: '1px solid var(--border-default)',
              background: '#ffffff',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            className="hover-row"
          >
            {word}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ background: 'var(--status-error-bg)', border: '1px solid var(--status-error)', borderRadius: 10, padding: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
          <AlertCircle size={16} style={{ color: 'var(--status-error)' }} />
          <span style={{ fontSize: '0.8rem', color: 'var(--status-error)' }}>{error}</span>
        </div>
      )}

      {/* Search results container */}
      {query.trim() === '' ? (
        <div
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            borderRadius: 12,
            padding: 24,
            display: 'flex',
            gap: 16,
            alignItems: 'flex-start'
          }}
        >
          <Info size={20} style={{ color: 'var(--brand-primary)', marginTop: 2, flexShrink: 0 }} />
          <div>
            <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Search Guidelines</h4>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 6, lineHeight: 1.4 }}>
              <li><strong>Namespace Filtering:</strong> Matches database fields, views, columns, and properties.</li>
              <li><strong>Description Scans:</strong> Matches comments registered on Postgres schemas/columns.</li>
              <li><strong>Datatypes Lookup:</strong> Find columns matching a specific type like <code>integer</code>, <code>uuid</code>, or <code>timestamp</code>.</li>
            </ul>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          
          {/* Tab Filter Pills */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-default)', gap: 16 }}>
            {[
              { id: 'all', label: `All (${results.length})` },
              { id: 'database', label: `Databases (${results.filter(r => r.type === 'database').length})` },
              { id: 'table', label: `Tables (${results.filter(r => r.type === 'table').length})` },
              { id: 'view', label: `Views (${results.filter(r => r.type === 'view').length})` },
              { id: 'column', label: `Columns (${results.filter(r => r.type === 'column').length})` },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  paddingBottom: 10,
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: activeTab === tab.id ? 'var(--brand-primary)' : 'var(--text-muted)',
                  border: 'none',
                  background: 'none',
                  borderBottom: `2px solid ${activeTab === tab.id ? 'var(--brand-primary)' : 'transparent'}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Results Lists */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {loading ? (
              // Loading cards skeletons
              Array.from({ length: 3 }).map((_, idx) => (
                <div 
                  key={idx} 
                  style={{ 
                    height: 90, 
                    borderRadius: 12, 
                    background: 'var(--bg-elevated)', 
                    border: '1px solid var(--border-default)',
                    animation: 'pulse 1.5s infinite ease-in-out'
                  }} 
                />
              ))
            ) : filteredResults.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '48px 0',
                  color: 'var(--text-muted)',
                  fontSize: '0.85rem',
                  background: 'var(--bg-elevated)',
                  border: '1px dashed var(--border-default)',
                  borderRadius: 12,
                }}
              >
                No catalog matches found for "{query}".
              </div>
            ) : (
              filteredResults.map(item => {
                // Type icon (differentiated by shape, not color — monochrome per the design system)
                const typeIcons: Record<string, React.ReactNode> = {
                  database: <Database size={12} />,
                  table: <Table size={12} />,
                  view: <Eye size={12} />,
                  column: <Columns size={12} />,
                };
                const icon = typeIcons[item.type] || <Layers size={12} />;

                return (
                  <div
                    key={item.id + '_' + item.type + '_' + item.name}
                    onClick={() => handleItemClick(item)}
                    style={{
                      background: '#ffffff',
                      border: '1px solid var(--border-default)',
                      borderRadius: 12,
                      padding: 16,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    className="hover-card"
                  >
                    <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                      <div
                        style={{
                          width: 32,
                          height: 32,
                          borderRadius: 8,
                          background: 'var(--bg-elevated)',
                          color: 'var(--text-primary)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginTop: 2,
                          flexShrink: 0
                        }}
                      >
                        {icon}
                      </div>
                      <div>
                        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 4 }}>
                          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>{item.name}</span>
                          <span
                            style={{
                              fontSize: '0.62rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '1px 8px',
                              borderRadius: 9999,
                              background: '#000000',
                              color: '#ffffff'
                            }}
                          >
                            {item.type}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>via {item.data_source_name}</span>
                        </div>
                        <p style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)', margin: '0 0 4px 0' }}>
                          {item.details}
                        </p>
                        {item.description && (
                          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0 }}>
                            {item.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div style={{ color: 'var(--text-disabled)' }} className="arrow-hover">
                      <ArrowRight size={16} />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

import { useState } from 'react';
import { Terminal, Copy, Check, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
// @ts-ignore
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
// @ts-ignore
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface SQLBlockProps {
  sql: string;
  queryType?: string;
  databaseId?: string;
  databaseName?: string;
}

export default function SQLBlock({ sql, queryType = 'SQL_QUERY', databaseId, databaseName }: SQLBlockProps) {
  const [copied, setCopied] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenInEditor = () => {
    if (!databaseId) return;
    
    // Redirect to Query Editor in CatalogPage via query parameters
    const params = new URLSearchParams();
    params.set('queryToolDbId', databaseId);
    params.set('queryToolDbName', databaseName || 'Database');
    params.set('sql', sql);
    
    window.open(`/catalog?${params.toString()}`, '_blank');
  };

  return (
    <div
      style={{
        margin: '12px 0',
        borderRadius: '6px',
        border: '1px solid var(--border-default)',
        background: '#1e1e1e',
        overflow: 'hidden',
      }}
    >
      {/* Header toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 14px',
          background: '#181818',
          borderBottom: '1px solid #2d2d2d',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: 600, color: '#9ca3af' }}>
          <Terminal size={14} />
          <span>{queryType === 'MONGO_QUERY' ? 'Generated MongoDB Pipeline' : 'Generated SQL Query'}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Collapse toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {isCollapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
          </button>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.72rem',
            }}
            className="hover:text-white"
          >
            {copied ? <Check size={13} color="#16a34a" /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Open in Editor Link (only for SQL queries when DB info is resolved) */}
          {queryType !== 'MONGO_QUERY' && databaseId && (
            <button
              onClick={handleOpenInEditor}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem',
              }}
              className="hover:text-white"
            >
              <ExternalLink size={13} />
              <span>Query Editor</span>
            </button>
          )}
        </div>
      </div>

      {/* Code body */}
      {!isCollapsed && (
        <div style={{ fontSize: '0.8rem' }}>
          <SyntaxHighlighter
            language={queryType === 'MONGO_QUERY' ? 'json' : 'sql'}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: '12px 16px',
              background: '#1e1e1e',
            }}
          >
            {sql}
          </SyntaxHighlighter>
        </div>
      )}
    </div>
  );
}

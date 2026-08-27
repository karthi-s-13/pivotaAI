import { useState } from 'react';
import { Database, ChevronDown, Check, Server } from 'lucide-react';
import { useAIStore } from '../stores/aiStore';

export default function DataContextSelector() {
  const { dataSources, selectedContext, setSelectedContext } = useAIStore();
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (ds: any, db: any, schema: string) => {
    setSelectedContext({
      dataSourceId: ds.id,
      dataSourceName: ds.name,
      provider: ds.provider,
      database: db.name,
      schema,
    });
    setIsOpen(false);
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '9999px',
          border: '1px solid var(--border-default)',
          background: 'var(--bg-surface)',
          fontSize: '0.82rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
          cursor: 'pointer',
          transition: 'all var(--transition-fast)',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = 'var(--bg-elevated)';
        }}
        onMouseLeave={e => {
          if (!isOpen) e.currentTarget.style.background = 'var(--bg-surface)';
        }}
      >
        <Database size={15} style={{ color: 'var(--text-secondary)' }} />
        <span>
          {selectedContext
            ? `${selectedContext.dataSourceName} • ${selectedContext.database}${
                selectedContext.schema ? `.${selectedContext.schema}` : ''
              }`
            : 'Select Data Context'}
        </span>
        <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
      </button>

      {isOpen && (
        <>
          <div
            onClick={() => setIsOpen(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 99,
            }}
          />
          <div
            style={{
              position: 'absolute',
              right: 0,
              top: '110%',
              width: '320px',
              maxHeight: '400px',
              overflowY: 'auto',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: '8px',
              zIndex: 100,
              padding: '8px 0',
            }}
          >
            <div style={{ padding: '6px 16px', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Select Active Database
            </div>

            {dataSources.length === 0 ? (
              <div style={{ padding: '16px', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                No active connections available.
              </div>
            ) : (
              dataSources.map((ds) => (
                <div key={ds.id} style={{ borderBottom: '1px solid var(--bg-elevated)', padding: '4px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 16px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                    <Server size={12} />
                    <span>{ds.name}</span>
                    <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>({ds.provider})</span>
                  </div>

                  {ds.databases.map((db) => (
                    <div key={db.name}>
                      {db.schemas.length === 0 ? (
                        <button
                          onClick={() => handleSelect(ds, db, '')}
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '6px 24px',
                            background: 'transparent',
                            border: 'none',
                            textAlign: 'left',
                            fontSize: '0.8rem',
                            color: 'var(--text-primary)',
                            cursor: 'pointer',
                          }}
                          className="hover:bg-[var(--bg-elevated)]"
                        >
                          <span>{db.name}</span>
                          {selectedContext?.dataSourceId === ds.id && selectedContext?.database === db.name && (
                            <Check size={14} />
                          )}
                        </button>
                      ) : (
                        db.schemas.map((schema) => (
                          <button
                            key={schema}
                            onClick={() => handleSelect(ds, db, schema)}
                            style={{
                              width: '100%',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '6px 24px',
                              background: 'transparent',
                              border: 'none',
                              textAlign: 'left',
                              fontSize: '0.8rem',
                              color: 'var(--text-primary)',
                              cursor: 'pointer',
                            }}
                            className="hover:bg-[var(--bg-elevated)]"
                          >
                            <span style={{ display: 'flex', gap: 4 }}>
                              <span style={{ fontWeight: 500 }}>{db.name}</span>
                              <span style={{ color: 'var(--text-muted)' }}>.{schema}</span>
                            </span>
                            {selectedContext?.dataSourceId === ds.id &&
                              selectedContext?.database === db.name &&
                              selectedContext?.schema === schema && (
                                <Check size={14} />
                              )}
                          </button>
                        ))
                      )}
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

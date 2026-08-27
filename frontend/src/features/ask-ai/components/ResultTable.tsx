import { useState } from 'react';
import { ChevronLeft, ChevronRight, Table } from 'lucide-react';

interface ResultTableProps {
  columns: string[];
  rows: Record<string, any>[];
  pageSize?: number;
}

export default function ResultTable({ columns, rows, pageSize = 8 }: ResultTableProps) {
  const [currentPage, setCurrentPage] = useState(1);

  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 6,
          padding: '24px',
          border: '1px dashed var(--border-default)',
          borderRadius: '6px',
          color: 'var(--text-secondary)',
          fontSize: '0.82rem',
          margin: '8px 0',
        }}
      >
        <Table size={20} />
        <span>No query records returned.</span>
      </div>
    );
  }

  // Pagination calculation
  const totalRows = rows.length;
  const totalPages = Math.ceil(totalRows / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedRows = rows.slice(startIndex, startIndex + pageSize);

  const formatValue = (val: any) => {
    if (val === null || val === undefined) return <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', fontStyle: 'italic' }}>NULL</span>;
    if (typeof val === 'boolean') return val ? 'TRUE' : 'FALSE';
    if (typeof val === 'object') return JSON.stringify(val);
    return String(val);
  };

  return (
    <div
      style={{
        margin: '12px 0',
        border: '1px solid var(--border-default)',
        borderRadius: '6px',
        background: 'var(--bg-surface)',
        overflow: 'hidden',
      }}
    >
      <div style={{ overflowX: 'auto', width: '100%' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-default)' }}>
              {columns.map((col) => (
                <th
                  key={col}
                  style={{
                    padding: '8px 12px',
                    fontWeight: 700,
                    color: 'var(--text-secondary)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: idx < paginatedRows.length - 1 ? '1px solid var(--bg-elevated)' : 'none',
                }}
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    style={{
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      maxWidth: '240px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={String(row[col] || '')}
                  >
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 12px',
            background: 'var(--bg-elevated)',
            borderTop: '1px solid var(--border-default)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
          }}
        >
          <span>
            Showing <b>{startIndex + 1}</b> to <b>{Math.min(startIndex + pageSize, totalRows)}</b> of <b>{totalRows}</b> results
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '4px',
                borderRadius: '4px',
                border: '1px solid var(--border-default)',
                background: 'var(--bg-surface)',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                opacity: currentPage === 1 ? 0.5 : 1,
              }}
            >
              <ChevronLeft size={14} />
            </button>
            <span>Page <b>{currentPage}</b> of {totalPages}</span>
            <button
              onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '4px',
                borderRadius: '4px',
                border: '1px solid var(--border-default)',
                background: 'var(--bg-surface)',
                cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                opacity: currentPage === totalPages ? 0.5 : 1,
              }}
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

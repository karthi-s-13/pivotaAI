/**
 * Table Node — Represents a table, view, or collection.
 * Displays column count, type badge, and relationship indicator.
 * When expanded, shows inline column chips.
 *
 * Object type (TABLE / VIEW / COLLECTION / MAT VIEW) is differentiated
 * by its badge label only — no color-coding.
 */

import React from 'react';
import type { TableMetadata } from '../../types/dataMap.types';

// Augmented metadata when columns are loaded
interface FullTableMetadata extends TableMetadata {
  columns?: Array<{
    id: string;
    name: string;
    data_type: string;
    native_type: string | null;
    is_primary_key: boolean;
    is_foreign_key: boolean;
    nullable: boolean;
  }>;
  relationships_outbound?: Array<{ id: string; to_table_name: string }>;
  relationships_inbound?: Array<{ id: string; from_table_name: string }>;
}

interface TableNodeProps {
  x: number;
  y: number;
  label: string;
  metadata: FullTableMetadata;
  selected: boolean;
  highlighted: boolean;
  expanded: boolean;
  status: string;
  onSingleClick: () => void;
  onDoubleClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

const BASE_W = 148;
const BASE_H = 62;
const COL_ROW_H = 20;
const MAX_COLS_INLINE = 8;

function getTypeLabel(type: string): string {
  switch (type.toUpperCase()) {
    case 'VIEW': return 'VIEW';
    case 'MATERIALIZED_VIEW': return 'MAT VIEW';
    case 'COLLECTION': return 'COLLECTION';
    default: return 'TABLE';
  }
}

function getDataTypeShort(dtype: string, native: string | null): string {
  const t = (native || dtype).toUpperCase();
  if (t.includes('INT')) return 'INT';
  if (t.includes('VARCHAR') || t.includes('CHAR') || t.includes('TEXT') || t.includes('STRING')) return 'STR';
  if (t.includes('FLOAT') || t.includes('DOUBLE') || t.includes('DECIMAL') || t.includes('NUMERIC')) return 'NUM';
  if (t.includes('BOOL')) return 'BOOL';
  if (t.includes('DATE') || t.includes('TIME') || t.includes('TIMESTAMP')) return 'DATE';
  if (t.includes('JSON') || t.includes('JSONB') || t.includes('OBJECT')) return 'JSON';
  if (t.includes('UUID')) return 'UUID';
  if (t.includes('BYTE') || t.includes('BINARY') || t.includes('BLOB')) return 'BIN';
  return t.slice(0, 4);
}

export const TableNode = React.memo(function TableNode({
  x,
  y,
  label,
  metadata,
  selected,
  highlighted,
  expanded,
  status,
  onSingleClick,
  onDoubleClick,
  onContextMenu,
}: TableNodeProps) {
  const typeLabel = getTypeLabel(metadata.type);
  const isLoading = status === 'loading';

  // If columns loaded and expanded, show inline column list
  const columns = metadata.columns ?? [];
  const showColumns = expanded && columns.length > 0;
  const displayCols = showColumns ? columns.slice(0, MAX_COLS_INLINE) : [];
  const extraCols = showColumns ? Math.max(0, columns.length - MAX_COLS_INLINE) : 0;

  const cardH = showColumns
    ? BASE_H + displayCols.length * COL_ROW_H + (extraCols > 0 ? 18 : 4)
    : BASE_H;

  const px = x - BASE_W / 2;
  const py = y - cardH / 2;

  const borderColor = selected ? '#000000' : highlighted ? '#111827' : '#d1d5db';

  const opacity = highlighted ? 1 : 0.95;

  // Relationship indicators
  const hasRelationships =
    (metadata.relationships_outbound?.length ?? 0) +
    (metadata.relationships_inbound?.length ?? 0) > 0;

  return (
    <g
      transform={`translate(${px}, ${py})`}
      style={{ cursor: 'pointer', opacity }}
      onClick={onSingleClick}
      onDoubleClick={onDoubleClick}
      onContextMenu={onContextMenu}
    >
      {/* Background */}
      <rect
        width={BASE_W}
        height={cardH}
        rx={10}
        fill="#ffffff"
        stroke={borderColor}
        strokeWidth={selected ? 2 : 1.2}
        style={{ transition: 'stroke 0.2s' }}
      />

      {/* Header accent */}
      <rect width={BASE_W} height={4} rx={2} fill="#111827" style={{ pointerEvents: 'none' }} />

      {/* Table grid icon (monochrome) */}
      <g transform="translate(10, 16)" style={{ pointerEvents: 'none' }}>
        <rect width={20} height={18} rx={2} fill="#f3f4f6" stroke="#9ca3af" strokeWidth={1} />
        {/* Grid lines */}
        <line x1={0} y1={6} x2={20} y2={6} stroke="#d1d5db" strokeWidth={0.7} />
        <line x1={0} y1={12} x2={20} y2={12} stroke="#d1d5db" strokeWidth={0.7} />
        <line x1={7} y1={0} x2={7} y2={18} stroke="#d1d5db" strokeWidth={0.7} />
      </g>

      {/* Table name */}
      <text
        x={38}
        y={24}
        fill="#111827"
        fontSize="11"
        fontWeight="700"
        fontFamily="'Open Sans', sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {label.length > 14 ? label.slice(0, 13) + '…' : label}
      </text>

      {/* Type badge — differentiated by label text, not color */}
      <g transform="translate(38, 30)" style={{ pointerEvents: 'none' }}>
        <rect width={typeLabel.length * 5.5 + 6} height={13} rx={3} fill="#f3f4f6" />
        <text
          x={(typeLabel.length * 5.5 + 6) / 2}
          y={9.5}
          textAnchor="middle"
          fill="#374151"
          fontSize="7"
          fontWeight="800"
          fontFamily="'Open Sans', sans-serif"
          letterSpacing="0.5"
        >
          {typeLabel}
        </text>
      </g>

      {/* Column count */}
      {metadata.column_count > 0 && (
        <text
          x={BASE_W - 10}
          y={24}
          textAnchor="end"
          fill="#9ca3af"
          fontSize="8"
          fontFamily="'Open Sans', sans-serif"
          style={{ pointerEvents: 'none' }}
        >
          {metadata.column_count} cols
        </text>
      )}

      {/* Relationship indicator — monochrome dot */}
      {hasRelationships && (
        <circle
          cx={BASE_W - 10}
          cy={38}
          r={3.5}
          fill="#111827"
          style={{ pointerEvents: 'none' }}
        />
      )}

      {/* Row count */}
      {metadata.row_count_estimate > 0 && (
        <text
          x={BASE_W - 16}
          y={38}
          textAnchor="end"
          fill="#9ca3af"
          fontSize="7.5"
          fontFamily="'Open Sans', sans-serif"
          style={{ pointerEvents: 'none' }}
        >
          {metadata.row_count_estimate >= 1000000
            ? `${(metadata.row_count_estimate / 1000000).toFixed(1)}M`
            : metadata.row_count_estimate >= 1000
            ? `${(metadata.row_count_estimate / 1000).toFixed(1)}K`
            : metadata.row_count_estimate}
        </text>
      )}

      {/* Loading indicator */}
      {isLoading && (
        <text
          x={BASE_W / 2}
          y={BASE_H - 8}
          textAnchor="middle"
          fill="#6b7280"
          fontSize="7.5"
          fontFamily="'Open Sans', sans-serif"
          style={{ pointerEvents: 'none' }}
        >
          Loading columns…
        </text>
      )}

      {/* Expand chevron */}
      <g
        transform={`translate(${BASE_W - 18}, ${BASE_H / 2 - 10})`}
        onClick={(e) => {
          e.stopPropagation();
          onDoubleClick();
        }}
        style={{ cursor: 'pointer' }}
      >
        <rect x={-4} y={-4} width={20} height={20} fill="transparent" />
        {expanded ? (
          <path d="M2,11 L6,5 L10,11" fill="none" stroke="#9ca3af" strokeWidth="1.3" />
        ) : (
          <path d="M2,5 L6,11 L10,5" fill="none" stroke="#9ca3af" strokeWidth="1.3" />
        )}
      </g>

      {/* Inline column list */}
      {showColumns && (
        <g transform={`translate(0, ${BASE_H})`} style={{ pointerEvents: 'none' }}>
          {/* Divider */}
          <line x1={8} y1={0} x2={BASE_W - 8} y2={0} stroke="#e5e7eb" strokeWidth={1} />

          {displayCols.map((col, idx) => (
            <g key={col.id} transform={`translate(0, ${idx * COL_ROW_H})`}>
              {/* Alternate row background */}
              {idx % 2 === 0 && (
                <rect width={BASE_W} height={COL_ROW_H} fill="#fafafa" />
              )}
              {/* PK indicator — filled dot */}
              {col.is_primary_key && (
                <circle cx={11} cy={11} r={2.5} fill="#111827" />
              )}
              {/* FK indicator — ring */}
              {col.is_foreign_key && !col.is_primary_key && (
                <circle cx={11} cy={11} r={2.5} fill="none" stroke="#6b7280" strokeWidth={1.2} />
              )}
              {/* Column name */}
              <text
                x={col.is_primary_key || col.is_foreign_key ? 22 : 10}
                y={14}
                fill={col.is_primary_key ? '#111827' : '#374151'}
                fontSize="8.5"
                fontWeight={col.is_primary_key ? '700' : '400'}
                fontFamily="'JetBrains Mono', monospace"
              >
                {col.name.length > 14 ? col.name.slice(0, 13) + '…' : col.name}
              </text>
              {/* Type */}
              <text
                x={BASE_W - 8}
                y={14}
                textAnchor="end"
                fill="#9ca3af"
                fontSize="7.5"
                fontFamily="'JetBrains Mono', monospace"
              >
                {getDataTypeShort(col.data_type, col.native_type)}
              </text>
              {/* Nullable dot */}
              {col.nullable && (
                <circle cx={BASE_W - 22} cy={10} r={2} fill="#d1d5db" />
              )}
            </g>
          ))}

          {/* Extra columns indicator */}
          {extraCols > 0 && (
            <text
              x={BASE_W / 2}
              y={displayCols.length * COL_ROW_H + 13}
              textAnchor="middle"
              fill="#9ca3af"
              fontSize="7.5"
              fontFamily="'Open Sans', sans-serif"
            >
              +{extraCols} more columns
            </text>
          )}
        </g>
      )}
    </g>
  );
});

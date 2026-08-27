/**
 * Data Map Toolbar — Floating controls for the Data Constellation.
 */

import React, { useRef, useEffect } from 'react';
import {
  Map,
  Search,
  Filter,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  X,
  Loader2,
} from 'lucide-react';
import type { SearchResult } from '../types/dataMap.types';

interface DataMapToolbarProps {
  searchQuery: string;
  searchResults: SearchResult[];
  searchLoading: boolean;
  filtersActive: boolean;
  onSearch: (q: string) => void;
  onSelectResult: (r: SearchResult) => void;
  onToggleFilter: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToScreen: () => void;
  onRefreshAll: () => void;
}

export default function DataMapToolbar({
  searchQuery,
  searchResults,
  searchLoading,
  filtersActive,
  onSearch,
  onSelectResult,
  onToggleFilter,
  onZoomIn,
  onZoomOut,
  onFitToScreen,
  onRefreshAll,
}: DataMapToolbarProps) {
  const searchRef = useRef<HTMLInputElement>(null);
  const [showResults, setShowResults] = React.useState(false);

  useEffect(() => {
    setShowResults(searchQuery.trim().length > 0 && searchResults.length > 0);
  }, [searchQuery, searchResults]);

  const typeIcon: Record<string, string> = {
    database: '▣',
    table: '▦',
    view: '◈',
    column: '□',
    collection: '◉',
    default: '·',
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--glass-border)',
        borderRadius: 12,
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
        position: 'relative',
        zIndex: 10,
      }}
    >
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: '#000000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Map size={13} color="#ffffff" />
        </div>
        <span
          style={{
            fontSize: '0.78rem',
            fontWeight: 800,
            letterSpacing: 1,
            textTransform: 'uppercase',
            color: 'var(--text-primary)',
          }}
        >
          Data Map
        </span>
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 24, background: 'var(--glass-border)', opacity: 0.15 }} />

      {/* Search */}
      <div style={{ position: 'relative', flex: 1, minWidth: 200, maxWidth: 360 }}>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          {searchLoading ? (
            <Loader2 size={14} className="animate-spin" style={{ position: 'absolute', left: 12, color: 'var(--text-muted)' }} />
          ) : (
            <Search size={14} style={{ position: 'absolute', left: 12, color: 'var(--text-muted)', pointerEvents: 'none' }} />
          )}
          <input
            ref={searchRef}
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
            onFocus={() => setShowResults(searchResults.length > 0)}
            onBlur={() => setTimeout(() => setShowResults(false), 200)}
            placeholder="Search providers, databases, tables, columns…"
            className="input-field"
            style={{ padding: '7px 32px 7px 34px', fontSize: '0.78rem' }}
          />
          {searchQuery && (
            <button
              onClick={() => { onSearch(''); setShowResults(false); }}
              style={{
                position: 'absolute',
                right: 10,
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                display: 'flex',
                padding: 2,
              }}
            >
              <X size={12} />
            </button>
          )}
        </div>

        {/* Search Results Dropdown */}
        {showResults && (
          <div
            style={{
              position: 'absolute',
              top: 'calc(100% + 6px)',
              left: 0,
              right: 0,
              background: 'var(--bg-surface)',
              border: '1px solid var(--glass-border)',
              borderRadius: 12,
              zIndex: 100,
              maxHeight: 280,
              overflowY: 'auto',
            }}
          >
            {searchResults.map((r, i) => (
              <button
                key={i}
                onClick={() => { onSelectResult(r); setShowResults(false); }}
                style={{
                  width: '100%',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                  textAlign: 'left',
                  borderBottom: i < searchResults.length - 1 ? '1px solid var(--bg-elevated)' : 'none',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-elevated)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
              >
                <span style={{ fontSize: '0.85rem', flexShrink: 0, marginTop: 1, color: 'var(--text-muted)' }}>
                  {typeIcon[r.type] ?? typeIcon.default}
                </span>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {r.label}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    {r.details}
                  </div>
                </div>
                <span
                  style={{
                    marginLeft: 'auto',
                    fontSize: '0.6rem',
                    fontWeight: 700,
                    padding: '1px 8px',
                    borderRadius: 9999,
                    background: 'var(--bg-elevated)',
                    color: 'var(--text-secondary)',
                    textTransform: 'uppercase',
                    flexShrink: 0,
                  }}
                >
                  {r.type}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 24, background: 'var(--glass-border)', opacity: 0.15 }} />

      {/* Icon controls */}
      <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
        <ToolbarButton
          icon={<Filter size={14} />}
          title="Filters"
          active={filtersActive}
          onClick={onToggleFilter}
        />
        <ToolbarButton icon={<ZoomIn size={14} />} title="Zoom In" onClick={onZoomIn} />
        <ToolbarButton icon={<ZoomOut size={14} />} title="Zoom Out" onClick={onZoomOut} />
        <ToolbarButton icon={<Maximize2 size={14} />} title="Fit to Screen" onClick={onFitToScreen} />
        <ToolbarButton icon={<RefreshCw size={14} />} title="Refresh All" onClick={onRefreshAll} />
      </div>
    </div>
  );
}

function ToolbarButton({
  icon,
  title,
  onClick,
  active,
}: {
  icon: React.ReactNode;
  title: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      style={{
        width: 32,
        height: 32,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: active ? '#000000' : 'transparent',
        border: active ? '1px solid #000000' : '1px solid transparent',
        borderRadius: 9999,
        cursor: 'pointer',
        color: active ? '#ffffff' : 'var(--text-secondary)',
        transition: 'all 0.15s',
      }}
      onMouseEnter={(e) => {
        if (!active) {
          (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-elevated)';
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-primary)';
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
          (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)';
        }
      }}
    >
      {icon}
    </button>
  );
}

/**
 * Context Menu — Right-click menu for Data Map nodes.
 */

import React, { useEffect, useRef } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Info,
  RefreshCw,
  ExternalLink,
  Minus,
} from 'lucide-react';
import type { DataMapNode } from '../types/dataMap.types';

interface ContextMenuProps {
  x: number;
  y: number;
  node: DataMapNode | null;
  onClose: () => void;
  onExpand: () => void;
  onCollapse: () => void;
  onSelect: () => void;
  onRefresh: () => void;
  onOpenCatalog: () => void;
}

export default function ContextMenu({
  x,
  y,
  node,
  onClose,
  onExpand,
  onCollapse,
  onSelect,
  onRefresh,
  onOpenCatalog,
}: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  if (!node) return null;

  const items: Array<{
    label: string;
    icon: React.ReactNode;
    onClick: () => void;
    danger?: boolean;
    disabled?: boolean;
    separator?: boolean;
  }> = [
    {
      label: 'View Details',
      icon: <Info size={12} />,
      onClick: () => { onSelect(); onClose(); },
    },
    {
      label: node.expanded ? 'Collapse' : 'Expand',
      icon: node.expanded ? <Minus size={12} /> : <ChevronRight size={12} />,
      onClick: () => { node.expanded ? onCollapse() : onExpand(); onClose(); },
      disabled: node.type === 'root',
    },
    { label: '', icon: null, onClick: () => {}, separator: true },
    {
      label: 'Refresh Metadata',
      icon: <RefreshCw size={12} />,
      onClick: () => { onRefresh(); onClose(); },
      disabled: node.type !== 'provider',
    },
    {
      label: 'Open in Catalog',
      icon: <ExternalLink size={12} />,
      onClick: () => { onOpenCatalog(); onClose(); },
      disabled: node.type !== 'table',
    },
  ];

  return (
    <div
      ref={menuRef}
      style={{
        position: 'fixed',
        left: x,
        top: y,
        background: '#1a2235',
        border: '1px solid rgba(148,163,184,0.12)',
        borderRadius: 10,
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        zIndex: 1000,
        minWidth: 172,
        overflow: 'hidden',
        animation: 'fadeIn 0.1s ease-out forwards',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '8px 12px 6px',
          borderBottom: '1px solid rgba(148,163,184,0.06)',
        }}
      >
        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          {node.label}
        </div>
        <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
          {node.type}
        </div>
      </div>

      {/* Menu items */}
      {items.map((item, i) => {
        if (item.separator) {
          return <div key={i} style={{ height: 1, background: 'rgba(148,163,184,0.06)', margin: '2px 0' }} />;
        }
        return (
          <button
            key={i}
            onClick={item.disabled ? undefined : item.onClick}
            disabled={item.disabled}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              background: 'none',
              border: 'none',
              cursor: item.disabled ? 'not-allowed' : 'pointer',
              color: item.disabled
                ? 'var(--text-disabled)'
                : item.danger
                ? '#ef4444'
                : 'var(--text-secondary)',
              fontSize: '0.75rem',
              textAlign: 'left',
              transition: 'background 0.1s, color 0.1s',
            }}
            onMouseEnter={(e) => {
              if (!item.disabled) {
                (e.currentTarget as HTMLButtonElement).style.background = 'rgba(99,102,241,0.08)';
                (e.currentTarget as HTMLButtonElement).style.color = item.danger ? '#ef4444' : 'var(--text-primary)';
              }
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = 'none';
              (e.currentTarget as HTMLButtonElement).style.color = item.disabled
                ? 'var(--text-disabled)'
                : 'var(--text-secondary)';
            }}
          >
            {item.icon}
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

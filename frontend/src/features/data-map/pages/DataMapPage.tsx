/**
 * Pivota Data Map Page — Data Constellation Explorer.
 *
 * A fully interactive visualization of all connected data sources,
 * their databases, schemas, tables, and FK relationships.
 * Built as a radial constellation with Pivota at the center.
 */

import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, WifiOff } from 'lucide-react';
import { useDataMap } from '../hooks/useDataMap';
import DataMapCanvas from '../components/DataMapCanvas';
import DataMapToolbar from '../components/DataMapToolbar';
import DataMapLegend from '../components/DataMapLegend';
import InspectorPanel from '../components/InspectorPanel';
import ContextMenu from '../components/ContextMenu';
import EmptyState from '../components/EmptyState';

export default function DataMapPage() {
  const navigate = useNavigate();
  const [showFilter, setShowFilter] = useState(false);

  const {
    nodes,
    edges,
    selectedNodeId,
    viewport,
    setViewport,
    searchQuery,
    searchResults,
    searchLoading,
    highlightedNodeId,
    contextMenu,
    globalLoading,
    globalError,

    expandNode,
    collapseNode,
    selectNode,
    openContextMenu,
    closeContextMenu,
    handleSearch,
    focusSearchResult,
    zoomIn,
    zoomOut,
    resetView,
    setCanvasDimensions,
    refreshProvider,
  } = useDataMap();

  // ─── Derived state ───
  const selectedNode = selectedNodeId ? nodes[selectedNodeId] : null;
  const contextNode = contextMenu.nodeId ? nodes[contextMenu.nodeId] : null;

  // Check if there are any provider nodes
  const providerCount = Object.values(nodes).filter((n) => n.type === 'provider').length;
  const isEmpty = !globalLoading && !globalError && providerCount === 0;

  // ─── Node interaction handlers ───
  const handleNodeClick = useCallback(
    (nodeId: string) => {
      selectNode(nodeId === selectedNodeId ? null : nodeId);
    },
    [selectNode, selectedNodeId]
  );

  const handleNodeDoubleClick = useCallback(
    (nodeId: string) => {
      const node = nodes[nodeId];
      if (!node) return;
      if (node.expanded) {
        collapseNode(nodeId);
      } else {
        expandNode(nodeId);
      }
    },
    [nodes, expandNode, collapseNode]
  );

  const handleNodeContextMenu = useCallback(
    (nodeId: string, x: number, y: number) => {
      selectNode(nodeId);
      openContextMenu(nodeId, x, y);
    },
    [selectNode, openContextMenu]
  );

  const handleRefreshAll = useCallback(() => {
    Object.values(nodes)
      .filter((n) => n.type === 'provider')
      .forEach((n) => refreshProvider(n.id));
  }, [nodes, refreshProvider]);

  const handleOpenCatalog = useCallback(() => {
    if (contextMenu.nodeId) {
      const objectId = contextMenu.nodeId.replace('table-', '');
      navigate(`/catalog?objectId=${objectId}`);
    }
  }, [contextMenu.nodeId, navigate]);

  // ─── Loading state ───
  if (globalLoading) {
    return (
      <div
        className="animate-fade-in"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 'calc(100vh - 130px)',
          gap: 24,
        }}
      >
        {/* Animated constellation loader */}
        <div style={{ position: 'relative', width: 120, height: 120 }}>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              border: '2px solid rgba(99,102,241,0.2)',
              animation: 'spin 3s linear infinite',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 15,
              borderRadius: '50%',
              border: '1px dashed rgba(99,102,241,0.15)',
              animation: 'spin 5s linear infinite reverse',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 30,
              borderRadius: '50%',
              background: 'var(--brand-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(99,102,241,0.3)',
            }}
          >
            <Loader2 size={22} color="white" style={{ animation: 'spin 1.5s linear infinite' }} />
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: 6 }}>
            Building Data Constellation
          </p>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Connecting to your data sources…
          </p>
        </div>
      </div>
    );
  }

  // ─── Error state ───
  if (globalError) {
    return (
      <div
        className="animate-fade-in"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 'calc(100vh - 130px)',
          gap: 16,
        }}
      >
        <div
          style={{
            width: 60,
            height: 60,
            borderRadius: 16,
            background: 'rgba(239,68,68,0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <AlertCircle size={28} style={{ color: 'var(--status-error)' }} />
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
            Connection Error
          </p>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: 380 }}>
            {globalError}
          </p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="btn-ghost"
          style={{ fontSize: '0.82rem' }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        height: 'calc(100vh - 120px)',
        position: 'relative',
      }}
    >
      {/* ── Toolbar ── */}
      <DataMapToolbar
        searchQuery={searchQuery}
        searchResults={searchResults}
        searchLoading={searchLoading}
        filtersActive={showFilter}
        onSearch={handleSearch}
        onSelectResult={focusSearchResult}
        onToggleFilter={() => setShowFilter((v) => !v)}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onFitToScreen={resetView}
        onRefreshAll={handleRefreshAll}
      />

      {/* ── Main area ── */}
      <div style={{ flex: 1, display: 'flex', gap: 12, overflow: 'hidden', minHeight: 0 }}>
        {/* Canvas + overlays */}
        <div style={{ flex: 1, position: 'relative', display: 'flex', overflow: 'hidden' }}>
          {isEmpty ? (
            <div
              style={{
                flex: 1,
                background: '#080d18',
                borderRadius: 16,
                border: '1px solid rgba(148,163,184,0.08)',
                display: 'flex',
              }}
            >
              <EmptyState />
            </div>
          ) : (
            <DataMapCanvas
              nodes={nodes}
              edges={edges}
              selectedNodeId={selectedNodeId}
              highlightedNodeId={highlightedNodeId}
              viewport={viewport}
              onViewportChange={setViewport}
              onNodeClick={handleNodeClick}
              onNodeDoubleClick={handleNodeDoubleClick}
              onNodeContextMenu={handleNodeContextMenu}
              onCanvasDimensions={setCanvasDimensions}
            />
          )}

          {/* Legend overlay — bottom-left */}
          {!isEmpty && (
            <div
              style={{
                position: 'absolute',
                bottom: 16,
                left: 16,
                zIndex: 10,
              }}
            >
              <DataMapLegend />
            </div>
          )}

          {/* Hint bubble — top-right of canvas */}
          {!isEmpty && !selectedNodeId && (
            <div
              style={{
                position: 'absolute',
                top: 12,
                right: 12,
                background: 'rgba(17,24,39,0.75)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(148,163,184,0.08)',
                borderRadius: 8,
                padding: '6px 12px',
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
                pointerEvents: 'none',
                zIndex: 5,
              }}
            >
              Double-click a node to expand · Scroll to zoom · Drag to pan
            </div>
          )}

          {/* Error providers warning — only for genuine errors */}
          {!isEmpty && Object.values(nodes).some((n) => n.type === 'provider' && n.status === 'error') && (
            <div
              style={{
                position: 'absolute',
                top: 12,
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(245,158,11,0.12)',
                border: '1px solid rgba(245,158,11,0.25)',
                borderRadius: 8,
                padding: '6px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: '0.7rem',
                color: '#f59e0b',
                zIndex: 5,
              }}
            >
              <WifiOff size={12} />
              Some providers have connection errors. Click a provider to retry.
            </div>
          )}
        </div>

        {/* ── Inspector Panel ── */}
        <InspectorPanel
          node={selectedNode}
          onClose={() => selectNode(null)}
          onRefresh={refreshProvider}
          onNavigate={(nodeId) => {
            const objectId = nodeId.replace('table-', '');
            navigate(`/catalog?objectId=${objectId}`);
          }}
        />
      </div>

      {/* ── Context Menu ── */}
      {contextMenu.visible && contextNode && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          node={contextNode}
          onClose={closeContextMenu}
          onExpand={() => expandNode(contextMenu.nodeId!)}
          onCollapse={() => collapseNode(contextMenu.nodeId!)}
          onSelect={() => selectNode(contextMenu.nodeId!)}
          onRefresh={() => refreshProvider(contextMenu.nodeId!)}
          onOpenCatalog={handleOpenCatalog}
        />
      )}
    </div>
  );
}

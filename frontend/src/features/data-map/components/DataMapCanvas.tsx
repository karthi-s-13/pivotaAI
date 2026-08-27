/**
 * Data Map Canvas — Main SVG visualization surface.
 * Handles zoom/pan, node/edge rendering, and mouse interactions.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { RootNode } from './nodes/RootNode';
import { ProviderNode } from './nodes/ProviderNode';
import { DatabaseNode } from './nodes/DatabaseNode';
import { SchemaNode } from './nodes/SchemaNode';
import { TableNode } from './nodes/TableNode';
import { HierarchyEdge, RelationshipEdge, EdgeMarkerDefs } from './edges/Edges';
import type {
  DataMapNode,
  DataMapEdge,
  ViewportState,
  ProviderMetadata,
  DatabaseMetadata,
  SchemaMetadata,
  TableMetadata,
} from '../types/dataMap.types';

interface DataMapCanvasProps {
  nodes: Record<string, DataMapNode>;
  edges: DataMapEdge[];
  selectedNodeId: string | null;
  highlightedNodeId: string | null;
  viewport: ViewportState;
  onViewportChange: (vp: ViewportState) => void;
  onNodeClick: (nodeId: string) => void;
  onNodeDoubleClick: (nodeId: string) => void;
  onNodeContextMenu: (nodeId: string, x: number, y: number) => void;
  onCanvasDimensions: (w: number, h: number) => void;
}

// ─────────────────────────────────────────────
// Canvas dot/grid background
// ─────────────────────────────────────────────

function CanvasBackground() {
  return (
    <defs>
      <pattern id="dot-grid" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">
        <circle cx="1" cy="1" r="0.8" fill="rgba(0,0,0,0.08)" />
      </pattern>
    </defs>
  );
}

export default function DataMapCanvas({
  nodes,
  edges,
  selectedNodeId,
  highlightedNodeId: _highlightedNodeId,
  viewport,
  onViewportChange,
  onNodeClick,
  onNodeDoubleClick,
  onNodeContextMenu,
  onCanvasDimensions,
}: DataMapCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [, setTooltip] = useState<{ x: number; y: number; node: DataMapNode } | null>(null);

  // Report dimensions to parent
  useEffect(() => {
    const obs = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (rect) onCanvasDimensions(rect.width, rect.height);
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, [onCanvasDimensions]);

  // ─── Mouse wheel zoom ───
  const handleWheel = useCallback(
    (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 1.1 : 0.9;
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      onViewportChange({
        zoom: Math.min(Math.max(viewport.zoom * delta, 0.12), 3),
        panX: mx - (mx - viewport.panX) * delta,
        panY: my - (my - viewport.panY) * delta,
      });
    },
    [viewport, onViewportChange]
  );

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // ─── Pan drag handlers ───
  const handleMouseDown = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if ((e.target as SVGElement).closest('[data-node]')) return;
      setDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
      setPanStart({ x: viewport.panX, y: viewport.panY });
    },
    [viewport]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!dragging) return;
      onViewportChange({
        zoom: viewport.zoom,
        panX: panStart.x + (e.clientX - dragStart.x),
        panY: panStart.y + (e.clientY - dragStart.y),
      });
    },
    [dragging, dragStart, panStart, viewport, onViewportChange]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(false);
  }, []);

  // ─── Tooltip handler ───
  const handleNodeHoverEnter = useCallback((nodeId: string, _e: React.MouseEvent) => {
    setHoveredNodeId(nodeId);
    const node = nodes[nodeId];
    if (node) {
      const rect = svgRef.current?.getBoundingClientRect();
      if (rect) {
        setTooltip({
          x: node.x * viewport.zoom + viewport.panX + rect.left,
          y: node.y * viewport.zoom + viewport.panY + rect.top,
          node,
        });
      }
    }
  }, [nodes, viewport]);

  const handleNodeHoverLeave = useCallback(() => {
    setHoveredNodeId(null);
    setTooltip(null);
  }, []);

  // ─── Is edge highlighted? ───
  const isEdgeHighlighted = useCallback(
    (edge: DataMapEdge) => {
      const activeId = hoveredNodeId ?? selectedNodeId;
      if (!activeId) return false;
      return edge.source === activeId || edge.target === activeId;
    },
    [hoveredNodeId, selectedNodeId]
  );

  const visibleNodes = Object.values(nodes).filter((n) => n.visible);

  // Separate hierarchy and relationship edges
  const hierarchyEdges = edges.filter((e) => e.type === 'hierarchy');
  const relationshipEdges = edges.filter((e) => e.type === 'relationship');

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        flex: 1,
        background: 'var(--bg-elevated)',
        borderRadius: 12,
        border: '1px solid var(--glass-border)',
        overflow: 'hidden',
      }}
    >
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        style={{
          cursor: dragging ? 'grabbing' : 'grab',
          userSelect: 'none',
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <CanvasBackground />
        <EdgeMarkerDefs />

        {/* Dot grid background */}
        <rect width="100%" height="100%" fill="url(#dot-grid)" />

        <g transform={`translate(${viewport.panX}, ${viewport.panY}) scale(${viewport.zoom})`}>
          {/* ── Layer 1: Relationship edges (draw first, below everything) ── */}
          {relationshipEdges.map((edge) => {
            const src = nodes[edge.source];
            const tgt = nodes[edge.target];
            if (!src || !tgt) return null;
            const isHL = isEdgeHighlighted(edge);
            const isSel = edge.source === selectedNodeId || edge.target === selectedNodeId;
            return (
              <RelationshipEdge
                key={edge.id}
                edge={edge}
                sourceNode={src}
                targetNode={tgt}
                isHighlighted={isHL}
                isSelected={isSel}
                markerId={isHL ? 'fk-arrow-highlighted' : 'fk-arrow'}
              />
            );
          })}

          {/* ── Layer 2: Hierarchy edges ── */}
          {hierarchyEdges.map((edge) => {
            const src = nodes[edge.source];
            const tgt = nodes[edge.target];
            if (!src || !tgt) return null;
            const isHL = isEdgeHighlighted(edge);
            const isSel = edge.source === selectedNodeId || edge.target === selectedNodeId;
            return (
              <HierarchyEdge
                key={edge.id}
                edge={edge}
                sourceNode={src}
                targetNode={tgt}
                isHighlighted={isHL}
                isSelected={isSel}
              />
            );
          })}

          {/* ── Layer 3: Nodes ── */}
          {visibleNodes.map((node) => {
            const isSelected = node.id === selectedNodeId;
            const isHighlighted = hoveredNodeId === null
              ? true
              : node.id === hoveredNodeId ||
                edges.some(
                  (e) =>
                    (e.source === hoveredNodeId && e.target === node.id) ||
                    (e.target === hoveredNodeId && e.source === node.id)
                );

            // Shared mouse handlers wrapped in data-node attr
            const nodeGroupProps = {
              'data-node': node.id,
              onMouseEnter: (e: React.MouseEvent) => handleNodeHoverEnter(node.id, e),
              onMouseLeave: handleNodeHoverLeave,
            };

            if (node.type === 'root') {
              return (
                <g key={node.id} {...nodeGroupProps}>
                  <RootNode
                    x={node.x}
                    y={node.y}
                    selected={isSelected}
                    highlighted={isHighlighted}
                    onClick={() => onNodeClick(node.id)}
                  />
                </g>
              );
            }

            if (node.type === 'provider') {
              return (
                <g key={node.id} {...nodeGroupProps}>
                  <ProviderNode
                    id={node.id}
                    x={node.x}
                    y={node.y}
                    label={node.label}
                    metadata={node.metadata as ProviderMetadata}
                    selected={isSelected}
                    highlighted={isHighlighted}
                    expanded={node.expanded}
                    status={node.status}
                    onSingleClick={() => onNodeClick(node.id)}
                    onDoubleClick={() => onNodeDoubleClick(node.id)}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      onNodeContextMenu(node.id, e.clientX, e.clientY);
                    }}
                  />
                </g>
              );
            }

            if (node.type === 'database') {
              return (
                <g key={node.id} {...nodeGroupProps}>
                  <DatabaseNode
                    x={node.x}
                    y={node.y}
                    label={node.label}
                    metadata={node.metadata as DatabaseMetadata}
                    selected={isSelected}
                    highlighted={isHighlighted}
                    expanded={node.expanded}
                    status={node.status}
                    onSingleClick={() => onNodeClick(node.id)}
                    onDoubleClick={() => onNodeDoubleClick(node.id)}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      onNodeContextMenu(node.id, e.clientX, e.clientY);
                    }}
                  />
                </g>
              );
            }

            if (node.type === 'schema') {
              return (
                <g key={node.id} {...nodeGroupProps}>
                  <SchemaNode
                    x={node.x}
                    y={node.y}
                    label={node.label}
                    metadata={node.metadata as SchemaMetadata}
                    selected={isSelected}
                    highlighted={isHighlighted}
                    expanded={node.expanded}
                    status={node.status}
                    onSingleClick={() => onNodeClick(node.id)}
                    onDoubleClick={() => onNodeDoubleClick(node.id)}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      onNodeContextMenu(node.id, e.clientX, e.clientY);
                    }}
                  />
                </g>
              );
            }

            if (node.type === 'table') {
              return (
                <g key={node.id} {...nodeGroupProps}>
                  <TableNode
                    x={node.x}
                    y={node.y}
                    label={node.label}
                    metadata={node.metadata as TableMetadata}
                    selected={isSelected}
                    highlighted={isHighlighted}
                    expanded={node.expanded}
                    status={node.status}
                    onSingleClick={() => onNodeClick(node.id)}
                    onDoubleClick={() => onNodeDoubleClick(node.id)}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      onNodeContextMenu(node.id, e.clientX, e.clientY);
                    }}
                  />
                </g>
              );
            }

            return null;
          })}
        </g>

        {/* Zoom level indicator */}
        <text
          x={10}
          y={20}
          fill="rgba(0,0,0,0.3)"
          fontSize="10"
          fontFamily="JetBrains Mono, monospace"
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          {Math.round(viewport.zoom * 100)}%
        </text>
      </svg>

      {/* Node count indicator */}
      <div
        style={{
          position: 'absolute',
          bottom: 12,
          right: 12,
          display: 'flex',
          gap: 8,
          alignItems: 'center',
        }}
      >
        <span
          style={{
            fontSize: '0.65rem',
            color: 'var(--text-disabled)',
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {visibleNodes.length} nodes · {edges.length} edges
        </span>
      </div>
    </div>
  );
}

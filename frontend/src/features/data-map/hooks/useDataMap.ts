/**
 * Pivota Data Map — Core State Management Hook.
 *
 * Manages the entire graph state: nodes, edges, expansion, selection,
 * viewport, search, and filters. Handles lazy loading of child nodes.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { dataMapApi } from '../api/dataMapApi';
import type { ProviderRecord } from '../api/dataMapApi';
import { computeRadialLayout, applyLayout, fitToScreen } from '../layout/radialLayout';
import type {
  DataMapNode,
  DataMapEdge,
  ViewportState,
  FilterState,
  ContextMenuState,
  ProviderMetadata,
  DatabaseMetadata as DBMeta,
  SchemaMetadata as SchemaMeta,
  TableMetadata,
  SearchResult,
} from '../types/dataMap.types';

// ─────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────

const ROOT_ID = 'pivota-root';
const CANVAS_W = 1800;
const CANVAS_H = 1200;

// ─────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────

export function useDataMap() {
  const [nodes, setNodes] = useState<Record<string, DataMapNode>>({});
  const [edges, setEdges] = useState<DataMapEdge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [viewport, setViewport] = useState<ViewportState>({ zoom: 0.7, panX: 0, panY: 0 });
  const [filters, setFilters] = useState<FilterState>({
    providerTypes: [],
    objectTypes: [],
    connectionStatuses: [],
    showColumns: false,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    nodeId: null, x: 0, y: 0, visible: false,
  });
  const [globalLoading, setGlobalLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [relationshipEdges, setRelationshipEdges] = useState<DataMapEdge[]>([]);

  // Cache set to prevent redundant fetches
  const fetchedCache = useRef<Set<string>>(new Set());
  const searchDebounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  const canvasDims = useRef({ w: CANVAS_W, h: CANVAS_H });

  // ─────────────────────────────────────────────
  // Internal helpers
  // ─────────────────────────────────────────────

  const updateNodes = useCallback((updater: (prev: Record<string, DataMapNode>) => Record<string, DataMapNode>) => {
    setNodes((prev) => {
      const next = updater(prev);
      const positions = computeRadialLayout(next);
      return applyLayout(next, positions);
    });
  }, []);

  const makeNode = (
    id: string,
    type: DataMapNode['type'],
    label: string,
    parentId: string | null,
    metadata: DataMapNode['metadata'],
    status: DataMapNode['status'] = 'ready'
  ): DataMapNode => ({
    id,
    type,
    label,
    parentId,
    x: 0,
    y: 0,
    expanded: false,
    childrenLoaded: false,
    status,
    metadata,
    childIds: [],
    visible: true,
    animKey: 0,
  });

  // ─────────────────────────────────────────────
  // Bootstrap: load providers on mount
  // ─────────────────────────────────────────────

  useEffect(() => {
    async function bootstrap() {
      setGlobalLoading(true);
      setGlobalError(null);
      try {
        const providers: ProviderRecord[] = await dataMapApi.fetchProviders();
        const rels = await dataMapApi.fetchAllRelationships();

        // Build relationship edges (these are always available after sync)
        const relEdges: DataMapEdge[] = rels.map((r) => ({
          id: `rel-${r.id}`,
          source: r.from_object_id,
          target: r.to_object_id,
          type: 'relationship' as const,
          label: `${r.from_columns.join(', ')} → ${r.to_columns.join(', ')}`,
          fromColumns: r.from_columns,
          toColumns: r.to_columns,
        }));
        setRelationshipEdges(relEdges);

        // Create root node
        const rootNode = makeNode(ROOT_ID, 'root', 'PIVOTA', null, {
          label: 'PIVOTA',
          subtitle: 'Unified Data Intelligence',
        }, 'ready');
        rootNode.childIds = providers.map((p) => `provider-${p.id}`);
        rootNode.childrenLoaded = true;
        rootNode.expanded = true;

        // Create provider nodes
        const providerNodes: Record<string, DataMapNode> = {};
        for (const p of providers) {
          const id = `provider-${p.id}`;
          const pm: ProviderMetadata = {
            provider_type: p.provider_type,
            environment: p.environment,
            host: p.host,
            port: p.port ?? null,
            database_name: p.database_name,
            connection_status: p.connection_status,
            health_status: p.health_status,
            last_tested_at: p.last_tested_at,
            last_sync_at: p.last_sync_at,
            databases_count: p.databases_count,
            tables_count: p.tables_count,
            columns_count: p.columns_count,
          };
          providerNodes[id] = makeNode(
            id,
            'provider',
            p.name,
            ROOT_ID,
            pm,
            p.connection_status === 'connected'
              ? 'ready'
              : p.connection_status === 'error'
              ? 'error'
              : p.health_status === 'syncing'
              ? 'syncing'
              : 'idle'   // unknown / disconnected → idle (not an alarm state)
          );
        }

        // Build initial hierarchy edges (root → providers)
        const hierarchyEdges: DataMapEdge[] = providers.map((p) => ({
          id: `edge-root-provider-${p.id}`,
          source: ROOT_ID,
          target: `provider-${p.id}`,
          type: 'hierarchy' as const,
        }));

        const allNodes = { [ROOT_ID]: rootNode, ...providerNodes };
        const positions = computeRadialLayout(allNodes);
        const laid = applyLayout(allNodes, positions);

        setNodes(laid);
        setEdges(hierarchyEdges);

        // Fit to screen
        const vp = fitToScreen(laid, canvasDims.current.w, canvasDims.current.h);
        setViewport(vp);
      } catch (err) {
        console.error('Data Map bootstrap error:', err);
        setGlobalError('Failed to load data sources. Make sure the backend is running.');
      } finally {
        setGlobalLoading(false);
      }
    }
    bootstrap();
  }, []);

  // ─────────────────────────────────────────────
  // Expand a node — lazy-loads children
  // ─────────────────────────────────────────────

  const expandNode = useCallback(async (nodeId: string) => {
    const node = nodes[nodeId];
    if (!node) return;

    // If already expanded, collapse instead
    if (node.expanded && node.childrenLoaded) {
      collapseNode(nodeId);
      return;
    }

    // Mark as loading
    updateNodes((prev) => ({
      ...prev,
      [nodeId]: { ...prev[nodeId], status: 'loading', expanded: true },
    }));

    if (node.childrenLoaded && node.childIds.length > 0) {
      // Just re-expand (show children)
      updateNodes((prev) => ({
        ...prev,
        [nodeId]: { ...prev[nodeId], status: 'ready', expanded: true },
      }));
      return;
    }

    const cacheKey = `loaded-${nodeId}`;
    if (fetchedCache.current.has(cacheKey)) {
      updateNodes((prev) => ({
        ...prev,
        [nodeId]: { ...prev[nodeId], status: 'ready', expanded: true, childrenLoaded: true },
      }));
      return;
    }

    try {
      if (node.type === 'provider') {
        // Load databases for this provider
        const meta = node.metadata as ProviderMetadata;
        // Extract the original source ID from nodeId (`provider-<uuid>`)
        const sourceId = nodeId.replace('provider-', '');
        const rawDatabases = await dataMapApi.fetchDatabases(sourceId);
        // Deduplicate databases by name to prevent multiple nodes for the same DB
        const databases = rawDatabases.filter((db, idx, self) =>
          self.findIndex((d) => d.name === db.name) === idx
        );

        const dbNodes: Record<string, DataMapNode> = {};
        const hierarchyEdges: DataMapEdge[] = [];
        const childIds: string[] = [];

        for (const db of databases) {
          const dbId = `db-${db.id}`;
          childIds.push(dbId);
          const dbMeta: DBMeta = {
            owner: db.owner,
            encoding: db.encoding,
            data_source_id: db.data_source_id,
            data_source_name: db.data_source_name,
          };
          dbNodes[dbId] = makeNode(dbId, 'database', db.name, nodeId, dbMeta);
          hierarchyEdges.push({
            id: `edge-${nodeId}-${dbId}`,
            source: nodeId,
            target: dbId,
            type: 'hierarchy',
          });
        }

        fetchedCache.current.add(cacheKey);
        updateNodes((prev) => ({
          ...prev,
          [nodeId]: {
            ...prev[nodeId],
            status: databases.length === 0 ? 'ready' : 'ready',
            expanded: true,
            childrenLoaded: true,
            childIds,
          },
          ...dbNodes,
        }));
        setEdges((prev) => [...prev, ...hierarchyEdges]);

      } else if (node.type === 'database') {
        // Load schemas for this database
        const dbId = nodeId.replace('db-', '');
        const schemas = await dataMapApi.fetchSchemas(dbId);

        const schemaNodes: Record<string, DataMapNode> = {};
        const hierarchyEdges: DataMapEdge[] = [];
        const childIds: string[] = [];

        for (const sch of schemas) {
          const schId = `schema-${sch.id}`;
          childIds.push(schId);
          const schMeta: SchemaMeta = {
            owner: sch.owner,
            database_id: sch.database_id,
            database_name: sch.database_name,
          };
          schemaNodes[schId] = makeNode(schId, 'schema', sch.name, nodeId, schMeta);
          hierarchyEdges.push({
            id: `edge-${nodeId}-${schId}`,
            source: nodeId,
            target: schId,
            type: 'hierarchy',
          });
        }

        fetchedCache.current.add(cacheKey);
        updateNodes((prev) => ({
          ...prev,
          [nodeId]: {
            ...prev[nodeId],
            status: 'ready',
            expanded: true,
            childrenLoaded: true,
            childIds,
          },
          ...schemaNodes,
        }));
        setEdges((prev) => [...prev, ...hierarchyEdges]);

      } else if (node.type === 'schema') {
        // Load tables for this schema
        const schemaId = nodeId.replace('schema-', '');
        const objects = await dataMapApi.fetchObjects(schemaId);

        const tableNodes: Record<string, DataMapNode> = {};
        const hierarchyEdges: DataMapEdge[] = [];
        const childIds: string[] = [];

        for (const obj of objects) {
          const tableId = `table-${obj.id}`;
          childIds.push(tableId);
          const tableMeta: TableMetadata = {
            type: obj.type as TableMetadata['type'],
            description: obj.description,
            row_count_estimate: obj.row_count_estimate,
            schema_id: obj.schema_id,
            schema_name: obj.schema_name,
            database_name: obj.database_name,
            data_source_name: obj.data_source_name,
            column_count: 0,
            relationship_count: 0,
          };
          tableNodes[tableId] = makeNode(tableId, 'table', obj.name, nodeId, tableMeta);
          hierarchyEdges.push({
            id: `edge-${nodeId}-${tableId}`,
            source: nodeId,
            target: tableId,
            type: 'hierarchy',
          });
        }

        fetchedCache.current.add(cacheKey);
        updateNodes((prev) => ({
          ...prev,
          [nodeId]: {
            ...prev[nodeId],
            status: 'ready',
            expanded: true,
            childrenLoaded: true,
            childIds,
          },
          ...tableNodes,
        }));
        setEdges((prev) => [...prev, ...hierarchyEdges]);

      } else if (node.type === 'table') {
        // Load column details for this table
        const objectId = nodeId.replace('table-', '');
        const detail = await dataMapApi.fetchObjectDetail(objectId);

        // Update the table node with column count + relationship count
        const tableMeta = { ...(node.metadata as TableMetadata) };
        tableMeta.column_count = detail.columns.length;
        tableMeta.relationship_count =
          detail.relationships_inbound.length + detail.relationships_outbound.length;

        fetchedCache.current.add(cacheKey);
        updateNodes((prev) => ({
          ...prev,
          [nodeId]: {
            ...prev[nodeId],
            status: 'ready',
            expanded: true,
            childrenLoaded: true,
            childIds: [],
            metadata: {
              ...tableMeta,
              columns: detail.columns,
              relationships_outbound: detail.relationships_outbound,
              relationships_inbound: detail.relationships_inbound,
              indexes: detail.indexes,
            },
          },
        }));
      }
    } catch (err) {
      console.error(`Failed to expand node ${nodeId}:`, err);
      updateNodes((prev) => ({
        ...prev,
        [nodeId]: { ...prev[nodeId], status: 'error', expanded: false },
      }));
    }
  }, [nodes, updateNodes]);

  // ─────────────────────────────────────────────
  // Collapse a node
  // ─────────────────────────────────────────────

  const collapseNode = useCallback((nodeId: string) => {
    updateNodes((prev) => {
      if (!prev[nodeId]) return prev;
      return { ...prev, [nodeId]: { ...prev[nodeId], expanded: false } };
    });
  }, [updateNodes]);

  // ─────────────────────────────────────────────
  // Select node
  // ─────────────────────────────────────────────

  const selectNode = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
    setHighlightedNodeId(nodeId);
    setContextMenu({ nodeId: null, x: 0, y: 0, visible: false });
  }, []);

  // ─────────────────────────────────────────────
  // Context Menu
  // ─────────────────────────────────────────────

  const openContextMenu = useCallback((nodeId: string, x: number, y: number) => {
    setContextMenu({ nodeId, x, y, visible: true });
  }, []);

  const closeContextMenu = useCallback(() => {
    setContextMenu({ nodeId: null, x: 0, y: 0, visible: false });
  }, []);

  // ─────────────────────────────────────────────
  // Search
  // ─────────────────────────────────────────────

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setHighlightedNodeId(null);
      return;
    }
    if (searchDebounce.current) clearTimeout(searchDebounce.current);
    searchDebounce.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const resp = await dataMapApi.search(query);
        const results: SearchResult[] = resp.results.map((r) => ({
          nodeId: r.id ? `table-${r.id}` : null,
          label: r.name,
          type: r.type,
          details: r.details,
          data_source_name: r.data_source_name,
        }));
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
  }, []);

  const focusSearchResult = useCallback((result: SearchResult) => {
    if (result.nodeId && nodes[result.nodeId]) {
      setHighlightedNodeId(result.nodeId);
      setSelectedNodeId(result.nodeId);
      const node = nodes[result.nodeId];
      if (node) {
        const { w, h } = { w: canvasDims.current.w, h: canvasDims.current.h };
        setViewport({
          zoom: 1.0,
          panX: w / 2 - node.x,
          panY: h / 2 - node.y,
        });
      }
    }
    setSearchQuery('');
    setSearchResults([]);
  }, [nodes]);

  // ─────────────────────────────────────────────
  // Viewport Controls
  // ─────────────────────────────────────────────

  const zoomIn = useCallback(() => {
    setViewport((v) => ({ ...v, zoom: Math.min(2.5, v.zoom + 0.15) }));
  }, []);

  const zoomOut = useCallback(() => {
    setViewport((v) => ({ ...v, zoom: Math.max(0.15, v.zoom - 0.15) }));
  }, []);

  const resetView = useCallback(() => {
    const vp = fitToScreen(nodes, canvasDims.current.w, canvasDims.current.h);
    setViewport(vp);
  }, [nodes]);

  const setCanvasDimensions = useCallback((w: number, h: number) => {
    canvasDims.current = { w, h };
  }, []);

  // ─────────────────────────────────────────────
  // Refresh a provider
  // ─────────────────────────────────────────────

  const refreshProvider = useCallback(async (nodeId: string) => {
    const sourceId = nodeId.replace('provider-', '');
    try {
      await dataMapApi.refreshProvider(sourceId);
      // Clear cache for this provider's subtree
      fetchedCache.current.delete(`loaded-${nodeId}`);
    } catch (err) {
      console.error('Failed to refresh provider:', err);
    }
  }, []);

  // ─────────────────────────────────────────────
  // Computed: visible edges
  // ─────────────────────────────────────────────

  // Hierarchy edges: visible only when both endpoints are visible nodes
  const visibleNodes = Object.values(nodes).filter((n) => n.visible);
  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

  // Only show hierarchy edges where both nodes exist and parent is expanded
  const visibleHierarchyEdges = edges.filter((e) => {
    if (e.type !== 'hierarchy') return false;
    const src = nodes[e.source];
    const tgt = nodes[e.target];
    return src && tgt && src.expanded && visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target);
  });

  // Relationship (FK) edges: only show when both table nodes are visible and expanded
  const visibleRelationshipEdges = relationshipEdges.filter((e) => {
    const srcId = `table-${e.source}`;
    const tgtId = `table-${e.target}`;
    return visibleNodeIds.has(srcId) && visibleNodeIds.has(tgtId);
  }).map((e) => ({
    ...e,
    source: `table-${e.source}`,
    target: `table-${e.target}`,
  }));

  const allVisibleEdges = [...visibleHierarchyEdges, ...visibleRelationshipEdges];

  // ─────────────────────────────────────────────
  // Return public API
  // ─────────────────────────────────────────────

  return {
    // State
    nodes,
    edges: allVisibleEdges,
    selectedNodeId,
    viewport,
    setViewport,
    filters,
    setFilters,
    searchQuery,
    searchResults,
    searchLoading,
    highlightedNodeId,
    contextMenu,
    globalLoading,
    globalError,

    // Actions
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
  };
}

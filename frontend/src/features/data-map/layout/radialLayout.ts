/**
 * Pivota Data Map — Radial Tree Layout Engine.
 *
 * Positions nodes in a constellation pattern:
 *   Pivota (center) → Providers (ring) → Databases → Schemas → Tables
 *
 * All positions are absolute canvas coordinates.
 */

import type { DataMapNode } from '../types/dataMap.types';

// ─────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────

const RADII: Record<string, number> = {
  root: 0,
  provider: 300,
  database: 220,
  schema: 190,
  table: 170,
  column: 0, // columns rendered inline, not as graph nodes
};

// Spread angle (in radians) allocated per child subtree
const MIN_SPREAD = Math.PI / 8; // minimum angle between siblings
const CANVAS_CENTER_X = 900;
const CANVAS_CENTER_Y = 600;

// ─────────────────────────────────────────────
// Helper: polar to cartesian
// ─────────────────────────────────────────────

function polar(
  cx: number,
  cy: number,
  radius: number,
  angleRad: number
): { x: number; y: number } {
  return {
    x: cx + radius * Math.cos(angleRad),
    y: cy + radius * Math.sin(angleRad),
  };
}

// ─────────────────────────────────────────────
// Main layout function
// ─────────────────────────────────────────────

/**
 * Compute canvas positions for all nodes in the graph.
 * Returns a map of { nodeId → {x, y} }.
 *
 * Only computes positions for expanded sub-trees.
 */
export function computeRadialLayout(
  nodes: Record<string, DataMapNode>
): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};

  // Root is always at canvas center
  const rootNode = Object.values(nodes).find((n) => n.type === 'root');
  if (!rootNode) return positions;
  positions[rootNode.id] = { x: CANVAS_CENTER_X, y: CANVAS_CENTER_Y };

  // Get provider-level children of root
  const providers = rootNode.childIds
    .map((id) => nodes[id])
    .filter(Boolean);

  if (providers.length === 0) return positions;

  // Distribute providers evenly around root
  const providerAngleStep = (2 * Math.PI) / providers.length;
  const providerOffset = -Math.PI / 2; // start from top

  providers.forEach((provider, pIdx) => {
    const providerAngle = providerOffset + pIdx * providerAngleStep;
    const pPos = polar(CANVAS_CENTER_X, CANVAS_CENTER_Y, RADII.provider, providerAngle);
    positions[provider.id] = pPos;

    if (!provider.expanded || provider.childIds.length === 0) return;

    // Position databases around the provider
    const databases = provider.childIds.map((id) => nodes[id]).filter(Boolean);
    const dbSpread = Math.max(MIN_SPREAD, (Math.PI / 2) / Math.max(databases.length, 1));
    const dbStartAngle = providerAngle - ((databases.length - 1) / 2) * dbSpread;

    databases.forEach((db, dIdx) => {
      const dbAngle = dbStartAngle + dIdx * dbSpread;
      const dbPos = polar(pPos.x, pPos.y, RADII.database, dbAngle);
      positions[db.id] = dbPos;

      if (!db.expanded || db.childIds.length === 0) return;

      // Position schemas around the database
      const schemas = db.childIds.map((id) => nodes[id]).filter(Boolean);
      const schemaSpread = Math.max(MIN_SPREAD * 0.8, (Math.PI / 3) / Math.max(schemas.length, 1));
      const schemaStartAngle = dbAngle - ((schemas.length - 1) / 2) * schemaSpread;

      schemas.forEach((schema, sIdx) => {
        const schemaAngle = schemaStartAngle + sIdx * schemaSpread;
        const schemaPos = polar(dbPos.x, dbPos.y, RADII.schema, schemaAngle);
        positions[schema.id] = schemaPos;

        if (!schema.expanded || schema.childIds.length === 0) return;

        // Position tables around the schema in concentric rings to avoid overlap
        const tables = schema.childIds.map((id) => nodes[id]).filter(Boolean);
        
        const ringSpacing = 160;
        const baseRadius = 280;
        
        let tableCounter = 0;
        let ring = 0;
        
        while (tableCounter < tables.length) {
          const ringRadius = baseRadius + ring * ringSpacing;
          
          // Outer rings hold more tables
          const ringCapacity = 6 + ring * 4;
          const ringTables = tables.slice(tableCounter, tableCounter + ringCapacity);
          
          const idealPhysicalDistance = 260; // Desired distance between nodes in pixels
          const idealSpread = idealPhysicalDistance / ringRadius;
          const arcSpan = 1.4 * Math.PI; // Max arc span (about 250 degrees)
          
          const ringSpread = ringTables.length > 1
            ? Math.min(idealSpread, arcSpan / (ringTables.length - 1))
            : 0;
            
          const totalSpan = (ringTables.length - 1) * ringSpread;
          const ringStartAngle = schemaAngle - (totalSpan / 2);
          
          ringTables.forEach((table, tIdx) => {
            const angle = ringTables.length === 1
              ? schemaAngle
              : ringStartAngle + tIdx * ringSpread;
              
            const tablePos = polar(schemaPos.x, schemaPos.y, ringRadius, angle);
            positions[table.id] = tablePos;
          });
          
          tableCounter += ringTables.length;
          ring += 1;
        }
      });
    });
  });

  return positions;
}

/**
 * Apply computed positions back to the nodes record.
 */
export function applyLayout(
  nodes: Record<string, DataMapNode>,
  positions: Record<string, { x: number; y: number }>
): Record<string, DataMapNode> {
  const updated = { ...nodes };
  for (const [id, pos] of Object.entries(positions)) {
    if (updated[id]) {
      updated[id] = { ...updated[id], x: pos.x, y: pos.y };
    }
  }
  return updated;
}

/**
 * Compute the bounding box of all visible nodes.
 */
export function getBoundingBox(nodes: Record<string, DataMapNode>): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
  centerX: number;
  centerY: number;
} {
  const visible = Object.values(nodes).filter((n) => n.visible);
  if (visible.length === 0) {
    return { minX: 0, minY: 0, maxX: 1800, maxY: 1200, width: 1800, height: 1200, centerX: 900, centerY: 600 };
  }

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of visible) {
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.x > maxX) maxX = n.x;
    if (n.y > maxY) maxY = n.y;
  }

  const width = maxX - minX;
  const height = maxY - minY;
  return {
    minX,
    minY,
    maxX,
    maxY,
    width,
    height,
    centerX: (minX + maxX) / 2,
    centerY: (minY + maxY) / 2,
  };
}

/**
 * Compute viewport transform to fit all visible nodes.
 */
export function fitToScreen(
  nodes: Record<string, DataMapNode>,
  canvasWidth: number,
  canvasHeight: number,
  padding = 120
): { zoom: number; panX: number; panY: number } {
  const bb = getBoundingBox(nodes);
  const scaleX = (canvasWidth - padding * 2) / Math.max(bb.width + 200, 1);
  const scaleY = (canvasHeight - padding * 2) / Math.max(bb.height + 200, 1);
  const zoom = Math.min(Math.max(Math.min(scaleX, scaleY), 0.15), 1.5);
  const panX = canvasWidth / 2 - bb.centerX * zoom;
  const panY = canvasHeight / 2 - bb.centerY * zoom;
  return { zoom, panX, panY };
}

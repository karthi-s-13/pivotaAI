import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Layers, 
  Table, 
  Eye, 
  Key, 
  Share2, 
  FileText, 
  Search, 
  AlertCircle,
  ArrowRight,
  Loader2,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  Play,
  Terminal,
  X
} from 'lucide-react';
import { catalogApi } from '../api/catalogApi';
import type { 
  DatabaseMetadata, 
  SchemaMetadata, 
  ObjectSummary, 
  ObjectDetail 
} from '../api/catalogApi';

export default function CatalogPage() {
  // State
  const [databases, setDatabases] = useState<DatabaseMetadata[]>([]);
  const [schemas, setSchemas] = useState<SchemaMetadata[]>([]);
  const [objects, setObjects] = useState<ObjectSummary[]>([]);
  const [selectedDb, setSelectedDb] = useState<string>('');
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [selectedObjectId, setSelectedObjectId] = useState<string>('');
  const [objectDetails, setObjectDetails] = useState<ObjectDetail | null>(null);

  // Folder tree expanded nodes mapping
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  // Table Records state
  const [records, setRecords] = useState<any[]>([]);
  const [recordColumns, setRecordColumns] = useState<string[]>([]);
  const [recordsTotalCount, setRecordsTotalCount] = useState<number>(0);
  const [recordsPage, setRecordsPage] = useState<number>(1);
  const [loadingRecords, setLoadingRecords] = useState<boolean>(false);

  // SQL Query Tool state
  const [queryToolOpen, setQueryToolOpen] = useState<boolean>(false);
  const [queryToolDbId, setQueryToolDbId] = useState<string>('');
  const [queryToolDbName, setQueryToolDbName] = useState<string>('');
  const [sqlQuery, setSqlQuery] = useState<string>('');
  const [runningQuery, setRunningQuery] = useState<boolean>(false);
  const [queryResult, setQueryResult] = useState<{ columns: string[], rows: any[] } | null>(null);
  const [queryError, setQueryError] = useState<string>('');
  const [queryLanguage, setQueryLanguage] = useState<string>('postgresql');

  // Loading/Error state
  const [loadingSidebar, setLoadingSidebar] = useState<boolean>(false);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'records' | 'columns' | 'indexes' | 'relationships' | 'query_results'>('records');

  // Load all databases, schemas, and objects upfront for tree exploration
  useEffect(() => {
    async function loadAllCatalog() {
      setLoadingSidebar(true);
      setError('');
      try {
        const [dbs, schs, objs] = await Promise.all([
          catalogApi.getDatabases(),
          catalogApi.getSchemas(),
          catalogApi.getObjects()
        ]);
        setDatabases(dbs);
        setSchemas(schs);
        setObjects(objs);

        // Check if objectId is in URL
        const params = new URLSearchParams(window.location.search);
        const urlObjectId = params.get('objectId');
        
        const initialExpanded: Record<string, boolean> = {};
        if (urlObjectId) {
          try {
            const details = await catalogApi.getObjectDetails(urlObjectId);
            setSelectedDb(details.database_id);
            setSelectedSchema(details.schema_id);
            setSelectedObjectId(details.id);
            initialExpanded[details.database_id] = true;
            initialExpanded[details.schema_id] = true;
          } catch (e) {
            console.error('Failed to load url objectId details:', e);
          }
        } else if (dbs.length > 0) {
          setSelectedDb(dbs[0].id);
          initialExpanded[dbs[0].id] = true;
          const firstDbSchemas = schs.filter(s => s.database_id === dbs[0].id);
          if (firstDbSchemas.length > 0) {
            setSelectedSchema(firstDbSchemas[0].id);
            initialExpanded[firstDbSchemas[0].id] = true;
          }
        }
        setExpandedNodes(initialExpanded);
      } catch (err: any) {
        setError('Failed to load databases catalog. Make sure data source discovery has run.');
      } finally {
        setLoadingSidebar(false);
      }
    }
    loadAllCatalog();
  }, []);

  // Fetch object details and first page of records when table selection changes
  useEffect(() => {
    if (!selectedObjectId) {
      setObjectDetails(null);
      setRecords([]);
      setRecordColumns([]);
      setRecordsTotalCount(0);
      return;
    }
    async function loadDetails() {
      setLoadingDetails(true);
      try {
        const details = await catalogApi.getObjectDetails(selectedObjectId);
        setObjectDetails(details);
        
        // Default back to Table Records preview tab
        setActiveTab('records');
        
        // Fetch paginated table records
        await loadRecords(selectedObjectId, 1);
      } catch (err) {
        setError('Failed to fetch detailed object schemas.');
      } finally {
        setLoadingDetails(false);
      }
    }
    loadDetails();
  }, [selectedObjectId]);

  // Load records handler
  const loadRecords = async (objectId: string, page: number) => {
    setLoadingRecords(true);
    try {
      const limit = 20;
      const offset = (page - 1) * limit;
      const res = await catalogApi.getRecords(objectId, limit, offset);
      setRecordColumns(res.columns);
      setRecords(res.rows);
      setRecordsTotalCount(res.total_count);
      setRecordsPage(page);
    } catch (err) {
      console.error('Failed to load records:', err);
    } finally {
      setLoadingRecords(false);
    }
  };

  // Run SQL Query handler
  const handleRunQuery = async () => {
    if (!sqlQuery.trim() || !queryToolDbId) return;
    setRunningQuery(true);
    setQueryError('');
    try {
      const res = await catalogApi.runQuery(queryToolDbId, sqlQuery);
      if (res.error) {
        setQueryError(res.error);
        setQueryResult(null);
      } else {
        setQueryResult(res);
        setActiveTab('query_results');
      }
    } catch (err: any) {
      setQueryError(err.response?.data?.detail || 'Failed to execute query. Check connection or SQL syntax.');
      setQueryResult(null);
    } finally {
      setRunningQuery(false);
    }
  };

  // Open Query Tool split panel
  const openQueryTool = (dbId: string, dbName: string, dataSourceName: string = '') => {
    setQueryToolDbId(dbId);
    setQueryToolDbName(dbName);
    setQueryToolOpen(true);
    
    // Auto-detect dialect from database name or data source name
    let detectedDialect = 'postgresql';
    const combinedName = (dbName + ' ' + dataSourceName).toLowerCase();
    if (combinedName.includes('mysql') || combinedName.includes('mariadb')) {
      detectedDialect = 'mysql';
    } else if (combinedName.includes('sqlserver') || combinedName.includes('mssql') || combinedName.includes('sql server')) {
      detectedDialect = 'sqlserver';
    } else if (combinedName.includes('mongo')) {
      detectedDialect = 'mongodb';
    }
    setQueryLanguage(detectedDialect);
    
    if (detectedDialect === 'mongodb') {
      setSqlQuery(`// MongoDB Query Language\n// Format: { "collection": "YOUR_COLLECTION_NAME", "action": "find", "filter": {} }\n{\n  "collection": "YOUR_COLLECTION_NAME",\n  "action": "find",\n  "filter": {}\n}`);
    } else if (detectedDialect === 'sqlserver') {
      setSqlQuery(`-- SQL Server Dialect\nSELECT TOP 10 * FROM `);
    } else if (detectedDialect === 'mysql') {
      setSqlQuery(`-- MySQL Dialect\nSELECT * FROM \nLIMIT 10;`);
    } else {
      setSqlQuery(`-- PostgreSQL Dialect\nSELECT * FROM \nLIMIT 10;`);
    }
    
    setQueryResult(null);
    setQueryError('');
  };

  // Node toggle click
  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };

  // Node expansion helper under filter
  const isNodeExpanded = (nodeId: string) => {
    if (searchFilter) return true; // Keep all open during search
    return !!expandedNodes[nodeId];
  };

  // Compute filtered tree data
  const getTreeData = () => {
    if (!searchFilter) {
      return { databases, schemas, objects };
    }
    
    const filter = searchFilter.toLowerCase();
    const filteredObjects = objects.filter(obj => 
      obj.name.toLowerCase().includes(filter)
    );
    
    const matchingSchemaIds = new Set(filteredObjects.map(obj => obj.schema_id));
    const filteredSchemas = schemas.filter(s => matchingSchemaIds.has(s.id));
    
    const matchingDatabaseIds = new Set(filteredSchemas.map(s => s.database_id));
    const filteredDatabases = databases.filter(db => matchingDatabaseIds.has(db.id));
    
    return {
      databases: filteredDatabases,
      schemas: filteredSchemas,
      objects: filteredObjects
    };
  };

  const treeData = getTreeData();

  // Create list of tabs
  const tabs = [
    { id: 'records', label: 'Table Records' },
    { id: 'columns', label: `Columns (${objectDetails?.columns.length || 0})` },
    { id: 'indexes', label: `Indexes (${objectDetails?.indexes.length || 0})` },
    { id: 'relationships', label: `Relationships (${(objectDetails?.relationships_outbound.length || 0) + (objectDetails?.relationships_inbound.length || 0)})` },
  ];

  if (queryResult) {
    tabs.push({ id: 'query_results', label: 'Query Results' });
  }

  return (
    <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 24, height: 'calc(100vh - 120px)' }}>
      
      {/* Sidebar Browser (Data Explorer tree) */}
      <div 
        style={{ 
          background: 'var(--bg-elevated)', 
          border: '1px solid var(--border-default)', 
          borderRadius: 16, 
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          height: '100%',
          overflowY: 'auto'
        }}
      >
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>Catalog Explorer</h3>
        
        {/* Search filter list */}
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search tables..." 
            value={searchFilter} 
            onChange={e => setSearchFilter(e.target.value)} 
            className="input-field"
            style={{ paddingLeft: 34, height: 34, fontSize: '0.8rem' }}
          />
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid var(--border-default)', margin: '0' }} />

        {/* Tree Render */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, overflowY: 'auto', flex: 1 }}>
          {loadingSidebar ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
              <Loader2 size={20} className="animate-spin" style={{ color: 'var(--brand-primary)' }} />
            </div>
          ) : treeData.databases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No relations found.
            </div>
          ) : (
            treeData.databases.map(db => {
              const dbSchemas = treeData.schemas.filter(s => s.database_id === db.id);
              const isDbExpanded = isNodeExpanded(db.id);
              
              return (
                <div key={db.id} style={{ display: 'flex', flexDirection: 'column', marginBottom: 2 }}>
                  {/* Database Node */}
                  <div 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between', 
                      padding: '8px 10px', 
                      borderRadius: 8,
                      cursor: 'pointer',
                      background: 'rgba(255,255,255,0.01)',
                      transition: 'background 0.2s',
                      userSelect: 'none'
                    }}
                    onClick={() => toggleNode(db.id)}
                    className="hover-row"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {isDbExpanded ? <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} /> : <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />}
                      <Database size={14} style={{ color: 'var(--brand-primary)' }} />
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{db.name}</span>
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        openQueryTool(db.id, db.name, db.data_source_name);
                      }}
                      style={{
                        background: 'rgba(99,102,241,0.08)',
                        border: 'none',
                        borderRadius: 6,
                        width: 26,
                        height: 26,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        color: 'var(--brand-primary)',
                        transition: 'all 0.2s'
                      }}
                      title={`Open SQL Query Tool for ${db.name}`}
                    >
                      <Terminal size={12} />
                    </button>
                  </div>

                  {/* Schemas */}
                  {isDbExpanded && (
                    <div style={{ paddingLeft: 12, display: 'flex', flexDirection: 'column', borderLeft: '1px dashed var(--border-default)', marginLeft: 16, marginTop: 4, gap: 4 }}>
                      {dbSchemas.length === 0 ? (
                        <div style={{ padding: '6px 12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>No schemas</div>
                      ) : (
                        dbSchemas.map(schema => {
                          const schemaObjects = treeData.objects.filter(obj => obj.schema_id === schema.id);
                          const isSchemaExpanded = isNodeExpanded(schema.id);
                          
                          return (
                            <div key={schema.id} style={{ display: 'flex', flexDirection: 'column' }}>
                              {/* Schema Node */}
                              <div 
                                style={{ 
                                  display: 'flex', 
                                  alignItems: 'center', 
                                  padding: '6px 8px', 
                                  borderRadius: 6,
                                  cursor: 'pointer',
                                  transition: 'background 0.2s',
                                  userSelect: 'none'
                                }}
                                onClick={() => toggleNode(schema.id)}
                                className="hover-row"
                              >
                                {isSchemaExpanded ? <ChevronDown size={12} style={{ color: 'var(--text-muted)', marginRight: 6 }} /> : <ChevronRight size={12} style={{ color: 'var(--text-muted)', marginRight: 6 }} />}
                                <Layers size={12} style={{ color: '#8b5cf6', marginRight: 8 }} />
                                <span style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)' }}>{schema.name}</span>
                              </div>

                              {/* Tables & Views */}
                              {isSchemaExpanded && (
                                <div style={{ paddingLeft: 12, display: 'flex', flexDirection: 'column', borderLeft: '1px dashed var(--border-default)', marginLeft: 12, marginTop: 4, gap: 2 }}>
                                  {schemaObjects.length === 0 ? (
                                    <div style={{ padding: '4px 12px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>No tables</div>
                                  ) : (
                                    schemaObjects.map(obj => {
                                      const isSelected = obj.id === selectedObjectId;
                                      return (
                                        <button
                                          key={obj.id}
                                          onClick={() => {
                                            setSelectedObjectId(obj.id);
                                            setSelectedSchema(obj.schema_id);
                                            setSelectedDb(db.id);
                                          }}
                                          style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            padding: '6px 10px',
                                            borderRadius: 6,
                                            border: 'none',
                                            textAlign: 'left',
                                            background: isSelected ? 'rgba(99,102,241,0.08)' : 'transparent',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s',
                                            width: '100%',
                                            gap: 8
                                          }}
                                          className="hover-row"
                                        >
                                          {obj.type === 'VIEW' ? (
                                            <Eye size={12} style={{ color: '#8b5cf6' }} />
                                          ) : (
                                            <Table size={12} style={{ color: 'var(--brand-primary)' }} />
                                          )}
                                          <span 
                                            style={{ 
                                              fontSize: '0.75rem', 
                                              fontWeight: isSelected ? 600 : 400, 
                                              color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)',
                                              overflow: 'hidden',
                                              textOverflow: 'ellipsis',
                                              whiteSpace: 'nowrap',
                                              flex: 1
                                            }}
                                          >
                                            {obj.name}
                                          </span>
                                        </button>
                                      );
                                    })
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Panel Content Area (upper/lower layout) */}
      <div 
        style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: 16, 
          height: '100%',
          overflow: 'hidden'
        }}
      >
        
        {/* Upper Area: Record View / Metadata Tabs */}
        <div 
          style={{ 
            flex: queryToolOpen ? '1 1 50%' : '1 1 100%', 
            minHeight: 0, 
            display: 'flex', 
            flexDirection: 'column', 
            gap: 16,
            overflowY: 'auto'
          }}
        >
          {error && (
            <div style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: 10, padding: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
              <AlertCircle size={16} style={{ color: 'var(--status-error)' }} />
              <span style={{ fontSize: '0.8rem', color: 'var(--status-error)' }}>{error}</span>
            </div>
          )}

          {loadingDetails ? (
            <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: '40vh' }}>
              <Loader2 size={32} className="animate-spin" style={{ color: 'var(--brand-primary)' }} />
            </div>
          ) : !objectDetails && !queryResult ? (
            <div 
              style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center', 
                flex: 1,
                background: 'var(--bg-elevated)',
                border: '1px dashed var(--border-default)',
                borderRadius: 16,
                textAlign: 'center',
                padding: 40,
                minHeight: '40vh'
              }}
            >
              <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(99,102,241,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                <FileText size={28} style={{ color: 'var(--brand-primary)' }} />
              </div>
              <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 6 }}>No Relation Selected</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', maxWidth: 360, lineHeight: 1.4 }}>
                Select a database, schema, and table/view from the left data explorer to preview records, or open the SQL Query Tool on a database node.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, flex: 1, minHeight: 0 }}>
              
              {/* Header Detail Card (Rendered if object is selected) */}
              {objectDetails && (
                <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 16, padding: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>{objectDetails.name}</h2>
                        <span 
                          style={{ 
                            fontSize: '0.68rem', 
                            fontWeight: 600, 
                            padding: '2px 8px', 
                            borderRadius: 6, 
                            background: objectDetails.type === 'VIEW' ? 'rgba(139,92,246,0.1)' : 'rgba(99,102,241,0.1)',
                            color: objectDetails.type === 'VIEW' ? '#8b5cf6' : 'var(--brand-primary)',
                          }}
                        >
                          {objectDetails.type}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0 }}>
                        DataSource: <strong>{objectDetails.data_source_name}</strong> • Database: <strong>{objectDetails.database_name}</strong> • Schema: <strong>{objectDetails.schema_name}</strong>
                      </p>
                    </div>
                    {objectDetails.row_count_estimate > 0 && (
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>{objectDetails.row_count_estimate.toLocaleString()}</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Est. Rows</div>
                      </div>
                    )}
                  </div>
                  {objectDetails.description && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '8px 0 0 0', lineHeight: 1.4 }}>
                      {objectDetails.description}
                    </p>
                  )}
                </div>
              )}

              {/* Tabs list */}
              <div style={{ display: 'flex', borderBottom: '1px solid var(--border-default)', gap: 20 }}>
                {tabs.map(tab => (
                  <button 
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    style={{
                      paddingBottom: 10,
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      color: activeTab === tab.id ? 'var(--brand-primary)' : 'var(--text-muted)',
                      border: 'none',
                      background: 'none',
                      borderBottom: `2px solid ${activeTab === tab.id ? 'var(--brand-primary)' : 'transparent'}`,
                      cursor: 'pointer',
                      marginBottom: -1,
                      transition: 'all 0.2s'
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content rendering */}
              <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
                
                {/* 1. Records Preview Tab */}
                {activeTab === 'records' && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, flex: 1 }}>
                    {loadingRecords ? (
                      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 }}>
                        <Loader2 size={24} className="animate-spin" style={{ color: 'var(--brand-primary)' }} />
                      </div>
                    ) : records.length === 0 ? (
                      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                        No records found in this relation.
                      </div>
                    ) : (
                      <>
                        <div style={{ overflow: 'auto', flex: 1, minHeight: 0 }}>
                          <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: 600 }}>
                            <thead>
                              <tr style={{ borderBottom: '1px solid var(--border-default)', background: 'rgba(255,255,255,0.02)', position: 'sticky', top: 0, zIndex: 1 }}>
                                {recordColumns.map(col => (
                                  <th key={col} style={{ padding: '10px 14px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', background: 'var(--bg-elevated)' }}>
                                    {col}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {records.map((row, idx) => (
                                <tr key={idx} style={{ borderBottom: '1px solid var(--border-default)' }} className="hover-row">
                                  {recordColumns.map(col => {
                                    const val = row[col];
                                    return (
                                      <td key={col} style={{ padding: '10px 14px', fontSize: '0.78rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 220 }}>
                                        {val === null ? (
                                          <span style={{ color: 'var(--text-disabled)', fontStyle: 'italic' }}>NULL</span>
                                        ) : typeof val === 'boolean' ? (
                                          <span style={{
                                            fontSize: '0.62rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                                            background: val ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                                            color: val ? '#10b981' : '#ef4444'
                                          }}>
                                            {val.toString().toUpperCase()}
                                          </span>
                                        ) : typeof val === 'object' ? (
                                          <span style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                            {JSON.stringify(val)}
                                          </span>
                                        ) : (
                                          val.toString()
                                        )}
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Pagination Controls */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '12px 20px', borderTop: '1px solid var(--border-default)', background: 'rgba(255,255,255,0.01)' }}>
                          <button
                            onClick={() => loadRecords(selectedObjectId, recordsPage - 1)}
                            disabled={recordsPage === 1 || loadingRecords}
                            style={{
                              background: 'none', border: '1px solid var(--border-default)', borderRadius: 8,
                              width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
                              cursor: recordsPage === 1 ? 'not-allowed' : 'pointer', color: 'var(--text-primary)',
                              opacity: recordsPage === 1 ? 0.4 : 1, transition: 'all 0.2s'
                            }}
                          >
                            <ChevronLeft size={16} />
                          </button>
                          
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                            Page <strong>{recordsPage}</strong> of <strong>{Math.ceil(recordsTotalCount / 20) || 1}</strong>
                            <span style={{ margin: '0 8px', color: 'var(--border-default)' }}>|</span>
                            Showing {Math.min((recordsPage - 1) * 20 + 1, recordsTotalCount)}-{Math.min(recordsPage * 20, recordsTotalCount)} of {recordsTotalCount} records
                          </span>

                          <button
                            onClick={() => loadRecords(selectedObjectId, recordsPage + 1)}
                            disabled={recordsPage * 20 >= recordsTotalCount || loadingRecords}
                            style={{
                              background: 'none', border: '1px solid var(--border-default)', borderRadius: 8,
                              width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
                              cursor: recordsPage * 20 >= recordsTotalCount ? 'not-allowed' : 'pointer', color: 'var(--text-primary)',
                              opacity: recordsPage * 20 >= recordsTotalCount ? 0.4 : 1, transition: 'all 0.2s'
                            }}
                          >
                            <ChevronRight size={16} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* 2. Columns Tab */}
                {activeTab === 'columns' && objectDetails && (
                  <div style={{ overflow: 'auto', flex: 1 }}>
                    <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-default)', background: 'rgba(255,255,255,0.02)' }}>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', width: 60 }}>#</th>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Name</th>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Type</th>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', width: 140 }}>Constraints</th>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', width: 90 }}>Nullable</th>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Default</th>
                          <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {objectDetails.columns.map(col => (
                          <tr key={col.id} style={{ borderBottom: '1px solid var(--border-default)' }} className="hover-row">
                            <td style={{ padding: '12px 16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{col.ordinal_position}</td>
                            <td style={{ padding: '12px 16px', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>{col.name}</td>
                            <td style={{ padding: '12px 16px', fontSize: '0.78rem', color: 'var(--brand-primary-light)', fontFamily: 'monospace' }}>
                              {col.native_type || col.data_type}
                            </td>
                            <td style={{ padding: '12px 16px' }}>
                              <div style={{ display: 'flex', gap: 6 }}>
                                {col.is_primary_key && (
                                  <span style={{ fontSize: '0.62rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4, background: 'rgba(245,158,11,0.1)', color: '#f59e0b', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                                    <Key size={10} /> PK
                                  </span>
                                )}
                                {col.is_foreign_key && (
                                  <span style={{ fontSize: '0.62rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4, background: 'rgba(16,185,129,0.1)', color: '#10b981', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                                    <Share2 size={10} /> FK
                                  </span>
                                )}
                                {!col.is_primary_key && !col.is_foreign_key && (
                                  <span style={{ fontSize: '0.72rem', color: 'var(--text-disabled)' }}>—</span>
                                )}
                              </div>
                            </td>
                            <td style={{ padding: '12px 16px', fontSize: '0.78rem', color: col.nullable ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                              {col.nullable ? 'YES' : 'NO'}
                            </td>
                            <td style={{ padding: '12px 16px', fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                              {col.default_value || <span style={{ color: 'var(--text-disabled)' }}>NULL</span>}
                            </td>
                            <td style={{ padding: '12px 16px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                              {col.description || <span style={{ color: 'var(--text-disabled)', fontSize: '0.75rem' }}>No comment</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 3. Indexes Tab */}
                {activeTab === 'indexes' && objectDetails && (
                  <div style={{ padding: 6, overflow: 'auto', flex: 1 }}>
                    {objectDetails.indexes.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        No database indexes found on this object.
                      </div>
                    ) : (
                      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-default)', background: 'rgba(255,255,255,0.02)' }}>
                            <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Index Name</th>
                            <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Columns</th>
                            <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Unique</th>
                            <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Primary</th>
                            <th style={{ padding: '12px 16px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)' }}>Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {objectDetails.indexes.map(idx => (
                            <tr key={idx.id} style={{ borderBottom: '1px solid var(--border-default)' }} className="hover-row">
                              <td style={{ padding: '12px 16px', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>{idx.name}</td>
                              <td style={{ padding: '12px 16px', fontSize: '0.78rem', color: 'var(--brand-primary-light)', fontFamily: 'monospace' }}>
                                {idx.columns.join(', ')}
                              </td>
                              <td style={{ padding: '12px 16px', fontSize: '0.78rem' }}>
                                {idx.unique ? (
                                  <span style={{ color: 'var(--status-success)', fontWeight: 600 }}>YES</span>
                                ) : (
                                  <span style={{ color: 'var(--text-muted)' }}>NO</span>
                                )}
                              </td>
                              <td style={{ padding: '12px 16px', fontSize: '0.78rem' }}>
                                {idx.primary ? (
                                  <span style={{ color: '#f59e0b', fontWeight: 600 }}>YES</span>
                                ) : (
                                  <span style={{ color: 'var(--text-muted)' }}>NO</span>
                                )}
                              </td>
                              <td style={{ padding: '12px 16px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{idx.type || 'BTREE'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}

                {/* 4. Relationships Tab */}
                {activeTab === 'relationships' && objectDetails && (
                  <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 20, overflow: 'auto', flex: 1 }}>
                    
                    {/* Outbound keys */}
                    <div>
                      <h4 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
                        Outbound Keys (References to other tables)
                      </h4>
                      {objectDetails.relationships_outbound.length === 0 ? (
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, paddingLeft: 4 }}>This table does not reference any other tables.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {objectDetails.relationships_outbound.map(rel => (
                            <div 
                              key={rel.id} 
                              style={{ 
                                padding: 12, 
                                borderRadius: 10, 
                                background: 'rgba(255,255,255,0.01)', 
                                border: '1px solid var(--border-default)', 
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--brand-primary-light)' }}>
                                  {rel.from_columns.join(', ')}
                                </span>
                                <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                                <button 
                                  onClick={() => setSelectedObjectId(rel.to_object_id)}
                                  style={{
                                    background: 'none', border: 'none', padding: 0, cursor: 'pointer',
                                    fontSize: '0.78rem', fontWeight: 600, color: 'var(--brand-primary)',
                                    textDecoration: 'underline'
                                  }}
                                >
                                  {rel.to_table_name}
                                </button>
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                  ({rel.to_columns.join(', ')})
                                </span>
                              </div>
                              <div style={{ textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                <div>Constraint: <strong>{rel.constraint_name}</strong></div>
                                {rel.delete_action && <div>ON DELETE: <strong>{rel.delete_action}</strong></div>}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Inbound keys */}
                    <div>
                      <h4 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
                        Inbound Keys (Referenced by other tables)
                      </h4>
                      {objectDetails.relationships_inbound.length === 0 ? (
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, paddingLeft: 4 }}>No other tables reference this table.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {objectDetails.relationships_inbound.map(rel => (
                            <div 
                              key={rel.id} 
                              style={{ 
                                padding: 12, 
                                borderRadius: 10, 
                                background: 'rgba(255,255,255,0.01)', 
                                border: '1px solid var(--border-default)', 
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <button 
                                  onClick={() => setSelectedObjectId(rel.from_object_id)}
                                  style={{
                                    background: 'none', border: 'none', padding: 0, cursor: 'pointer',
                                    fontSize: '0.78rem', fontWeight: 600, color: 'var(--brand-primary)',
                                    textDecoration: 'underline'
                                  }}
                                >
                                  {rel.from_table_name}
                                </button>
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                  ({rel.from_columns.join(', ')})
                                </span>
                                <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--brand-primary-light)' }}>
                                  {rel.to_columns.join(', ')}
                                </span>
                              </div>
                              <div style={{ textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                <div>Constraint: <strong>{rel.constraint_name}</strong></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 5. SQL Query Results Tab */}
                {activeTab === 'query_results' && queryResult && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, flex: 1 }}>
                    <div style={{ padding: '10px 16px', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-default)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        SQL Query execution output
                      </span>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: 6, background: 'rgba(16,185,129,0.1)', color: '#10b981' }}>
                        {queryResult.rows.length} rows returned
                      </span>
                    </div>

                    <div style={{ overflow: 'auto', flex: 1, minHeight: 0 }}>
                      <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: 600 }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-default)', background: 'rgba(255,255,255,0.01)', position: 'sticky', top: 0, zIndex: 1 }}>
                            {queryResult.columns.map(col => (
                              <th key={col} style={{ padding: '10px 14px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', background: 'var(--bg-elevated)' }}>
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {queryResult.rows.map((row, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid var(--border-default)' }} className="hover-row">
                              {queryResult.columns.map(col => {
                                const val = row[col];
                                return (
                                  <td key={col} style={{ padding: '10px 14px', fontSize: '0.78rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 220 }}>
                                    {val === null ? (
                                      <span style={{ color: 'var(--text-disabled)', fontStyle: 'italic' }}>NULL</span>
                                    ) : typeof val === 'boolean' ? (
                                      <span style={{
                                        fontSize: '0.62rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                                        background: val ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                                        color: val ? '#10b981' : '#ef4444'
                                      }}>
                                        {val.toString().toUpperCase()}
                                      </span>
                                    ) : typeof val === 'object' ? (
                                      <span style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                        {JSON.stringify(val)}
                                      </span>
                                    ) : (
                                      val.toString()
                                    )}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Lower Area: SQL Query Tool (Horizontal split when open) */}
        {queryToolOpen && (
          <div 
            style={{ 
              flex: '0 0 260px', 
              minHeight: 0,
              background: 'var(--bg-elevated)', 
              border: '1px solid var(--border-default)', 
              borderRadius: 16, 
              padding: 16, 
              display: 'flex', 
              flexDirection: 'column', 
              gap: 12
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Terminal size={15} style={{ color: 'var(--brand-primary)' }} />
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    Query Tool — <span style={{ color: 'var(--brand-primary-light)' }}>{queryToolDbName}</span>
                  </h4>
                </div>
                
                {/* Options / Dialect Selector */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Dialect:</span>
                  <select
                    value={queryLanguage}
                    onChange={(e) => {
                      const lang = e.target.value;
                      setQueryLanguage(lang);
                      if (lang === 'mongodb') {
                        setSqlQuery(`// MongoDB Query Language\n// Format: { "collection": "YOUR_COLLECTION_NAME", "action": "find", "filter": {} }\n{\n  "collection": "YOUR_COLLECTION_NAME",\n  "action": "find",\n  "filter": {}\n}`);
                      } else if (lang === 'sqlserver') {
                        setSqlQuery(`-- SQL Server Dialect\nSELECT TOP 10 * FROM `);
                      } else if (lang === 'mysql') {
                        setSqlQuery(`-- MySQL Dialect\nSELECT * FROM \nLIMIT 10;`);
                      } else {
                        setSqlQuery(`-- PostgreSQL Dialect\nSELECT * FROM \nLIMIT 10;`);
                      }
                    }}
                    style={{
                      height: 24,
                      padding: '0 6px',
                      fontSize: '0.72rem',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border-default)',
                      borderRadius: 6,
                      color: 'var(--text-primary)',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                    <option value="sqlserver">MS SQL Server</option>
                    <option value="mongodb">MongoDB</option>
                  </select>
                </div>
              </div>
              
              <button 
                onClick={() => {
                  setQueryToolOpen(false);
                  setQueryResult(null);
                  if (activeTab === 'query_results') {
                    setActiveTab('records');
                  }
                }}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 4, borderRadius: 4
                }}
                className="hover-row"
              >
                <X size={15} />
              </button>
            </div>
            
            {/* SQL Input Area */}
            <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
              <textarea
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                placeholder="Enter SQL SELECT statement..."
                style={{
                  width: '100%',
                  height: '100%',
                  background: 'rgba(0,0,0,0.15)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 8,
                  padding: 10,
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  color: 'var(--text-primary)',
                  resize: 'none',
                  outline: 'none'
                }}
              />
            </div>

            {/* Run query actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Press <strong>Run Query</strong> to execute and display results in upper panel.
              </span>
              
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={handleRunQuery}
                  disabled={runningQuery || !sqlQuery.trim()}
                  style={{
                    background: 'var(--brand-primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: 8,
                    padding: '6px 14px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    cursor: runningQuery || !sqlQuery.trim() ? 'not-allowed' : 'pointer',
                    opacity: runningQuery || !sqlQuery.trim() ? 0.6 : 1,
                    transition: 'all 0.2s'
                  }}
                >
                  {runningQuery ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Play size={12} />
                  )}
                  Run Query
                </button>
              </div>
            </div>

            {/* Error messaging */}
            {queryError && (
              <div style={{ color: 'var(--status-error)', fontSize: '0.75rem', background: 'rgba(239,68,68,0.06)', padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(239,68,68,0.12)' }}>
                {queryError}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

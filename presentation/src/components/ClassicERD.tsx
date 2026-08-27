import React, { useState } from 'react';

interface AttrField {
  name: string;
  type: string;
  key?: 'PK' | 'FK';
}

interface EntityData {
  title: string;
  desc: string;
  fields: AttrField[];
  relations: string[];
  connectedTo: string[];
  connectedRels: string[];
}

const erModelData: Record<string, EntityData> = {
  organization: {
    title: "organizations (Root Tenant Entity)",
    desc: "The absolute root node of the system database. All platform administrators, access permission policies, active data sources, and discovered schemas are bound to this Organization ID. This guarantees complete, logical multi-tenant isolation.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "name", type: "VARCHAR" },
      { name: "slug", type: "VARCHAR" }
    ],
    relations: [
      "Owns -> Admin Users (1 to N relationship)",
      "Owns -> Access Policies (1 to N relationship)",
      "Owns -> Database Connections (1 to N relationship)",
      "Owns -> Invited Employees (1 to N relationship)"
    ],
    connectedTo: ["user", "iam_user", "iam_policy", "data_source"],
    connectedRels: ["owns", "manages"]
  },
  user: {
    title: "users (Admin Accounts)",
    desc: "System administrators who configure database connections and invite staff. Accounts are strictly bound to their parent Organization ID. Admin logins require verified passwords followed by Google Authenticator (TOTP) email verification.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "organization_id", type: "UUID", key: "FK" },
      { name: "email", type: "VARCHAR" },
      { name: "hashed_password", type: "VARCHAR" },
      { name: "is_2fa_verified", type: "BOOL" }
    ],
    relations: [
      "Belongs to -> Organization (organization_id references organizations.id)",
      "Invites -> Invited Employees (created_by_id references users.id)"
    ],
    connectedTo: ["organization", "iam_user"],
    connectedRels: ["owns", "invites"]
  },
  iam_policy: {
    title: "iam_policies (Access Permission Rules)",
    desc: "Defines rules for employee access. Contains JSON flags mapping allowed databases, catalog schemas, metadata logs, query tools, and wizard screens.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "organization_id", type: "UUID", key: "FK" },
      { name: "name", type: "VARCHAR" },
      { name: "permissions", type: "JSON" }
    ],
    relations: [
      "Belongs to -> Organization (organization_id references organizations.id)",
      "Binds -> Employees (policy_id references iam_policies.id)"
    ],
    connectedTo: ["organization", "iam_user"],
    connectedRels: ["manages", "binds"]
  },
  iam_user: {
    title: "iam_users (Invited Employees)",
    desc: "Staff accounts created by admins. They do not require rotating 2FA email codes but are strictly limited in what they can browse, query, or edit by their bound access policy.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "organization_id", type: "UUID", key: "FK" },
      { name: "policy_id", type: "UUID", key: "FK" },
      { name: "created_by_id", type: "UUID", key: "FK" },
      { name: "iam_id", type: "VARCHAR" },
      { name: "status", type: "VARCHAR" }
    ],
    relations: [
      "Belongs to -> Organization (organization_id references organizations.id)",
      "Follows -> Access Rule Policy (policy_id references iam_policies.id)",
      "Invited by -> Admin User (created_by_id references users.id)"
    ],
    connectedTo: ["organization", "iam_policy", "user"],
    connectedRels: ["invites", "binds"]
  },
  data_source: {
    title: "data_sources (Database Connections)",
    desc: "Configuration parameters mapping registered external databases (like PostgreSQL, MySQL, and MongoDB). Houses host IP, TLS settings, and health check check times.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "organization_id", type: "UUID", key: "FK" },
      { name: "provider", type: "VARCHAR" },
      { name: "host", type: "VARCHAR" },
      { name: "tls", type: "BOOL" }
    ],
    relations: [
      "Belongs to -> Organization (organization_id references organizations.id)",
      "Triggers -> Crawl Logs (one-to-many relationship)",
      "Catalogs -> Discovered Databases (one-to-many relationship)"
    ],
    connectedTo: ["organization", "metadata_snapshot", "database_metadata"],
    connectedRels: ["triggers", "catalogs"]
  },
  metadata_snapshot: {
    title: "metadata_snapshots (Crawl History Logs)",
    desc: "Logs of database crawling sync tasks. Records crawlers start/end time, duration in milliseconds, discovery status, and error logs if target databases reject crawling.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "data_source_id", type: "UUID", key: "FK" },
      { name: "status", type: "VARCHAR" },
      { name: "duration_ms", type: "INT" }
    ],
    relations: [
      "Belongs to -> Database Connection (data_source_id references data_sources.id)"
    ],
    connectedTo: ["data_source"],
    connectedRels: ["triggers"]
  },
  database_metadata: {
    title: "database_metadata (Discovered Databases)",
    desc: "Logical databases discovered on a connected host. Maps physical database names (for example, 'billing_prod', 'sales_warehouse').",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "data_source_id", type: "UUID", key: "FK" },
      { name: "name", type: "VARCHAR" }
    ],
    relations: [
      "Belongs to -> Database Connection (data_source_id references data_sources.id)",
      "Contains -> Schemas (one-to-many relationship)"
    ],
    connectedTo: ["data_source", "schema_metadata"],
    connectedRels: ["catalogs", "contains"]
  },
  schema_metadata: {
    title: "schema_metadata (Namespaces / Folders)",
    desc: "Schema namespace paths discovered within a database (e.g. 'public', 'core', 'auth', 'logging').",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "database_id", type: "UUID", key: "FK" },
      { name: "name", type: "VARCHAR" }
    ],
    relations: [
      "Belongs to -> Database Name (database_id references database_metadata.id)",
      "Declares -> Tables & Views (one-to-many relationship)"
    ],
    connectedTo: ["database_metadata", "object_metadata"],
    connectedRels: ["contains", "declares"]
  },
  object_metadata: {
    title: "object_metadata (Tables and Views)",
    desc: "Individual tables and views discovered inside a schema namespace. Tracks object name, type (TABLE or VIEW), and estimated row count totals.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "schema_id", type: "UUID", key: "FK" },
      { name: "name", type: "VARCHAR" },
      { name: "type", type: "VARCHAR" }
    ],
    relations: [
      "Belongs to -> Schema Folder (schema_id references schema_metadata.id)",
      "Defines -> Columns (one-to-many relationship)",
      "Defines -> Indexes (one-to-many relationship)",
      "Maps -> Connections / Constraints (one-to-many relationship)"
    ],
    connectedTo: ["schema_metadata", "column_metadata", "index_metadata", "relationship_metadata"],
    connectedRels: ["declares", "defines", "maps"]
  },
  column_metadata: {
    title: "column_metadata (Table Fields)",
    desc: "Columns inside a table. Records data type names (e.g. text, integer, double precision) and marks primary key / foreign key constraints.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "object_id", type: "UUID", key: "FK" },
      { name: "name", type: "VARCHAR" },
      { name: "data_type", type: "VARCHAR" }
    ],
    relations: [
      "Belongs to -> Table Name (object_id references object_metadata.id)"
    ],
    connectedTo: ["object_metadata"],
    connectedRels: ["defines"]
  },
  index_metadata: {
    title: "index_metadata (Table Indexes)",
    desc: "Index structures discovered. Identifies which columns are indexed and unique/primary keys for query planning.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "object_id", type: "UUID", key: "FK" },
      { name: "name", type: "VARCHAR" },
      { name: "columns", type: "JSON" }
    ],
    relations: [
      "Belongs to -> Table Name (object_id references object_metadata.id)"
    ],
    connectedTo: ["object_metadata"],
    connectedRels: ["defines"]
  },
  relationship_metadata: {
    title: "relationship_metadata (Table Links)",
    desc: "Foreign keys mapping how fields in one table reference fields in another table (e.g. orders.user_id -> users.id). Used by AI search to trace relational paths.",
    fields: [
      { name: "id", type: "UUID", key: "PK" },
      { name: "from_object_id", type: "UUID", key: "FK" },
      { name: "to_object_id", type: "UUID", key: "FK" },
      { name: "constraint_name", type: "VARCHAR" }
    ],
    relations: [
      "Belongs to -> Source Table (from_object_id references object_metadata.id)",
      "Points to -> Target Table (to_object_id references object_metadata.id)"
    ],
    connectedTo: ["object_metadata"],
    connectedRels: ["maps"]
  }
};

export const ClassicERD: React.FC = () => {
  const [activeEntity, setActiveEntity] = useState<string | null>(null);

  const handleEntityClick = (entityId: string) => {
    setActiveEntity(entityId);
  };

  const getNodeContentClass = (entityId: string) => {
    if (activeEntity === entityId) return 'erd-node-content active';
    if (activeEntity && erModelData[activeEntity]?.connectedTo.includes(entityId)) {
      return 'erd-node-content highlighted';
    }
    return 'erd-node-content';
  };

  const renderOvals = (fields: AttrField[]) => {
    return fields.map((f, i) => {
      let keyClass = '';
      if (f.key === 'PK') keyClass = 'pk';
      else if (f.key === 'FK') keyClass = 'fk';
      
      return (
        <div className={`erd-node-oval ${keyClass}`} key={i} title={`${f.name} (${f.type})`}>
          {f.name}
          {f.key ? `:${f.key}` : ''}
        </div>
      );
    });
  };

  return (
    <div className="er-diagram-container">
      {/* Hierarchical Node Tree */}
      <div className="erd-tree-container">
        
        {/* Level 0: organizations */}
        <div className="erd-tree-root">
          <div className={getNodeContentClass('organization')} onClick={() => handleEntityClick('organization')}>
            <div className="erd-node-rect">organizations</div>
            <div className="erd-node-ovals">
              {renderOvals(erModelData.organization.fields)}
            </div>
          </div>
          
          {/* Level 1: Tenant children */}
          <div style={{ paddingLeft: '24px' }}>
            
            {/* Child Node: users */}
            <div className="erd-tree-node">
              <div className={getNodeContentClass('user')} onClick={() => handleEntityClick('user')}>
                <div className="erd-node-rect">users</div>
                <div className="erd-node-ovals">
                  {renderOvals(erModelData.user.fields)}
                </div>
              </div>
            </div>

            {/* Child Node: iam_policies */}
            <div className="erd-tree-node">
              <div className={getNodeContentClass('iam_policy')} onClick={() => handleEntityClick('iam_policy')}>
                <div className="erd-node-rect">iam_policies</div>
                <div className="erd-node-ovals">
                  {renderOvals(erModelData.iam_policy.fields)}
                </div>
              </div>
              
              {/* Level 2 Child: iam_users */}
              <div style={{ paddingLeft: '24px' }}>
                <div className="erd-tree-node">
                  <div className={getNodeContentClass('iam_user')} onClick={() => handleEntityClick('iam_user')}>
                    <div className="erd-node-rect">iam_users</div>
                    <div className="erd-node-ovals">
                      {renderOvals(erModelData.iam_user.fields)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Child Node: data_sources */}
            <div className="erd-tree-node">
              <div className={getNodeContentClass('data_source')} onClick={() => handleEntityClick('data_source')}>
                <div className="erd-node-rect">data_sources</div>
                <div className="erd-node-ovals">
                  {renderOvals(erModelData.data_source.fields)}
                </div>
              </div>
              
              {/* Level 2 Children */}
              <div style={{ paddingLeft: '24px' }}>
                
                {/* Child Node: metadata_snapshots */}
                <div className="erd-tree-node">
                  <div className={getNodeContentClass('metadata_snapshot')} onClick={() => handleEntityClick('metadata_snapshot')}>
                    <div className="erd-node-rect">metadata_snapshots</div>
                    <div className="erd-node-ovals">
                      {renderOvals(erModelData.metadata_snapshot.fields)}
                    </div>
                  </div>
                </div>

                {/* Child Node: database_metadata */}
                <div className="erd-tree-node">
                  <div className={getNodeContentClass('database_metadata')} onClick={() => handleEntityClick('database_metadata')}>
                    <div className="erd-node-rect">database_metadata</div>
                    <div className="erd-node-ovals">
                      {renderOvals(erModelData.database_metadata.fields)}
                    </div>
                  </div>

                  {/* Level 3 Child: schema_metadata */}
                  <div style={{ paddingLeft: '24px' }}>
                    <div className="erd-tree-node">
                      <div className={getNodeContentClass('schema_metadata')} onClick={() => handleEntityClick('schema_metadata')}>
                        <div className="erd-node-rect">schema_metadata</div>
                        <div className="erd-node-ovals">
                          {renderOvals(erModelData.schema_metadata.fields)}
                        </div>
                      </div>

                      {/* Level 4 Child: object_metadata */}
                      <div style={{ paddingLeft: '24px' }}>
                        <div className="erd-tree-node">
                          <div className={getNodeContentClass('object_metadata')} onClick={() => handleEntityClick('object_metadata')}>
                            <div className="erd-node-rect">object_metadata</div>
                            <div className="erd-node-ovals">
                              {renderOvals(erModelData.object_metadata.fields)}
                            </div>
                          </div>

                          {/* Level 5 Children */}
                          <div style={{ paddingLeft: '24px' }}>
                            
                            {/* Child Node: column_metadata */}
                            <div className="erd-tree-node">
                              <div className={getNodeContentClass('column_metadata')} onClick={() => handleEntityClick('column_metadata')}>
                                <div className="erd-node-rect">column_metadata</div>
                                <div className="erd-node-ovals">
                                  {renderOvals(erModelData.column_metadata.fields)}
                                </div>
                              </div>
                            </div>

                            {/* Child Node: index_metadata */}
                            <div className="erd-tree-node">
                              <div className={getNodeContentClass('index_metadata')} onClick={() => handleEntityClick('index_metadata')}>
                                <div className="erd-node-rect">index_metadata</div>
                                <div className="erd-node-ovals">
                                  {renderOvals(erModelData.index_metadata.fields)}
                                </div>
                              </div>
                            </div>

                            {/* Child Node: relationship_metadata */}
                            <div className="erd-tree-node">
                              <div className={getNodeContentClass('relationship_metadata')} onClick={() => handleEntityClick('relationship_metadata')}>
                                <div className="erd-node-rect">relationship_metadata</div>
                                <div className="erd-node-ovals">
                                  {renderOvals(erModelData.relationship_metadata.fields)}
                                </div>
                              </div>
                            </div>

                          </div>
                        </div>
                      </div>

                    </div>
                  </div>

                </div>
              </div>

            </div>

          </div>
        </div>

      </div>

      {/* Details explorer pane */}
      <div className="erd-tree-details-panel">
        {activeEntity && erModelData[activeEntity] ? (
          <>
            <h3>{erModelData[activeEntity].title}</h3>
            <p>{erModelData[activeEntity].desc}</p>
            <div className="er-relationships-list" style={{ marginTop: '8px' }}>
              {erModelData[activeEntity].relations.map((rel, index) => (
                <div className="er-rel-item" key={index}>{rel}</div>
              ))}
            </div>
          </>
        ) : (
          <>
            <h3>Hierarchical Schema Explorer</h3>
            <p>Click any entity rectangle in the node tree above to highlight its path hierarchy and inspect its fields (ovals) and references in simple English.</p>
          </>
        )}
      </div>
    </div>
  );
};

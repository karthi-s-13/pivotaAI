"""
Data Source Service.

Coordinates database adapter execution, secret storage, and capability-gated metadata discovery.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.connectors.manager import get_connector, get_provider_capabilities
from app.core.exceptions import raise_not_found
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.data_source import (
    ConnectionTestRequest,
    ConnectionTestResult,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
)
from app.services import secret_manager


def _merge_connection_string(connection_string: str, request: DataSourceCreate) -> None:
    """Parse connection URI and merge connection parameters into request sections in-place."""
    from app.core.uri_parser import parse_connection_string

    parsed = parse_connection_string(connection_string)

    request.identity.provider = parsed["provider"]
    request.connectivity.host = parsed["host"]
    request.connectivity.port = parsed["port"]

    config = request.connectivity.provider_config or {}
    config.update(parsed["provider_config"])
    config["database_name"] = parsed["database_name"]
    request.connectivity.provider_config = config

    # Extract credentials/username if parsed
    if parsed["username"]:
        config["username"] = parsed["username"]
    if parsed["password"]:
        request.security.password = parsed["password"]


def _build_adapter_config(db: Session, ds: DataSource) -> dict:
    """Build connection configuration for the adapter, resolving credentials from the secret manager."""
    password = None
    if ds.secret_reference:
        password = secret_manager.retrieve_secret(db, ds.secret_reference)

    config = ds.provider_config or {}

    return {
        "host": ds.host,
        "port": ds.port,
        "database_name": config.get("database_name", ""),
        "username": config.get("username") or ds.username,
        "password": password,
        "ssl_enabled": ds.tls,
        **config,
    }


def create_data_source(
    db: Session, request: DataSourceCreate, user: User
) -> DataSourceResponse:
    """Register a new data source connection, parsing connection strings immediately."""
    # Parse URI connection string if provided
    if request.connection_string:
        _merge_connection_string(request.connection_string, request)

    # Store credential in secret manager
    secret_ref = None
    if request.security.password:
        secret_ref = secret_manager.store_secret(db, request.security.password)
    elif request.security.secret_reference:
        secret_ref = request.security.secret_reference

    # Extract username if in connectivity provider_config
    username = request.connectivity.provider_config.get("username") if request.connectivity.provider_config else None

    ds = DataSource(
        name=request.identity.name,
        description=request.description,
        provider=request.identity.provider,
        environment=request.identity.environment,
        host=request.connectivity.host,
        port=request.connectivity.port,
        connection_mode=request.connectivity.connection_mode,
        network_mode=request.connectivity.network_mode,
        provider_config=request.connectivity.provider_config,
        auth_method=request.security.auth_method,
        tls=request.security.tls,
        secret_reference=secret_ref,
        access_policy=request.security.access_policy,
        username=username,
        organization_id=user.organization_id,
        created_by=user.id,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)

    # Run initial connection testing and schema discovery
    try:
        test_connection_for_source(db, ds.id, user.organization_id)
        db.refresh(ds)
    except Exception:
        pass

    caps = get_provider_capabilities(ds.provider)
    return DataSourceResponse.from_orm_model(ds, caps)


def update_data_source(
    db: Session, source_id: str, request: DataSourceUpdate, organization_id: str
) -> DataSourceResponse:
    """Update configuration for an existing data source registration."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found")

    # If connection string provided, parse into update payload
    if request.connection_string:
        # Reconstruct full create payload structure to reuse helper
        from app.schemas.data_source import IdentitySection, ConnectivitySection, SecuritySectionCreate
        temp_create = DataSourceCreate(
            identity=IdentitySection(
                name=ds.name, provider=ds.provider, environment=ds.environment
            ),
            connectivity=ConnectivitySection(
                host=ds.host,
                port=ds.port,
                connection_mode=ds.connection_mode,
                network_mode=ds.network_mode,
                provider_config=dict(ds.provider_config or {}),
            ),
            security=SecuritySectionCreate(
                auth_method=ds.auth_method,
                tls=ds.tls,
                secret_reference=ds.secret_reference,
            ),
            connection_string=request.connection_string,
        )
        _merge_connection_string(request.connection_string, temp_create)

        # Merge results into request update sections
        request.name = temp_create.identity.name
        request.connectivity = temp_create.connectivity
        request.security = temp_create.security
        request.environment = temp_create.identity.environment

    if request.name is not None:
        ds.name = request.name
    if request.description is not None:
        ds.description = request.description
    if request.environment is not None:
        ds.environment = request.environment

    if request.connectivity is not None:
        c = request.connectivity
        if c.host is not None:
            ds.host = c.host
        if c.port is not None:
            ds.port = c.port
        if c.connection_mode is not None:
            ds.connection_mode = c.connection_mode
        if c.network_mode is not None:
            ds.network_mode = c.network_mode
        if c.provider_config is not None:
            # Merge config keys
            config = dict(ds.provider_config or {})
            config.update(c.provider_config)
            ds.provider_config = config
            if "username" in config:
                ds.username = config["username"]

    if request.security is not None:
        s = request.security
        if s.auth_method is not None:
            ds.auth_method = s.auth_method
        if s.tls is not None:
            ds.tls = s.tls
        if s.access_policy is not None:
            ds.access_policy = s.access_policy

        if s.password is not None:
            if ds.secret_reference:
                secret_manager.delete_secret(db, ds.secret_reference)
            ds.secret_reference = secret_manager.store_secret(db, s.password)
        elif s.secret_reference is not None:
            ds.secret_reference = s.secret_reference

    db.commit()
    db.refresh(ds)

    # Retest and refresh metadata
    try:
        test_connection_for_source(db, ds.id, organization_id)
        db.refresh(ds)
    except Exception:
        pass

    caps = get_provider_capabilities(ds.provider)
    return DataSourceResponse.from_orm_model(ds, caps)


def delete_data_source(db: Session, source_id: str, organization_id: str) -> None:
    """Soft-delete a data source registration and purge associated secrets."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found")

    ds.status = "deleted"

    if ds.secret_reference:
        secret_manager.delete_secret(db, ds.secret_reference)
        ds.secret_reference = None

    db.commit()


def list_data_sources(db: Session, organization_id: str) -> List[DataSourceResponse]:
    """List all registered data sources."""
    sources = (
        db.query(DataSource)
        .filter(
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .order_by(DataSource.created_at.desc())
        .all()
    )

    result = []
    for s in sources:
        caps = get_provider_capabilities(s.provider)
        result.append(DataSourceResponse.from_orm_model(s, caps))
    return result


def get_data_source(db: Session, source_id: str, organization_id: str) -> DataSourceResponse:
    """Retrieve details of a single data source connection."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found")

    caps = get_provider_capabilities(ds.provider)
    return DataSourceResponse.from_orm_model(ds, caps)


def test_connection_for_source(
    db: Session, source_id: str, organization_id: str
) -> ConnectionTestResult:
    """Test connection for an existing data source registration."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found")

    # Set status to testing
    ds.health_status = "testing"
    db.commit()

    config = _build_adapter_config(db, ds)
    connector = get_connector(ds.provider, config)
    try:
        result = connector.test_connection()

        # Update local cache values in table with detailed classification
        if result.success:
            ds.health_status = "healthy"
            ds.health_last_error = None
        else:
            err_code = "error"
            if result.details and "error_code" in result.details:
                err_code = result.details["error_code"].lower()
            
            if err_code == "authentication_failed":
                ds.health_status = "auth_failed"
            elif err_code in ("network_error", "dns_error", "timeout"):
                ds.health_status = "network_error"
            elif err_code in ("permission_denied", "database_not_found", "metadata_permission_denied"):
                ds.health_status = "permission_denied"
            else:
                ds.health_status = "error"
            
            ds.health_last_error = result.message

        ds.health_last_check = datetime.now(timezone.utc)
        db.commit()

        # If connection succeeds, synchronize schema details
        if result.success:
            try:
                sync_data_source_metadata_stats(db, source_id, organization_id)
            except Exception:
                pass

        # Format and return Pydantic ConnectionTestResult
        from app.schemas.data_source import ConnectionTestResult as SchemaTestResult, ConnectionTestStep as SchemaTestStep
        steps = [
            SchemaTestStep(
                name=s.name,
                status=s.status,
                message=s.message,
                latency_ms=s.latency_ms
            ) for s in result.steps
        ]
        return SchemaTestResult(
            success=result.success,
            message=result.message,
            latency_ms=result.latency_ms,
            server_version=result.server_version,
            details=result.details,
            steps=steps,
        )
    finally:
        connector.close()


def test_connection_unsaved(request: ConnectionTestRequest) -> ConnectionTestResult:
    """Test a database connection configuration prior to registration."""
    # Parse URI connection string if provided
    if request.connection_string:
        from app.core.uri_parser import parse_connection_string
        parsed = parse_connection_string(request.connection_string)

        request.provider = parsed["provider"]
        request.host = parsed["host"]
        request.port = parsed["port"]
        config = request.provider_config or {}
        config.update(parsed["provider_config"])
        config["database_name"] = parsed["database_name"]
        request.provider_config = config

        if parsed["username"]:
            config["username"] = parsed["username"]
        if parsed["password"]:
            request.password = parsed["password"]

    db_name = request.database_name or (request.provider_config.get("database_name") if request.provider_config else "")
    username = request.username or (request.provider_config.get("username") if request.provider_config else None)

    config = {
        "host": request.host,
        "port": request.port,
        "database_name": db_name,
        "username": username,
        "password": request.password,
        "ssl_enabled": request.ssl_enabled,
        **(request.provider_config or {}),
    }

    connector = get_connector(request.provider, config)
    try:
        result = connector.test_connection()
        from app.schemas.data_source import ConnectionTestResult as SchemaTestResult, ConnectionTestStep as SchemaTestStep
        steps = [
            SchemaTestStep(
                name=s.name,
                status=s.status,
                message=s.message,
                latency_ms=s.latency_ms
            ) for s in result.steps
        ]
        return SchemaTestResult(
            success=result.success,
            message=result.message,
            latency_ms=result.latency_ms,
            server_version=result.server_version,
            details=result.details,
            steps=steps,
        )
    finally:
        connector.close()


def sync_data_source_metadata_stats(
    db: Session, source_id: str, organization_id: str
) -> None:
    """Trigger metadata auto-discovery from the database provider, updating statistics."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        return

    # Update state to syncing
    ds.health_status = "syncing"
    db.commit()

    from app.models.metadata import (
        MetadataSnapshot,
        DatabaseMetadata,
        SchemaMetadata,
        ObjectMetadata,
        ColumnMetadata,
        IndexMetadata,
        RelationshipMetadata,
    )

    # Initialize MetadataSnapshot
    snapshot = MetadataSnapshot(
        data_source_id=source_id,
        organization_id=organization_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(snapshot)
    db.commit()

    config = _build_adapter_config(db, ds)
    connector = get_connector(ds.provider, config)
    try:
        # 1. Connect
        connector.validate_config()
        test_res = connector.test_connection()
        if not test_res.success:
            raise Exception(test_res.message)

        # 2. Extract version & info
        server_info = connector.get_server_info()
        server_version = server_info.get("server_version", "Unknown")

        # 3. Retrieve databases
        target_db = config.get("database_name")
        if target_db:
            databases = [target_db]
        else:
            try:
                databases = connector.list_databases()
            except Exception:
                databases = ["postgres"]

        # 4. Retrieve schemas (gated by capabilities)
        caps = connector.get_capabilities()
        schemas = ["default"]
        if caps.get("schemas", False):
            try:
                schemas = connector.list_schemas()
            except Exception:
                schemas = ["public"]

        # Limit scans to target database or first database to keep run lightweight
        target_db = config.get("database_name") or "postgres"
        dbs_to_scan = [target_db] if target_db in databases else (databases[:1] if databases else [])

        all_objects = []
        all_columns = []
        all_relationships = []
        all_indexes = []

        # Delete existing relational metadata to avoid duplicates (atomic sync replacement)
        db.query(DatabaseMetadata).filter(
            DatabaseMetadata.data_source_id == source_id,
            DatabaseMetadata.organization_id == organization_id
        ).delete(synchronize_session=False)

        db.query(RelationshipMetadata).filter(
            RelationshipMetadata.data_source_id == source_id,
            RelationshipMetadata.organization_id == organization_id
        ).delete(synchronize_session=False)

        db.commit()

        # Database mapping for relational insertions
        db_models_dict = {}
        schema_models_dict = {}
        object_models_dict = {}

        for db_name in dbs_to_scan:
            # Create DatabaseMetadata
            db_meta = DatabaseMetadata(
                data_source_id=source_id,
                organization_id=organization_id,
                name=db_name,
                owner=server_info.get("user"),
                encoding=None,
            )
            db.add(db_meta)
            db.flush()
            db_models_dict[db_name] = db_meta

            for sch_name in schemas:
                # Create SchemaMetadata with provider metadata if Supabase
                schema_provider_metadata = None
                if ds.provider == "supabase":
                    is_managed = sch_name in {"auth", "storage", "realtime", "extensions", "graphql", "supabase", "pg_catalog", "information_schema"}
                    schema_provider_metadata = {
                        "provider": "supabase",
                        "schema_role": "platform" if is_managed else "application",
                        "provider_managed": is_managed
                    }

                sch_meta = SchemaMetadata(
                    database_id=db_meta.id,
                    data_source_id=source_id,
                    organization_id=organization_id,
                    name=sch_name,
                    owner=server_info.get("user"),
                    provider_metadata=schema_provider_metadata,
                )
                db.add(sch_meta)
                db.flush()
                schema_models_dict[(db_name, sch_name)] = sch_meta

                try:
                    objs = connector.list_objects(database=db_name, schema=sch_name)
                    for obj in objs:
                        # Create ObjectMetadata
                        obj_meta = ObjectMetadata(
                            schema_id=sch_meta.id,
                            data_source_id=source_id,
                            organization_id=organization_id,
                            name=obj["name"],
                            type=obj["type"],  # TABLE, VIEW
                            description=obj.get("description", ""),
                            row_count_estimate=obj.get("estimated_row_count", 0),
                            provider_metadata=obj.get("provider_metadata") if ds.provider == "supabase" else None,
                        )
                        db.add(obj_meta)
                        db.flush()
                        object_models_dict[(db_name, sch_name, obj["name"])] = obj_meta
                        all_objects.append(obj)

                        # Fetch Columns
                        try:
                            cols = connector.get_columns(
                                database=db_name, schema=sch_name, object_name=obj["name"]
                            )
                            for idx, col in enumerate(cols):
                                # Create ColumnMetadata
                                col_meta = ColumnMetadata(
                                    object_id=obj_meta.id,
                                    data_source_id=source_id,
                                    organization_id=organization_id,
                                    name=col["name"],
                                    ordinal_position=col.get("ordinal_position", idx + 1),
                                    data_type=col["data_type"],
                                    native_type=col.get("native_type") or col["data_type"],
                                    nullable=col.get("nullable", True),
                                    default_value=col.get("default_value"),
                                    is_primary_key=col.get("is_primary_key", False),
                                    is_foreign_key=col.get("is_foreign_key", False),
                                    description=col.get("description", ""),
                                )
                                db.add(col_meta)
                                # Append to flat list for backward compatibility cache
                                col_flat = col.copy()
                                col_flat["table_name"] = obj["name"]
                                col_flat["schema_name"] = sch_name
                                col_flat["database_name"] = db_name
                                all_columns.append(col_flat)
                        except Exception:
                            pass

                    indexes = []
                    if ds.provider in ("postgresql", "supabase"):
                        try:
                            from app.connectors.postgresql.extractor import PostgreSQLMetadataExtractor
                            pg_extractor = PostgreSQLMetadataExtractor(connector._get_connection())
                            indexes = pg_extractor.get_indexes(sch_name)
                        except Exception:
                            pass
                    elif ds.provider == "mysql":
                        try:
                            from app.connectors.mysql.extractor import MySQLMetadataExtractor
                            mysql_extractor = MySQLMetadataExtractor(connector._get_connection())
                            indexes = mysql_extractor.get_indexes(db_name)
                        except Exception:
                            pass
                    elif ds.provider == "sqlserver":
                        try:
                            from app.connectors.sqlserver.extractor import SQLServerMetadataExtractor
                            sqlserver_extractor = SQLServerMetadataExtractor(connector._get_connection())
                            indexes = sqlserver_extractor.get_indexes(sch_name)
                        except Exception:
                            pass
                    elif ds.provider == "mongodb":
                        try:
                            from app.connectors.mongodb.extractor import MongoDBMetadataExtractor
                            mongo_client = connector._get_connection()
                            mongo_extractor = MongoDBMetadataExtractor(mongo_client)
                            for obj in all_objects:
                                col_indexes = mongo_extractor.get_indexes(db_name, obj["name"])
                                for midx in col_indexes:
                                    midx["table_name"] = obj["name"]
                                indexes.extend(col_indexes)
                        except Exception:
                            pass

                    for idx_info in indexes:
                        try:
                            obj_m = object_models_dict.get((db_name, sch_name, idx_info["table_name"]))
                            if obj_m:
                                idx_meta = IndexMetadata(
                                    object_id=obj_m.id,
                                    data_source_id=source_id,
                                    organization_id=organization_id,
                                    name=idx_info["name"],
                                    columns=idx_info["columns"],
                                    unique=idx_info["unique"],
                                    primary=idx_info["primary"],
                                    type=idx_info["type"],
                                )
                                db.add(idx_meta)
                                all_indexes.append(idx_info)
                        except Exception:
                            pass
                except Exception:
                    pass

        # Retrieve & Store relationships (gated by capabilities)
        caps_rel = caps.get("relationships", "none")
        if caps_rel not in ("none", "inferred"):
            # Standard FK-based relational providers
            for db_name in dbs_to_scan:
                for sch_name in schemas:
                    try:
                        rels = connector.get_relationships(database=db_name, schema=sch_name)
                        rel_groups = {}
                        for rel in rels:
                            c_name = rel.get("constraint_name") or f"fk_{rel['from_table']}_{rel['from_column']}"
                            if c_name not in rel_groups:
                                rel_groups[c_name] = {
                                    "constraint_name": c_name,
                                    "from_table": rel["from_table"],
                                    "to_table": rel["to_table"],
                                    "from_columns": [],
                                    "to_columns": [],
                                    "update_action": rel.get("update_action"),
                                    "delete_action": rel.get("delete_action"),
                                }
                            rel_groups[c_name]["from_columns"].append(rel["from_column"])
                            rel_groups[c_name]["to_columns"].append(rel["to_column"])
                            all_relationships.append(rel)

                        for c_name, g in rel_groups.items():
                            from_obj = object_models_dict.get((db_name, sch_name, g["from_table"]))
                            to_obj = object_models_dict.get((db_name, sch_name, g["to_table"]))
                            if from_obj and to_obj:
                                rel_meta = RelationshipMetadata(
                                    data_source_id=source_id,
                                    organization_id=organization_id,
                                    constraint_name=c_name,
                                    from_object_id=from_obj.id,
                                    from_columns=g["from_columns"],
                                    to_object_id=to_obj.id,
                                    to_columns=g["to_columns"],
                                    update_action=g["update_action"],
                                    delete_action=g["delete_action"],
                                )
                                db.add(rel_meta)
                    except Exception:
                        pass

        # MongoDB: persist inferred cross-collection relationships
        elif caps_rel == "inferred" and ds.provider == "mongodb":
            try:
                inferred_rels = connector.get_inferred_relationships(
                    database=config.get("database_name")
                )
                for rel in inferred_rels:
                    sch_name = "default"
                    from_obj = object_models_dict.get(
                        (config.get("database_name", ""), sch_name, rel["from_table"])
                    )
                    to_obj = object_models_dict.get(
                        (config.get("database_name", ""), sch_name, rel["to_table"])
                    )
                    if from_obj and to_obj:
                        c_name = rel.get(
                            "constraint_name",
                            f"INFERRED:{rel['from_table']}.{rel['from_column']}->{rel['to_table']}.{rel['to_column']}"
                        )
                        rel_meta = RelationshipMetadata(
                            data_source_id=source_id,
                            organization_id=organization_id,
                            constraint_name=c_name,
                            from_object_id=from_obj.id,
                            from_columns=[rel["from_column"]],
                            to_object_id=to_obj.id,
                            to_columns=[rel["to_column"]],
                            update_action="inferred",
                            delete_action=None,
                        )
                        db.add(rel_meta)
                        all_relationships.append(rel)
            except Exception:
                pass

        # Supabase-specific extra discovery
        extensions_list = []
        functions_list = []
        triggers_list = []
        if ds.provider == "supabase":
            try:
                extensions_list = connector.get_extensions()
            except Exception:
                pass
            
            for sch_name in schemas:
                try:
                    functions_list.extend(connector.get_functions(sch_name))
                except Exception:
                    pass
                try:
                    triggers_list.extend(connector.get_triggers(sch_name))
                except Exception:
                    pass

        # Write statistics & populate flat dictionary cache for compatibility
        stats = {
            "databases_count": len(databases),
            "schemas_count": len(schemas),
            "objects_count": len(all_objects),
            "columns_count": len(all_columns),
            "relationships_count": len(all_relationships),
            "indexes_count": len(all_indexes),
            "functions_count": len(functions_list),
            "triggers_count": len(triggers_list),
            "extensions_count": len(extensions_list),
        }

        metadata_normalized = {
            "databases": databases,
            "schemas": schemas,
            "objects": all_objects,
            "columns": all_columns,
            "relationships": all_relationships,
            "statistics": stats,
            "extensions": extensions_list,
            "functions": functions_list,
            "triggers": triggers_list,
        }

        # Update metadata stats on DataSource record
        ds.metadata_normalized = metadata_normalized
        ds.databases_count = stats["databases_count"]
        ds.tables_count = stats["objects_count"]
        ds.columns_count = stats["columns_count"]
        ds.last_sync_at = datetime.now(timezone.utc)
        ds.health_status = "healthy"
        ds.health_last_error = None

        # Complete MetadataSnapshot
        completed_at = datetime.now(timezone.utc)
        duration = int((completed_at - snapshot.started_at).total_seconds() * 1000)
        snapshot.status = "success"
        snapshot.completed_at = completed_at
        snapshot.databases_count = stats["databases_count"]
        snapshot.schemas_count = stats["schemas_count"]
        snapshot.objects_count = stats["objects_count"]
        snapshot.columns_count = stats["columns_count"]
        snapshot.relationships_count = stats["relationships_count"]
        snapshot.duration_ms = duration
        
        # Supabase-specific snapshot details
        snapshot.provider = ds.provider
        snapshot.function_count = len(functions_list)
        snapshot.trigger_count = len(triggers_list)
        snapshot.extension_count = len(extensions_list)

        db.commit()

    except Exception as e:
        db.rollback()
        # Fail Snapshot
        completed_at = datetime.now(timezone.utc)
        snapshot.status = "failed"
        snapshot.error_message = str(e)
        snapshot.completed_at = completed_at
        
        # Update DataSource health
        ds.health_status = "error"
        ds.health_last_error = str(e)
        db.commit()
        raise e
    finally:
        connector.close()


def connect_source(db: Session, source_id: str, organization_id: str) -> DataSourceResponse:
    """Establish active database connection status."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found")

    config = _build_adapter_config(db, ds)
    connector = get_connector(ds.provider, config)
    try:
        result = connector.test_connection()
        ds.health_status = "healthy" if result.success else "error"
        ds.health_last_check = datetime.now(timezone.utc)
        ds.health_last_error = None if result.success else result.message
        db.commit()
    finally:
        connector.close()

    caps = get_provider_capabilities(ds.provider)
    return DataSourceResponse.from_orm_model(ds, caps)


def disconnect_source(db: Session, source_id: str, organization_id: str) -> DataSourceResponse:
    """Disconnect and set health status to disconnected."""
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found")

    ds.health_status = "disconnected"
    ds.health_last_check = datetime.now(timezone.utc)
    db.commit()

    caps = get_provider_capabilities(ds.provider)
    return DataSourceResponse.from_orm_model(ds, caps)


def sync_data_source_background(source_id: str, organization_id: str, user_id: str) -> None:
    """
    Background discovery runner that spawns its own DB session for thread safety.
    """
    from app.db.base import SessionLocal
    from app.services import audit_service

    db = SessionLocal()
    try:
        sync_data_source_metadata_stats(db, source_id, organization_id)

        # Automatically trigger schema embedding indexing to pgvector
        try:
            from app.ai.schema.schema_indexer import index_data_source_schema
            index_data_source_schema(
                db=db,
                data_source_id=source_id,
                organization_id=organization_id,
            )
        except Exception as idx_err:
            logger.error(f"Failed to auto-index data source {source_id} to pgvector: {idx_err}")

        # Log discovery completed audit event
        audit_service.log_event(
            db=db,
            action="METADATA_DISCOVERED",
            organization_id=organization_id,
            user_id=user_id,
            resource_type="data_source",
            resource_id=source_id,
            details={"status": "success"}
        )
    except Exception as e:
        # Log discovery failed audit event
        audit_service.log_event(
            db=db,
            action="METADATA_DISCOVERY_FAILED",
            organization_id=organization_id,
            user_id=user_id,
            resource_type="data_source",
            resource_id=source_id,
            details={"status": "failed", "error": str(e)}
        )
    finally:
        db.close()

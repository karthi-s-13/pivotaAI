"""
Catalog Pydantic Schemas.

Structures the requests and responses for browsing, searching,
and visualizing data relationship maps.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DatabaseResponse(BaseModel):
    id: str
    name: str
    owner: Optional[str] = None
    encoding: Optional[str] = None
    created_at: datetime
    data_source_id: str
    data_source_name: str

    model_config = {"from_attributes": True}


class SchemaResponse(BaseModel):
    id: str
    name: str
    owner: Optional[str] = None
    created_at: datetime
    database_id: str
    database_name: str

    model_config = {"from_attributes": True}


class ObjectSummaryResponse(BaseModel):
    id: str
    name: str
    type: str  # TABLE, VIEW
    description: Optional[str] = None
    row_count_estimate: int
    schema_id: str
    schema_name: str
    database_name: str
    data_source_name: str
    provider_metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ColumnResponse(BaseModel):
    id: str
    name: str
    ordinal_position: int
    data_type: str
    native_type: Optional[str] = None
    nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool
    is_foreign_key: bool
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class IndexResponse(BaseModel):
    id: str
    name: str
    columns: List[str]
    unique: bool
    primary: bool
    type: Optional[str] = None

    model_config = {"from_attributes": True}


class RelationshipResponse(BaseModel):
    id: str
    constraint_name: str
    from_object_id: str
    from_table_name: str
    from_columns: List[str]
    to_object_id: str
    to_table_name: str
    to_columns: List[str]
    update_action: Optional[str] = None
    delete_action: Optional[str] = None

    model_config = {"from_attributes": True}


class ObjectDetailResponse(BaseModel):
    id: str
    name: str
    type: str  # TABLE, VIEW
    description: Optional[str] = None
    row_count_estimate: int
    schema_id: str
    schema_name: str
    database_id: str
    database_name: str
    data_source_name: str
    columns: List[ColumnResponse] = []
    indexes: List[IndexResponse] = []
    relationships_outbound: List[RelationshipResponse] = []
    relationships_inbound: List[RelationshipResponse] = []
    provider_metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class SearchMatchItem(BaseModel):
    id: str
    name: str
    type: str  # database, schema, table, view, column
    details: str  # Context representation (e.g. "sales.public.orders")
    description: Optional[str] = None
    data_source_name: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchMatchItem] = []

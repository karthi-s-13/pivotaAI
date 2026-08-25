"""
Supabase Connector Module.
"""

from app.connectors.supabase.config import SupabaseConnectionConfig
from app.connectors.supabase.connector import SupabaseConnector

__all__ = ["SupabaseConnectionConfig", "SupabaseConnector"]

import os
import sys

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.connectors.sqlserver.connector import SQLServerConnector
from app.connectors.exceptions import InvalidConfigurationError

print("==================================================")
print("TESTING SQL SERVER CONNECTOR COMPLIANCE & VALIDATION")
print("==================================================")

# Test 1: Configuration Validation
print("\n--- Test 1: Invalid Configuration Validation ---")
try:
    conn = SQLServerConnector({
        "provider_type": "sqlserver",
        "host": "",
        "database_name": "master"
    })
    conn.validate_config()
    print("FAILED: Did not raise validation error on empty host")
except ValueError as e:
    print("SUCCESS: Correctly raised ValueError:", e)

try:
    conn = SQLServerConnector({
        "provider_type": "sqlserver",
        "host": "localhost",
        "database_name": ""
    })
    conn.validate_config()
    print("FAILED: Did not raise validation error on empty database name")
except ValueError as e:
    print("SUCCESS: Correctly raised ValueError:", e)

# Test 2: URI Parsing
print("\n--- Test 2: URI Parameter Extraction ---")
uri_config = {
    "provider_type": "sqlserver",
    "connection_string": "mssql+pyodbc://dbuser:dbpass%40123@sql-host:1433/sales_db?driver=ODBC+Driver+18+for+SQL+Server&encrypt=true&trustservercertificate=true&connect_timeout=20"
}
conn = SQLServerConnector(uri_config)
print("Parsed Host:", conn.sql_config.host)
print("Parsed Port:", conn.sql_config.port)
print("Parsed Database:", conn.sql_config.database)
print("Parsed Username:", conn.sql_config.username)
print("Parsed Password (Secret):", conn.sql_config.password.get_secret_value() if conn.sql_config.password else None)
print("Parsed Connect Timeout:", conn.sql_config.connect_timeout)
print("Parsed Driver:", conn.sql_config.driver)
print("Parsed Encrypt:", conn.sql_config.encrypt)
print("Parsed Trust Server Certificate:", conn.sql_config.trust_server_certificate)

assert conn.sql_config.host == "sql-host"
assert conn.sql_config.port == 1433
assert conn.sql_config.database == "sales_db"
assert conn.sql_config.username == "dbuser"
assert conn.sql_config.password.get_secret_value() if conn.sql_config.password else None == "dbpass@123"
assert conn.sql_config.connect_timeout == 20
assert conn.sql_config.driver == "ODBC Driver 18 for SQL Server"
assert conn.sql_config.encrypt is True
assert conn.sql_config.trust_server_certificate is True
print("SUCCESS: URI parameters parsed correctly!")

# Test 3: Integrated Windows Auth connection string mapping
print("\n--- Test 3: Integrated Auth Connection String Mapping ---")
int_config = {
    "provider_type": "sqlserver",
    "host": "localhost",
    "database_name": "master",
    "authentication_method": "integrated",
}
conn = SQLServerConnector(int_config)
odbc_str = conn.sql_config.to_odbc_connection_string()
print("Integrated ODBC Connection String:", odbc_str)
assert "Trusted_Connection=yes" in odbc_str
assert "UID=" not in odbc_str
assert "PWD=" not in odbc_str
print("SUCCESS: Integrated Auth Connection String mapped correctly!")

# Test 4: Driver Unavailable Error Check
print("\n--- Test 4: Driver Unavailable Diagnostic Validation ---")
import pyodbc
original_drivers = pyodbc.drivers
pyodbc.drivers = lambda: []  # Mock no drivers installed

bad_driver_config = {
    "provider_type": "sqlserver",
    "host": "localhost",
    "database_name": "master",
    "username": "sa",
    "password": "password",
    "driver": "NonExistentDriverName"
}
conn = SQLServerConnector(bad_driver_config)
result = conn.test_connection()
pyodbc.drivers = original_drivers

print("Success:", result.success)
print("Message:", result.message)
print("Steps Checklist:")
for step in result.steps:
    print(f" - Step: {step.name} | Status: {step.status} | Msg: {step.message}")

driver_step = next(s for s in result.steps if s.name == "driver")
print(f"Driver step status: {driver_step.status} | Msg: {driver_step.message}")
assert driver_step.status == "failed"
assert result.details.get("error_code") == "DRIVER_NOT_AVAILABLE"
print("SUCCESS: Driver Unavailable diagnostics raised DRIVER_NOT_AVAILABLE correctly!")

# Test 5: Offline Staged Diagnostics Refusal / Timeout Error Mapping
print("\n--- Test 5: Offline Staged Diagnostics Check ---")
offline_config = {
    "provider_type": "sqlserver",
    "host": "192.0.2.1",  # Test-Net-1 non-routable IP
    "database_name": "sales_db",
    "username": "sa",
    "password": "password",
    "connect_timeout": 2,
    "driver": "SQL Server",
    "encrypt": False,
}
conn = SQLServerConnector(offline_config)
result = conn.test_connection()
print("Success:", result.success)
print("Message:", result.message)
print("Steps Checklist:")
for step in result.steps:
    print(f" - Step: {step.name} | Status: {step.status} | Msg: {step.message}")

assert result.success is False
net_step = next(s for s in result.steps if s.name == "network")
print(f"Network step status: {net_step.status}")
assert net_step.status == "failed"

print("\n==================================================")
print("ALL SQL SERVER CONNECTOR VERIFICATIONS PASSED!")
print("==================================================")

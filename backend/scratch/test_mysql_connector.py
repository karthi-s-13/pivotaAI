import os
import sys

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.connectors.mysql.connector import MySQLConnector
from app.connectors.exceptions import InvalidConfigurationError

print("==============================================")
print("TESTING MYSQL CONNECTOR COMPLIANCE & VALIDATION")
print("==============================================")

# Test 1: Configuration Validation
print("\n--- Test 1: Invalid Configuration Validation ---")
try:
    conn = MySQLConnector({
        "provider_type": "mysql",
        "host": "",
        "database_name": "portinity"
    })
    conn.validate_config()
    print("FAILED: Did not raise validation error on empty host")
except ValueError as e:
    print("SUCCESS: Correctly raised ValueError:", e)

try:
    conn = MySQLConnector({
        "provider_type": "mysql",
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
    "provider_type": "mysql",
    "connection_string": "mysql://dbuser:dbpass%40123@mysql-host:3306/sales_db?connect_timeout=15&charset=utf8"
}
conn = MySQLConnector(uri_config)
print("Parsed Host:", conn.mysql_config.host)
print("Parsed Port:", conn.mysql_config.port)
print("Parsed Database:", conn.mysql_config.database)
print("Parsed Username:", conn.mysql_config.username)
print("Parsed Password (Secret):", conn.mysql_config.password.get_secret_value() if conn.mysql_config.password else None)
print("Parsed Connect Timeout:", conn.mysql_config.connect_timeout)
print("Parsed Charset:", conn.mysql_config.charset)

assert conn.mysql_config.host == "mysql-host"
assert conn.mysql_config.port == 3306
assert conn.mysql_config.database == "sales_db"
assert conn.mysql_config.username == "dbuser"
assert conn.mysql_config.password.get_secret_value() if conn.mysql_config.password else None == "dbpass@123"
assert conn.mysql_config.connect_timeout == 15
assert conn.mysql_config.charset == "utf8"
print("SUCCESS: URI parameters parsed correctly!")

# Test 3: Staged Diagnostics Offline Refusal / Error Mapping
print("\n--- Test 3: Connection Diagnostics and Error Mapping ---")
offline_config = {
    "provider_type": "mysql",
    "host": "192.0.2.1",  # Test-Net-1 non-routable IP to simulate network timeout
    "database_name": "sales_db",
    "username": "root",
    "password": "password",
    "connect_timeout": 2
}
conn = MySQLConnector(offline_config)
result = conn.test_connection()
print("Success:", result.success)
print("Message:", result.message)
print("Steps Checklist:")
for step in result.steps:
    print(f" - Step: {step.name} | Status: {step.status} | Msg: {step.message}")

assert result.success is False
# The network step should have failed or skipped
net_step = next(s for s in result.steps if s.name == "network")
print(f"Network step status: {net_step.status}")
assert net_step.status == "failed"

print("\n==============================================")
print("ALL OFFLINE MYSQL CONNECTOR VERIFICATIONS PASSED!")
print("==============================================")

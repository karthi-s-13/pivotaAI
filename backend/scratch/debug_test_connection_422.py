import os
import sys

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_active_user
from app.models.user import User

client = TestClient(app)

mock_user = User(
    id="test-user-id",
    email="test-refine@pivota.ai",
    organization_id="some-org-id",
    role="admin"
)
app.dependency_overrides[get_current_active_user] = lambda: mock_user

# Test 1: Payload with port=0
print("\n--- Test 1: port=0 ---")
p1 = {
    "provider": "postgresql",
    "host": "localhost",
    "port": 0,
    "database_name": "pivota",
    "username": "postgres",
    "password": "password",
}
resp1 = client.post("/api/v1/data-sources/test-connection", json=p1)
print("p1 Status:", resp1.status_code)
if resp1.status_code != 200:
    print("p1 Error:", resp1.json())

# Test 2: Payload with port=None
print("\n--- Test 2: port=None ---")
p2 = {
    "provider": "postgresql",
    "host": "localhost",
    "port": None,
    "database_name": "pivota",
    "username": "postgres",
    "password": "password",
}
resp2 = client.post("/api/v1/data-sources/test-connection", json=p2)
print("p2 Status:", resp2.status_code)
if resp2.status_code != 200:
    print("p2 Error:", resp2.json())

# Test 3: Payload with provider_config having auth_source
print("\n--- Test 3: provider_config check ---")
p3 = {
    "provider": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "pivota",
    "username": "postgres",
    "password": "password",
    "provider_config": {
        "auth_source": "admin"
    }
}
resp3 = client.post("/api/v1/data-sources/test-connection", json=p3)
print("p3 Status:", resp3.status_code)
if resp3.status_code != 200:
    print("p3 Error:", resp3.json())

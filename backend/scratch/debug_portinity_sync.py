import os
import sys

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.schemas.data_source import ConnectionTestRequest
from app.services import data_source_service

request = ConnectionTestRequest(
    provider="postgresql",
    connection_string="postgresql://postgres:karthikeyan%4013@localhost:5432/portinity",
    ssl_enabled=False
)

result = data_source_service.test_connection_unsaved(request)
print("Success:", result.success)
print("Message:", result.message)
print("Steps Checklist:")
for step in result.steps:
    print(f" - Step: {step.name} | Status: {step.status} | Msg: {step.message}")
print("Details:", result.details)

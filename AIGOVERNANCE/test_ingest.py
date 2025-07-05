import os
import asyncio
from fastapi.testclient import TestClient

# 1) Point at a fresh in-memory SQLite before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# 2) Import your FastAPI app and init_db function
from app import app, init_db

# 3) Create tables in the in-memory DB
asyncio.run(init_db())

# 4) Spin up TestClient
client = TestClient(app)

# 5) Call /ingest
response = client.post(
    "/ingest",
    json={"application_id": "app1", "features": {"age": 30, "score": 720}},
    headers={"x-api-key": "secret-key"},
)

# 6) Print out results
print("Status code:", response.status_code)
print("Response JSON:", response.json())

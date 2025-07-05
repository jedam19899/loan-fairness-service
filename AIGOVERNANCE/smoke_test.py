import requests

BASE = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json", "x-api-key": "secret-key"}

# 1) Test /ingest
r1 = requests.post(
    f"{BASE}/ingest", 
    json={"application_id": "app1", "features": {"age": 30, "score": 720}},
    headers=HEADERS
)
print("/ingest →", r1.status_code, repr(r1.text))

# 2) Test /bias/disparate-impact
r2 = requests.get(
    f"{BASE}/bias/disparate-impact",
    params={"privileged": "male", "unprivileged": "female"},
    headers=HEADERS
)
print("/bias/disparate-impact →", r2.status_code, repr(r2.text))

# 3) Test /explain
r3 = requests.post(
    f"{BASE}/explain", 
    json={"application_id": "app1"},
    headers=HEADERS
)
print("/explain →", r3.status_code, repr(r3.text))

# 4) Test /agent
r4 = requests.post(
    f"{BASE}/agent", 
    json={"prompt": "Calculate the disparate impact ratio for privileged group \"male\" and unprivileged group \"female\""},
    headers=HEADERS
)
print("/agent →", r4.status_code, repr(r4.text))

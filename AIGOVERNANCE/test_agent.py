import requests
import pytest

API_URL = "http://127.0.0.1:8000/agent"
API_KEY = "secret-key"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

@pytest.fixture(scope="module")
def base_payload():
    return {
        "prompt": "Calculate the disparate impact ratio for privileged group \"male\" and unprivileged group \"female\""
    }

def test_agent_disparate_impact(base_payload):
    # Send request to /agent
    resp = requests.post(API_URL, json=base_payload, headers=HEADERS)
    # Verify HTTP status
    assert resp.status_code == 200, f"Unexpected status code: {resp.status_code}"

    data = resp.json()
    # Verify response structure
    assert "response" in data, "Missing 'response' field"
    assert "tool_result" in data, "Missing 'tool_result' field"

    # Verify tool_result content
    tool = data["tool_result"]
    assert isinstance(tool, dict), "tool_result is not a dict"
    assert "ratio" in tool, "tool_result missing 'ratio'"
    assert isinstance(tool["ratio"], (float, int)), "ratio is not numeric"

    # Optional: ensure placeholder logic is invoked
    assert tool["ratio"] == 1.23, f"Unexpected ratio value: {tool['ratio']}"

if __name__ == "__main__":
    # Allow running directly without pytest
    pytest.main([__file__])

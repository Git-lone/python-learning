from fastapi.testclient import TestClient
from agent_lab.api import create_app

if __name__ == "__main__":
    with TestClient(create_app()) as client:
        response = client.post(
            "/answer",
            json={"question": "password reset"},
            headers={"Authorization": "Bearer demo-alpha"},
        )
        assert response.status_code == 200
        assert "event: done" in response.text
        assert "PRIVATE" not in response.text
        print("API status=200 done=True tenant_isolated=True")

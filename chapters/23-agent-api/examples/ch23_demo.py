from fastapi.testclient import TestClient
from agent_lab.api import create_app

if __name__ == "__main__":
    # TestClient 直接调用 ASGI 应用，无需监听端口；默认使用离线模型网关。
    with TestClient(create_app()) as client:
        response = client.post(
            "/answer",
            json={"question": "password reset"},
            headers={"Authorization": "Bearer demo-alpha"},
        )
        assert response.status_code == 200
        # HTTP 200 只证明响应已建立，还需确认完成事件，并检查其他租户的资料未泄漏。
        assert "event: done" in response.text
        assert "PRIVATE" not in response.text
        print("API status=200 done=True tenant_isolated=True")

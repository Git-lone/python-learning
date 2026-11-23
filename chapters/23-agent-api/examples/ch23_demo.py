"""第 23 章最小演示：用测试客户端跑通认证、租户检索和离线 SSE 问答。

从 agent_lab.api.create_app 跟到 answer 与 events，观察哪些错误在建立流之前
返回，哪些通过流中事件报告。本例检查完整响应文本，不测真实网络首字延迟，
也不能证明浏览器断连或多客户端并发时的行为。
"""

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
        # TestClient 在这里读取完整响应后才返回，分片发送机制要继续阅读 API 的生成器。
        # HTTP 200 只证明响应已建立，还需确认完成事件，并检查其他租户的资料未泄漏。
        assert "event: done" in response.text
        assert "PRIVATE" not in response.text
        print("API status=200 done=True tenant_isolated=True")

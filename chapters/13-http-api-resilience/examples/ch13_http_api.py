"""使用本地 HTTP 服务演示超时、状态码和 JSON 边界。"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from urllib.request import urlopen


class DemoHandler(BaseHTTPRequestHandler):
    """返回固定 JSON 的本地测试服务；所有 GET 路径都走相同响应，不演示路由。"""

    def do_GET(self) -> None:
        # 使用本地固定响应，教程无需访问互联网也能验证真实 HTTP 流程。
        body = json.dumps({"service": "catalog", "items": 2}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # HTTP 长度按编码后的字节数计算，不能用原始字符串的字符数代替。
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        # 关闭示例服务器的默认访问日志，使教学输出稳定；真实服务应保留可观测性。
        return


def main() -> int:
    """启动本地服务、发起一次请求，再确定性关闭线程与监听端口。

    本例只演示成功响应和超时参数；没有重试，也未校验 JSON 的业务字段类型。
    重试的边界与练习实现放在本章参考答案中，不能由一次成功请求推断可靠性。
    """

    # 端口 0 让操作系统选择空闲端口，避免测试机器上的端口冲突。
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        # timeout 约束阻塞网络操作，不是整个业务流程的统一截止时间。
        with urlopen(f"http://127.0.0.1:{port}/catalog", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
            status = response.status
    finally:
        # 网络示例也必须有确定的资源回收路径。
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    print(f"status={status} service={payload['service']} items={payload['items']}")
    print("timeout=explicit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

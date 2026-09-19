# 第 23 章：FastAPI 服务与 SSE 协议

先修：第 10、13、19、22 章。本章把检索和模型网关组合成只读 API，不提供自动执行写操作的入口。

## 学习目标

- 通过可验证的服务协议提供检索增强答案。
- 客户端识别 error/done 终态；鉴权在流开始前完成。
- 完成“安全编码 SSE，正文换行不能伪造事件”并解释失败测试的意义。

## Java 对照

### FastAPI 服务与 SSE 协议 {#compare-agent-api}

- 共同用途：通过可验证的服务协议提供检索增强答案。
- 可验证行为差异：Python async 生命周期与 Java WebFlux 相似，但不要在事件循环中阻塞。
- Python 适用场景：流式输出、身份校验和调用失败反馈。
- Java 开发者常见误区：已发响应头后还尝试改 HTTP 状态码。
- 修正方式：客户端识别 error/done 终态；鉴权在流开始前完成。



FastAPI 路由、Pydantic 请求模型、依赖注入可类比 Controller、DTO、认证上下文。流式响应可以类比 WebFlux；不能在响应头已经发出后再依赖 HTTP 500 告知模型失败。

## Python 知识

### 请求经过哪些边界

1. `Authorization` 映射服务端 principal，本地固定演示 token 对应 alpha 租户。
2. 请求体只接收 1～2000 字符的非空问题，额外 tenant 字段直接拒绝。
3. 按 principal 检索，空证据直接 abstain，不调用模型。
4. 逐个发送 start、delta、done 或 error；用 JSON 编码正文，避免换行注入 SSE。

实现：[api.py](../../agent_lab/api.py)，验证：[test_api.py](../../tests/test_api.py)。默认 `OfflineGateway`，不会产生模型费用。生产切换需要显式注入真正网关并管理客户端生命周期，不会自动读取 API key 开启计费。

## 可运行示例

### 运行记录：ch23-demo

```powershell
python -m tools.run_example --chapter 23
python -m pytest tests/test_api.py -q
python -m uvicorn agent_lab.api:app --host 127.0.0.1 --port 8765
```

最后一条用于手动启动；端口占用时换一个。文档入口 `http://127.0.0.1:8765/docs`，可使用终端发起流式请求：

```powershell
curl.exe -N http://127.0.0.1:8765/answer -H "Authorization: Bearer demo-alpha" -H "Content-Type: application/json" --data-raw '{"question":"password reset"}'
```

预期 start 带引用 ID，delta 返回离线证据，done 的 token 数为 null。null 表示没有计量，不是调用了真实模型且恰好免费。

### 失败约定

- 鉴权失败 401；无效问题或非法字段 422，都发生在开流前。
- 开流后超时：`event: error`，code 为 timeout；其他模型失败使用 model_failed，不回传供应商敏感错误正文。
- 完成只能看 done，收到 HTTP 200 但连接断了不代表任务完成；error 后不能拼成成功答案。
- async cancellation 应向上传播。单元测试覆盖生成器取消和关闭，尚未验证真实代理层的断网、缓冲和背压。

## 练习

完成 [encode_sse](exercises/exercise_ch23.py)：事件名只允许小写字母与下划线；正文用 `json.dumps`；每条以两个换行结束。正文内的换行不能变成新的事件。

```powershell
python -m tools.check_exercise --chapter 23
python -m tools.check_exercise --chapter 23 --solution
```

[参考答案](../../solutions/ch23_agent_api.py)。扩展时增加真实认证、限流、并发上限、服务端保存 request 归属及断连测试。

**部署边界：** `demo-alpha` 是公开演示口令，仅允许 loopback 学习。不得直接暴露到公网或公司生产网。当前没有 OAuth、持久化多租户存储、分布式任务队列或生产限流。

依据：[FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/)。本项目没有另建网页前端，主要通过 API 文档和测试操作。

## 验证方式

运行 `python -m tools.check_exercise --chapter 23` 验证自己的实现，`--solution` 用于核对参考答案。示例合同由 `python -m tools.run_example --chapter 23` 验证；工程异常测试见根目录 tests。

## 章节总结

客户端识别 error/done 终态；鉴权在流开始前完成。面试时同时说明实现、测试证据和未实现边界；公开原帖与自编练习分别见 [真实面经](../../career/INTERVIEW_EXPERIENCES.md) 和 [面试练习](../../career/INTERVIEW_PRACTICE.md)。

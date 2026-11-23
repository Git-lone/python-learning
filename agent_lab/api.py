"""第 23 章只读问答 API：校验请求 → 确定租户 → 检索资料 → 逐条转发 SSE。

create_app 是应用工厂，可注入离线、真实或故障网关。请求校验和认证发生在流建立前，
生成失败则发生在流内部，需要用事件向客户端报告。本模块仅演示固定 token 的本地
认证与异步资源管理，不包含生产鉴权、持久化会话或跨进程任务调度。
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing
import json
import logging
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_lab.gateway import Gateway, OfflineGateway
from agent_lab.retrieval import retrieve

logger = logging.getLogger(__name__)


# 请求模型类似 Java 的 DTO + Bean Validation；此处的模型说明不用 docstring，
# 避免 Pydantic 将教学文字变成接口 JSON Schema 的 description。
class Question(BaseModel):
    # 请求边界做真实数据校验；长度限制之外，还要拒绝全空白文本。
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


def principal(authorization: Annotated[str | None, Header()] = None) -> str:
    # 仅用于本地演示的固定凭据，不能直接部署；租户来自认证结果，不接收请求自报租户。
    if authorization != "Bearer demo-alpha":
        raise HTTPException(401, "invalid demo token")
    return "alpha"


def sse(event: str, data: dict[str, object]) -> str:
    """把事件名和结构化载荷编码成 SSE 文本帧；传输分块不等于事件边界。"""

    # 调用方使用固定事件名；JSON 转义正文换行，末尾空行划分 SSE 消息边界。
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n"


def create_app(gateway: Gateway | None = None, timeout_seconds: float = 35) -> FastAPI:
    """构造可注入依赖的 FastAPI 应用，将 HTTP 契约与模型供应商解耦。

    timeout_seconds 限制模型事件流阶段，不涵盖前面的同步检索，也不是完整接口
    SLA。健康检查只说明应用能响应，不会验证模型、检索库或外部系统可用性。
    """

    # 注入网关便于用离线替身或错误替身测试，默认不会调用计费模型接口。
    backend = gateway or OfflineGateway()
    app = FastAPI(title="Agent Career Lab (offline)")

    @app.get("/health")
    def health() -> dict[str, str]:
        # 路由函数说明使用普通注释，避免 FastAPI 把 docstring 加入 OpenAPI 描述。
        return {"status": "ok"}

    @app.post("/answer")
    def answer(body: Question, tenant: Annotated[str, Depends(principal)]) -> StreamingResponse:
        # Depends 先调用认证依赖，再把可信租户注入路由；不能从问答正文提取租户权限。
        # 同步路由由 FastAPI 在线程池运行，检索不会直接占用流式输出的事件循环。
        hits = retrieve(body.question, tenant)
        citations = [hit.document.id for hit in hits]
        context = "\n".join(f"[{hit.document.id}] {hit.document.text}" for hit in hits)
        request_id = str(uuid4())

        async def events() -> AsyncIterator[str]:
            """按消费速度产生 SSE 帧，并负责流中失败和资源关闭。

            start 中的 citations 是提供给网关的检索结果，不是答案真实性证明。
            无证据时返回 abstain + done；模型成功时返回 delta + done；超时或
            异常时返回 error。客户端需按事件判断终态，不能仅凭 HTTP 200 判成功。
            """

            yield sse("start", {"request_id": request_id, "citations": citations})
            if not hits:
                # 没有证据时直接拒答，避免无依据生成，同时省去模型调用。
                yield sse("abstain", {"reason": "no_evidence"})
                yield sse("done", {"request_id": request_id})
                return
            try:
                finished = False
                async with asyncio.timeout(timeout_seconds):
                    # 提前 break 或客户端断开时也关闭异步生成器，让底层网络流释放资源。
                    async with aclosing(backend.stream(body.question, context)) as stream:
                        async for event in stream:
                            if event.kind == "delta":
                                yield sse("delta", {"text": event.text})
                            elif event.kind == "done":
                                finished = True
                                yield sse(
                                    "done",
                                    {
                                        "request_id": request_id,
                                        "input_tokens": event.input_tokens,
                                        "output_tokens": event.output_tokens,
                                    },
                                )
                                break
                if not finished:
                    # 即使收到部分文本，没有 done 也不能当作完整响应。
                    raise RuntimeError("missing completion")
            except TimeoutError:
                # 已经发出的 delta 无法撤回；error 表示这次答案不完整，不再追加成功 done。
                yield sse("error", {"request_id": request_id, "code": "timeout"})
            except Exception:
                # HTTP 流已开始后用 error 事件报告失败，不把供应商错误正文或客户资料外传。
                # CancelledError 属于 BaseException，不在这里吞掉，保留断连取消语义。
                logger.warning("model_stream_failed request_id=%s", request_id)
                yield sse("error", {"request_id": request_id, "code": "model_failed"})

        return StreamingResponse(
            # 这里传生成器而非拼好的文本；ASGI 服务在后续发送阶段逐步拉取内容。
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Request-ID": request_id},
        )

    return app


app = create_app()

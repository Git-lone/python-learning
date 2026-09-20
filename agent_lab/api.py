"""Local read-only service; demo auth must be replaced before deployment."""

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
    # 调用方使用固定事件名；JSON 转义正文换行，末尾空行划分 SSE 消息边界。
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n"


def create_app(gateway: Gateway | None = None, timeout_seconds: float = 35) -> FastAPI:
    # 注入网关便于用离线替身或错误替身测试，默认不会调用计费模型接口。
    backend = gateway or OfflineGateway()
    app = FastAPI(title="Agent Career Lab (offline)")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/answer")
    def answer(body: Question, tenant: Annotated[str, Depends(principal)]) -> StreamingResponse:
        # 同步路由由 FastAPI 在线程池运行，检索不会直接占用流式输出的事件循环。
        hits = retrieve(body.question, tenant)
        citations = [hit.document.id for hit in hits]
        context = "\n".join(f"[{hit.document.id}] {hit.document.text}" for hit in hits)
        request_id = str(uuid4())

        async def events() -> AsyncIterator[str]:
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
                yield sse("error", {"request_id": request_id, "code": "timeout"})
            except Exception:
                # HTTP 流已开始后用 error 事件报告失败，不把供应商错误正文或客户资料外传。
                # CancelledError 属于 BaseException，不在这里吞掉，保留断连取消语义。
                logger.warning("model_stream_failed request_id=%s", request_id)
                yield sse("error", {"request_id": request_id, "code": "model_failed"})

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Request-ID": request_id},
        )

    return app


app = create_app()

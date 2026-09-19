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
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


def principal(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization != "Bearer demo-alpha":
        raise HTTPException(401, "invalid demo token")
    return "alpha"


def sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n"


def create_app(gateway: Gateway | None = None, timeout_seconds: float = 35) -> FastAPI:
    backend = gateway or OfflineGateway()
    app = FastAPI(title="Agent Career Lab (offline)")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/answer")
    def answer(body: Question, tenant: Annotated[str, Depends(principal)]) -> StreamingResponse:
        hits = retrieve(body.question, tenant)
        citations = [hit.document.id for hit in hits]
        context = "\n".join(f"[{hit.document.id}] {hit.document.text}" for hit in hits)
        request_id = str(uuid4())

        async def events() -> AsyncIterator[str]:
            yield sse("start", {"request_id": request_id, "citations": citations})
            if not hits:
                yield sse("abstain", {"reason": "no_evidence"})
                yield sse("done", {"request_id": request_id})
                return
            try:
                finished = False
                async with asyncio.timeout(timeout_seconds):
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
                    raise RuntimeError("missing completion")
            except TimeoutError:
                yield sse("error", {"request_id": request_id, "code": "timeout"})
            except Exception:
                # Do not leak prompts, provider error bodies, credentials or customer data.
                logger.warning("model_stream_failed request_id=%s", request_id)
                yield sse("error", {"request_id": request_id, "code": "model_failed"})

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Request-ID": request_id},
        )

    return app


app = create_app()

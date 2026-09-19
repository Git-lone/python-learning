import asyncio
import json

from fastapi.testclient import TestClient
import pytest

from agent_lab.api import create_app, sse
from agent_lab.gateway import Event

HEADERS = {"Authorization": "Bearer demo-alpha"}


def test_auth_schema_and_tenant_injection():
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/answer", json={"question": "invoice"}).status_code == 401
        for data in (
            {"question": " "},
            {"question": "x" * 2001},
            {"question": "invoice", "tenant": "beta"},
        ):
            assert client.post("/answer", json=data, headers=HEADERS).status_code == 422


@pytest.mark.parametrize("question, event", [("password reset", "delta"), ("volcano", "abstain")])
def test_stream_success_or_abstention(question, event):
    with TestClient(create_app()) as client:
        response = client.post("/answer", json={"question": question}, headers=HEADERS)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert f"event: {event}" in response.text
        assert response.text.count("event: done") == 1
        assert "PRIVATE" not in response.text
        assert "kb-private" not in response.text


def test_sse_json_prevents_newline_event_injection():
    value = 'hello\n\nevent: forged\ndata: secret\n"'
    wire = sse("delta", {"text": value})
    assert wire.count("\n\n") == 1
    assert json.loads(wire.split("data: ", 1)[1])["text"] == value


@pytest.mark.parametrize("mode", ["raise", "timeout", "truncated"])
def test_stream_failure_is_explicit_and_redacted(mode):
    class Broken:
        async def stream(self, question, context):
            yield Event("delta", "partial")
            if mode == "timeout":
                await asyncio.sleep(10)
            elif mode == "raise":
                raise RuntimeError("SECRET-provider-message")

    with TestClient(create_app(Broken(), timeout_seconds=0.01)) as client:
        response = client.post("/answer", json={"question": "invoice"}, headers=HEADERS)
        assert "event: error" in response.text
        assert "event: done" not in response.text
        assert "SECRET" not in response.text


def test_cancellation_propagates_and_closes_gateway():
    # Exercise generator cancellation directly rather than claiming TestClient simulates TCP loss.
    closed = []

    class Cancellable:
        async def stream(self, question, context):
            try:
                yield Event("delta", "partial")
                raise asyncio.CancelledError()
            finally:
                closed.append(True)

    with TestClient(create_app(Cancellable())) as client:
        response = client.post("/answer", json={"question": "invoice"}, headers=HEADERS)
        assert "event: done" not in response.text
        assert closed == [True]

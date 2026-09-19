import asyncio
import json

import httpx2
from openai import AsyncOpenAI
import pytest

from agent_lab.gateway import OfflineGateway, OpenAIGateway, collect


def test_offline_does_not_invent_usage():
    async def scenario():
        events = [event async for event in OfflineGateway().stream("q", "evidence")]
        assert events[-1].kind == "done"
        assert events[-1].input_tokens is None
        assert "".join(event.text for event in events) == "OFFLINE evidence: evidence"

    asyncio.run(scenario())


@pytest.mark.parametrize("terminal", ["response.completed", "response.incomplete", "eof"])
def test_real_sdk_parses_fixture_sse_and_handles_incomplete(terminal):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        events = [
            {
                "type": "response.output_text.delta",
                "delta": "Hello",
                "item_id": "msg_demo",
                "output_index": 0,
                "content_index": 0,
                "sequence_number": 0,
            }
        ]
        if terminal != "eof":
            events.append(
                {
                    "type": terminal,
                    "sequence_number": 1,
                    "response": {
                        "id": "resp_demo",
                        "object": "response",
                        "created_at": 1,
                        "model": "fixture-model",
                        "status": "completed" if terminal.endswith("completed") else "incomplete",
                        "output": [],
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 2,
                            "total_tokens": 12,
                            "input_tokens_details": {"cached_tokens": 0},
                            "output_tokens_details": {"reasoning_tokens": 0},
                        },
                    },
                }
            )
        wire = "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events)
        return httpx2.Response(
            200, headers={"Content-Type": "text/event-stream"}, content=wire.encode()
        )

    async def scenario():
        async with AsyncOpenAI(
            api_key="fixture-only",
            max_retries=0,
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
        ) as client:
            gateway = OpenAIGateway(client, "fixture-model")
            if terminal == "response.completed":
                events = [event async for event in gateway.stream("q", "evidence")]
                assert events[-1].input_tokens == 10
                assert events[-1].output_tokens == 2
                assert events[0].text == "Hello"
            else:
                with pytest.raises(RuntimeError):
                    await collect(gateway, "q", "evidence")

    asyncio.run(scenario())
    assert len(requests) == 1
    assert requests[0]["store"] is False
    assert requests[0]["max_output_tokens"] == 300

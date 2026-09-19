"""Default: offline. --live is an explicit opt-in to a potentially billable API."""

import argparse
import asyncio
import os

from openai import AsyncOpenAI

from agent_lab.gateway import OfflineGateway, OpenAIGateway, collect


async def demo(live: bool) -> None:
    question, context = "How do I recover access?", "[kb-reset] Use the password reset page."
    if not live:
        print(await collect(OfflineGateway(), question, context))
        return
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise ValueError("--live requires OPENAI_API_KEY and OPENAI_MODEL")
    async with AsyncOpenAI(timeout=20, max_retries=0) as client:
        print(await collect(OpenAIGateway(client, os.environ["OPENAI_MODEL"]), question, context))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    asyncio.run(demo(args.live))


if __name__ == "__main__":
    main()

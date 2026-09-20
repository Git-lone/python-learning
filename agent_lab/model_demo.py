"""Default: offline. --live is an explicit opt-in to a potentially billable API."""

import argparse
import asyncio
import os

from openai import AsyncOpenAI

from agent_lab.gateway import OfflineGateway, OpenAIGateway, collect


async def demo(live: bool) -> None:
    question, context = "How do I recover access?", "[kb-reset] Use the password reset page."
    # 默认分支不访问模型 API；只有显式 --live 才读取凭据并可能产生费用。
    if not live:
        print(await collect(OfflineGateway(), question, context))
        return
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise ValueError("--live requires OPENAI_API_KEY and OPENAI_MODEL")
    # 关闭 SDK 自动重试，让教学中一次调用的请求次数明确；客户端退出时关闭连接池。
    async with AsyncOpenAI(timeout=20, max_retries=0) as client:
        print(await collect(OpenAIGateway(client, os.environ["OPENAI_MODEL"]), question, context))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    asyncio.run(demo(args.live))


if __name__ == "__main__":
    main()

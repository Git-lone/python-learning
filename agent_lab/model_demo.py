"""第 19 章模型接入入口：默认跑离线替身，显式 --live 才调用可能计费的 API。

先看 demo 中网关如何替换，再读 gateway 中的事件转换。问题和资料保持相同，
便于观察依赖注入的作用；离线输出用于验证程序流程，不能作为模型效果评测。
"""

import argparse
import asyncio
import os

from openai import AsyncOpenAI

from agent_lab.gateway import OfflineGateway, OpenAIGateway, collect


async def demo(live: bool) -> None:
    """执行一次资料问答，并把异步流汇总后打印；真实模式要求显式提供模型配置。"""

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
    """解析命令行开关，并在同步入口创建、运行和关闭 asyncio 事件循环。"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    asyncio.run(demo(args.live))


if __name__ == "__main__":
    main()

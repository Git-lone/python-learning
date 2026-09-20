import asyncio
from agent_lab.model_demo import demo

if __name__ == "__main__":
    # False 选择离线网关；SDK 适配与流式事件转换的实现位于 agent_lab/gateway.py。
    asyncio.run(demo(False))

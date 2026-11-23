"""第 19 章最小演示：从同步脚本进入异步模型网关，并收集流式文本。

本入口固定使用离线模式，运行后可观察事件如何汇总为输出。接着阅读
agent_lab.model_demo.demo 与 gateway.Gateway，理解同一调用方如何替换实现。
真实调用需通过 model_demo 的 --live 显式开启，本例没有模型效果验收。
"""

import asyncio
from agent_lab.model_demo import demo

if __name__ == "__main__":
    # 类似 Java main 的入口保护：被 import 时不会启动事件循环或执行演示。
    # False 选择离线网关；SDK 适配与流式事件转换的实现位于 agent_lab/gateway.py。
    asyncio.run(demo(False))

# 第 19 章学案：真实模型 SDK 与流式完成

配合[本章讲解](README.md)使用。默认只运行离线模式；本学案不需要 API Key。

## 模型 SDK 和流式输出是什么

模型 SDK 是与推理服务通信的客户端，负责构造请求、鉴权、接收响应和转换错误。流式输出让服务端边生成边发送事件，用户可以较早看到文本片段；片段不是最终结果，只有明确完成事件才证明本次生成完整结束。网络断开、模型拒绝或输出被截断都应有不同终态。

## 技术栈与落地场景

本项目用锁定版本的 `openai` Python SDK、`AsyncOpenAI`、Responses API、异步生成器、`asyncio.timeout` 和 HTTPX mock transport。`Gateway` 是本项目自有端口，`OfflineGateway` 提供无网络替身，`OpenAIGateway` 适配真实服务。聊天界面的逐字显示、长摘要生成和 API 的 SSE 转发会用到流式处理；短小的后台分类任务也可以选择非流式调用。

一次模型请求要同时考虑输入上下文、输出 token 上限、单次网络超时和整个任务的时间预算。SDK 的自动重试与应用重试若同时开启，尝试次数可能超过预期；已经向客户端发出部分文本的请求也不能无条件重放。用量缺失记为 `None`，表示未知，不等于零成本。

## 代码怎样工作

[网关实现](../../agent_lab/gateway.py)把供应商事件统一成 `Event('delta', text)` 与 `Event('done', usage)`。真实流收到 `response.output_text.delta` 时转发文本，收到 `response.completed` 且状态正确时才完成；失败、不完整或流结束却无完成事件均报错。[离线演示](../../agent_lab/model_demo.py)默认不访问网络，只有显式 `--live` 才创建真实客户端。这里实现了模型调用边界，尚未把模型工具调用片段接入 Agent Loop。

## 课前热身

- 第 13 章的一次 HTTP 超时和整个 Agent 运行预算有什么差别？
- 流里已收到几段文字，但缺少完成事件时，可否宣告成功？

## 探究任务

1. 阅读[网关实现](../../agent_lab/gateway.py)，列出离线与真实 SDK 两个适配器共同向业务层暴露的事件：________。
2. 运行 `python -m tools.run_example --chapter 19`，记录默认输出和用量字段：________。解释 `None` 代表什么：________。
3. 阅读[测试](../../tests/test_gateway.py)，找出“缺少完成事件”和“超时”案例；写出部分文本与最终答案之间的区别：________。

## 动手完成

- 完成[练习](exercises/exercise_ch19.py)的 `parse_usage`。先处理合法的 0，再拒绝缺字段、字符串数字、负数和布尔值。
- 运行 `python -m tools.check_exercise --chapter 19`。记录首次失败类别：________。

## 过关自检

- 能区分 SDK 对象与本项目内部事件合同。
- 能说明为什么流关闭、完成事件和总预算都需要检查。
- 能说出真实调用可能计费，练习检查为何使用离线或 mock transport。完成后再看[参考答案](../../solutions/ch19_model_sdk.py)。

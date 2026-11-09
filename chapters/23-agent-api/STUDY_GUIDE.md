# 第 23 章学案：FastAPI 与 SSE

配合[本章讲解](README.md)使用，默认在本地离线运行。

## Agent API 与 SSE 是什么

Agent API 把模型或检索能力通过 HTTP 暴露给调用方。SSE（Server-Sent Events）让服务端在一个响应中连续发送事件，每个事件有名称与数据，适合单向推送文本增量。HTTP 状态码只能在响应开始前确定；开流后的模型失败需要发送 `error` 事件，客户端必须看到 `done` 才能把内容认定为完整答案。

## 技术栈与落地场景

本项目用 FastAPI、Pydantic 请求校验、`StreamingResponse`、异步生成器、JSON 编码和离线 `Gateway`。适用于知识问答 API、聊天界面文本流和后端聚合服务。真实部署还需认证、授权、限流、并发控制、断连取消与反向代理缓冲测试；公开演示 token 只供本地 loopback 使用。[FastAPI 流式响应说明](https://fastapi.tiangolo.com/advanced/custom-response/)。

身份必须由服务端根据 Authorization 映射，不能让请求体自称属于哪个 tenant。先按身份过滤文档，再把证据交给模型；无证据直接拒答。正文用 JSON 编码后放入 SSE 数据行，防止用户文本中的换行伪造另一个事件。

## 代码怎样工作

[API 实现](../../agent_lab/api.py)先校验身份和问题，再检索对应租户文档；正常流依次发 `start`、若干 `delta`、`done`。模型超时或失败发生在开流后时发 `error`，取消则向上传播。[练习](exercises/exercise_ch23.py)实现单条 SSE 帧编码。`OfflineGateway` 只回显合成证据，不代表接通真实模型或完成生产认证。

## 课前热身

- 第 13 章的 HTTP 状态码能否表达“流已开始后模型才失败”？
- 客户端收到 HTTP 200，但没有 `done` 事件，能否当作完整答案？

## 探究任务

1. 阅读[API 实现](../../agent_lab/api.py)，画出鉴权、请求校验、租户检索、`start/delta/done` 的顺序：________。
2. 运行 `python -m tools.run_example --chapter 23`，记录正常流的事件名和无证据请求的行为：________。
3. 在[测试](../../tests/test_api.py)中找出 401、422、流内超时及取消案例。分别说明错误发生在开流前还是开流后：________。

## 动手完成

- 完成[练习](exercises/exercise_ch23.py)的 `encode_sse`，验证正文含换行时仍只形成一条 JSON 编码事件。
- 运行 `python -m tools.check_exercise --chapter 23`。记录事件帧末尾的分隔符：________。

## 过关自检

- 能说明租户身份为什么由服务端 principal 决定。
- 能区分 HTTP 错误与 SSE `error` 事件。
- 能解释断连后没有 `done` 的文本为何不能交付为最终结果。完成后再看[参考答案](../../solutions/ch23_agent_api.py)。

# 第 24 章：上线指标与作品集验收

先修：第 18、21、22、23 章。把“可以跑”变成“能解释边界、验证风险、展示证据”，但不把教学项目包装成已上线产品。

**配套学案：** [阅读概念讲义并完成实践](STUDY_GUIDE.md)

## 学习目标

- 基于可观察证据决定是否发布，而不只展示成功截图。
- 先校验指标有效性，权限失败作为硬门禁。
- 完成“安全底线不能被平均指标掩盖”并解释失败测试的意义。

## Java 对照

### 上线指标与作品集验收 {#compare-production-readiness}

- 共同用途：基于可观察证据决定是否发布，而不只展示成功截图。
- 可验证行为差异：金额用 Decimal，不能用二进制浮点假装精确货币。
- Python 适用场景：成本核算、指标门禁和项目演示。
- Java 开发者常见误区：把异常值 NaN 或权限失败混入平均数后放行。
- 修正方式：先校验指标有效性，权限失败作为硬门禁。



Java 服务已有的日志、限流、幂等、发布回滚经验仍然适用。Agent 还需要观察模型版本、prompt 版本、工具选择、证据引用和业务成功判定。费用用 `Decimal`，对应 Java `BigDecimal`，不要用浮点比较制造账差。

## Python 知识

### 可运行内容

[operations.py](../../agent_lab/operations.py) 按明确传入的输入/输出单价计算费用，并提供教学发布门禁。单价 2 和 8 是**人为例子，不对应任何厂商报价**；结果的货币单位由输入单价约定，示例没有税费、缓存或特殊 token 计价。

### 教案：用证据决定能否发布（建议 40 分钟）

1. **先定口径（5 分钟）：** 写出成功率、p95 延迟、越权次数和费用各自依赖的原始样本。不要把本章示例单价和阈值当作真实供应商报价或团队目标。
2. **读代码（10 分钟）：** 追踪 `operations.py` 的 Decimal 费用计算和发布门禁。解释为什么即使成功率达到 100%，只要越权次数大于 0 也不能放行。
3. **运行观察（10 分钟）：** 运行示例与测试，记录输出值；将“样例通过”“服务具备发布条件”“生产运行稳定”分成不同结论。
4. **练习（10 分钟）：** 在阈值边界两侧各选一个数，并加入 NaN、无限值和负计数，先写预期再实现 `release_allowed`。自测：只记录平均延迟能否替代 p95？不能；长尾请求会被平均值掩盖。
5. **复盘（5 分钟）：** 对照本章演示清单，挑一项未实现的生产验证写出实验步骤和证据来源；作品集只陈述亲自验证过的能力。

## 可运行示例

### 运行记录：ch24-demo

```powershell
python -m tools.run_example --chapter 24
python -m pytest tests/test_operations.py -q
```

输出 `illustrative_cost=0.0036`；哪怕成功率为 100%，出现 1 次越权也拒绝发布。阈值 90% 和 2000ms 只是练习合同，真实阈值需要业务和样本支撑。

### 演示清单

| 场景 | 当前证据 | 生产仍缺的验证 |
|---|---|---|
| 工具读取 | MCP 子进程测试 | 远程认证、超时、恶意结果、版本不兼容 |
| 审批与恢复 | 两个进程之间恢复、接受/拒绝测试 | 多 worker 竞争、下游不可幂等场景、状态迁移 |
| 权限隔离 | API 不接收 tenant，检索按 principal 过滤 | 对象级授权、缓存键、日志、向量检索权限 |
| 检索效果 | 5 条合成题 | 真实脱敏数据、分桶、独立测试集、人工标注 |
| 流式接口 | 部分输出、失败、超时、取消测试 | 真实网络断开、反向代理缓冲、慢消费者 |
| 费用核算 | Decimal 单价公式 | provider 用量对账、重试/失败请求、缓存收费 |

### 应记录什么

一条安全的 trace 至少能串联 request_id、run_id、模型与 prompt 版本、阶段耗时、工具名称和结果状态、检索文档 ID、终态和用量。正文默认不落日志；需要诊断时先脱敏、限制权限与保留期。

示例 API 目前只生成 request_id 和最小错误日志，并未接入完整 OpenTelemetry tracing。这是下一步实验，不要在简历里写成已实现。

## 练习

实现 [release_allowed](exercises/exercise_ch24.py)：成功率至少 0.9、p95 不超过 2000ms、权限失败为 0；非法区间、NaN、无限值或负计数报错。

```powershell
python -m tools.check_exercise --chapter 24
python -m tools.check_exercise --chapter 24 --solution
python -m tools.run_example --all
python -m tools.check_exercise --all --solution
python -m pytest -q
python -m mypy
python -m tools.validate_content
```

[参考答案](../../solutions/ch24_production_readiness.py)。全部基础验收完成后，按[作品集指南](../../career/PORTFOLIO.md)再做一个独立扩展，展示改动前后的原始数据，而不是照读参考代码。

## 验证方式

运行 `python -m tools.check_exercise --chapter 24` 验证自己的实现，`--solution` 用于核对参考答案。示例合同由 `python -m tools.run_example --chapter 24` 验证；工程异常测试见根目录 tests。

## 章节总结

先校验指标有效性，权限失败作为硬门禁。面试时同时说明实现、测试证据和未实现边界；公开原帖与自编练习分别见 [真实面经](../../career/INTERVIEW_EXPERIENCES.md) 和 [面试练习](../../career/INTERVIEW_PRACTICE.md)。

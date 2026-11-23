"""第 22 章最小演示：输出 BM25 检索的可重复回归指标。

先在 agent_lab.evaluate 查看问题与相关文档真值，再读 retrieval 中两个指标的
公式。本入口只测资料排序和负例拒答，不调用 LLM，因此不评估生成内容或模型成本。
"""

import json
from agent_lab.evaluate import evaluate

if __name__ == "__main__":
    # 输出可机器读取的回归指标；合成样例的高分不等于生产检索效果。
    print(json.dumps(evaluate(), sort_keys=True))

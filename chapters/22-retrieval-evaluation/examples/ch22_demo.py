import json
from agent_lab.evaluate import evaluate

if __name__ == "__main__":
    # 输出可机器读取的回归指标；合成样例的高分不等于生产检索效果。
    print(json.dumps(evaluate(), sort_keys=True))

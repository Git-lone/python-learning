import json
from agent_lab.evaluate import evaluate

if __name__ == "__main__":
    print(json.dumps(evaluate(), sort_keys=True))

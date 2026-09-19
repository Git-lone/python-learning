"""Reference answer for CH19; inspect only after attempting the exercise."""


def parse_usage(payload: dict[str, object]) -> tuple[int, int]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("usage missing")
    counts = usage.get("input_tokens"), usage.get("output_tokens")
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("invalid token counts")
    return counts

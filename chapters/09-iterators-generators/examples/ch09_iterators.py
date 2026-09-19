"""迭代器协议和惰性生成器。"""

from collections.abc import Iterator


class Countdown(Iterator[int]):
    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self) -> Iterator[int]:
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


def running_totals(numbers: Iterator[int]) -> Iterator[int]:
    total = 0
    for number in numbers:
        total += number
        yield total


def main() -> int:
    print(f"countdown={list(Countdown(3))}")
    print(f"running_totals={list(running_totals(iter([2, 3, 5])))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

from metrun import analyse, get_records, print_report, trace


@trace
def slow_query(n):
    return sum(i * i for i in range(n))


@trace
def handler(items):
    return [slow_query(i) for i in items]


def main() -> None:
    handler(list(range(25)))
    print_report(analyse(get_records()))


if __name__ == "__main__":
    main()

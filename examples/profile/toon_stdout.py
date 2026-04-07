"""Example: TOON/YAML format output to stdout."""
from metrun import analyse, get_records, reset, trace
from metrun.toon import generate_toon


@trace
def slow_query(n):
    return sum(i * i for i in range(n))


@trace
def handler(items):
    return [slow_query(i) for i in items]


def main():
    reset()
    handler(list(range(25)))

    records = get_records()
    bottlenecks = analyse(records)
    toon_yaml = generate_toon(bottlenecks, records, top_n=5)

    print(toon_yaml)


if __name__ == "__main__":
    main()

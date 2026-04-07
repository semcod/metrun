"""Example: generate TOON metric tree from profiling."""
from pathlib import Path

from metrun import analyse, get_records, reset, trace
from metrun.toon import generate_toon, save_toon


@trace
def slow(n):
    return sum(range(n))


@trace
def main_work(items):
    return [slow(i) for i in items]


def main():
    reset()
    main_work(range(50))

    records = get_records()
    bottlenecks = analyse(records)
    toon = generate_toon(bottlenecks, records, top_n=5)

    output_path = Path("/tmp/metrun_example.toon.yaml")
    save_toon(toon, output_path)
    print(f"TOON output saved to: {output_path}")
    print("\n--- Content ---")
    print(toon[:500] + "...")


if __name__ == "__main__":
    main()

"""Example: export and re-import profiling records as JSON."""
from pathlib import Path

from metrun import analyse, get_records, reset, trace, save_records_json, load_records_file


@trace
def work(n):
    return sum(range(n))


def main():
    reset()
    for i in range(10, 50, 10):
        work(i)

    # Export records
    records = get_records()
    json_path = Path("/tmp/metrun_records.json")
    save_records_json(records, json_path)
    print(f"Saved {len(records)} records to {json_path}")

    # Re-import and analyse
    loaded = load_records_file(json_path)
    bottlenecks = analyse(loaded)
    print(f"\nTop bottleneck: {bottlenecks[0].name if bottlenecks else 'none'}")


if __name__ == "__main__":
    main()

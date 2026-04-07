#!/usr/bin/env python3
"""Standalone metrun example — copy this into your project."""
# Requirements: pip install metrun

from metrun import analyse, get_records, reset, trace
from metrun.toon import generate_toon


@trace
def process_data(items):
    return [item * 2 for item in items]


@trace
def load_data(n):
    return list(range(n))


def main():
    reset()
    data = load_data(1000)
    result = process_data(data)
    print(f"Processed {len(result)} items")

    # Generate TOON/YAML report
    records = get_records()
    bottlenecks = analyse(records)
    toon_yaml = generate_toon(bottlenecks, records, top_n=5)
    print(toon_yaml)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Standalone metrun example — copy this into your project."""
# Requirements: pip install metrun

from metrun import analyse, get_records, print_report, trace


@trace
def process_data(items):
    return [item * 2 for item in items]


@trace
def load_data(n):
    return list(range(n))


def main():
    data = load_data(1000)
    result = process_data(data)
    print(f"Processed {len(result)} items")

    # Generate performance report
    bottlenecks = analyse(get_records())
    print_report(bottlenecks)


if __name__ == "__main__":
    main()

"""Example: cProfile bridge for profiling any callable."""
from metrun import analyse, print_report
from metrun.cprofile_bridge import CProfileBridge


def compute(n):
    return sum(i * i for i in range(n))


def main():
    bridge = CProfileBridge()

    # Profile a function
    decorated = bridge.profile_func(compute)
    for i in range(10, 100, 10):
        decorated(i)

    # Get records and report
    records = bridge.to_records(exclude_stdlib=True)
    print_report(analyse(records))


if __name__ == "__main__":
    main()

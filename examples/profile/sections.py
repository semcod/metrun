"""Example: section context manager for code blocks."""
from metrun import analyse, get_records, print_report, section


def main():
    with section("data_load"):
        data = list(range(1000))

    with section("processing"):
        result = [x * 2 for x in data]

    with section("save"):
        _ = len(result)

    print_report(analyse(get_records()))


if __name__ == "__main__":
    main()

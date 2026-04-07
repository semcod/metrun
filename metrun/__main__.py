"""Module entry-point for `python -m metrun`."""

from metrun.cli import cli


if __name__ == "__main__":
    raise SystemExit(cli())

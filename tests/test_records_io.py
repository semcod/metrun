from click.testing import CliRunner

from metrun import FunctionRecord
from metrun.cli import cli
from metrun.records_io import dump_records_json, load_records_file, load_records_json, save_records_json


def _make_records(language: str = "javascript"):
    return {
        "root": FunctionRecord(
            name="root",
            total_time=1.0,
            calls=1,
            children=["child"],
            language=language,
        ),
        "child": FunctionRecord(
            name="child",
            total_time=0.25,
            calls=4,
            parents=["root"],
            language=language,
        ),
    }


def test_records_json_round_trip_preserves_language():
    records = _make_records("rust")
    payload = dump_records_json(records)
    loaded = load_records_json(payload)

    assert set(loaded) == {"child", "root"}
    assert loaded["root"].language == "rust"
    assert loaded["child"].parents == ["root"]
    assert loaded["root"].children == ["child"]


def test_load_records_file_supports_jsonl_and_merges_duplicates(tmp_path):
    path = tmp_path / "profile.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"name":"root","total_time":1.0,"calls":1,"children":["child"],"language":"javascript"}',
                '{"name":"root","total_time":0.5,"calls":2,"children":["child"],"language":"javascript"}',
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_records_file(path)
    assert loaded["root"].total_time == 1.5
    assert loaded["root"].calls == 3
    assert loaded["root"].language == "javascript"


def test_cli_inspect_accepts_language_neutral_records(tmp_path):
    path = tmp_path / "profile.json"
    save_records_json(_make_records("javascript"), path)

    result = CliRunner().invoke(cli, ["inspect", str(path)])

    assert result.exit_code == 0, result.output
    assert "language: javascript" in result.output
    assert "node --prof" in result.output or "clinic flame" in result.output

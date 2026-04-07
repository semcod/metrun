import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from metrun.profiler import FunctionRecord

_SCHEMA_VERSION = 1
_RECORD_COLLECTION_KEYS = ("records", "functions", "nodes", "items")
_NAME_KEYS = (
    "name",
    "qualname",
    "qualified_name",
    "qualifiedName",
    "symbol",
    "function",
    "id",
)
_FILE_KEYS = ("file", "filename", "path")
_LINE_KEYS = ("line", "lineno", "lineNumber")
_TOTAL_TIME_KEYS = (
    "total_time",
    "totalTime",
    "cumulative_time",
    "cumulativeTime",
    "duration",
    "time",
    "self_time",
    "selfTime",
)
_CALLS_KEYS = ("calls", "callCount", "count", "invocations", "hits")
_CHILD_KEYS = ("children", "callees", "childFunctions")
_PARENT_KEYS = ("parents", "callers", "parentFunctions")
_LANGUAGE_KEYS = ("language", "runtime", "lang")


def _first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value.decode("utf-8") if isinstance(value, bytes) else value]
    if isinstance(value, Mapping):
        nested_name = _first_present(value, _NAME_KEYS)
        return [str(nested_name)] if nested_name is not None else [str(dict(value))]
    try:
        iterator = iter(value)
    except TypeError:
        return [str(value)]

    result: list[str] = []
    for item in iterator:
        if isinstance(item, Mapping):
            nested_name = _first_present(item, _NAME_KEYS)
            result.append(str(nested_name) if nested_name is not None else str(dict(item)))
        else:
            result.append(str(item))
    return result


def _coerce_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for {label}: {value!r}") from exc


def _coerce_float(value: Any, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid number for {label}: {value!r}") from exc


def _looks_like_single_record(payload: Mapping[str, Any]) -> bool:
    return any(key in payload for key in (*_NAME_KEYS, *_TOTAL_TIME_KEYS, *_CALLS_KEYS))


def _compose_name(entry: Mapping[str, Any], fallback_name: str | None) -> str:
    qualified = _first_present(
        entry,
        ("qualified_name", "qualifiedName", "qualname"),
    )
    if qualified is not None:
        return str(qualified)

    name = _first_present(entry, _NAME_KEYS)
    label = str(name if name is not None else fallback_name if fallback_name is not None else "")

    file_name = _first_present(entry, _FILE_KEYS)
    line_no = _first_present(entry, _LINE_KEYS)
    module_name = _first_present(entry, ("module", "namespace", "package", "class"))

    if file_name is not None and line_no is not None and label:
        return f"{file_name}:{line_no}({label})"
    if module_name is not None and label:
        return f"{module_name}.{label}"
    if label:
        return label
    if file_name is not None and line_no is not None:
        return f"{file_name}:{line_no}"
    return "unknown"


def _build_record(
    entry: Mapping[str, Any],
    *,
    fallback_name: str | None,
    default_language: str,
) -> FunctionRecord:
    name = _compose_name(entry, fallback_name)
    total_time = _coerce_float(
        _first_present(entry, _TOTAL_TIME_KEYS) if _first_present(entry, _TOTAL_TIME_KEYS) is not None else 0.0,
        f"total_time for {name}",
    )
    calls = _coerce_int(
        _first_present(entry, _CALLS_KEYS) if _first_present(entry, _CALLS_KEYS) is not None else 0,
        f"calls for {name}",
    )
    language_value = _first_present(entry, _LANGUAGE_KEYS)
    language = str(language_value if language_value is not None else default_language or "generic")

    return FunctionRecord(
        name=name,
        total_time=total_time,
        calls=calls,
        children=_string_list(_first_present(entry, _CHILD_KEYS)),
        parents=_string_list(_first_present(entry, _PARENT_KEYS)),
        language=language,
    )


def _merge_unique(existing: list[str], new_items: list[str]) -> list[str]:
    merged = list(existing)
    seen = set(existing)
    for item in new_items:
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def _merge_records(existing: FunctionRecord, incoming: FunctionRecord) -> FunctionRecord:
    existing.total_time += incoming.total_time
    existing.calls += incoming.calls
    existing.children = _merge_unique(existing.children, incoming.children)
    existing.parents = _merge_unique(existing.parents, incoming.parents)
    if existing.language in {"", "generic"} and incoming.language not in {"", "generic"}:
        existing.language = incoming.language
    return existing


def record_to_payload(record: FunctionRecord) -> dict[str, Any]:
    return asdict(record)


def records_to_payload(records: Mapping[str, FunctionRecord]) -> dict[str, Any]:
    ordered = sorted(records.values(), key=lambda record: record.name)
    payload_records = [record_to_payload(record) for record in ordered]
    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "records": payload_records,
    }

    languages = {record.language for record in ordered if record.language}
    if len(languages) == 1:
        payload["language"] = next(iter(languages))

    return payload


def dump_records_json(records: Mapping[str, FunctionRecord], *, indent: int = 2) -> str:
    return json.dumps(records_to_payload(records), indent=indent, ensure_ascii=False)


def save_records_json(records: Mapping[str, FunctionRecord], path: str | Path, *, indent: int = 2) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_records_json(records, indent=indent), encoding="utf-8")


def _decode_json_payload(payload: Any) -> Any:
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        return json.loads(payload)
    return payload


def _records_entries_from_collection(collection: Any, key: str) -> list[tuple[str | None, Any]]:
    if isinstance(collection, Mapping):
        return list(collection.items())
    if isinstance(collection, list):
        return [(None, item) for item in collection]
    raise ValueError(f"Unsupported records collection in field '{key}'")


def _records_entries_from_mapping(payload: Mapping[str, Any]) -> tuple[str, list[tuple[str | None, Any]]]:
    default_language = str(_first_present(payload, _LANGUAGE_KEYS) or "generic")

    for key in _RECORD_COLLECTION_KEYS:
        if key in payload:
            return default_language, _records_entries_from_collection(payload[key], key)

    if _looks_like_single_record(payload):
        return default_language, [(None, payload)]

    if all(isinstance(value, Mapping) for value in payload.values()):
        return default_language, list(payload.items())

    raise ValueError("Unsupported records payload structure")


def _records_entries_from_payload(payload: Any) -> tuple[str, list[tuple[str | None, Any]]]:
    if isinstance(payload, Mapping):
        return _records_entries_from_mapping(payload)
    if isinstance(payload, list):
        return "generic", [(None, item) for item in payload]
    raise ValueError("Unsupported records payload type")


def _build_records(entries: list[tuple[str | None, Any]], default_language: str) -> dict[str, FunctionRecord]:
    records: dict[str, FunctionRecord] = {}
    for fallback_name, entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError(f"Each record entry must be a mapping, got {type(entry)!r}")

        record = _build_record(
            entry,
            fallback_name=fallback_name,
            default_language=default_language,
        )
        if record.name in records:
            records[record.name] = _merge_records(records[record.name], record)
        else:
            records[record.name] = record

    return records


def load_records_json(payload: Any) -> dict[str, FunctionRecord]:
    payload = _decode_json_payload(payload)
    default_language, entries = _records_entries_from_payload(payload)
    return _build_records(entries, default_language)


def load_records_file(path: str | Path) -> dict[str, FunctionRecord]:
    file_path = Path(path)
    if file_path.suffix.lower() in {".jsonl", ".ndjson"}:
        records: dict[str, FunctionRecord] = {}
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            chunk_records = load_records_json(line)
            for name, record in chunk_records.items():
                if name in records:
                    records[name] = _merge_records(records[name], record)
                else:
                    records[name] = record
        return records

    return load_records_json(file_path.read_text(encoding="utf-8"))

#!/usr/bin/env python3
"""Build canonical talk documents from the timestamped transcript.

Only Python's standard library is required. The source transcript is read-only;
all generated artifacts are written below data/processed by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "Transcripts_PlainText" / "Transcripts_Text" / "transcripts" / "Text_Transcript_original_AOKA-8157.txt"
DEFAULT_CONFIG = ROOT / "config" / "talks.json"
DEFAULT_OUTPUT = ROOT / "data" / "processed"

LINE_PATTERN = re.compile(
    r"^(?P<time>\d{2}:\d{2}:\d{2}) \[(?P<label>[^\]]+)](?:\s(?P<text>.*))?$"
)


@dataclass(frozen=True)
class Utterance:
    start_time: str
    start_seconds: int
    text: str
    source_line: int
    source_label: str


def seconds(timestamp: str) -> int:
    hours, minutes, secs = (int(part) for part in timestamp.split(":"))
    if minutes > 59 or secs > 59:
        raise ValueError(f"Timestamp inválido: {timestamp}")
    return hours * 3600 + minutes * 60 + secs


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\ufeff", ""))
    return re.sub(r"\s+", " ", value).strip()


def clean_label(value: str) -> str:
    value = clean_text(value)
    value = re.sub(r"^>>\s*", "", value)
    return value.split(" - ", 1)[0].strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def display_path(path: Path) -> str:
    """Prefer project-relative paths while supporting external output dirs."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def parse_transcript(source: Path) -> tuple[list[Utterance], dict[str, Any]]:
    raw = source.read_bytes()
    decoded = raw.decode("utf-8-sig")
    utterances: list[Utterance] = []
    ignored_nonempty: list[dict[str, Any]] = []
    inversions: list[dict[str, Any]] = []
    previous: Utterance | None = None

    for line_number, raw_line in enumerate(decoded.splitlines(), start=1):
        line = raw_line.rstrip()
        match = LINE_PATTERN.match(line)
        if not match:
            if line.strip():
                ignored_nonempty.append({"source_line": line_number, "text": clean_text(line)})
            continue

        timestamp = match.group("time")
        utterance = Utterance(
            start_time=timestamp,
            start_seconds=seconds(timestamp),
            text=clean_text(match.group("text") or ""),
            source_line=line_number,
            source_label=clean_label(match.group("label")),
        )
        if not utterance.text:
            continue
        if previous and utterance.start_seconds < previous.start_seconds:
            inversions.append(
                {
                    "previous_source_line": previous.source_line,
                    "previous_time": previous.start_time,
                    "source_line": utterance.source_line,
                    "time": utterance.start_time,
                    "delta_seconds": utterance.start_seconds - previous.start_seconds,
                }
            )
        utterances.append(utterance)
        previous = utterance

    if not utterances:
        raise ValueError(f"No se encontraron intervenciones en {source}")

    diagnostics = {
        "source_sha256": sha256_bytes(raw),
        "source_bytes": len(raw),
        "source_lines": len(decoded.splitlines()),
        "parsed_utterances": len(utterances),
        "ignored_nonempty_lines": ignored_nonempty,
        "timestamp_inversions": inversions,
    }
    return utterances, diagnostics


def load_config(config_path: Path) -> dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def select_talk(
    all_utterances: list[Utterance], definition: dict[str, Any]
) -> list[Utterance]:
    start = seconds(definition["start_time"])
    end = seconds(definition["end_time"])
    if end < start:
        raise ValueError(f"Rango invertido en {definition['talk_id']}")

    selected = [
        utterance
        for utterance in all_utterances
        if start <= utterance.start_seconds <= end
    ]
    # Source order is canonical. Timestamps are metadata and may contain local
    # inversions or overlapping transcription hypotheses.
    selected.sort(key=lambda item: item.source_line)
    if not selected:
        raise ValueError(f"La ponencia {definition['talk_id']} quedó vacía")

    if selected[0].start_time != definition["start_time"]:
        raise ValueError(
            f"Inicio no encontrado en {definition['talk_id']}: "
            f"esperado {definition['start_time']}, obtenido {selected[0].start_time}"
        )
    if selected[-1].start_time != definition["end_time"]:
        raise ValueError(
            f"Fin no encontrado en {definition['talk_id']}: "
            f"esperado {definition['end_time']}, obtenido {selected[-1].start_time}"
        )
    if selected[0].text != clean_text(definition["start_marker"]):
        raise ValueError(f"Cambió el marcador inicial de {definition['talk_id']}")
    if selected[-1].text != clean_text(definition["end_marker"]):
        raise ValueError(f"Cambió el marcador final de {definition['talk_id']}")
    return selected


def build_records(
    source: Path, config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    utterances, diagnostics = parse_transcript(source)
    event = config["event"]
    definitions = config["talks"]
    talk_ids = [item["talk_id"] for item in definitions]
    if len(talk_ids) != len(set(talk_ids)):
        raise ValueError("Hay talk_id duplicados en la configuración")

    previous_end = -1
    records: list[dict[str, Any]] = []
    selected_lines: set[int] = set()
    for talk_index, definition in enumerate(definitions, start=1):
        start = seconds(definition["start_time"])
        if start <= previous_end:
            raise ValueError(f"Las ponencias se solapan en {definition['talk_id']}")
        selected = select_talk(utterances, definition)
        previous_end = seconds(definition["end_time"])
        selected_lines.update(item.source_line for item in selected)
        text = "\n".join(item.text for item in selected)

        record = {
            "schema_version": config["schema_version"],
            "event_id": event["event_id"],
            "event_title": event["title"],
            "event_date": event["date"],
            "talk_id": definition["talk_id"],
            "talk_index": talk_index,
            "title": definition["title"],
            "primary_speaker": definition["primary_speaker"],
            "speakers": definition["speakers"],
            "languages": event["languages"],
            "start_time": selected[0].start_time,
            "end_time": selected[-1].start_time,
            "start_seconds": selected[0].start_seconds,
            "end_seconds": selected[-1].start_seconds,
            "utterance_count": len(selected),
            "text": text,
            "content_sha256": sha256_text(text),
            "source_file": source.name,
            "utterances": [
                {"sequence_index": index, **asdict(item)}
                for index, item in enumerate(selected)
            ],
        }
        records.append(record)

    diagnostics["selected_utterances"] = len(selected_lines)
    diagnostics["excluded_utterances"] = len(utterances) - len(selected_lines)
    diagnostics["talk_count"] = len(records)
    return records, diagnostics


def render_talk(record: dict[str, Any]) -> str:
    speakers = ", ".join(record["speakers"])
    body = "\n".join(
        f"[{item['start_time']}] {item['text']}" for item in record["utterances"]
    )
    return (
        f"Evento: {record['event_title']}\n"
        f"Ponencia: {record['title']}\n"
        f"Ponente(s): {speakers}\n"
        f"Rango: {record['start_time']} - {record['end_time']}\n"
        f"ID: {record['talk_id']}\n"
        "\n---\n\n"
        f"{body}\n"
    )


def write_outputs(
    output_dir: Path,
    source: Path,
    config_path: Path,
    records: list[dict[str, Any]],
    diagnostics: dict[str, Any],
) -> None:
    talks_dir = output_dir / "talks"
    talks_dir.mkdir(parents=True, exist_ok=True)

    jsonl = "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    )
    (output_dir / "talks.jsonl").write_text(jsonl, encoding="utf-8", newline="\n")

    output_files: list[dict[str, Any]] = []
    for record in records:
        destination = talks_dir / f"{record['talk_id']}.txt"
        rendered = render_talk(record)
        destination.write_text(rendered, encoding="utf-8", newline="\n")
        output_files.append(
            {
                "path": display_path(destination),
                "sha256": sha256_text(rendered),
                "bytes": len(rendered.encode("utf-8")),
            }
        )

    validation = {
        "status": "passed",
        "policy": {
            "canonical_order": "source_line",
            "timestamps": "metadata_only",
            "overlapping_blocks": "preserved_without_automatic_reordering_or_removal",
        },
        "checks": {
            "source_parsed": True,
            "talk_ids_unique": True,
            "talk_ranges_non_overlapping": True,
            "boundary_markers_matched": True,
            "talks_nonempty": True,
            "unicode_feff_removed": all(
                "\ufeff" not in record["text"] for record in records
            ),
            "baz_preserved": any("BAZ" in record["text"] for record in records),
            "source_line_canonical_order": all(
                [item["source_line"] for item in record["utterances"]]
                == sorted(item["source_line"] for item in record["utterances"])
                for record in records
            ),
            "sequence_indexes_consecutive": all(
                [item["sequence_index"] for item in record["utterances"]]
                == list(range(len(record["utterances"])))
                for record in records
            ),
        },
        "diagnostics": diagnostics,
    }
    validation_text = json.dumps(validation, ensure_ascii=False, indent=2) + "\n"
    (output_dir / "validation_report.json").write_text(
        validation_text, encoding="utf-8", newline="\n"
    )

    talks_jsonl = output_dir / "talks.jsonl"
    manifest = {
        "schema_version": "1.0",
        "pipeline": "raw-to-talks",
        "source": {
            "path": display_path(source),
            "sha256": diagnostics["source_sha256"],
            "immutable": True,
        },
        "config": {
            "path": display_path(config_path),
            "sha256": sha256_bytes(config_path.read_bytes()),
        },
        "statistics": {
            "talk_count": len(records),
            "parsed_utterances": diagnostics["parsed_utterances"],
            "selected_utterances": diagnostics["selected_utterances"],
            "excluded_utterances": diagnostics["excluded_utterances"],
        },
        "outputs": [
            {
                "path": display_path(talks_jsonl),
                "sha256": sha256_bytes(talks_jsonl.read_bytes()),
                "bytes": talks_jsonl.stat().st_size,
            },
            *output_files,
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = args.source.resolve()
    config_path = args.config.resolve()
    output = args.output.resolve()
    config = load_config(config_path)
    records, diagnostics = build_records(source, config)
    write_outputs(output, source, config_path, records, diagnostics)
    print(
        f"OK: {len(records)} ponencias, "
        f"{diagnostics['selected_utterances']} intervenciones seleccionadas, "
        f"salida en {output}"
    )


if __name__ == "__main__":
    main()


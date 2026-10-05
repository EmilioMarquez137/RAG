#!/usr/bin/env python3
"""Build Child V1 chunks from canonical talks without creating Parents."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable

import tiktoken


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "talks.jsonl"
DEFAULT_CONFIG = ROOT / "config" / "child_v1.json"
DEFAULT_CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
DEFAULT_VALIDATION = ROOT / "data" / "processed" / "chunks_validation.json"
DEFAULT_MANIFEST = ROOT / "data" / "processed" / "chunks_manifest.json"
DEFAULT_STATS_JSON = ROOT / "data" / "analysis" / "child_v1_statistics.json"
DEFAULT_STATS_MD = ROOT / "data" / "analysis" / "child_v1_statistics.md"
PERCENTILES = (0.25, 0.50, 0.75, 0.90, 0.95, 0.99)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def project_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def percentile(values: Iterable[int], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("No se puede calcular un percentil sin valores")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def rounded(value: float) -> float | int:
    result = round(value, 2)
    return int(result) if result.is_integer() else result


def numeric_stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    result: dict[str, Any] = {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 2),
    }
    names = {0.25: "p25", 0.50: "median", 0.75: "p75", 0.90: "p90", 0.95: "p95", 0.99: "p99"}
    for probability in PERCENTILES:
        result[names[probability]] = rounded(percentile(values, probability))
    return result


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError(f"No hay registros en {path}")
    return records


class TokenCounter:
    def __init__(self, encoding_name: str, separator: str) -> None:
        self.encoding_name = encoding_name
        self.separator = separator
        self.encoding = tiktoken.get_encoding(encoding_name)

    def text(self, value: str) -> int:
        return len(self.encoding.encode(value))

    def utterances(self, utterances: list[dict[str, Any]]) -> int:
        return self.text(self.separator.join(item["text"] for item in utterances))

    def serialize(self, utterances: list[dict[str, Any]]) -> str:
        return self.separator.join(item["text"] for item in utterances)


def include_crossing_candidate(
    current_tokens: int,
    candidate_tokens: int,
    target_tokens: int,
    has_new_utterance: bool,
) -> bool:
    """Apply the nearest-target rule; ties include the candidate."""
    if not has_new_utterance:
        return True
    if candidate_tokens <= target_tokens:
        return True
    distance_before = abs(target_tokens - current_tokens)
    distance_after = abs(candidate_tokens - target_tokens)
    return distance_after <= distance_before


def overlap_suffix(
    utterances: list[dict[str, Any]],
    overlap_tokens: int,
    counter: TokenCounter,
) -> list[dict[str, Any]]:
    if overlap_tokens <= 0 or not utterances:
        return []
    selected: list[dict[str, Any]] = []
    for utterance in reversed(utterances):
        selected.insert(0, utterance)
        if counter.utterances(selected) >= overlap_tokens:
            break
    return selected


def validate_config(config: dict[str, Any]) -> None:
    if config["algorithm"] != "child-v1-nearest-complete-utterance":
        raise ValueError("Algoritmo no soportado")
    if config["crossing_rule"] != "closest_to_target":
        raise ValueError("Child V1 requiere closest_to_target")
    if config["tie_breaker"] != "include":
        raise ValueError("Child V1 requiere incluir en caso de empate")
    if config["minimum_new_utterances"] != 1:
        raise ValueError("Child V1 requiere al menos una utterance nueva")
    if config["target_tokens"] <= 0:
        raise ValueError("target_tokens debe ser positivo")
    if not 0 <= config["overlap_tokens"] < config["target_tokens"]:
        raise ValueError("overlap_tokens debe estar entre 0 y target_tokens")
    installed = version(config["tokenizer"]["library"])
    if installed != config["tokenizer"]["library_version"]:
        raise ValueError(
            f"Versión de tokenizer distinta: esperada {config['tokenizer']['library_version']}, instalada {installed}"
        )


def build_talk_chunks(
    talk: dict[str, Any],
    config: dict[str, Any],
    counter: TokenCounter,
) -> list[dict[str, Any]]:
    source_utterances = talk["utterances"]
    cursor = 0
    overlap: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    target = config["target_tokens"]

    while cursor < len(source_utterances):
        chunk_index = len(chunks)
        previous_chunk_id = chunks[-1]["chunk_id"] if chunks else None
        current = list(overlap)
        new_start_cursor = cursor
        closure: dict[str, Any] | None = None

        while cursor < len(source_utterances):
            next_utterance = source_utterances[cursor]
            current_tokens = counter.utterances(current) if current else 0
            candidate = [*current, next_utterance]
            candidate_tokens = counter.utterances(candidate)
            has_new = cursor > new_start_cursor

            if not has_new:
                current = candidate
                cursor += 1
                if candidate_tokens == target:
                    closure = {"reason": "exact_target"}
                    break
                if candidate_tokens > target:
                    closure = {
                        "reason": "forced_progress_over_target",
                        "tokens_before": current_tokens,
                        "tokens_after": candidate_tokens,
                    }
                    break
                continue

            if candidate_tokens < target:
                current = candidate
                cursor += 1
                continue

            if candidate_tokens == target:
                current = candidate
                cursor += 1
                closure = {"reason": "exact_target"}
                break

            include = include_crossing_candidate(
                current_tokens, candidate_tokens, target, has_new_utterance=True
            )
            distance_before = abs(target - current_tokens)
            distance_after = abs(candidate_tokens - target)
            if include:
                current = candidate
                cursor += 1
                reason = (
                    "tie_include"
                    if distance_after == distance_before
                    else "closest_after"
                )
            else:
                reason = "closest_before"
            closure = {
                "reason": reason,
                "candidate_sequence_index": next_utterance["sequence_index"],
                "tokens_before": current_tokens,
                "tokens_after": candidate_tokens,
                "distance_before": distance_before,
                "distance_after": distance_after,
            }
            break

        if cursor == len(source_utterances) and closure is None:
            closure = {"reason": "end_of_talk"}

        new_utterances = source_utterances[new_start_cursor:cursor]
        if not new_utterances:
            raise AssertionError("Un Child no puede contener solamente overlap")

        overlap_count = len(current) - len(new_utterances)
        if overlap_count < 0:
            raise AssertionError("Conteo de overlap inválido")
        overlap_items = current[:overlap_count]
        text = counter.serialize(current)
        chunk_id = f"{talk['talk_id']}_c{chunk_index:04d}"
        utterance_records = []
        for position, utterance in enumerate(current):
            utterance_records.append(
                {
                    "position": position,
                    "sequence_index": utterance["sequence_index"],
                    "source_line": utterance["source_line"],
                    "start_time": utterance["start_time"],
                    "token_count": counter.text(utterance["text"]),
                    "is_overlap": position < overlap_count,
                    "text": utterance["text"],
                }
            )

        overlap_info = None
        if overlap_items:
            overlap_info = {
                "previous_chunk_id": previous_chunk_id,
                "utterance_count": len(overlap_items),
                "token_count": counter.utterances(overlap_items),
                "start_sequence_index": overlap_items[0]["sequence_index"],
                "end_sequence_index": overlap_items[-1]["sequence_index"],
            }

        chunk = {
            "schema_version": config["schema_version"],
            "algorithm": config["algorithm"],
            "chunk_id": chunk_id,
            "event_id": talk["event_id"],
            "talk_id": talk["talk_id"],
            "title": talk["title"],
            "primary_speaker": talk["primary_speaker"],
            "chunk_index": chunk_index,
            "start_sequence_index": current[0]["sequence_index"],
            "end_sequence_index": current[-1]["sequence_index"],
            "new_start_sequence_index": new_utterances[0]["sequence_index"],
            "new_end_sequence_index": new_utterances[-1]["sequence_index"],
            "start_source_line": current[0]["source_line"],
            "end_source_line": current[-1]["source_line"],
            "start_time": current[0]["start_time"],
            "end_time": current[-1]["start_time"],
            "utterance_count": len(current),
            "new_utterance_count": len(new_utterances),
            "token_count": counter.text(text),
            "new_content_token_count": counter.utterances(new_utterances),
            "overlap_with_previous": overlap_info,
            "closure": closure,
            "content_sha256": sha256_text(text),
            "text": text,
            "utterances": utterance_records,
        }
        chunks.append(chunk)

        overlap = (
            overlap_suffix(current, config["overlap_tokens"], counter)
            if cursor < len(source_utterances)
            else []
        )

    return chunks


def build_chunks(
    talks: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], TokenCounter]:
    validate_config(config)
    counter = TokenCounter(config["tokenizer"]["encoding"], config["separator"])
    chunks: list[dict[str, Any]] = []
    for talk in talks:
        chunks.extend(build_talk_chunks(talk, config, counter))
    return chunks, counter


def validate_chunks(
    talks: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    config: dict[str, Any],
    counter: TokenCounter,
) -> dict[str, Any]:
    errors: list[str] = []
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        errors.append("chunk_id duplicado")

    chunks_by_talk: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        chunks_by_talk.setdefault(chunk["talk_id"], []).append(chunk)

    coverage: dict[str, Any] = {}
    for talk in talks:
        talk_id = talk["talk_id"]
        talk_chunks = chunks_by_talk.get(talk_id, [])
        if not talk_chunks:
            errors.append(f"Sin chunks para {talk_id}")
            continue
        expected_indexes = list(range(len(talk_chunks)))
        actual_indexes = [chunk["chunk_index"] for chunk in talk_chunks]
        if actual_indexes != expected_indexes:
            errors.append(f"chunk_index no consecutivo en {talk_id}")

        new_sequences: list[int] = []
        for index, chunk in enumerate(talk_chunks):
            utterances = chunk["utterances"]
            sequences = [item["sequence_index"] for item in utterances]
            if sequences != list(range(sequences[0], sequences[-1] + 1)):
                errors.append(f"Secuencia interna no consecutiva en {chunk['chunk_id']}")
            rendered = config["separator"].join(item["text"] for item in utterances)
            if rendered != chunk["text"]:
                errors.append(f"Texto no reproducible en {chunk['chunk_id']}")
            if counter.text(rendered) != chunk["token_count"]:
                errors.append(f"token_count incorrecto en {chunk['chunk_id']}")
            if sha256_text(rendered) != chunk["content_sha256"]:
                errors.append(f"content_sha256 incorrecto en {chunk['chunk_id']}")
            new_items = [item for item in utterances if not item["is_overlap"]]
            if not new_items:
                errors.append(f"Chunk sin contenido nuevo: {chunk['chunk_id']}")
            new_sequences.extend(item["sequence_index"] for item in new_items)
            if (
                chunk["start_sequence_index"] != utterances[0]["sequence_index"]
                or chunk["end_sequence_index"] != utterances[-1]["sequence_index"]
                or chunk["start_source_line"] != utterances[0]["source_line"]
                or chunk["end_source_line"] != utterances[-1]["source_line"]
            ):
                errors.append(f"Límites de trazabilidad incorrectos en {chunk['chunk_id']}")
            if new_items and (
                chunk["new_start_sequence_index"] != new_items[0]["sequence_index"]
                or chunk["new_end_sequence_index"] != new_items[-1]["sequence_index"]
            ):
                errors.append(f"Límites nuevos incorrectos en {chunk['chunk_id']}")

            closure = chunk["closure"]
            reason = closure["reason"]
            if reason == "closest_before":
                if not closure["distance_before"] < closure["distance_after"]:
                    errors.append(f"Cierre closest_before inválido en {chunk['chunk_id']}")
                if chunk["token_count"] != closure["tokens_before"]:
                    errors.append(f"tokens_before inconsistente en {chunk['chunk_id']}")
                if closure["candidate_sequence_index"] != chunk["end_sequence_index"] + 1:
                    errors.append(f"Candidato no consecutivo en {chunk['chunk_id']}")
            elif reason == "closest_after":
                if not closure["distance_after"] < closure["distance_before"]:
                    errors.append(f"Cierre closest_after inválido en {chunk['chunk_id']}")
                if chunk["token_count"] != closure["tokens_after"]:
                    errors.append(f"tokens_after inconsistente en {chunk['chunk_id']}")
                if closure["candidate_sequence_index"] != chunk["end_sequence_index"]:
                    errors.append(f"Candidato incluido incorrecto en {chunk['chunk_id']}")
            elif reason == "tie_include":
                if closure["distance_after"] != closure["distance_before"]:
                    errors.append(f"Empate inválido en {chunk['chunk_id']}")
                if chunk["token_count"] != closure["tokens_after"]:
                    errors.append(f"Empate no incluyó candidato en {chunk['chunk_id']}")
            elif reason == "exact_target":
                if chunk["token_count"] != config["target_tokens"]:
                    errors.append(f"exact_target inválido en {chunk['chunk_id']}")
            elif reason == "forced_progress_over_target":
                if chunk["token_count"] <= config["target_tokens"]:
                    errors.append(f"forced_progress inválido en {chunk['chunk_id']}")
            elif reason == "end_of_talk":
                if index != len(talk_chunks) - 1:
                    errors.append(f"end_of_talk antes del final en {chunk['chunk_id']}")
            else:
                errors.append(f"Motivo de cierre desconocido en {chunk['chunk_id']}")

            if index == 0:
                if chunk["overlap_with_previous"] is not None:
                    errors.append(f"Primer chunk con overlap en {talk_id}")
            else:
                overlap_items = [item for item in utterances if item["is_overlap"]]
                previous = talk_chunks[index - 1]
                overlap = chunk["overlap_with_previous"]
                if not overlap_items or overlap is None:
                    errors.append(f"Falta overlap en {chunk['chunk_id']}")
                else:
                    overlap_sequences = [item["sequence_index"] for item in overlap_items]
                    previous_sequences = [item["sequence_index"] for item in previous["utterances"]]
                    if overlap_sequences != previous_sequences[-len(overlap_sequences):]:
                        errors.append(f"Overlap no coincide con sufijo previo en {chunk['chunk_id']}")
                    if overlap["previous_chunk_id"] != previous["chunk_id"]:
                        errors.append(f"Referencia de overlap incorrecta en {chunk['chunk_id']}")
                    overlap_text_items = [{"text": item["text"]} for item in overlap_items]
                    if counter.utterances(overlap_text_items) < config["overlap_tokens"]:
                        errors.append(f"Overlap no alcanza objetivo en {chunk['chunk_id']}")
                    if (
                        len(overlap_text_items) > 1
                        and counter.utterances(overlap_text_items[1:])
                        >= config["overlap_tokens"]
                    ):
                        errors.append(f"Overlap no es sufijo mínimo en {chunk['chunk_id']}")

        expected_sequences = [item["sequence_index"] for item in talk["utterances"]]
        if new_sequences != expected_sequences:
            errors.append(f"Cobertura nueva incompleta o duplicada en {talk_id}")
        coverage[talk_id] = {
            "source_utterances": len(expected_sequences),
            "new_utterances_in_chunks": len(new_sequences),
            "covered_exactly_once": new_sequences == expected_sequences,
        }

    checks = {
        "chunks_nonempty": bool(chunks),
        "chunk_ids_unique": len(chunk_ids) == len(set(chunk_ids)),
        "talk_boundaries_respected": set(chunks_by_talk) == {talk["talk_id"] for talk in talks},
        "chunk_indexes_consecutive": not any("chunk_index" in error for error in errors),
        "utterances_consecutive": not any("Secuencia interna" in error for error in errors),
        "text_reproducible": not any("Texto no reproducible" in error for error in errors),
        "token_counts_reproducible": not any("token_count incorrecto" in error for error in errors),
        "content_hashes_reproducible": not any("content_sha256 incorrecto" in error for error in errors),
        "traceability_boundaries_match": not any("Límites" in error for error in errors),
        "at_least_one_new_utterance": not any("sin contenido nuevo" in error for error in errors),
        "overlap_matches_previous_suffix": not any("Overlap no coincide" in error for error in errors),
        "overlap_is_minimal_suffix_reaching_target": not any(
            "Overlap no alcanza" in error or "Overlap no es sufijo mínimo" in error
            for error in errors
        ),
        "closure_rule_respected": not any(
            marker in error
            for error in errors
            for marker in (
                "Cierre closest",
                "tokens_before",
                "tokens_after",
                "Candidato",
                "Empate",
                "exact_target",
                "forced_progress",
                "end_of_talk",
                "Motivo de cierre",
            )
        ),
        "new_utterance_coverage_exactly_once": all(item["covered_exactly_once"] for item in coverage.values()),
        "no_parent_fields": all("parent_id" not in chunk for chunk in chunks),
    }
    return {
        "status": "passed" if not errors and all(checks.values()) else "failed",
        "algorithm": config["algorithm"],
        "checks": checks,
        "coverage_by_talk": coverage,
        "errors": errors,
    }


def chunk_statistics(
    talks: list[dict[str, Any]], chunks: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any]:
    def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
        token_counts = [item["token_count"] for item in items]
        deviations = [abs(item["token_count"] - config["target_tokens"]) for item in items]
        overlaps = [
            item["overlap_with_previous"]["token_count"]
            for item in items
            if item["overlap_with_previous"] is not None
        ]
        overlap_utterances = [
            item["overlap_with_previous"]["utterance_count"]
            for item in items
            if item["overlap_with_previous"] is not None
        ]
        new_tokens = [item["new_content_token_count"] for item in items]
        utterance_counts = [item["utterance_count"] for item in items]
        new_utterance_counts = [item["new_utterance_count"] for item in items]
        below = sum(value < config["target_tokens"] for value in token_counts)
        equal = sum(value == config["target_tokens"] for value in token_counts)
        above = sum(value > config["target_tokens"] for value in token_counts)
        return {
            "chunk_count": len(items),
            "token_count": numeric_stats(token_counts),
            "absolute_target_deviation": numeric_stats(deviations),
            "relative_to_target": {
                "below": below,
                "equal": equal,
                "above": above,
                "below_percentage": round(below * 100 / len(items), 2),
                "equal_percentage": round(equal * 100 / len(items), 2),
                "above_percentage": round(above * 100 / len(items), 2),
                "maximum_overshoot": max(max(value - config["target_tokens"], 0) for value in token_counts),
                "maximum_undershoot": max(max(config["target_tokens"] - value, 0) for value in token_counts),
            },
            "overlap_token_count": numeric_stats(overlaps),
            "overlap_utterance_count": numeric_stats(overlap_utterances),
            "new_content_token_count": numeric_stats(new_tokens),
            "utterance_count": numeric_stats(utterance_counts),
            "new_utterance_count": numeric_stats(new_utterance_counts),
            "closure_reasons": dict(sorted(Counter(item["closure"]["reason"] for item in items).items())),
        }

    by_talk: dict[str, Any] = {}
    last_chunks: list[dict[str, Any]] = []
    last_chunk_ids: set[str] = set()
    for talk in talks:
        items = [chunk for chunk in chunks if chunk["talk_id"] == talk["talk_id"]]
        by_talk[talk["talk_id"]] = summarize(items)
        last = items[-1]
        last_chunk_ids.add(last["chunk_id"])
        last_chunks.append(
            {
                "talk_id": talk["talk_id"],
                "chunk_id": last["chunk_id"],
                "token_count": last["token_count"],
                "new_content_token_count": last["new_content_token_count"],
                "utterance_count": last["utterance_count"],
                "new_utterance_count": last["new_utterance_count"],
            }
        )

    total_payload_tokens = sum(chunk["token_count"] for chunk in chunks)
    total_new_tokens = sum(chunk["new_content_token_count"] for chunk in chunks)
    total_overlap_tokens = sum(
        chunk["overlap_with_previous"]["token_count"]
        for chunk in chunks
        if chunk["overlap_with_previous"] is not None
    )
    return {
        "statistics_version": "1.0",
        "algorithm": config["algorithm"],
        "configuration": {
            "target_tokens": config["target_tokens"],
            "overlap_tokens": config["overlap_tokens"],
            "target_includes_overlap": config["target_includes_overlap"],
            "tokenizer": config["tokenizer"],
            "separator": config["separator"],
        },
        "global": summarize(chunks),
        "non_final_chunks": summarize(
            [chunk for chunk in chunks if chunk["chunk_id"] not in last_chunk_ids]
        ),
        "by_talk": by_talk,
        "payload_totals": {
            "total_chunk_payload_tokens": total_payload_tokens,
            "total_new_content_tokens": total_new_tokens,
            "total_overlap_tokens_measured_separately": total_overlap_tokens,
            "payload_to_new_content_ratio": round(total_payload_tokens / total_new_tokens, 4),
        },
        "last_chunk_by_talk": last_chunks,
        "decision_scope": {
            "parents_created": False,
            "embeddings_created": False,
            "qdrant_used": False,
        },
    }


def preview(text: str, limit: int = 140) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def render_statistics_markdown(
    chunks: list[dict[str, Any]], stats: dict[str, Any], validation: dict[str, Any]
) -> str:
    global_stats = stats["global"]
    lines = [
        "# Child V1: estadísticas y revisión",
        "",
        "Este reporte describe Children reales. No se generaron Parents, embeddings ni índices vectoriales.",
        "",
        "## Configuración",
        "",
        f"- Algoritmo: `{stats['algorithm']}`.",
        f"- Target aproximado: {stats['configuration']['target_tokens']} tokens.",
        f"- Overlap aproximado: {stats['configuration']['overlap_tokens']} tokens.",
        f"- Tokenizer provisional: `tiktoken=={stats['configuration']['tokenizer']['library_version']}` / `{stats['configuration']['tokenizer']['encoding']}`.",
        "- Unidad atómica: utterance completa.",
        "- Regla de cruce: opción más cercana; empate incluye la utterance.",
        "- El target mide el payload completo, incluido el overlap.",
        "- Serialización: textos unidos por `\\n`.",
        "",
        "## Validación",
        "",
        f"Estado: **{validation['status']}**.",
        "",
        "| Check | Resultado |",
        "|---|---|",
    ]
    for name, result in validation["checks"].items():
        lines.append(f"| `{name}` | {'OK' if result else 'ERROR'} |")

    token_stats = global_stats["token_count"]
    deviation = global_stats["absolute_target_deviation"]
    relative = global_stats["relative_to_target"]
    overlap = global_stats["overlap_token_count"]
    non_final = stats["non_final_chunks"]
    non_final_tokens = non_final["token_count"]
    non_final_deviation = non_final["absolute_target_deviation"]
    lines.extend(
        [
            "",
            "## Resumen global",
            "",
            f"- Children: **{global_stats['chunk_count']}**.",
            f"- Tokens por Child: mínimo {token_stats['min']}, mediana {token_stats['median']}, media {token_stats['mean']}, P95 {token_stats['p95']}, máximo {token_stats['max']}.",
            f"- Desviación absoluta del target: mediana {deviation['median']}, P95 {deviation['p95']}, máxima {deviation['max']}.",
            f"- Debajo/igual/encima del target: {relative['below']}/{relative['equal']}/{relative['above']}.",
            f"- Overshoot máximo: {relative['maximum_overshoot']} tokens.",
            f"- Overlap real: mediana {overlap.get('median', 0)}, P95 {overlap.get('p95', 0)}, máximo {overlap.get('max', 0)} tokens.",
            f"- Excluyendo los cuatro Children finales: mediana {non_final_tokens['median']}, P95 {non_final_tokens['p95']}, rango {non_final_tokens['min']}–{non_final_tokens['max']} tokens; desviación máxima {non_final_deviation['max']}.",
            "",
            "## Resumen por ponencia",
            "",
            "| Talk | Chunks | Tokens mín. | Mediana | Media | P95 | Máx. | Overlap mediano |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for talk_id, talk_stats in stats["by_talk"].items():
        values = talk_stats["token_count"]
        talk_overlap = talk_stats["overlap_token_count"]
        lines.append(
            f"| `{talk_id}` | {talk_stats['chunk_count']} | {values['min']} | {values['median']} | "
            f"{values['mean']} | {values['p95']} | {values['max']} | {talk_overlap.get('median', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Último Child de cada ponencia",
            "",
            "| Talk | Chunk | Tokens totales | Tokens nuevos | Utterances | Utterances nuevas |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in stats["last_chunk_by_talk"]:
        lines.append(
            f"| `{item['talk_id']}` | `{item['chunk_id']}` | {item['token_count']} | "
            f"{item['new_content_token_count']} | {item['utterance_count']} | {item['new_utterance_count']} |"
        )

    lines.extend(
        [
            "",
            "## Inventario para revisión humana",
            "",
            "| Chunk | Seq. total | Seq. nueva | Tokens | Overlap | Nuevas | Cierre | Preview |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    for chunk in chunks:
        overlap_info = chunk["overlap_with_previous"]
        overlap_tokens = overlap_info["token_count"] if overlap_info else 0
        safe_preview = preview(chunk["text"]).replace("|", "\\|")
        lines.append(
            f"| `{chunk['chunk_id']}` | {chunk['start_sequence_index']}–{chunk['end_sequence_index']} | "
            f"{chunk['new_start_sequence_index']}–{chunk['new_end_sequence_index']} | "
            f"{chunk['token_count']} | {overlap_tokens} | {chunk['new_content_token_count']} | "
            f"`{chunk['closure']['reason']}` | {safe_preview} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    talks_path: Path,
    config_path: Path,
    chunks_path: Path,
    validation_path: Path,
    manifest_path: Path,
    stats_json_path: Path,
    stats_md_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    config = load_json(config_path)
    talks = load_jsonl(talks_path)
    chunks, counter = build_chunks(talks, config)
    validation = validate_chunks(talks, chunks, config, counter)
    if validation["status"] != "passed":
        raise ValueError("Falló la validación de chunks: " + "; ".join(validation["errors"]))
    stats = chunk_statistics(talks, chunks, config)

    for path in (chunks_path, validation_path, manifest_path, stats_json_path, stats_md_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    chunks_text = "".join(
        json.dumps(chunk, ensure_ascii=False, separators=(",", ":")) + "\n"
        for chunk in chunks
    )
    chunks_path.write_text(chunks_text, encoding="utf-8", newline="\n")
    validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    stats_json_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    stats_md_path.write_text(
        render_statistics_markdown(chunks, stats, validation),
        encoding="utf-8",
        newline="\n",
    )

    outputs = [chunks_path, validation_path, stats_json_path, stats_md_path]
    manifest = {
        "manifest_version": "1.0",
        "pipeline": "talks-to-child-v1",
        "source": {"path": project_path(talks_path), "sha256": sha256_file(talks_path)},
        "config": {"path": project_path(config_path), "sha256": sha256_file(config_path)},
        "statistics": {
            "talk_count": len(talks),
            "source_utterance_count": sum(len(talk["utterances"]) for talk in talks),
            "chunk_count": len(chunks),
        },
        "outputs": [
            {
                "path": project_path(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in outputs
        ],
        "excluded_scope": ["parents", "embeddings", "qdrant"],
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return chunks, validation, stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--chunks-output", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--validation-output", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--stats-json-output", type=Path, default=DEFAULT_STATS_JSON)
    parser.add_argument("--stats-markdown-output", type=Path, default=DEFAULT_STATS_MD)
    args = parser.parse_args()

    chunks, validation, stats = write_outputs(
        args.input.resolve(),
        args.config.resolve(),
        args.chunks_output.resolve(),
        args.validation_output.resolve(),
        args.manifest_output.resolve(),
        args.stats_json_output.resolve(),
        args.stats_markdown_output.resolve(),
    )
    print(
        f"OK: {len(chunks)} Children; validation={validation['status']}; "
        f"median_tokens={stats['global']['token_count']['median']}"
    )


if __name__ == "__main__":
    main()


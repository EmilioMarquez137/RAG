#!/usr/bin/env python3
"""Analyze utterance token lengths without creating retrieval chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable

import tiktoken


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "talks.jsonl"
DEFAULT_JSON = ROOT / "data" / "analysis" / "utterance_length_analysis.json"
DEFAULT_MARKDOWN = ROOT / "data" / "analysis" / "utterance_length_analysis.md"
ENCODING_NAME = "cl100k_base"
THRESHOLDS = (250, 500, 750, 1000)
PERCENTILES = (0.25, 0.75, 0.90, 0.95, 0.99)
PERCENTILE_NAMES = {
    0.25: "p25_tokens",
    0.75: "p75_tokens",
    0.90: "p90_tokens",
    0.95: "p95_tokens",
    0.99: "p99_tokens",
}
BINS = (
    (0, 0, "0"),
    (1, 5, "1-5"),
    (6, 10, "6-10"),
    (11, 20, "11-20"),
    (21, 40, "21-40"),
    (41, 80, "41-80"),
    (81, 120, "81-120"),
    (121, 160, "121-160"),
    (161, 250, "161-250"),
    (251, None, "251+"),
)


def percentile(values: Iterable[int], probability: float) -> float:
    """Hyndman-Fan type 7 percentile (the default used by NumPy/R)."""
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


def distribution(values: list[int]) -> list[dict[str, Any]]:
    total = len(values)
    result = []
    for lower, upper, label in BINS:
        count = sum(
            1
            for value in values
            if value >= lower and (upper is None or value <= upper)
        )
        result.append(
            {
                "range": label,
                "min_inclusive": lower,
                "max_inclusive": upper,
                "count": count,
                "percentage": round(count * 100 / total, 2),
            }
        )
    return result


def descriptive_stats(values: list[int]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "utterance_count": len(values),
        "total_tokens": sum(values),
        "min_tokens": min(values),
        "max_tokens": max(values),
        "mean_tokens": round(statistics.mean(values), 2),
        "median_tokens": rounded(statistics.median(values)),
    }
    for probability in PERCENTILES:
        result[PERCENTILE_NAMES[probability]] = rounded(
            percentile(values, probability)
        )
    result["distribution"] = distribution(values)
    return result


def metric_stats(values: list[int], suffix: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        f"min_{suffix}": min(values),
        f"max_{suffix}": max(values),
        f"mean_{suffix}": round(statistics.mean(values), 2),
        f"median_{suffix}": rounded(statistics.median(values)),
    }
    for probability in PERCENTILES:
        key = PERCENTILE_NAMES[probability].replace("tokens", suffix)
        result[key] = rounded(percentile(values, probability))
    return result


def windows_to_threshold(
    token_counts: list[int], threshold: int
) -> dict[str, Any]:
    utterance_counts: list[int] = []
    achieved_tokens: list[int] = []
    for start in range(len(token_counts)):
        total = 0
        for end in range(start, len(token_counts)):
            total += token_counts[end]
            if total >= threshold:
                utterance_counts.append(end - start + 1)
                achieved_tokens.append(total)
                break

    result: dict[str, Any] = {
        "threshold_tokens": threshold,
        "possible_start_positions": len(token_counts),
        "windows_reaching_threshold": len(utterance_counts),
        "tail_starts_not_reaching_threshold": len(token_counts)
        - len(utterance_counts),
    }
    if utterance_counts:
        result["utterance_count_stats"] = metric_stats(
            utterance_counts, "utterances"
        )
        result["achieved_token_stats"] = metric_stats(
            achieved_tokens, "tokens"
        )
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def load_talks(path: Path) -> list[dict[str, Any]]:
    talks = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not talks:
        raise ValueError(f"No hay ponencias en {path}")
    return talks


def analyze(path: Path) -> dict[str, Any]:
    talks = load_talks(path)
    encoding = tiktoken.get_encoding(ENCODING_NAME)
    all_items: list[dict[str, Any]] = []
    by_talk_items: dict[str, list[dict[str, Any]]] = {}

    for talk in talks:
        talk_items = []
        for utterance in talk["utterances"]:
            item = {
                "talk_id": talk["talk_id"],
                "sequence_index": utterance["sequence_index"],
                "source_line": utterance["source_line"],
                "token_count": len(encoding.encode(utterance["text"])),
                "text": utterance["text"],
            }
            talk_items.append(item)
            all_items.append(item)
        by_talk_items[talk["talk_id"]] = talk_items

    all_counts = [item["token_count"] for item in all_items]
    p25 = percentile(all_counts, 0.25)
    p75 = percentile(all_counts, 0.75)
    outer_fence = p75 + 3 * (p75 - p25)
    extreme_items = [
        {
            "talk_id": item["talk_id"],
            "sequence_index": item["sequence_index"],
            "source_line": item["source_line"],
            "token_count": item["token_count"],
            "preview": preview(item["text"]),
        }
        for item in sorted(
            all_items,
            key=lambda item: (-item["token_count"], item["talk_id"], item["sequence_index"]),
        )
        if item["token_count"] > outer_fence
    ]

    global_windows: dict[str, Any] = {}
    by_talk_windows: dict[str, dict[str, Any]] = {}
    for threshold in THRESHOLDS:
        aggregate_counts: list[int] = []
        aggregate_tokens: list[int] = []
        possible = 0
        reached = 0
        for talk_id, items in by_talk_items.items():
            result = windows_to_threshold(
                [item["token_count"] for item in items], threshold
            )
            by_talk_windows.setdefault(talk_id, {})[str(threshold)] = result
            possible += result["possible_start_positions"]
            reached += result["windows_reaching_threshold"]

            counts = [item["token_count"] for item in items]
            for start in range(len(counts)):
                total = 0
                for end in range(start, len(counts)):
                    total += counts[end]
                    if total >= threshold:
                        aggregate_counts.append(end - start + 1)
                        aggregate_tokens.append(total)
                        break

        global_windows[str(threshold)] = {
            "threshold_tokens": threshold,
            "possible_start_positions": possible,
            "windows_reaching_threshold": reached,
            "tail_starts_not_reaching_threshold": possible - reached,
            "utterance_count_stats": metric_stats(
                aggregate_counts, "utterances"
            ),
            "achieved_token_stats": metric_stats(aggregate_tokens, "tokens"),
        }

    return {
        "analysis_version": "1.0",
        "source": {
            "path": path.resolve().relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "talk_count": len(talks),
            "utterance_count": len(all_items),
        },
        "tokenizer": {
            "library": "tiktoken",
            "library_version": version("tiktoken"),
            "encoding": ENCODING_NAME,
            "definitive_for_embedding_model": False,
            "input_counted": "utterance.text only; timestamps, metadata and separators excluded",
        },
        "methodology": {
            "percentiles": "Hyndman-Fan type 7 linear interpolation",
            "distribution_bins": [item[2] for item in BINS],
            "extremely_long_definition": "token_count > global P75 + 3 * IQR (Tukey outer fence)",
            "consecutive_windows": (
                "For every possible start within each talk, accumulate canonical consecutive "
                "utterances until the threshold is first reached. Incomplete tail starts are "
                "reported and excluded from window percentiles. Counts sum utterance text tokens "
                "and do not add separator tokens. Windows never cross talk boundaries."
            ),
            "canonical_order": "sequence_index/source_line from talks.jsonl",
        },
        "utterance_lengths": {
            "global": descriptive_stats(all_counts),
            "by_talk": {
                talk_id: descriptive_stats(
                    [item["token_count"] for item in items]
                )
                for talk_id, items in by_talk_items.items()
            },
        },
        "extremely_long_utterances": {
            "outer_fence_tokens": rounded(outer_fence),
            "count": len(extreme_items),
            "items": extreme_items,
        },
        "consecutive_utterances_to_threshold": {
            "thresholds_analyzed": list(THRESHOLDS),
            "global": global_windows,
            "by_talk": by_talk_windows,
        },
        "decision_status": {
            "target_tokens_selected": False,
            "overlap_tokens_selected": False,
        },
    }


def format_number(value: Any) -> str:
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def stats_row(name: str, stats: dict[str, Any]) -> str:
    fields = (
        "utterance_count",
        "min_tokens",
        "max_tokens",
        "mean_tokens",
        "median_tokens",
        "p25_tokens",
        "p75_tokens",
        "p90_tokens",
        "p95_tokens",
        "p99_tokens",
    )
    return "| " + name + " | " + " | ".join(format_number(stats[key]) for key in fields) + " |"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Análisis exploratorio de longitud de utterances",
        "",
        "Este artefacto analiza la fuente canónica sin generar chunks, parents, embeddings ni índices.",
        "No selecciona `target_tokens` ni `overlap_tokens`.",
        "",
        "## Tokenizer y metodología",
        "",
        f"- Biblioteca: `tiktoken=={report['tokenizer']['library_version']}`.",
        f"- Encoding exploratorio: `{report['tokenizer']['encoding']}`.",
        "- El encoding no se considera todavía el tokenizer definitivo del modelo de embeddings.",
        "- Se tokeniza únicamente `utterance.text`; no se cuentan timestamps, metadata ni separadores.",
        "- Percentiles: Hyndman-Fan tipo 7 con interpolación lineal.",
        "- Una utterance extremadamente larga supera `P75 + 3×IQR` global.",
        "- Las ventanas consecutivas parten de cada utterance, no cruzan ponencias y se detienen al alcanzar por primera vez cada umbral.",
        "- Los inicios al final de una ponencia que no alcanzan el umbral se reportan, pero no entran en los percentiles.",
        "",
        "## Estadísticas de longitud",
        "",
        "| Ámbito | N | Mín. | Máx. | Media | Mediana | P25 | P75 | P90 | P95 | P99 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        stats_row("Global", report["utterance_lengths"]["global"]),
    ]
    for talk_id, stats in report["utterance_lengths"]["by_talk"].items():
        lines.append(stats_row(f"`{talk_id}`", stats))

    lines.extend(["", "## Distribución global", "", "| Tokens | Utterances | Porcentaje |", "|---:|---:|---:|"])
    for bucket in report["utterance_lengths"]["global"]["distribution"]:
        lines.append(
            f"| {bucket['range']} | {bucket['count']} | {bucket['percentage']:.2f}% |"
        )

    lines.extend(["", "### Distribución por ponencia", ""])
    for talk_id, stats in report["utterance_lengths"]["by_talk"].items():
        lines.extend(
            [
                f"#### `{talk_id}`",
                "",
                "| Tokens | Utterances | Porcentaje |",
                "|---:|---:|---:|",
            ]
        )
        for bucket in stats["distribution"]:
            lines.append(
                f"| {bucket['range']} | {bucket['count']} | {bucket['percentage']:.2f}% |"
            )
        lines.append("")

    extreme = report["extremely_long_utterances"]
    lines.extend(
        [
            "## Utterances extremadamente largas",
            "",
            f"Criterio: más de **{extreme['outer_fence_tokens']} tokens** (`P75 + 3×IQR`). ",
            f"Se identificaron **{extreme['count']}**.",
            "",
            "| Talk | Seq. | Línea | Tokens | Preview |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in extreme["items"]:
        safe_preview = item["preview"].replace("|", "\\|")
        lines.append(
            f"| `{item['talk_id']}` | {item['sequence_index']} | {item['source_line']} | "
            f"{item['token_count']} | {safe_preview} |"
        )

    lines.extend(
        [
            "",
            "## Utterances consecutivas para alcanzar cada umbral",
            "",
            "Los valores son conteos de utterances, no tamaños de chunks elegidos.",
            "",
            "### Global",
            "",
            "| Umbral | Ventanas | Colas incompletas | Mín. | Mediana | P25 | P75 | P90 | P95 | P99 | Máx. |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for threshold, result in report["consecutive_utterances_to_threshold"]["global"].items():
        stats = result["utterance_count_stats"]
        lines.append(
            f"| {threshold} | {result['windows_reaching_threshold']} | "
            f"{result['tail_starts_not_reaching_threshold']} | {stats['min_utterances']} | "
            f"{stats['median_utterances']} | {stats['p25_utterances']} | "
            f"{stats['p75_utterances']} | {stats['p90_utterances']} | "
            f"{stats['p95_utterances']} | {stats['p99_utterances']} | "
            f"{stats['max_utterances']} |"
        )

    lines.extend(
        [
            "",
            "### Por ponencia",
            "",
            "| Talk | Umbral | Ventanas | Colas incompletas | Mediana | P25 | P75 | P90 | P95 | P99 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for talk_id, thresholds in report["consecutive_utterances_to_threshold"]["by_talk"].items():
        for threshold, result in thresholds.items():
            stats = result["utterance_count_stats"]
            lines.append(
                f"| `{talk_id}` | {threshold} | {result['windows_reaching_threshold']} | "
                f"{result['tail_starts_not_reaching_threshold']} | {stats['median_utterances']} | "
                f"{stats['p25_utterances']} | {stats['p75_utterances']} | "
                f"{stats['p90_utterances']} | {stats['p95_utterances']} | "
                f"{stats['p99_utterances']} |"
            )

    global_stats = report["utterance_lengths"]["global"]
    lines.extend(
        [
            "",
            "## Observaciones",
            "",
            f"- La utterance mediana tiene {global_stats['median_tokens']} tokens; P75 es "
            f"{global_stats['p75_tokens']} y P95 es {global_stats['p95_tokens']}.",
            f"- El máximo observado es {global_stats['max_tokens']} tokens.",
            f"- {extreme['count']} utterances superan la cerca exterior estadística de "
            f"{extreme['outer_fence_tokens']} tokens; se reportan sin modificarlas.",
            "- La cantidad de utterances necesaria varía por ponencia y por punto de inicio; el JSON conserva el detalle completo.",
            "- Estos resultados son insumos para una decisión manual posterior. No constituyen una elección de tamaño ni overlap.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()

    report = analyze(args.input.resolve())
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    args.markdown_output.write_text(
        render_markdown(report), encoding="utf-8", newline="\n"
    )
    print(
        f"OK: {report['source']['utterance_count']} utterances analizadas con "
        f"{report['tokenizer']['encoding']}"
    )


if __name__ == "__main__":
    main()


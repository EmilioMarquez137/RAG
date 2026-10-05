#!/usr/bin/env python3
"""Compare Child V1 token counts with the official GTE tokenizer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "Alibaba-NLP/gte-multilingual-base"
DEFAULT_INPUT = ROOT / "data" / "processed" / "chunks.jsonl"
DEFAULT_JSON = ROOT / "data" / "analysis" / "gte_tokenizer_analysis.json"
DEFAULT_MARKDOWN = ROOT / "data" / "analysis" / "gte_tokenizer_analysis.md"
PERCENTILES = (0.75, 0.90, 0.95, 0.99)
BINS = (
    (0, 255, "0-255"),
    (256, 383, "256-383"),
    (384, 511, "384-511"),
    (512, 639, "512-639"),
    (640, 767, "640-767"),
    (768, 1023, "768-1023"),
    (1024, None, "1024+"),
)


def percentile(values: Iterable[float], probability: float) -> float:
    """Return a Hyndman-Fan type 7 percentile."""
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
    result = round(value, 4)
    return int(result) if result.is_integer() else result


def descriptive(values: list[int]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "count": len(values),
        "min": min(values),
        "mean": round(statistics.mean(values), 2),
        "median": rounded(statistics.median(values)),
    }
    for probability in PERCENTILES:
        result[f"p{int(probability * 100)}"] = rounded(
            percentile(values, probability)
        )
    result["max"] = max(values)
    return result


def ratio_stats(values: list[float]) -> dict[str, Any]:
    return {
        "min": round(min(values), 4),
        "mean": round(statistics.mean(values), 4),
        "median": round(statistics.median(values), 4),
        "p75": round(percentile(values, 0.75), 4),
        "p90": round(percentile(values, 0.90), 4),
        "p95": round(percentile(values, 0.95), 4),
        "p99": round(percentile(values, 0.99), 4),
        "max": round(max(values), 4),
    }


def distribution(values: list[int]) -> list[dict[str, Any]]:
    total = len(values)
    result = []
    for lower, upper, label in BINS:
        count = sum(
            value >= lower and (upper is None or value <= upper)
            for value in values
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def load_chunks(path: Path) -> list[dict[str, Any]]:
    chunks = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not chunks:
        raise ValueError(f"No hay Children en {path}")
    required = {"chunk_id", "talk_id", "token_count", "text"}
    for index, chunk in enumerate(chunks, start=1):
        missing = required - chunk.keys()
        if missing:
            raise ValueError(f"Línea {index}: faltan campos {sorted(missing)}")
        if not isinstance(chunk["text"], str):
            raise TypeError(f"Línea {index}: text no es string")
        if chunk["token_count"] <= 0:
            raise ValueError(f"Línea {index}: token_count debe ser positivo")
    return chunks


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    gte = [item["gte_tokens"] for item in items]
    cl100k = [item["cl100k_tokens"] for item in items]
    ratios = [item["ratio"] for item in items]
    differences = [item["difference_tokens"] for item in items]
    return {
        "chunk_count": len(items),
        "gte_token_count": descriptive(gte),
        "cl100k_token_count": descriptive(cl100k),
        "totals": {
            "gte_tokens": sum(gte),
            "cl100k_tokens": sum(cl100k),
            "difference_tokens": sum(gte) - sum(cl100k),
        },
        "aggregate_ratio_gte_over_cl100k": round(sum(gte) / sum(cl100k), 4),
        "per_child_ratio_gte_over_cl100k": ratio_stats(ratios),
        "difference_gte_minus_cl100k": {
            **descriptive(differences),
            "gte_greater": sum(value > 0 for value in differences),
            "equal": sum(value == 0 for value in differences),
            "gte_lower": sum(value < 0 for value in differences),
        },
        "gte_distribution": distribution(gte),
    }


def analyze(
    path: Path, revision: str, *, local_files_only: bool = False
) -> dict[str, Any]:
    chunks = load_chunks(path)
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        revision=revision,
        trust_remote_code=False,
        use_fast=True,
        local_files_only=local_files_only,
    )
    config_path = hf_hub_download(
        MODEL_ID,
        "config.json",
        revision=revision,
        local_files_only=local_files_only,
    )
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    # hf_hub_download returns .../snapshots/<commit>/config.json. Do not call
    # resolve() here: on Windows it follows the cache link into blobs and loses
    # the snapshot commit identifier.
    resolved_revision = Path(config_path).parent.name
    tokenizer_max_length = int(tokenizer.model_max_length)
    config_max_positions = int(config["max_position_embeddings"])
    effective_context = min(tokenizer_max_length, config_max_positions)

    items: list[dict[str, Any]] = []
    by_talk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        input_ids = tokenizer(
            chunk["text"],
            add_special_tokens=True,
            truncation=False,
            return_attention_mask=False,
            return_token_type_ids=False,
        )["input_ids"]
        without_special = tokenizer(
            chunk["text"],
            add_special_tokens=False,
            truncation=False,
            return_attention_mask=False,
            return_token_type_ids=False,
        )["input_ids"]
        cl100k_tokens = int(chunk["token_count"])
        gte_tokens = len(input_ids)
        item = {
            "chunk_id": chunk["chunk_id"],
            "talk_id": chunk["talk_id"],
            "chunk_index": chunk.get("chunk_index"),
            "start_sequence_index": chunk.get("start_sequence_index"),
            "end_sequence_index": chunk.get("end_sequence_index"),
            "cl100k_tokens": cl100k_tokens,
            "gte_tokens": gte_tokens,
            "gte_tokens_without_special_tokens": len(without_special),
            "special_tokens_added": gte_tokens - len(without_special),
            "difference_tokens": gte_tokens - cl100k_tokens,
            "ratio": round(gte_tokens / cl100k_tokens, 6),
            "exceeds_model_context": gte_tokens > effective_context,
            "preview": preview(chunk["text"]),
        }
        items.append(item)
        by_talk[chunk["talk_id"]].append(item)

    global_summary = summarize(items)
    longest = max(items, key=lambda item: item["gte_tokens"])
    over_context = [item for item in items if item["exceeds_model_context"]]
    auto_map = config.get("auto_map")
    return {
        "analysis_version": "1.0",
        "source": {
            "path": path.resolve().relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "chunk_count": len(chunks),
            "canonical_input_modified": False,
            "payload_tokenized": "chunk.text exactly as stored; no prefix or metadata added",
        },
        "tokenizer": {
            "model_id": MODEL_ID,
            "requested_revision": revision,
            "resolved_revision": resolved_revision,
            "class": type(tokenizer).__name__,
            "class_module": type(tokenizer).__module__,
            "is_fast": tokenizer.is_fast,
            "vocabulary_size": tokenizer.vocab_size,
            "tokenizer_model_max_length": tokenizer_max_length,
            "config_max_position_embeddings": config_max_positions,
            "effective_context_tokens": effective_context,
            "effective_context_basis": (
                "Conservative minimum of tokenizer.model_max_length and the model "
                "config max_position_embeddings. The official model card also states 8192."
            ),
            "context_metadata_mismatch": tokenizer_max_length != config_max_positions,
            "add_special_tokens": True,
            "truncation": False,
            "padding": False,
            "special_tokens_per_child": sorted(
                {item["special_tokens_added"] for item in items}
            ),
            "trust_remote_code": False,
            "remote_code_executed": False,
            "remote_code_note": (
                "AutoTokenizer loads the standard XLM-R tokenizer implementation from "
                "transformers and does not require repository Python code. The repository's "
                "custom AutoModel mapping is relevant when loading the embedding model, not "
                "for this tokenizer-only analysis."
            ),
            "model_auto_map": auto_map,
            "libraries": {
                "transformers": version("transformers"),
                "tokenizers": version("tokenizers"),
                "sentencepiece": version("sentencepiece"),
                "huggingface_hub": version("huggingface-hub"),
            },
        },
        "methodology": {
            "percentiles": "Hyndman-Fan type 7 linear interpolation",
            "primary_gte_count": (
                "Length of input_ids for the exact Child text with model special tokens; "
                "no truncation and no padding."
            ),
            "cl100k_comparison": (
                "Existing chunks.jsonl token_count generated by Child V1 with cl100k_base. "
                "It is read unchanged and is not recalculated here."
            ),
            "aggregate_ratio": "sum(gte_tokens) / sum(cl100k_tokens)",
            "per_child_ratio": "gte_tokens / cl100k_tokens for each Child",
        },
        "global": global_summary,
        "by_talk": {
            talk_id: summarize(talk_items)
            for talk_id, talk_items in sorted(by_talk.items())
        },
        "context_risk": {
            "maximum_context_tokens": effective_context,
            "children_exceeding_context": len(over_context),
            "percentage_exceeding_context": round(
                len(over_context) * 100 / len(items), 4
            ),
            "largest_child_context_usage_percentage": round(
                longest["gte_tokens"] * 100 / effective_context, 4
            ),
            "largest_child": longest,
            "exceeding_children": over_context,
        },
        "children": items,
    }


def fmt(value: Any) -> str:
    return f"{value:.4f}" if isinstance(value, float) else str(value)


def render_markdown(report: dict[str, Any]) -> str:
    tokenizer = report["tokenizer"]
    global_stats = report["global"]
    gte = global_stats["gte_token_count"]
    risk = report["context_risk"]
    longest = risk["largest_child"]
    lines = [
        "# Validación del tokenizer de GTE sobre Child V1",
        "",
        "Este análisis no modifica `chunks.jsonl` ni genera embeddings, Parents o índices.",
        "",
        "## Tokenizer y método",
        "",
        f"- Modelo: `{tokenizer['model_id']}`.",
        f"- Revisión resuelta: `{tokenizer['resolved_revision']}`.",
        f"- Implementación: `{tokenizer['class']}` (`{tokenizer['class_module']}`).",
        f"- `tokenizer.model_max_length`: {tokenizer['tokenizer_model_max_length']} tokens.",
        f"- `config.max_position_embeddings`: {tokenizer['config_max_position_embeddings']} tokens.",
        f"- Contexto efectivo conservador usado: {tokenizer['effective_context_tokens']} tokens.",
        "- Existe una discrepancia de metadata entre tokenizer y modelo; para seguridad prevalece el límite del modelo.",
        "- Se tokeniza exactamente `Child.text`, sin prefijos ni metadata.",
        "- Conteo principal: `input_ids` con tokens especiales del modelo, sin padding y sin truncación.",
        "- `trust_remote_code=False`: el tokenizer usa la implementación estándar XLM-R de `transformers`.",
        "- El código personalizado del repositorio aplica al cargar `AutoModel`; no se ejecutó en este análisis.",
        "",
        "## Resultado global",
        "",
        "| Children | Mín. | Media | Mediana | P75 | P90 | P95 | P99 | Máx. |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| " + " | ".join(
            fmt(value)
            for value in (
                gte["count"], gte["min"], gte["mean"], gte["median"],
                gte["p75"], gte["p90"], gte["p95"], gte["p99"], gte["max"],
            )
        ) + " |",
        "",
        "## Comparación con `cl100k_base`",
        "",
        f"- Tokens GTE totales: **{global_stats['totals']['gte_tokens']}**.",
        f"- Tokens `cl100k_base` totales: **{global_stats['totals']['cl100k_tokens']}**.",
        f"- Ratio agregado `GTE / cl100k`: **{global_stats['aggregate_ratio_gte_over_cl100k']:.4f}**.",
        f"- Ratio mediano por Child: **{global_stats['per_child_ratio_gte_over_cl100k']['median']:.4f}**.",
        "",
        "## Distribución por ponencia",
        "",
        "| Ponencia | Children | Mín. | Media | Mediana | P75 | P90 | P95 | P99 | Máx. | Ratio agregado |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for talk_id, stats in report["by_talk"].items():
        talk_gte = stats["gte_token_count"]
        lines.append(
            f"| `{talk_id}` | {talk_gte['count']} | {talk_gte['min']} | "
            f"{talk_gte['mean']:.2f} | {talk_gte['median']} | {talk_gte['p75']} | "
            f"{talk_gte['p90']} | {talk_gte['p95']} | {talk_gte['p99']} | "
            f"{talk_gte['max']} | {stats['aggregate_ratio_gte_over_cl100k']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Uso del contexto",
            "",
            f"- Children que superarían el contexto: **{risk['children_exceeding_context']} "
            f"de {report['source']['chunk_count']} ({risk['percentage_exceeding_context']:.4f}%)**.",
            f"- El Child más largo utiliza aproximadamente **{risk['largest_child_context_usage_percentage']:.2f}%** "
            "del contexto máximo.",
            f"- Child más largo: `{longest['chunk_id']}` de `{longest['talk_id']}`, con "
            f"**{longest['gte_tokens']} tokens GTE** frente a {longest['cl100k_tokens']} tokens `cl100k_base`.",
            f"- Preview: {longest['preview']}",
            "",
            "## Distribución global por rangos",
            "",
            "| Tokens GTE | Children | Porcentaje |",
            "|---:|---:|---:|",
        ]
    )
    for bucket in global_stats["gte_distribution"]:
        lines.append(
            f"| {bucket['range']} | {bucket['count']} | {bucket['percentage']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Conclusión automática",
            "",
            "- No existe riesgo de truncación si ningún Child supera el contexto declarado.",
            "- Las diferencias frente a `cl100k_base` son esperables porque se trata de vocabularios, "
            "segmentación y tokens especiales distintos.",
            "- Los límites de Child V1 permanecen congelados; este análisis no propone resegmentación.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--revision", default="main")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    report = analyze(
        args.input.resolve(),
        args.revision,
        local_files_only=args.local_files_only,
    )
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
        f"OK: {report['source']['chunk_count']} Children analizados; "
        f"máximo={report['global']['gte_token_count']['max']} tokens GTE; "
        f"exceden contexto={report['context_risk']['children_exceeding_context']}"
    )


if __name__ == "__main__":
    main()

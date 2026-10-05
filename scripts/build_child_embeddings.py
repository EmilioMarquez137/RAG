#!/usr/bin/env python3
"""Build and validate the pinned GTE dense embeddings for Child V1."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from gte_embedding_common import (
    DEFAULT_CHUNKS,
    DEFAULT_CONFIG,
    DEFAULT_EMBEDDINGS,
    DEFAULT_MANIFEST,
    DEFAULT_VALIDATION_JSON,
    DEFAULT_VALIDATION_MD,
    ROOT,
    encode_texts,
    load_chunks,
    load_embedding_artifact,
    load_embedding_config,
    load_gte_model,
    package_version,
    save_embedding_artifact,
    search_results,
    sha256,
    validate_embeddings,
)


SMOKE_QUERIES = (
    "¿Cuál es el origen y la historia de Grupo Salinas?",
    "¿Qué significa la batalla cultural y por qué es importante?",
    "¿Qué retos plantea la inteligencia artificial para el liderazgo empresarial?",
    "¿Cómo puede Claude ayudar a trabajar con documentos y presentaciones?",
)

REMOTE_CODE_FILES = {
    "configuration.py": "3411088045ffb8a9a0aa9936eae275896b39983a2ee5b08f091b44e6289e4fe4",
    "modeling.py": "374670b416fcc82f081c9cd28b5fd61c2bd91bbe18eb4798fcc48a81f9c250a0",
}


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def render_markdown(report: dict[str, Any]) -> str:
    runtime = report["runtime"]
    validation = report["validation"]
    timings = report["timings"]
    norms = validation["norms"]
    lines = [
        "# Validación de embeddings GTE para Child V1",
        "",
        "Este artefacto valida embeddings densos locales. No usa Qdrant, Parents, LLM ni thresholds.",
        "",
        "## Configuración reproducible",
        "",
        f"- Modelo: `{report['model']['model_id']}`.",
        f"- Revisión de pesos: `{report['model']['model_revision']}`.",
        f"- Código remoto: `{report['model']['remote_code_repo']}@{report['model']['remote_code_revision']}`.",
        f"- Backend efectivo: `{runtime['backend']}`.",
        f"- `transformers=={runtime['libraries']['transformers']}`.",
        f"- `sentence-transformers=={runtime['libraries']['sentence_transformers']}` instalado, no usado por la anomalía documentada.",
        f"- `torch=={runtime['libraries']['torch']}`; dispositivo `{runtime['device']}`; dtype `{runtime['dtype']}`.",
        f"- Batch size: {runtime['batch_size']}.",
        f"- Pooling: `{runtime['pooling']}`; dimensión: {validation['shape'][1]}; normalización L2: sí.",
        "- Se codifica exactamente `Child.text`, sin prefijos, metadata ni truncación.",
        "",
        "## Validación",
        "",
        f"- Estado: **{validation['status']}**.",
        f"- Embeddings: **{validation['embedding_count']}**.",
        f"- Shape: `{validation['shape']}`; dtype almacenado: `{validation['dtype']}`.",
        f"- NaN: {validation['nan_count']}; Inf: {validation['inf_count']}; IDs duplicados: {validation['duplicate_chunk_id_count']}.",
        f"- Normas L2: mínimo {norms['min']:.8f}, media {norms['mean']:.8f}, mediana {norms['median']:.8f}, máximo {norms['max']:.8f}.",
        f"- Máxima desviación absoluta respecto de 1: {norms['max_absolute_deviation_from_one']:.8f}.",
        "",
        "## Tiempos",
        "",
        f"- Carga del modelo: {timings['model_load_seconds']:.4f} s.",
        f"- Inferencia de 140 Children: {timings['corpus_inference_seconds']:.4f} s.",
        f"- Rendimiento: {timings['corpus_texts_per_second']:.4f} Children/s.",
        f"- Smoke queries, inferencia conjunta: {timings['smoke_query_inference_seconds']:.4f} s.",
        f"- Tiempo total: {timings['total_seconds']:.4f} s.",
        "",
        "## Anomalías y decisiones",
        "",
    ]
    for anomaly in report["anomalies"]:
        lines.append(f"- {anomaly}")
    if not report["anomalies"]:
        lines.append("- No se observaron anomalías.")

    lines.extend(
        [
            "",
            "## Smoke tests de retrieval",
            "",
            "Son inspecciones técnicas; los scores son similitudes coseno, no probabilidades. No se aplican thresholds ni se evalúa todavía la calidad.",
            "",
        ]
    )
    for smoke in report["smoke_tests"]:
        lines.extend(
            [
                f"### {smoke['query']}",
                "",
                "| Rank | Cosine | Chunk | Ponencia | Secuencias |",
                "|---:|---:|---|---|---|",
            ]
        )
        for item in smoke["results"]:
            lines.append(
                f"| {item['rank']} | {item['cosine_similarity']:.6f} | `{item['chunk_id']}` | "
                f"`{item['talk_id']}` | {item['start_sequence_index']}–{item['end_sequence_index']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--validation-md", type=Path, default=DEFAULT_VALIDATION_MD)
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    total_started = time.perf_counter()
    config_path = args.config.resolve()
    chunks_path = args.chunks.resolve()
    embeddings_path = args.embeddings.resolve()
    manifest_path = args.manifest.resolve()
    validation_json_path = args.validation_json.resolve()
    validation_md_path = args.validation_md.resolve()

    config = load_embedding_config(config_path)
    chunks_hash_before = sha256(chunks_path)
    chunks = load_chunks(chunks_path)
    if len(chunks) != 140:
        raise ValueError(f"Se esperaban 140 Children y se encontraron {len(chunks)}")
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    texts = [chunk[config["input_field"]] for chunk in chunks]

    tokenizer, model, model_runtime = load_gte_model(
        config, local_files_only=args.local_files_only
    )
    embeddings, corpus_timing = encode_texts(texts, tokenizer, model, config)
    validation = validate_embeddings(
        chunk_ids,
        embeddings,
        chunk_ids,
        int(config["embedding_dimension"]),
    )
    if validation["status"] != "passed":
        raise ValueError(f"Falló la validación previa al guardado: {validation['checks']}")

    save_started = time.perf_counter()
    save_embedding_artifact(embeddings_path, chunk_ids, embeddings)
    save_seconds = time.perf_counter() - save_started
    stored_ids, stored_embeddings = load_embedding_artifact(embeddings_path)
    stored_validation = validate_embeddings(
        stored_ids,
        stored_embeddings,
        chunk_ids,
        int(config["embedding_dimension"]),
    )
    if stored_validation["status"] != "passed":
        raise ValueError(f"Falló la validación del artefacto guardado: {stored_validation}")

    smoke_embeddings, smoke_timing = encode_texts(
        list(SMOKE_QUERIES), tokenizer, model, config
    )
    chunks_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    smoke_tests = []
    search_total = 0.0
    for query, query_embedding in zip(SMOKE_QUERIES, smoke_embeddings):
        search_started = time.perf_counter()
        results = search_results(
            query_embedding,
            stored_embeddings,
            stored_ids,
            chunks_by_id,
            top_k=5,
        )
        search_seconds = time.perf_counter() - search_started
        search_total += search_seconds
        smoke_tests.append(
            {
                "query": query,
                "top_k": 5,
                "search_seconds": round(search_seconds, 6),
                "results": results,
            }
        )

    chunks_hash_after = sha256(chunks_path)
    if chunks_hash_before != chunks_hash_after:
        raise RuntimeError("chunks.jsonl cambió durante la generación de embeddings")

    runtime = {
        "backend": "PyTorch + Transformers AutoModel; official CLS pooling reproduced explicitly",
        "device": model_runtime["device"],
        "dtype": model_runtime["dtype"],
        "batch_size": config["batch_size"],
        "pooling": config["pooling"],
        "normalize_embeddings": config["normalize_embeddings"],
        "model_class": model_runtime["model_class"],
        "tokenizer_class": model_runtime["tokenizer_class"],
        "torch_threads": model_runtime["torch_threads"],
        "platform": platform.platform(),
        "python": platform.python_version(),
        "libraries": {
            "numpy": np.__version__,
            "torch": torch.__version__,
            "transformers": package_version("transformers"),
            "sentence_transformers": package_version("sentence-transformers"),
            "tokenizers": package_version("tokenizers"),
            "sentencepiece": package_version("sentencepiece"),
        },
    }

    total_seconds = time.perf_counter() - total_started
    timings = {
        "model_load_seconds": model_runtime["load_seconds"],
        "corpus_inference_seconds": corpus_timing["seconds"],
        "corpus_texts_per_second": corpus_timing["texts_per_second"],
        "corpus_batches": corpus_timing["batches"],
        "maximum_corpus_tokens_seen": corpus_timing["maximum_input_tokens_seen"],
        "artifact_save_seconds": round(save_seconds, 4),
        "smoke_query_inference_seconds": smoke_timing["seconds"],
        "smoke_search_total_seconds": round(search_total, 6),
        "total_seconds": round(total_seconds, 4),
    }

    model_info = {
        "model_id": config["model_id"],
        "model_revision": config["model_revision"],
        "remote_code_repo": config["remote_code_repo"],
        "remote_code_revision": config["remote_code_revision"],
        "trust_remote_code": config["trust_remote_code"],
        "remote_code_files_sha256": REMOTE_CODE_FILES,
        "remote_code_review": (
            "Pinned configuration.py and modeling.py were inspected before execution; "
            "imports are limited to Python typing/dataclasses/math, torch and transformers, "
            "with no shell, network or filesystem operations in the reviewed files."
        ),
    }
    anomalies = [
        "`sentence-transformers==5.1.2` was installed but its top-level import requires Pillow; "
        "Windows denied reads from the installed PIL package. Pillow was removed because this "
        "text-only pipeline does not need it. Inference therefore uses Transformers directly "
        "with the model's official CLS pooling configuration.",
        "The model requires `trust_remote_code=True`; both the model revision and the external "
        "`Alibaba-NLP/new-impl` code revision are pinned and their two Python files were reviewed.",
        "Transformers reported that `classifier.weight` and `classifier.bias` were unused when "
        "initializing `NewModel`. This is expected for embedding inference because the base "
        "encoder is loaded without the checkpoint's task-specific classifier head.",
    ]

    report = {
        "report_version": "1.0",
        "scope": "Child V1 dense embeddings and local cosine smoke retrieval",
        "source": {
            "path": relative(chunks_path),
            "sha256_before": chunks_hash_before,
            "sha256_after": chunks_hash_after,
            "modified": False,
            "chunk_count": len(chunks),
            "input": "exact Child.text; no prefix, metadata or truncation",
        },
        "configuration": {
            "path": relative(config_path),
            "sha256": sha256(config_path),
        },
        "model": model_info,
        "runtime": runtime,
        "validation": stored_validation,
        "timings": timings,
        "artifacts": {
            "embeddings": {
                "path": relative(embeddings_path),
                "sha256": sha256(embeddings_path),
                "bytes": embeddings_path.stat().st_size,
                "format": "NumPy NPZ with non-pickle arrays: chunk_ids[str], embeddings[float32]",
            },
            "mapping": [
                {"row_index": index, "chunk_id": chunk_id}
                for index, chunk_id in enumerate(stored_ids)
            ],
        },
        "smoke_tests": smoke_tests,
        "score_interpretation": (
            "cosine_similarity is a ranking similarity, not a probability; no thresholds applied"
        ),
        "anomalies": anomalies,
        "excluded_scope": ["qdrant", "parents", "llm", "thresholds", "formal_evaluation"],
    }

    manifest = {
        "manifest_version": "1.0",
        "artifact_type": "child-v1-dense-embeddings",
        "source": report["source"],
        "configuration": report["configuration"],
        "model": model_info,
        "runtime": runtime,
        "embedding_count": stored_validation["embedding_count"],
        "embedding_dimension": stored_validation["shape"][1],
        "normalized": stored_validation["checks"]["vectors_l2_normalized"],
        "embeddings": report["artifacts"]["embeddings"],
        "mapping": report["artifacts"]["mapping"],
        "validation_report": relative(validation_json_path),
    }

    write_json(manifest_path, manifest)
    report["artifacts"]["manifest"] = {
        "path": relative(manifest_path),
        "sha256": sha256(manifest_path),
        "bytes": manifest_path.stat().st_size,
    }
    write_json(validation_json_path, report)
    validation_md_path.parent.mkdir(parents=True, exist_ok=True)
    validation_md_path.write_text(
        render_markdown(report), encoding="utf-8", newline="\n"
    )

    print(
        f"OK: {stored_validation['embedding_count']} embeddings "
        f"{tuple(stored_validation['shape'])}, {model_runtime['device']}/"
        f"{model_runtime['dtype']}; validación={stored_validation['status']}"
    )


if __name__ == "__main__":
    main()

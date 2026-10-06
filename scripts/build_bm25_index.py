#!/usr/bin/env python3
"""Build and validate the independent BM25 index for retrieval experiment 002."""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

from bm25_common import (
    DEFAULT_CONFIG,
    build_index,
    load_chunks,
    load_json,
    resolve_project_path,
    sha256,
    validate_index,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    started = time.perf_counter()
    config_path = args.config.resolve()
    config = load_json(config_path)
    source_path = resolve_project_path(config["source"]["path"])
    index_path = resolve_project_path(config["outputs"]["index"])
    validation_path = resolve_project_path(config["outputs"]["validation"])

    source_hash_before = sha256(source_path)
    if source_hash_before != config["source"]["sha256"]:
        raise ValueError(
            "El SHA-256 actual de chunks.jsonl no coincide con el experimento"
        )

    chunks = load_chunks(source_path)
    expected_ids = [str(chunk[config["source"]["id_field"]]) for chunk in chunks]
    index = build_index(chunks, config)
    index["source"] = {
        "path": config["source"]["path"],
        "sha256": source_hash_before,
        "input": "exact Child.text",
    }
    index["configuration"] = {
        "path": str(config_path.relative_to(resolve_project_path("."))).replace(
            "\\", "/"
        ),
        "sha256": sha256(config_path),
    }

    validation = validate_index(
        index,
        expected_ids,
        int(config["source"]["expected_document_count"]),
    )
    if validation["status"] != "passed":
        raise ValueError(f"El índice BM25 no pasó validación: {validation['checks']}")

    write_json(index_path, index)
    source_hash_after = sha256(source_path)
    lengths = index["document_lengths"]
    report = {
        "report_version": "1.0",
        "experiment_id": config["experiment_id"],
        "status": validation["status"],
        "source": {
            "path": config["source"]["path"],
            "sha256_before": source_hash_before,
            "sha256_after": source_hash_after,
            "modified": source_hash_before != source_hash_after,
            "input": "exact Child.text",
        },
        "configuration": {
            "path": index["configuration"]["path"],
            "sha256": index["configuration"]["sha256"],
        },
        "implementation": index["implementation"],
        "parameters": index["parameters"],
        "preprocessing": index["preprocessing"],
        "statistics": {
            "document_count": index["document_count"],
            "vocabulary_size": len(index["postings"]),
            "document_tokens": {
                "minimum": min(lengths),
                "mean": statistics.fmean(lengths),
                "median": statistics.median(lengths),
                "maximum": max(lengths),
                "total": sum(lengths),
            },
            "average_document_length_used_by_bm25": index[
                "average_document_length"
            ],
        },
        "validation": validation,
        "index_artifact": {
            "path": config["outputs"]["index"],
            "sha256": sha256(index_path),
            "bytes": index_path.stat().st_size,
            "format": "UTF-8 JSON; no pickle",
        },
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "excluded_scope": config["excluded_scope"],
    }
    write_json(validation_path, report)
    print(
        f"BM25 indexado y validado: {index['document_count']} Children, "
        f"{len(index['postings'])} términos, status={validation['status']}"
    )
    print(index_path)
    print(validation_path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run minimal local cosine retrieval over the derived Child V1 embeddings."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from gte_embedding_common import (
    DEFAULT_CHUNKS,
    DEFAULT_CONFIG,
    DEFAULT_EMBEDDINGS,
    DEFAULT_MANIFEST,
    encode_texts,
    load_chunks,
    load_embedding_artifact,
    load_embedding_config,
    load_gte_model,
    search_results,
    sha256,
    validate_embeddings,
)


def render_text(payload: dict) -> str:
    lines = [
        f"Query: {payload['query']}",
        (
            "Nota: cosine similarity es una medida de similitud para ranking; "
            "no es una probabilidad y no se aplicó ningún threshold."
        ),
        (
            f"Tiempos: carga={payload['timings']['model_load_seconds']:.4f}s, "
            f"query={payload['timings']['query_embedding_seconds']:.4f}s, "
            f"búsqueda={payload['timings']['search_seconds']:.6f}s"
        ),
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"{item['rank']}. cosine={item['cosine_similarity']:.8f}",
                f"   chunk_id: {item['chunk_id']}",
                f"   talk_id: {item['talk_id']}",
                f"   título: {item['title']}",
                f"   ponente: {item['primary_speaker']}",
                (
                    f"   sequence_index: {item['start_sequence_index']}–"
                    f"{item['end_sequence_index']}"
                ),
                f"   preview: {item['preview']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Consulta de texto")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    config_path = args.config.resolve()
    chunks_path = args.chunks.resolve()
    embeddings_path = args.embeddings.resolve()
    manifest_path = args.manifest.resolve()
    config = load_embedding_config(config_path)
    chunks = load_chunks(chunks_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if sha256(chunks_path) != manifest["source"]["sha256_before"]:
        raise ValueError("El hash actual de chunks.jsonl no coincide con el manifiesto")
    if sha256(config_path) != manifest["configuration"]["sha256"]:
        raise ValueError("La configuración no coincide con el manifiesto")
    if sha256(embeddings_path) != manifest["embeddings"]["sha256"]:
        raise ValueError("El artefacto de embeddings no coincide con el manifiesto")

    chunk_ids, embeddings = load_embedding_artifact(embeddings_path)
    expected_ids = [chunk["chunk_id"] for chunk in chunks]
    validation = validate_embeddings(
        chunk_ids,
        embeddings,
        expected_ids,
        int(config["embedding_dimension"]),
    )
    if validation["status"] != "passed":
        raise ValueError(f"El artefacto no pasó validación: {validation['checks']}")

    tokenizer, model, model_runtime = load_gte_model(
        config, local_files_only=args.local_files_only
    )
    query_embeddings, query_timing = encode_texts(
        [args.query], tokenizer, model, config, batch_size=1
    )
    chunks_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    search_started = time.perf_counter()
    results = search_results(
        query_embeddings[0],
        embeddings,
        chunk_ids,
        chunks_by_id,
        args.top_k,
    )
    search_seconds = time.perf_counter() - search_started
    payload = {
        "query": args.query,
        "top_k": args.top_k,
        "score_interpretation": (
            "cosine_similarity is a ranking similarity, not a probability; no threshold applied"
        ),
        "model_id": config["model_id"],
        "model_revision": config["model_revision"],
        "timings": {
            "model_load_seconds": model_runtime["load_seconds"],
            "query_embedding_seconds": query_timing["seconds"],
            "search_seconds": round(search_seconds, 6),
        },
        "results": results,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))


if __name__ == "__main__":
    main()

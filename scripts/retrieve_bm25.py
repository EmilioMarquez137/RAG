#!/usr/bin/env python3
"""Run independent BM25 retrieval for experiment 002; no Dense fusion."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from bm25_common import (
    DEFAULT_CONFIG,
    bm25_scores,
    load_chunks,
    load_json,
    preview,
    resolve_project_path,
    sha256,
    top_k_indices,
    validate_index,
)


def render_text(payload: dict) -> str:
    lines = [
        f"Query: {payload['query']}",
        f"Tokens BM25: {payload['query_tokens']}",
        (
            "Nota: BM25 es una señal lexical independiente; el score no es una "
            "probabilidad y no se aplicó threshold ni fusión con Dense."
        ),
        "",
    ]
    for result in payload["results"]:
        lines.extend(
            [
                f"{result['rank']}. bm25={result['bm25_score']:.8f}",
                f"   chunk_id: {result['chunk_id']}",
                f"   talk_id: {result['talk_id']}",
                f"   título: {result['title']}",
                f"   ponente: {result['primary_speaker']}",
                (
                    f"   sequence_index: {result['start_sequence_index']}–"
                    f"{result['end_sequence_index']}"
                ),
            ]
        )
        if "text" in result:
            lines.extend(
                ["   texto completo:", textwrap.indent(result["text"], "      ")]
            )
        else:
            lines.append(f"   preview: {result['preview']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Consulta de texto")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--full-text", action="store_true")
    args = parser.parse_args()

    config = load_json(args.config.resolve())
    chunks_path = resolve_project_path(config["source"]["path"])
    index_path = resolve_project_path(config["outputs"]["index"])
    if sha256(chunks_path) != config["source"]["sha256"]:
        raise ValueError("chunks.jsonl no coincide con la fuente fijada")

    chunks = load_chunks(chunks_path)
    chunks_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    expected_ids = [chunk["chunk_id"] for chunk in chunks]
    index = load_json(index_path)
    validation = validate_index(
        index,
        expected_ids,
        int(config["source"]["expected_document_count"]),
    )
    if validation["status"] != "passed":
        raise ValueError(f"El índice BM25 no pasó validación: {validation['checks']}")

    query_tokens, scores = bm25_scores(index, args.query)
    results = []
    for rank, document_index in enumerate(
        top_k_indices(scores, args.top_k), start=1
    ):
        chunk_id = index["chunk_ids"][document_index]
        chunk = chunks_by_id[chunk_id]
        result = {
            "rank": rank,
            "bm25_score": round(scores[document_index], 8),
            "chunk_id": chunk_id,
            "talk_id": chunk["talk_id"],
            "title": chunk["title"],
            "primary_speaker": chunk["primary_speaker"],
            "start_sequence_index": chunk["start_sequence_index"],
            "end_sequence_index": chunk["end_sequence_index"],
            "preview": preview(chunk["text"]),
        }
        if args.full_text:
            result["text"] = chunk["text"]
        results.append(result)

    payload = {
        "experiment_id": config["experiment_id"],
        "retriever": "bm25",
        "query": args.query,
        "query_tokens": query_tokens,
        "top_k": args.top_k,
        "score_interpretation": (
            "BM25 ranking score, not a probability; no threshold or Dense fusion"
        ),
        "results": results,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))


if __name__ == "__main__":
    main()

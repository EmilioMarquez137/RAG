"""Transparent BM25 Okapi utilities for the lexical retrieval experiment."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT / "experiments" / "retrieval" / "exp_002_dense_gte_bm25" / "config.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def resolve_project_path(value: str) -> Path:
    return (ROOT / value).resolve()


def load_chunks(path: Path) -> list[dict[str, Any]]:
    chunks = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en {path}, línea {line_number}") from exc
    return chunks


def lexical_tokenize(text: str, preprocessing: dict[str, Any]) -> list[str]:
    normalized = unicodedata.normalize(
        preprocessing["unicode_normalization"], text
    )
    if preprocessing["lowercase"]:
        normalized = normalized.lower()
    return re.findall(preprocessing["token_pattern"], normalized, flags=re.UNICODE)


def build_index(
    chunks: Sequence[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any]:
    id_field = config["source"]["id_field"]
    input_field = config["source"]["input_field"]
    preprocessing = config["preprocessing"]
    chunk_ids = [str(chunk[id_field]) for chunk in chunks]
    tokenized_documents = [
        lexical_tokenize(str(chunk[input_field]), preprocessing) for chunk in chunks
    ]
    document_lengths = [len(tokens) for tokens in tokenized_documents]
    document_count = len(chunks)
    average_document_length = (
        sum(document_lengths) / document_count if document_count else 0.0
    )

    term_frequencies = [Counter(tokens) for tokens in tokenized_documents]
    document_frequencies: Counter[str] = Counter()
    for frequencies in term_frequencies:
        document_frequencies.update(frequencies.keys())

    inverse_document_frequencies = {
        term: math.log(
            1.0
            + (document_count - frequency + 0.5) / (frequency + 0.5)
        )
        for term, frequency in sorted(document_frequencies.items())
    }
    postings = {
        term: [
            [document_index, int(frequencies[term])]
            for document_index, frequencies in enumerate(term_frequencies)
            if term in frequencies
        ]
        for term in inverse_document_frequencies
    }

    return {
        "schema_version": "1.0",
        "artifact_type": "bm25_okapi_index",
        "implementation": config["bm25"]["implementation"],
        "parameters": {
            "k1": config["bm25"]["k1"],
            "b": config["bm25"]["b"],
            "idf": config["bm25"]["idf"],
            "query_term_frequency": config["bm25"]["query_term_frequency"],
            "score_normalization": config["bm25"]["score_normalization"],
            "threshold": config["bm25"]["threshold"],
        },
        "preprocessing": preprocessing,
        "document_count": document_count,
        "average_document_length": average_document_length,
        "chunk_ids": chunk_ids,
        "document_lengths": document_lengths,
        "document_frequencies": dict(sorted(document_frequencies.items())),
        "inverse_document_frequencies": inverse_document_frequencies,
        "postings": postings,
    }


def validate_index(
    index: dict[str, Any],
    expected_chunk_ids: Sequence[str],
    expected_document_count: int,
) -> dict[str, Any]:
    indexed_ids = list(index["chunk_ids"])
    indexed_id_set = set(indexed_ids)
    expected_id_set = set(expected_chunk_ids)
    document_lengths = list(index["document_lengths"])
    postings = index["postings"]

    reconstructed_lengths = [0] * len(indexed_ids)
    postings_well_formed = True
    for term_postings in postings.values():
        previous_index = -1
        for document_index, term_frequency in term_postings:
            if (
                not isinstance(document_index, int)
                or document_index <= previous_index
                or document_index < 0
                or document_index >= len(indexed_ids)
                or not isinstance(term_frequency, int)
                or term_frequency < 1
            ):
                postings_well_formed = False
                continue
            reconstructed_lengths[document_index] += term_frequency
            previous_index = document_index

    checks = {
        "exactly_expected_document_count": len(indexed_ids)
        == expected_document_count,
        "exactly_140_children_indexed": len(indexed_ids) == 140,
        "chunk_ids_unique": len(indexed_ids) == len(indexed_id_set),
        "no_children_missing": not (expected_id_set - indexed_id_set),
        "no_unexpected_children": not (indexed_id_set - expected_id_set),
        "one_to_one_in_source_order": indexed_ids == list(expected_chunk_ids),
        "no_empty_documents_after_preprocessing": bool(document_lengths)
        and all(length > 0 for length in document_lengths),
        "document_lengths_complete": len(document_lengths) == len(indexed_ids),
        "postings_well_formed": postings_well_formed,
        "postings_reconstruct_document_lengths": reconstructed_lengths
        == document_lengths,
        "idf_and_posting_terms_match": set(
            index["inverse_document_frequencies"]
        )
        == set(postings),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "missing_chunk_ids": sorted(expected_id_set - indexed_id_set),
        "unexpected_chunk_ids": sorted(indexed_id_set - expected_id_set),
    }


def bm25_scores(index: dict[str, Any], query: str) -> tuple[list[str], list[float]]:
    query_tokens = lexical_tokenize(query, index["preprocessing"])
    if not query_tokens:
        raise ValueError("La consulta queda vacía después del preprocessing lexical")

    scores = [0.0] * int(index["document_count"])
    query_frequencies = Counter(query_tokens)
    k1 = float(index["parameters"]["k1"])
    b = float(index["parameters"]["b"])
    average_document_length = float(index["average_document_length"])
    document_lengths = index["document_lengths"]
    idf = index["inverse_document_frequencies"]

    for term, query_frequency in query_frequencies.items():
        if term not in idf:
            continue
        for document_index, term_frequency in index["postings"][term]:
            length_ratio = document_lengths[document_index] / average_document_length
            denominator = term_frequency + k1 * (1.0 - b + b * length_ratio)
            scores[document_index] += (
                query_frequency
                * idf[term]
                * (term_frequency * (k1 + 1.0) / denominator)
            )
    return query_tokens, scores


def top_k_indices(scores: Sequence[float], top_k: int) -> list[int]:
    if top_k < 1:
        raise ValueError("top_k debe ser al menos 1")
    return sorted(range(len(scores)), key=lambda index: (-scores[index], index))[
        : min(top_k, len(scores))
    ]


def preview(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"

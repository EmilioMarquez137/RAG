"""Shared GTE embedding and local cosine-retrieval utilities."""

from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
# Executable custom-model modules must stay inside the workspace. The managed
# environment can download to the global HF cache but denies Python imports
# from its generated transformers_modules directory.
LOCAL_HF_MODULES_CACHE = ROOT / ".cache" / "huggingface" / "modules"
os.environ.setdefault("HF_MODULES_CACHE", str(LOCAL_HF_MODULES_CACHE))

from transformers import AutoModel, AutoTokenizer  # noqa: E402


DEFAULT_CONFIG = ROOT / "config" / "gte_embedding_baseline.json"
DEFAULT_CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
DEFAULT_EMBEDDINGS = (
    ROOT / "data" / "derived" / "embeddings" / "gte_multilingual_base_child_v1.npz"
)
DEFAULT_MANIFEST = (
    ROOT / "data" / "derived" / "embeddings" / "gte_multilingual_base_child_v1_manifest.json"
)
DEFAULT_VALIDATION_JSON = ROOT / "data" / "analysis" / "gte_embedding_validation.json"
DEFAULT_VALIDATION_MD = ROOT / "data" / "analysis" / "gte_embedding_validation.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_chunks(path: Path) -> list[dict[str, Any]]:
    chunks = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not chunks:
        raise ValueError(f"No hay Children en {path}")

    required = {
        "chunk_id",
        "talk_id",
        "title",
        "primary_speaker",
        "start_sequence_index",
        "end_sequence_index",
        "text",
    }
    ids: list[str] = []
    for line_number, chunk in enumerate(chunks, start=1):
        missing = required - chunk.keys()
        if missing:
            raise ValueError(
                f"Línea {line_number} de {path}: faltan {sorted(missing)}"
            )
        if not isinstance(chunk["text"], str) or not chunk["text"]:
            raise ValueError(f"Línea {line_number}: Child.text debe ser no vacío")
        ids.append(chunk["chunk_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("chunks.jsonl contiene chunk_id duplicados")
    return chunks


def load_embedding_config(path: Path) -> dict[str, Any]:
    config = load_json(path)
    if config["pooling"] != "cls":
        raise ValueError("Este baseline solo implementa el pooling CLS oficial")
    if config["dtype"] != "float32":
        raise ValueError("Este baseline CPU fue fijado en float32")
    if config["device"] != "cpu":
        raise ValueError("Este baseline reproducible fue fijado en CPU")
    if not config["normalize_embeddings"]:
        raise ValueError("El artefacto baseline requiere normalización L2")
    return config


def load_gte_model(
    config: dict[str, Any], *, local_files_only: bool = False
) -> tuple[Any, Any, dict[str, Any]]:
    """Load the pinned tokenizer and custom GTE model implementation."""
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"],
        revision=config["model_revision"],
        trust_remote_code=False,
        use_fast=True,
        local_files_only=local_files_only,
    )
    model = AutoModel.from_pretrained(
        config["model_id"],
        revision=config["model_revision"],
        code_revision=config["remote_code_revision"],
        trust_remote_code=config["trust_remote_code"],
        dtype=torch.float32,
        local_files_only=local_files_only,
    )
    device = torch.device(config["device"])
    model.to(device)
    model.eval()
    parameter = next(model.parameters())
    metadata = {
        "load_seconds": round(time.perf_counter() - started, 4),
        "device": str(parameter.device),
        "dtype": str(parameter.dtype).removeprefix("torch."),
        "model_class": type(model).__name__,
        "tokenizer_class": type(tokenizer).__name__,
        "torch_threads": torch.get_num_threads(),
    }
    return tokenizer, model, metadata


def encode_texts(
    texts: Sequence[str],
    tokenizer: Any,
    model: Any,
    config: dict[str, Any],
    *,
    batch_size: int | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Encode exact texts with CLS pooling and optional L2 normalization."""
    if not texts:
        raise ValueError("Se requiere al menos un texto")
    actual_batch_size = batch_size or int(config["batch_size"])
    device = next(model.parameters()).device
    batches: list[np.ndarray] = []
    max_tokens_seen = 0
    started = time.perf_counter()

    with torch.inference_mode():
        for start in range(0, len(texts), actual_batch_size):
            batch = list(texts[start : start + actual_batch_size])
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=False,
                add_special_tokens=True,
                return_token_type_ids=False,
                return_tensors="pt",
            )
            lengths = encoded["attention_mask"].sum(dim=1)
            batch_max = int(lengths.max().item())
            max_tokens_seen = max(max_tokens_seen, batch_max)
            if batch_max > int(config["maximum_input_tokens"]):
                raise ValueError(
                    f"Input de {batch_max} tokens supera el límite fijado de "
                    f"{config['maximum_input_tokens']}; no se truncará silenciosamente"
                )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            outputs = model(**encoded)
            embeddings = outputs.last_hidden_state[:, 0]
            if config["normalize_embeddings"]:
                embeddings = F.normalize(embeddings, p=2, dim=1)
            batches.append(embeddings.detach().cpu().to(torch.float32).numpy())

    result = np.concatenate(batches, axis=0).astype(np.float32, copy=False)
    elapsed = time.perf_counter() - started
    return result, {
        "seconds": round(elapsed, 4),
        "texts": len(texts),
        "batch_size": actual_batch_size,
        "batches": math.ceil(len(texts) / actual_batch_size),
        "texts_per_second": round(len(texts) / elapsed, 4),
        "maximum_input_tokens_seen": max_tokens_seen,
    }


def percentile(values: Iterable[float], probability: float) -> float:
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


def norm_statistics(embeddings: np.ndarray) -> dict[str, float]:
    norms = np.linalg.norm(embeddings, axis=1)
    return {
        "min": round(float(norms.min()), 8),
        "mean": round(float(norms.mean()), 8),
        "median": round(float(statistics.median(norms.tolist())), 8),
        "max": round(float(norms.max()), 8),
        "max_absolute_deviation_from_one": round(
            float(np.max(np.abs(norms - 1.0))), 8
        ),
    }


def validate_embeddings(
    chunk_ids: Sequence[str],
    embeddings: np.ndarray,
    expected_chunk_ids: Sequence[str],
    expected_dimension: int,
) -> dict[str, Any]:
    ids = list(chunk_ids)
    expected = list(expected_chunk_ids)
    norms = norm_statistics(embeddings)
    checks = {
        "embedding_count_is_140": len(ids) == 140,
        "matrix_row_count_matches_ids": embeddings.shape[0] == len(ids),
        "dimension_is_expected": (
            embeddings.ndim == 2 and embeddings.shape[1] == expected_dimension
        ),
        "no_nan": not bool(np.isnan(embeddings).any()),
        "no_inf": not bool(np.isinf(embeddings).any()),
        "chunk_ids_unique": len(ids) == len(set(ids)),
        "one_to_one_with_chunks": set(ids) == set(expected),
        "same_order_as_chunks": ids == expected,
        "vectors_l2_normalized": norms["max_absolute_deviation_from_one"] <= 1e-5,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "embedding_count": len(ids),
        "shape": list(embeddings.shape),
        "dtype": str(embeddings.dtype),
        "nan_count": int(np.isnan(embeddings).sum()),
        "inf_count": int(np.isinf(embeddings).sum()),
        "duplicate_chunk_id_count": len(ids) - len(set(ids)),
        "norms": norms,
    }


def save_embedding_artifact(
    path: Path, chunk_ids: Sequence[str], embeddings: np.ndarray
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = np.asarray(list(chunk_ids), dtype=np.str_)
    np.savez(path, chunk_ids=ids, embeddings=embeddings.astype(np.float32))


def load_embedding_artifact(path: Path) -> tuple[list[str], np.ndarray]:
    with np.load(path, allow_pickle=False) as artifact:
        keys = set(artifact.files)
        if keys != {"chunk_ids", "embeddings"}:
            raise ValueError(f"Arrays inesperados en {path}: {sorted(keys)}")
        chunk_ids = artifact["chunk_ids"].astype(str).tolist()
        embeddings = artifact["embeddings"].astype(np.float32, copy=False)
    return chunk_ids, embeddings


def cosine_top_k(
    query_embedding: np.ndarray,
    embeddings: np.ndarray,
    top_k: int,
) -> tuple[np.ndarray, np.ndarray]:
    if top_k < 1:
        raise ValueError("top_k debe ser al menos 1")
    query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
    query_norm = float(np.linalg.norm(query))
    row_norms = np.linalg.norm(embeddings, axis=1)
    if query_norm == 0 or bool(np.any(row_norms == 0)):
        raise ValueError("No se puede calcular cosine similarity con vectores nulos")
    scores = (embeddings @ query) / (row_norms * query_norm)
    indices = np.argsort(-scores, kind="stable")[: min(top_k, len(scores))]
    return indices, scores[indices]


def preview(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def search_results(
    query_embedding: np.ndarray,
    embeddings: np.ndarray,
    chunk_ids: Sequence[str],
    chunks_by_id: dict[str, dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    indices, scores = cosine_top_k(query_embedding, embeddings, top_k)
    results = []
    for rank, (index, score) in enumerate(zip(indices, scores), start=1):
        chunk_id = chunk_ids[int(index)]
        chunk = chunks_by_id[chunk_id]
        results.append(
            {
                "rank": rank,
                "cosine_similarity": round(float(score), 8),
                "chunk_id": chunk_id,
                "talk_id": chunk["talk_id"],
                "title": chunk["title"],
                "primary_speaker": chunk["primary_speaker"],
                "start_sequence_index": chunk["start_sequence_index"],
                "end_sequence_index": chunk["end_sequence_index"],
                "preview": preview(chunk["text"]),
            }
        )
    return results

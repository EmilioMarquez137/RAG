import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bm25_common import (  # noqa: E402
    bm25_scores,
    build_index,
    lexical_tokenize,
    load_json,
    top_k_indices,
    validate_index,
    write_json,
)


def configuration(expected_count: int) -> dict:
    return {
        "source": {
            "id_field": "chunk_id",
            "input_field": "text",
            "expected_document_count": expected_count,
        },
        "bm25": {
            "implementation": "local_bm25_okapi_v1",
            "k1": 1.5,
            "b": 0.75,
            "idf": "ln(1 + (N - df + 0.5) / (df + 0.5))",
            "query_term_frequency": "linear_multiplier",
            "score_normalization": None,
            "threshold": None,
        },
        "preprocessing": {
            "unicode_normalization": "NFC",
            "lowercase": True,
            "token_pattern": r"[^\W_]+",
            "punctuation": "separator_and_discarded",
            "stopwords": "none",
            "accents": "preserved",
            "stemming": "none",
            "lemmatization": "none",
        },
    }


class Bm25Test(unittest.TestCase):
    def test_preprocessing_is_unicode_lowercase_and_preserves_accents(self):
        tokens = lexical_tokenize(
            "¡QUÉ tal, Acción_IA 2026!",
            configuration(1)["preprocessing"],
        )
        self.assertEqual(tokens, ["qué", "tal", "acción", "ia", "2026"])

    def test_bm25_ranks_matching_document_first(self):
        chunks = [
            {"chunk_id": "a", "text": "batalla cultural cultura"},
            {"chunk_id": "b", "text": "inteligencia artificial liderazgo"},
            {"chunk_id": "c", "text": "historia empresarial"},
        ]
        index = build_index(chunks, configuration(3))
        query_tokens, scores = bm25_scores(index, "Batalla cultural")
        ranking = top_k_indices(scores, 3)
        self.assertEqual(query_tokens, ["batalla", "cultural"])
        self.assertEqual(index["chunk_ids"][ranking[0]], "a")
        self.assertGreater(scores[ranking[0]], scores[ranking[1]])

    def test_index_round_trip_is_safe_json(self):
        chunks = [{"chunk_id": "a", "text": "texto con acento á"}]
        index = build_index(chunks, configuration(1))
        with TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            write_json(path, index)
            loaded = load_json(path)
            self.assertEqual(loaded, json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(loaded["chunk_ids"], ["a"])

    def test_validation_checks_exact_140_document_mapping(self):
        chunks = [
            {"chunk_id": f"chunk-{index}", "text": f"documento {index}"}
            for index in range(140)
        ]
        expected_ids = [chunk["chunk_id"] for chunk in chunks]
        index = build_index(chunks, configuration(140))
        validation = validate_index(index, expected_ids, 140)
        self.assertEqual(validation["status"], "passed")
        self.assertTrue(all(validation["checks"].values()))


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gte_embedding_common import (  # noqa: E402
    cosine_top_k,
    load_embedding_artifact,
    save_embedding_artifact,
    validate_embeddings,
)


class GteEmbeddingsTest(unittest.TestCase):
    def test_npz_round_trip_preserves_id_to_vector_mapping(self):
        ids = ["chunk-a", "chunk-b"]
        embeddings = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "embeddings.npz"
            save_embedding_artifact(path, ids, embeddings)
            stored_ids, stored_embeddings = load_embedding_artifact(path)

        self.assertEqual(stored_ids, ids)
        np.testing.assert_array_equal(stored_embeddings, embeddings)

    def test_cosine_top_k_orders_descending_without_probability_conversion(self):
        embeddings = np.asarray(
            [[1.0, 0.0], [0.8, 0.6], [-1.0, 0.0]], dtype=np.float32
        )
        indices, scores = cosine_top_k(
            np.asarray([1.0, 0.0], dtype=np.float32), embeddings, top_k=3
        )
        self.assertEqual(indices.tolist(), [0, 1, 2])
        np.testing.assert_allclose(scores, [1.0, 0.8, -1.0], atol=1e-6)

    def test_validation_detects_complete_normalized_mapping(self):
        ids = [f"chunk-{index}" for index in range(140)]
        embeddings = np.zeros((140, 768), dtype=np.float32)
        embeddings[:, 0] = 1.0
        report = validate_embeddings(ids, embeddings, ids, 768)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["checks"].values()))

    def test_validation_detects_duplicate_and_non_finite_values(self):
        ids = ["duplicate", "duplicate"]
        embeddings = np.asarray([[1.0, 0.0], [np.nan, np.inf]], dtype=np.float32)
        report = validate_embeddings(ids, embeddings, ["duplicate", "other"], 2)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["checks"]["no_nan"])
        self.assertFalse(report["checks"]["no_inf"])
        self.assertFalse(report["checks"]["chunk_ids_unique"])
        self.assertFalse(report["checks"]["one_to_one_with_chunks"])


if __name__ == "__main__":
    unittest.main()

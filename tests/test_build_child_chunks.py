import tempfile
import unittest
from pathlib import Path

from scripts.build_child_chunks import (
    DEFAULT_CONFIG,
    DEFAULT_INPUT,
    TokenCounter,
    build_chunks,
    include_crossing_candidate,
    load_json,
    load_jsonl,
    validate_chunks,
    write_outputs,
)


class ChildV1Test(unittest.TestCase):
    def test_closest_rule_and_tie_breaker(self) -> None:
        self.assertFalse(include_crossing_candidate(480, 580, 500, True))
        self.assertTrue(include_crossing_candidate(471, 505, 500, True))
        self.assertTrue(include_crossing_candidate(350, 650, 500, True))
        self.assertTrue(include_crossing_candidate(600, 700, 500, False))

    def test_real_corpus_has_exact_coverage_and_traceability(self) -> None:
        config = load_json(DEFAULT_CONFIG)
        talks = load_jsonl(DEFAULT_INPUT)
        chunks, counter = build_chunks(talks, config)
        validation = validate_chunks(talks, chunks, config, counter)

        self.assertEqual("passed", validation["status"])
        self.assertGreater(len(chunks), 0)
        self.assertTrue(validation["checks"]["new_utterance_coverage_exactly_once"])
        self.assertTrue(validation["checks"]["overlap_matches_previous_suffix"])
        self.assertTrue(validation["checks"]["overlap_is_minimal_suffix_reaching_target"])
        self.assertTrue(validation["checks"]["closure_rule_respected"])
        self.assertTrue(validation["checks"]["no_parent_fields"])
        self.assertTrue(all(chunk["new_utterance_count"] >= 1 for chunk in chunks))
        self.assertTrue(all("parent_id" not in chunk for chunk in chunks))

    def test_outputs_are_written_without_parent_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            chunks, validation, stats = write_outputs(
                DEFAULT_INPUT,
                DEFAULT_CONFIG,
                root / "chunks.jsonl",
                root / "chunks_validation.json",
                root / "chunks_manifest.json",
                root / "child_v1_statistics.json",
                root / "child_v1_statistics.md",
            )
            self.assertEqual("passed", validation["status"])
            self.assertEqual(len(chunks), stats["global"]["chunk_count"])
            self.assertEqual(
                len(chunks) - 4, stats["non_final_chunks"]["chunk_count"]
            )
            self.assertTrue((root / "chunks.jsonl").is_file())
            self.assertFalse((root / "parents.jsonl").exists())


if __name__ == "__main__":
    unittest.main()


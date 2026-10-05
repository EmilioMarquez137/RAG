import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_talks import (
    DEFAULT_CONFIG,
    DEFAULT_SOURCE,
    build_records,
    load_config,
    write_outputs,
)


class BuildTalksIntegrationTest(unittest.TestCase):
    def test_builds_expected_canonical_talks(self) -> None:
        config = load_config(DEFAULT_CONFIG)
        records, diagnostics = build_records(DEFAULT_SOURCE, config)

        self.assertEqual(4, len(records))
        self.assertEqual(
            [
                "ricardo-salinas-mensaje-apertura",
                "agustin-laje-batalla-cultural",
                "adrian-villasenor-liderazgo-ia",
                "luis-caro-manuel-quijano-taller-claude",
            ],
            [record["talk_id"] for record in records],
        )
        self.assertEqual(2470, diagnostics["parsed_utterances"])
        self.assertEqual(3, len(diagnostics["timestamp_inversions"]))
        self.assertTrue(any("BAZ" in record["text"] for record in records))
        self.assertTrue(all("\ufeff" not in record["text"] for record in records))

        for record in records:
            source_lines = [item["source_line"] for item in record["utterances"]]
            sequence_indexes = [
                item["sequence_index"] for item in record["utterances"]
            ]
            self.assertEqual(source_lines, sorted(source_lines))
            self.assertEqual(sequence_indexes, list(range(len(record["utterances"]))))
            self.assertGreater(record["utterance_count"], 0)

        laje = records[1]
        self.assertEqual("01:48:51", laje["start_time"])
        self.assertEqual(488, laje["utterances"][0]["source_line"])

        # Timestamp inversions remain visible because source order is canonical.
        ricardo_times = [
            item["start_seconds"] for item in records[0]["utterances"]
        ]
        workshop_times = [
            item["start_seconds"] for item in records[3]["utterances"]
        ]
        self.assertTrue(
            any(current < previous for previous, current in zip(ricardo_times, ricardo_times[1:]))
        )
        self.assertTrue(
            any(current < previous for previous, current in zip(workshop_times, workshop_times[1:]))
        )

    def test_writes_machine_and_human_outputs(self) -> None:
        config = load_config(DEFAULT_CONFIG)
        records, diagnostics = build_records(DEFAULT_SOURCE, config)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            write_outputs(
                output, DEFAULT_SOURCE, DEFAULT_CONFIG, records, diagnostics
            )
            jsonl_records = [
                json.loads(line)
                for line in (output / "talks.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            report = json.loads(
                (output / "validation_report.json").read_text(encoding="utf-8")
            )

            self.assertEqual(4, len(jsonl_records))
            self.assertEqual("passed", report["status"])
            self.assertTrue(report["checks"]["boundary_markers_matched"])
            self.assertTrue(report["checks"]["source_line_canonical_order"])
            self.assertTrue(report["checks"]["sequence_indexes_consecutive"])
            self.assertEqual("source_line", report["policy"]["canonical_order"])
            self.assertEqual(
                3, len(report["diagnostics"]["timestamp_inversions"])
            )
            self.assertEqual(4, len(list((output / "talks").glob("*.txt"))))


if __name__ == "__main__":
    unittest.main()


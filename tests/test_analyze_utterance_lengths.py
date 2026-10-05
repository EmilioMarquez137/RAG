import unittest

from scripts.analyze_utterance_lengths import (
    DEFAULT_INPUT,
    analyze,
    percentile,
    windows_to_threshold,
)


class AnalyzeUtteranceLengthsTest(unittest.TestCase):
    def test_type_7_percentile(self) -> None:
        self.assertEqual(1.75, percentile([1, 2, 3, 4], 0.25))
        self.assertEqual(3.25, percentile([1, 2, 3, 4], 0.75))

    def test_windows_do_not_require_a_chunking_decision(self) -> None:
        result = windows_to_threshold([100, 100, 100, 100], 250)
        self.assertEqual(2, result["windows_reaching_threshold"])
        self.assertEqual(2, result["tail_starts_not_reaching_threshold"])
        self.assertEqual(3, result["utterance_count_stats"]["median_utterances"])

    def test_corpus_analysis_is_complete_and_non_decisional(self) -> None:
        report = analyze(DEFAULT_INPUT)
        self.assertEqual(2301, report["source"]["utterance_count"])
        self.assertEqual("cl100k_base", report["tokenizer"]["encoding"])
        self.assertFalse(report["tokenizer"]["definitive_for_embedding_model"])
        self.assertEqual(
            2301, report["utterance_lengths"]["global"]["utterance_count"]
        )
        self.assertFalse(report["decision_status"]["target_tokens_selected"])
        self.assertFalse(report["decision_status"]["overlap_tokens_selected"])


if __name__ == "__main__":
    unittest.main()


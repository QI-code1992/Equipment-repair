import unittest

from stage6_performance import multipart_body, parse_levels, percentile, scenario_passes


class PerformanceThresholdTests(unittest.TestCase):
    def test_percentile_uses_nearest_rank(self) -> None:
        self.assertEqual(percentile([10, 20, 30, 40, 50], 95), 50)

    def test_scenario_fails_when_any_unexpected_error_occurs(self) -> None:
        self.assertFalse(
            scenario_passes(
                latencies_ms=[100, 200], unexpected_errors=1, p95_limit_ms=1_000
            )
        )

    def test_scenario_fails_when_p95_exceeds_limit(self) -> None:
        self.assertFalse(
            scenario_passes(
                latencies_ms=[100, 2_001], unexpected_errors=0, p95_limit_ms=2_000
            )
        )

    def test_multipart_body_carries_text_file_metadata(self) -> None:
        content_type, body = multipart_body("sample.txt", b"safe payload")
        self.assertIn("multipart/form-data; boundary=", content_type)
        self.assertIn(b'filename="sample.txt"', body)
        self.assertIn(b"safe payload", body)

    def test_parse_levels_rejects_values_above_the_approved_maximum(self) -> None:
        self.assertEqual(parse_levels("1,2,5,10"), [1, 2, 5, 10])
        with self.assertRaises(ValueError):
            parse_levels("1,11")


if __name__ == "__main__":
    unittest.main()

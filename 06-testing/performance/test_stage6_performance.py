import json
import inspect
import unittest
from unittest.mock import patch

from stage6_performance import (
    build_report,
    multipart_body,
    parse_levels,
    percentile,
    request_json,
    scenario_passes,
)


class _Response:
    def __init__(self, body: object) -> None:
        self.status = 200
        self._body = body

    def read(self) -> bytes:
        return json.dumps(self._body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        return None


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

    def test_agent_success_without_a_reference_is_an_invalid_outcome(self) -> None:
        with patch("stage6_performance.urlopen", return_value=_Response({
            "state": "QUESTIONING", "evidence": [], "manual_fallback": True,
        })):
            outcome = request_json(
                base_url="https://example.test", token="token", scenario="agent-success",
                agent_payload={}, expected_reference_text=None,
                expected_document_id=None, expected_chunk_id=None, insecure_tls=True,
            )

        self.assertFalse(outcome.valid)
        self.assertEqual(outcome.error, "agent_contract")

    def test_agent_unavailable_with_a_fabricated_reference_is_an_invalid_outcome(self) -> None:
        with patch("stage6_performance.urlopen", return_value=_Response({
            "state": "UNAVAILABLE", "evidence": [{"citation": "fake", "text": "fake"}],
            "manual_fallback": True,
        })):
            outcome = request_json(
                base_url="https://example.test", token="token", scenario="agent-unavailable",
                agent_payload={}, expected_reference_text=None,
                expected_document_id=None, expected_chunk_id=None, insecure_tls=True,
            )

        self.assertFalse(outcome.valid)
        self.assertEqual(outcome.error, "agent_contract")

    def test_agent_success_with_a_fabricated_reference_not_bound_to_fixture_is_invalid(self) -> None:
        with patch("stage6_performance.urlopen", return_value=_Response({
            "state": "QUESTIONING",
            "evidence": [{"citation": "fake", "text": "generic answer"}],
            "manual_fallback": True,
        })):
            outcome = request_json(
                base_url="https://example.test",
                token="token",
                scenario="agent-success",
                agent_payload={},
                expected_reference_text="TASK005 hydraulic pressure guidance",
                expected_document_id="fixture-document",
                expected_chunk_id="fixture-chunk",
                insecure_tls=True,
            )

        self.assertFalse(outcome.valid)
        self.assertEqual(outcome.error, "agent_contract")

    def test_agent_success_requires_a_fixture_document_and_chunk_pair(self) -> None:
        parameters = inspect.signature(request_json).parameters

        self.assertIn("expected_document_id", parameters)
        self.assertIn("expected_chunk_id", parameters)

    def test_agent_success_with_a_matching_marker_but_fabricated_fixture_ids_is_invalid(self) -> None:
        with patch("stage6_performance.urlopen", return_value=_Response({
            "state": "QUESTIONING",
            "evidence": [{
                "citation": "fixture-chunk",
                "document_id": "fabricated-document",
                "chunk_id": "fabricated-chunk",
                "text": "TASK005 hydraulic pressure guidance",
            }],
            "manual_fallback": True,
        })):
            outcome = request_json(
                base_url="https://example.test",
                token="token",
                scenario="agent-success",
                agent_payload={},
                expected_reference_text="TASK005 hydraulic pressure guidance",
                expected_document_id="fixture-document",
                expected_chunk_id="fixture-chunk",
                insecure_tls=True,
            )

        self.assertFalse(outcome.valid)
        self.assertEqual(outcome.error, "agent_contract")

    def test_report_binds_candidate_environment_fixture_and_harness(self) -> None:
        report = build_report(
            scenario="agent-success",
            levels=[{"concurrency": 10, "pass": True}],
            duration_seconds=300,
            p95_limit_ms=15_000,
            metadata={
                "sut_commit": "a" * 40,
                "harness_commit": "b" * 40,
                "environment": "isolated-compose-success",
                "fixture": "ragflow-dataset:example",
            },
        )

        self.assertEqual(report["metadata"]["sut_commit"], "a" * 40)
        self.assertEqual(report["metadata"]["harness_commit"], "b" * 40)
        self.assertEqual(report["metadata"]["environment"], "isolated-compose-success")
        self.assertEqual(report["metadata"]["fixture"], "ragflow-dataset:example")
        self.assertEqual(report["p95_limit_ms"], 15_000)

    def test_performance_result_records_execution_time_and_evidence_subject(self) -> None:
        with open("results-agent-success-final-v2.json", encoding="utf-8") as handle:
            report = json.load(handle)

        self.assertIn("executed_at_utc", report["metadata"])
        self.assertIn("evidence_subject_commit", report["metadata"])

    def test_recovery_readonly_result_binds_candidate_environment_fixture_and_harness(self) -> None:
        with open("results-backup-restore-readonly.json", encoding="utf-8") as handle:
            report = json.load(handle)

        self.assertEqual(report["scenario"], "auth")
        self.assertEqual(report["max_concurrency"], 10)
        self.assertEqual(report["metadata"]["sut_commit"], "ed0250cad87c8d814a5a2cc5cca8fb5217783064")
        self.assertEqual(report["metadata"]["harness_commit"], "ed0250cad87c8d814a5a2cc5cca8fb5217783064")
        self.assertEqual(report["metadata"]["evidence_subject_commit"], "2980c2041f35d462df563fa2e136445c26a2f2cd")
        self.assertIn("executed_at_utc", report["metadata"])
        self.assertEqual(
            report["metadata"]["fixture"],
            "backup:controlled-api-attachment-1;restore-project:equipment-task011-restore-current9d7d41;readonly:/api/auth/me",
        )


if __name__ == "__main__":
    unittest.main()

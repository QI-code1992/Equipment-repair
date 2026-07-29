import argparse
import base64
from collections import Counter
import json
import ssl
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from math import ceil
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def percentile(values: list[float], value: int) -> float:
    if not values:
        raise ValueError("percentile requires values")
    ordered = sorted(values)
    return ordered[ceil(len(ordered) * value / 100) - 1]


def scenario_passes(
    *, latencies_ms: list[float], unexpected_errors: int, p95_limit_ms: float
) -> bool:
    return bool(latencies_ms) and unexpected_errors == 0 and percentile(
        latencies_ms, 95
    ) <= p95_limit_ms


def parse_levels(value: str) -> list[int]:
    levels = [int(part) for part in value.split(",")]
    if not levels or any(level < 1 or level > 10 for level in levels):
        raise ValueError("concurrency levels must be between 1 and 10")
    return levels


@dataclass(frozen=True)
class Outcome:
    latency_ms: float
    status: int | None
    valid: bool
    error: str | None
    state: str | None = None
    reference_count: int = 0
    fixture_reference_count: int = 0
    manual_fallback: bool | None = None


def multipart_body(filename: str, content: bytes) -> tuple[str, bytes]:
    boundary = f"stage6-{uuid.uuid4().hex}"
    body = b"\r\n".join(
        [
            f"--{boundary}".encode(),
            b'Content-Disposition: form-data; name="file"; filename="' + filename.encode() + b'"',
            b"Content-Type: text/plain",
            b"",
            content,
            f"--{boundary}--".encode(),
            b"",
        ]
    )
    return f"multipart/form-data; boundary={boundary}", body


def request_json(
    *, base_url: str, token: str, scenario: str, agent_payload: dict[str, object] | None,
    expected_reference_text: str | None,
    expected_document_id: str | None,
    expected_chunk_id: str | None,
    insecure_tls: bool = False,
) -> Outcome:
    headers = {"Authorization": f"Bearer {token}"}
    method = "GET"
    path = "/api/auth/me"
    data: bytes | None = None
    if scenario.startswith("agent"):
        method = "POST"
        path = "/api/agent/operation-guidance"
        headers["Content-Type"] = "application/json"
        data = json.dumps(agent_payload).encode("utf-8")
    elif scenario == "attachment":
        method = "POST"
        path = "/api/attachments"
        content_type, data = multipart_body("stage6-performance.txt", b"stage6 safe attachment")
        headers["Content-Type"] = content_type
        headers["Idempotency-Key"] = f"stage6-performance-{uuid.uuid4()}"
    started = time.perf_counter()
    try:
        request = Request(f"{base_url}{path}", method=method, headers=headers, data=data)
        context = ssl._create_unverified_context() if insecure_tls else None
        with urlopen(request, timeout=40, context=context) as response:
            status = response.status
            raw_body = response.read() if scenario.startswith("agent") else None
        if not scenario.startswith("agent"):
            return Outcome(
                (time.perf_counter() - started) * 1_000,
                status,
                status == (201 if scenario == "attachment" else 200),
                None if status == (201 if scenario == "attachment" else 200) else "status",
            )
        try:
            body = json.loads(raw_body)
            if not isinstance(body, dict):
                raise ValueError("agent response is not an object")
            state = body["state"]
            evidence = body["evidence"]
            manual_fallback = body["manual_fallback"]
            if not isinstance(state, str) or not isinstance(evidence, list) or not isinstance(manual_fallback, bool):
                raise ValueError("agent response has invalid fields")
            references_valid = all(
                isinstance(item, dict)
                and isinstance(item.get("citation"), str)
                and bool(item["citation"].strip())
                and isinstance(item.get("text"), str)
                and bool(item["text"].strip())
                and isinstance(item.get("document_id"), str)
                and bool(item["document_id"].strip())
                and isinstance(item.get("chunk_id"), str)
                and bool(item["chunk_id"].strip())
                for item in evidence
            )
            fixture_reference_count = sum(
                1
                for item in evidence
                if expected_reference_text is not None
                and expected_document_id is not None
                and expected_chunk_id is not None
                and isinstance(item, dict)
                and expected_reference_text in str(item.get("text", ""))
                and item.get("document_id") == expected_document_id
                and item.get("chunk_id") == expected_chunk_id
            )
            fixture_bound = (
                bool(evidence)
                and fixture_reference_count == len(evidence)
            )
            expected_state = "UNAVAILABLE" if scenario == "agent-unavailable" else "QUESTIONING"
            expected_evidence = (
                evidence == []
                if scenario == "agent-unavailable"
                else bool(evidence) and references_valid and fixture_bound
            )
            valid = status == 200 and state == expected_state and manual_fallback and expected_evidence
            return Outcome(
                (time.perf_counter() - started) * 1_000,
                status,
                valid,
                None if valid else "agent_contract",
                state,
                len(evidence),
                fixture_reference_count,
                manual_fallback,
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return Outcome(
                (time.perf_counter() - started) * 1_000,
                status,
                False,
                "agent_response",
            )
    except HTTPError as error:
        return Outcome((time.perf_counter() - started) * 1_000, error.code, False, "http")
    except (URLError, TimeoutError, OSError) as error:
        return Outcome((time.perf_counter() - started) * 1_000, None, False, type(error).__name__)


def run_level(
    *, base_url: str, token: str, scenario: str, agent_payload: dict[str, object] | None,
    concurrency: int, duration_seconds: int, p95_limit_ms: int,
    expected_reference_text: str | None,
    expected_document_id: str | None,
    expected_chunk_id: str | None,
    insecure_tls: bool,
) -> dict[str, object]:
    deadline = time.monotonic() + duration_seconds
    outcomes: list[Outcome] = []
    lock = Lock()

    def worker() -> None:
        while time.monotonic() < deadline:
            started = time.perf_counter()
            try:
                outcome = request_json(
                    base_url=base_url, token=token, scenario=scenario,
                    agent_payload=agent_payload,
                    expected_reference_text=expected_reference_text,
                    expected_document_id=expected_document_id,
                    expected_chunk_id=expected_chunk_id,
                    insecure_tls=insecure_tls,
                )
            except Exception as error:
                outcome = Outcome(
                    (time.perf_counter() - started) * 1_000,
                    None,
                    False,
                    f"worker_{type(error).__name__}",
                )
            with lock:
                outcomes.append(outcome)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(worker) for _ in range(concurrency)]
        for future in futures:
            future.result()

    latencies = [item.latency_ms for item in outcomes]
    errors = sum(not item.valid for item in outcomes)
    states = Counter(item.state for item in outcomes if item.state is not None)
    return {
        "concurrency": concurrency,
        "requests": len(outcomes),
        "unexpected_errors": errors,
        "agent_states": dict(states),
        "responses_with_references": sum(item.reference_count > 0 for item in outcomes),
        "responses_without_references": sum(
            item.state is not None and item.reference_count == 0 for item in outcomes
        ),
        "responses_bound_to_fixture": sum(
            item.reference_count > 0
            and item.fixture_reference_count == item.reference_count
            for item in outcomes
        ),
        "responses_without_fixture_reference": sum(
            item.state is not None
            and item.reference_count > 0
            and item.fixture_reference_count != item.reference_count
            for item in outcomes
        ),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "pass": scenario_passes(
            latencies_ms=latencies, unexpected_errors=errors, p95_limit_ms=p95_limit_ms
        ),
    }


def build_report(
    *,
    scenario: str,
    levels: list[dict[str, object]],
    duration_seconds: int,
    p95_limit_ms: int,
    metadata: dict[str, str],
) -> dict[str, object]:
    return {
        "scenario": scenario,
        "metadata": metadata,
        "max_concurrency": max(int(result["concurrency"]) for result in levels),
        "duration_seconds_total": duration_seconds,
        "duration_seconds_per_level": duration_seconds // len(levels),
        "p95_limit_ms": p95_limit_ms,
        "levels": levels,
        "pass": all(bool(result["pass"]) for result in levels),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--scenario", choices=("auth", "attachment", "agent-success", "agent-unavailable"), required=True)
    parser.add_argument("--agent-payload-json")
    parser.add_argument("--agent-payload-base64")
    parser.add_argument("--expected-reference-text")
    parser.add_argument("--expected-document-id")
    parser.add_argument("--expected-chunk-id")
    parser.add_argument("--duration-seconds", type=int, default=300)
    parser.add_argument("--concurrency-levels", default="1,2,5,10")
    parser.add_argument("--p95-limit-ms", type=int, required=True)
    parser.add_argument("--sut-commit", required=True)
    parser.add_argument("--harness-commit", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--insecure-tls", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.scenario == "agent-success" and not all((
        args.expected_reference_text,
        args.expected_document_id,
        args.expected_chunk_id,
    )):
        parser.error(
            "agent-success requires --expected-reference-text, --expected-document-id, and --expected-chunk-id"
        )
    payload_text = args.agent_payload_json
    if args.agent_payload_base64 is not None:
        payload_text = base64.b64decode(args.agent_payload_base64).decode("utf-8")
    payload = None if payload_text is None else json.loads(payload_text)
    levels = parse_levels(args.concurrency_levels)
    level_duration_seconds = max(1, args.duration_seconds // len(levels))
    results = [
        run_level(
            base_url=args.base_url.rstrip("/"), token=args.token, scenario=args.scenario,
            agent_payload=payload, concurrency=level, duration_seconds=level_duration_seconds,
            p95_limit_ms=args.p95_limit_ms,
            expected_reference_text=args.expected_reference_text,
            expected_document_id=args.expected_document_id,
            expected_chunk_id=args.expected_chunk_id,
            insecure_tls=args.insecure_tls,
        )
        for level in levels
    ]
    report = build_report(
        scenario=args.scenario,
        levels=results,
        duration_seconds=args.duration_seconds,
        p95_limit_ms=args.p95_limit_ms,
        metadata={
            "sut_commit": args.sut_commit,
            "harness_commit": args.harness_commit,
            "environment": args.environment,
            "fixture": args.fixture,
            **(
                {"expected_reference_text": args.expected_reference_text}
                if args.expected_reference_text is not None
                else {}
            ),
            **(
                {
                    "expected_document_id": args.expected_document_id,
                    "expected_chunk_id": args.expected_chunk_id,
                }
                if args.expected_document_id is not None and args.expected_chunk_id is not None
                else {}
            ),
        },
    )
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

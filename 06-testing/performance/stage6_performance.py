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
            body = json.loads(response.read()) if scenario.startswith("agent") else None
        state = None if body is None else str(body.get("state"))
        valid = status == (201 if scenario == "attachment" else 200) and (
            not scenario.startswith("agent")
            or body["state"] == ("UNAVAILABLE" if scenario == "agent-unavailable" else "QUESTIONING")
        )
        return Outcome((time.perf_counter() - started) * 1_000, status, valid, None, state)
    except HTTPError as error:
        return Outcome((time.perf_counter() - started) * 1_000, error.code, False, "http")
    except (URLError, TimeoutError, OSError) as error:
        return Outcome((time.perf_counter() - started) * 1_000, None, False, type(error).__name__)


def run_level(
    *, base_url: str, token: str, scenario: str, agent_payload: dict[str, object] | None,
    concurrency: int, duration_seconds: int, p95_limit_ms: int,
    insecure_tls: bool,
) -> dict[str, object]:
    deadline = time.monotonic() + duration_seconds
    outcomes: list[Outcome] = []
    lock = Lock()

    def worker() -> None:
        while time.monotonic() < deadline:
            outcome = request_json(
                base_url=base_url, token=token, scenario=scenario,
                agent_payload=agent_payload,
                insecure_tls=insecure_tls,
            )
            with lock:
                outcomes.append(outcome)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for _ in range(concurrency):
            pool.submit(worker)

    latencies = [item.latency_ms for item in outcomes]
    errors = sum(not item.valid for item in outcomes)
    states = Counter(item.state for item in outcomes if item.state is not None)
    return {
        "concurrency": concurrency,
        "requests": len(outcomes),
        "unexpected_errors": errors,
        "agent_states": dict(states),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "pass": scenario_passes(
            latencies_ms=latencies, unexpected_errors=errors, p95_limit_ms=p95_limit_ms
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--scenario", choices=("auth", "attachment", "agent-success", "agent-unavailable"), required=True)
    parser.add_argument("--agent-payload-json")
    parser.add_argument("--agent-payload-base64")
    parser.add_argument("--duration-seconds", type=int, default=300)
    parser.add_argument("--concurrency-levels", default="1,2,5,10")
    parser.add_argument("--p95-limit-ms", type=int, required=True)
    parser.add_argument("--insecure-tls", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
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
            insecure_tls=args.insecure_tls,
        )
        for level in levels
    ]
    report = {
        "scenario": args.scenario,
        "max_concurrency": max(levels),
        "duration_seconds_total": args.duration_seconds,
        "duration_seconds_per_level": level_duration_seconds,
        "p95_limit_ms": args.p95_limit_ms,
        "levels": results,
        "pass": all(result["pass"] for result in results),
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

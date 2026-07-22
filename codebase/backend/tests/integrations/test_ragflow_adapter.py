import pytest

from app.integrations.ragflow.adapter import (
    KnowledgeDocumentRef,
    RagflowAdapter,
    RagflowError,
)


class FakeTransport:
    def __init__(self, responses: list[dict[str, object] | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def build_adapter(transport: FakeTransport) -> RagflowAdapter:
    return RagflowAdapter(
        base_url="http://ragflow:9380",
        api_key="test-key",
        timeout_seconds=2.0,
        transport=transport,
    )


def test_upload_starts_parsing_and_returns_remote_document_id() -> None:
    transport = FakeTransport(
        [
            {"code": 0, "data": [{"id": "remote-doc", "run": "UNSTART"}]},
            {"code": 0},
        ]
    )

    remote_id = build_adapter(transport).upload_and_parse(
        dataset_id="dataset-1",
        filename="manual.txt",
        content=b"safe operating instructions",
        content_type="text/plain",
    )

    assert remote_id == "remote-doc"
    assert transport.calls[0]["path"] == "/api/v1/datasets/dataset-1/documents"
    assert transport.calls[0]["multipart"]["file"][0] == "manual.txt"
    assert transport.calls[1] == {
        "method": "POST",
        "path": "/api/v1/datasets/dataset-1/chunks",
        "json_body": {"document_ids": ["remote-doc"]},
    }


@pytest.mark.parametrize(
    ("remote_status", "expected"),
    [("UNSTART", "UPLOADING"), ("RUNNING", "PARSING"), ("DONE", "READY")],
)
def test_document_status_maps_ragflow_lifecycle(
    remote_status: str, expected: str
) -> None:
    transport = FakeTransport(
        [{"code": 0, "data": {"docs": [{"id": "remote-doc", "run": remote_status}]}}]
    )

    status = build_adapter(transport).get_document_status("dataset-1", "remote-doc")

    assert status.status == expected
    assert status.failure_reason is None


def test_failed_document_exposes_sanitized_failure_reason() -> None:
    transport = FakeTransport(
        [
            {
                "code": 0,
                "data": {
                    "docs": [
                        {
                            "id": "remote-doc",
                            "run": "FAIL",
                            "progress_msg": "parser rejected malformed PDF",
                        }
                    ]
                },
            }
        ]
    )

    status = build_adapter(transport).get_document_status("dataset-1", "remote-doc")

    assert status.status == "FAILED"
    assert status.failure_reason == "parser rejected malformed PDF"


def test_retrieve_maps_only_ready_business_documents_to_citations() -> None:
    transport = FakeTransport(
        [
            {
                "code": 0,
                "data": {
                    "chunks": [
                        {
                            "id": "chunk-1",
                            "document_id": "remote-ready",
                            "content": "inspect the hydraulic line",
                            "similarity": 0.91,
                        }
                    ]
                },
            }
        ]
    )
    documents = [
        KnowledgeDocumentRef("business-ready", "remote-ready", "READY"),
        KnowledgeDocumentRef("business-failed", "remote-failed", "FAILED"),
    ]

    result = build_adapter(transport).retrieve(
        question="hydraulic inspection",
        dataset_ids=["dataset-1"],
        documents=documents,
        limit=5,
    )

    assert result.unavailable is False
    assert result.no_citation_reason is None
    assert [citation.business_document_id for citation in result.citations] == [
        "business-ready"
    ]
    assert result.citations[0].chunk_id == "chunk-1"
    assert transport.calls[0]["json_body"]["document_ids"] == ["remote-ready"]


def test_empty_retrieval_returns_explicit_no_citation() -> None:
    transport = FakeTransport([{"code": 0, "data": {"chunks": []}}])

    result = build_adapter(transport).retrieve(
        question="unknown",
        dataset_ids=["dataset-1"],
        documents=[KnowledgeDocumentRef("business-1", "remote-1", "READY")],
    )

    assert result.citations == []
    assert result.no_citation_reason == "NO_RETRIEVABLE_EVIDENCE"


def test_timeout_degrades_without_fabricating_citations() -> None:
    transport = FakeTransport([TimeoutError("request timed out")])

    result = build_adapter(transport).retrieve(
        question="inspection",
        dataset_ids=["dataset-1"],
        documents=[KnowledgeDocumentRef("business-1", "remote-1", "READY")],
    )

    assert result.unavailable is True
    assert result.citations == []
    assert result.no_citation_reason == "KNOWLEDGE_SERVICE_UNAVAILABLE"


def test_remote_error_does_not_leak_response_or_api_key() -> None:
    transport = FakeTransport(
        [{"code": 102, "message": "Authorization: Bearer test-key invalid"}]
    )

    with pytest.raises(RagflowError, match="RAGFlow request failed") as exc:
        build_adapter(transport).delete_document("dataset-1", "remote-doc")

    assert "test-key" not in str(exc.value)

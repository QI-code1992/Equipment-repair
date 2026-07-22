from dataclasses import dataclass, field
from typing import Protocol
from urllib.error import URLError
from urllib.parse import quote


class RagflowError(RuntimeError):
    pass


class RagflowTransport(Protocol):
    def request(self, **kwargs: object) -> dict[str, object]: ...


@dataclass(frozen=True)
class KnowledgeDocumentRef:
    business_document_id: str
    ragflow_document_id: str
    status: str


@dataclass(frozen=True)
class DocumentStatus:
    status: str
    failure_reason: str | None = None


@dataclass(frozen=True)
class KnowledgeCitation:
    business_document_id: str
    chunk_id: str
    content: str
    similarity: float | None


@dataclass(frozen=True)
class RetrievalResult:
    citations: list[KnowledgeCitation] = field(default_factory=list)
    no_citation_reason: str | None = None
    unavailable: bool = False


class RagflowAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
        transport: RagflowTransport,
    ) -> None:
        if not base_url or not api_key or timeout_seconds <= 0:
            raise ValueError("valid RAGFlow connection settings are required")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def upload_and_parse(
        self,
        *,
        dataset_id: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> str:
        path = self._documents_path(dataset_id)
        response = self.transport.request(
            method="POST",
            path=path,
            multipart={"file": (filename, content, content_type)},
        )
        data = self._data(response)
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise RagflowError("RAGFlow returned an invalid upload response")
        document_id = data[0].get("id")
        if not isinstance(document_id, str) or not document_id:
            raise RagflowError("RAGFlow returned an invalid document identifier")
        self._data(
            self.transport.request(
                method="POST",
                path=f"/api/v1/datasets/{quote(dataset_id, safe='')}/chunks",
                json_body={"document_ids": [document_id]},
            ),
            allow_missing=True,
        )
        return document_id

    def get_document_status(self, dataset_id: str, document_id: str) -> DocumentStatus:
        response = self.transport.request(
            method="GET",
            path=f"{self._documents_path(dataset_id)}?id={quote(document_id, safe='')}",
        )
        data = self._data(response)
        docs = data.get("docs") if isinstance(data, dict) else None
        if not isinstance(docs, list) or len(docs) != 1 or not isinstance(docs[0], dict):
            raise RagflowError("RAGFlow document was not found")
        remote_status = docs[0].get("run")
        status = {
            "UNSTART": "UPLOADING",
            "RUNNING": "PARSING",
            "DONE": "READY",
            "CANCEL": "FAILED",
            "FAIL": "FAILED",
        }.get(remote_status)
        if status is None:
            raise RagflowError("RAGFlow returned an unknown document status")
        reason = (
            self._failure_reason(docs[0].get("progress_msg"))
            if status == "FAILED"
            else None
        )
        return DocumentStatus(status=status, failure_reason=reason)

    def delete_document(self, dataset_id: str, document_id: str) -> None:
        response = self.transport.request(
            method="DELETE",
            path=self._documents_path(dataset_id),
            json_body={"ids": [document_id]},
        )
        self._data(response, allow_missing=True)

    def retrieve(
        self,
        *,
        question: str,
        dataset_ids: list[str],
        documents: list[KnowledgeDocumentRef],
        limit: int = 10,
    ) -> RetrievalResult:
        ready = {item.ragflow_document_id: item for item in documents if item.status == "READY"}
        if not ready:
            return RetrievalResult(no_citation_reason="NO_RETRIEVABLE_EVIDENCE")
        try:
            response = self.transport.request(
                method="POST",
                path="/api/v1/retrieval",
                json_body={
                    "question": question,
                    "dataset_ids": dataset_ids,
                    "document_ids": list(ready),
                    "page": 1,
                    "page_size": limit,
                    "keyword": True,
                },
            )
            data = self._data(response)
        except (TimeoutError, URLError):
            return RetrievalResult(
                no_citation_reason="KNOWLEDGE_SERVICE_UNAVAILABLE",
                unavailable=True,
            )
        chunks = data.get("chunks") if isinstance(data, dict) else None
        if not isinstance(chunks, list):
            raise RagflowError("RAGFlow returned an invalid retrieval response")
        citations = self._map_citations(chunks, ready)
        if not citations:
            return RetrievalResult(no_citation_reason="NO_RETRIEVABLE_EVIDENCE")
        return RetrievalResult(citations=citations)

    @staticmethod
    def _map_citations(
        chunks: list[object], ready: dict[str, KnowledgeDocumentRef]
    ) -> list[KnowledgeCitation]:
        citations = []
        for chunk in chunks:
            if not isinstance(chunk, dict) or chunk.get("document_id") not in ready:
                continue
            chunk_id, content = chunk.get("id"), chunk.get("content")
            if not isinstance(chunk_id, str) or not isinstance(content, str):
                continue
            document = ready[str(chunk["document_id"])]
            similarity = chunk.get("similarity")
            citations.append(
                KnowledgeCitation(
                    business_document_id=document.business_document_id,
                    chunk_id=chunk_id,
                    content=content,
                    similarity=float(similarity) if isinstance(similarity, int | float) else None,
                )
            )
        return citations

    @staticmethod
    def _data(response: dict[str, object], *, allow_missing: bool = False) -> object:
        if response.get("code") != 0:
            raise RagflowError("RAGFlow request failed")
        if "data" not in response and allow_missing:
            return None
        return response.get("data")

    @staticmethod
    def _failure_reason(value: object) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return "RAGFlow document processing failed"
        return value.strip()[:1000]

    @staticmethod
    def _documents_path(dataset_id: str) -> str:
        return f"/api/v1/datasets/{quote(dataset_id, safe='')}/documents"

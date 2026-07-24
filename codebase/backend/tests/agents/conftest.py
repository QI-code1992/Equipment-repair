import pytest
from fastapi.testclient import TestClient

from tests.modules.support import build_client


@pytest.fixture
def client() -> TestClient:
    return build_client()

import pytest


@pytest.fixture(autouse=True)
def globalgiving_environment(monkeypatch, mock_external_http):
    # Fictitious credential only. Unmatched HTTP is rejected by the shared fixture.
    monkeypatch.setenv("GLOBALGIVING_API_KEY", "test-globalgiving-key")
    yield mock_external_http

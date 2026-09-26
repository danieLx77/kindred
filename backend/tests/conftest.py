import httpx
import pytest
import respx

from main import app


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as test_client:
        yield test_client


@pytest.fixture
def mock_external_http():
    with respx.mock(assert_all_mocked=True) as router:
        yield router

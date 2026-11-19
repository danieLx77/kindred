import asyncio
import logging
import traceback
from collections.abc import AsyncIterator, Awaitable, Callable

import httpx
import pytest

from integrations.globalgiving import GlobalGivingDiscoveryAdapter
from integrations.globalgiving.mapping import summary
from projects.errors import ProviderError, ProviderFailure
from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    OrganizationReference,
    ProjectSummary,
)

BASE = "https://api.globalgiving.org/api/public/"
LIST = BASE + "projectservice/all/projects/summary"
SEARCH = BASE + "services/search/projects"
KEY = "test-globalgiving-key"


@pytest.fixture
async def adapter() -> AsyncIterator[GlobalGivingDiscoveryAdapter]:
    async with GlobalGivingDiscoveryAdapter() as instance:
        yield instance


def listing(projects: object, **metadata: object) -> dict[str, object]:
    return {"projects": {"project": projects, **metadata}}


def search(projects: object, start: int = 0, total: int = 999) -> dict[str, object]:
    return {
        "search": {
            "response": {
                "@start": start,
                "@numberFound": total,
                "projects": {"project": projects},
            }
        }
    }


async def test_browse_two_pages_and_replay(adapter, globalgiving_environment) -> None:
    route = globalgiving_environment.get(LIST).mock(
        side_effect=[
            httpx.Response(
                200, json=listing([{"id": 1}], hasNext=True, nextProjectId=2)
            ),
            httpx.Response(200, json=listing({"id": 2})),
            httpx.Response(200, json=listing({"id": 2})),
        ]
    )
    # Discovery has exactly the callable signature of ProjectProvider.discover.
    discover: Callable[
        [DiscoveryQuery, Continuation | None], Awaitable[DiscoveryResult]
    ] = adapter.discover
    first = await discover(DiscoveryQuery(), None)
    assert first.items == (ProjectSummary(id="1"),)
    assert first.continuation is not None
    second = await discover(DiscoveryQuery(), first.continuation)
    assert second == DiscoveryResult((ProjectSummary(id="2"),))
    assert await adapter.discover(continuation=first.continuation) == second
    assert "nextProjectId" not in route.calls[0].request.url.params
    assert route.calls[1].request.url.params["nextProjectId"] == "2"
    assert all(call.request.url.params["api_key"] == KEY for call in route.calls)
    assert all(
        call.request.headers["accept"] == "application/json" for call in route.calls
    )


async def test_listing_smaller_page_does_not_discard_items(
    adapter, globalgiving_environment
) -> None:
    route = globalgiving_environment.get(LIST).respond(
        200, json=listing([{"id": 1}, {"id": 2}, {"id": 3}])
    )
    query = DiscoveryQuery(page_size=2)
    first = await adapter.discover(query)
    assert [p.id for p in first.items] == ["1", "2"]
    assert first.continuation is not None
    second = await adapter.discover(query, first.continuation)
    assert second == DiscoveryResult((ProjectSummary(id="3"),))
    # Fixed external page is fetched again with an internal skip, not an inferred ID.
    assert route.calls[0].request.url == route.calls[1].request.url


async def test_listing_small_pages_eventually_use_provider_cursor(
    adapter, globalgiving_environment
) -> None:
    route = globalgiving_environment.get(LIST).mock(
        side_effect=[
            httpx.Response(
                200, json=listing([{"id": 1}, {"id": 2}], hasNext=True, nextProjectId=3)
            ),
            httpx.Response(
                200, json=listing([{"id": 1}, {"id": 2}], hasNext=True, nextProjectId=3)
            ),
            httpx.Response(200, json=listing({"id": 3}, hasNext=False)),
        ]
    )
    query = DiscoveryQuery(page_size=1)
    first = await adapter.discover(query)
    second = await adapter.discover(query, first.continuation)
    third = await adapter.discover(query, second.continuation)
    assert [first.items[0].id, second.items[0].id, third.items[0].id] == ["1", "2", "3"]
    assert third.continuation is None
    assert route.calls[2].request.url.params["nextProjectId"] == "3"


async def test_large_page_size_is_upper_bound_not_bulk_fetch(
    adapter, globalgiving_environment
) -> None:
    route = globalgiving_environment.get(LIST).respond(
        200, json=listing([{"id": i} for i in range(1, 11)])
    )
    result = await adapter.discover(DiscoveryQuery(page_size=50))
    assert len(result.items) == 10
    assert route.call_count == 1
    assert result.continuation is None


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_no_query_browses(adapter, globalgiving_environment, text) -> None:
    route = globalgiving_environment.get(LIST).respond(200, json=listing([]))
    assert await adapter.discover(DiscoveryQuery(text=text)) == DiscoveryResult()
    assert "q" not in route.calls.last.request.url.params


async def test_search_encoding_plural_route_and_unreliable_total(
    adapter, globalgiving_environment
) -> None:
    route = globalgiving_environment.get(SEARCH).mock(
        side_effect=[
            httpx.Response(200, json=search([{"id": 1}, {"id": 2}], total=2)),
            httpx.Response(200, json=search({"id": 3}, start=2, total=2)),
            httpx.Response(200, json={"search": {"response": {}}}),
        ]
    )
    query = DiscoveryQuery(text="educação & água + saúde/BR?")
    first = await adapter.discover(query)
    assert first.continuation is not None
    second = await adapter.discover(query, first.continuation)
    assert second.items == (ProjectSummary(id="3"),)
    assert second.continuation is not None
    assert await adapter.discover(query, second.continuation) == DiscoveryResult()
    assert [call.request.url.params["start"] for call in route.calls] == ["0", "2", "3"]
    assert all(call.request.url.params["q"] == query.text for call in route.calls)
    assert all(" " not in str(call.request.url) for call in route.calls)


async def test_search_small_page_advances_by_consumed_items(
    adapter, globalgiving_environment
) -> None:
    route = globalgiving_environment.get(SEARCH).mock(
        side_effect=[
            httpx.Response(200, json=search([{"id": 1}, {"id": 2}])),
            httpx.Response(200, json=search({"id": 2}, start=1)),
        ]
    )
    query = DiscoveryQuery(text="water", page_size=1)
    first = await adapter.discover(query)
    second = await adapter.discover(query, first.continuation)
    assert [first.items[0].id, second.items[0].id] == ["1", "2"]
    assert route.calls.last.request.url.params["start"] == "1"


@pytest.mark.parametrize(
    "body",
    [
        {"search": {"response": {}}},
        {"search": {"response": {"@numberFound": 0}}},
        {"search": {"response": {"projects": None}}},
        {"search": {"response": {"projects": {}}}},
        search([]),
        search(None),
    ],
)
async def test_valid_empty_search(adapter, globalgiving_environment, body) -> None:
    globalgiving_environment.get(SEARCH).respond(200, json=body)
    assert await adapter.discover(DiscoveryQuery(text="unknown")) == DiscoveryResult()


@pytest.mark.parametrize("body", [{"projects": {}}, listing([]), listing(None)])
async def test_valid_empty_listing(adapter, globalgiving_environment, body) -> None:
    globalgiving_environment.get(LIST).respond(200, json=body)
    assert await adapter.discover() == DiscoveryResult()


def test_mapping_uses_only_needed_fields_and_real_organization() -> None:
    result = summary(
        {
            "id": 123,
            "title": " Real project ",
            "summary": "Summary",
            "imageLink": "https://example.org/image.jpg",
            "themeName": "Education",
            "country": "Brazil",
            "organization": {
                "id": 456,
                "name": "Teachers",
                "url": "https://example.org",
            },
            "funding": 100,
            "goal": 90,
            "unknown": {"ignored": True},
        }
    )
    assert result == ProjectSummary(
        id="123",
        title="Real project",
        summary="Summary",
        image_url="https://example.org/image.jpg",
        theme="Education",
        country="Brazil",
        organization=OrganizationReference("456", "Teachers", "https://example.org"),
    )


@pytest.mark.parametrize(
    "organization", [None, {}, [], "invalid", {"name": "No ID"}, {"id": False}]
)
def test_partial_mapping_never_fabricates_organization(organization) -> None:
    assert summary(
        {
            "id": "123",
            "organization": organization,
            "title": None,
            "summary": {},
            "imageLink": "javascript:alert(1)",
            "themeName": [],
            "country": 42,
        }
    ) == ProjectSummary(id="123")


def test_organization_with_only_id_remains_usable() -> None:
    assert summary(
        {"id": 1, "organization": {"id": "2"}}
    ).organization == OrganizationReference("2")


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@example.org/a",
        "//example.org/a",
        "https://[",
        "https://example.org:bad",
        "https://example.org/a b",
        "",
        "data:image/png;base64,abc",
    ],
)
def test_invalid_optional_urls_are_omitted(url) -> None:
    assert summary({"id": 1, "imageLink": url}).image_url is None


@pytest.mark.parametrize("project_id", [None, 0, -1, True, 1.5, "", "abc", {}, []])
def test_invalid_required_id_is_not_fabricated(project_id) -> None:
    with pytest.raises(ProviderError) as error:
        summary({"id": project_id})
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE


@pytest.mark.parametrize(
    "body",
    [
        {},
        [],
        None,
        {"projects": None},
        {"projects": []},
        {"projects": {"wrong": []}},
        listing("wrong"),
        listing([None]),
        listing([{}]),
        listing([{"id": 1}, {"id": 1}]),
        listing([], hasNext=True, nextProjectId=1),
        listing({"id": 1}, hasNext=True),
        listing({"id": 1}, hasNext="yes"),
        listing({"id": 1}, hasNext=1),
        listing({"id": 1}, hasNext=1.0),
        listing([{"id": i} for i in range(1, 12)]),
    ],
)
async def test_invalid_listing_is_not_empty(
    adapter, globalgiving_environment, body
) -> None:
    globalgiving_environment.get(LIST).respond(200, json=body)
    with pytest.raises(ProviderError) as error:
        await adapter.discover()
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"search": {}},
        {"search": {"response": []}},
        search("wrong"),
        {"search": {"response": {"projects": {"wrong": []}}}},
        search([], start=99),
    ],
)
async def test_invalid_search_is_not_empty(
    adapter, globalgiving_environment, body
) -> None:
    globalgiving_environment.get(SEARCH).respond(200, json=body)
    with pytest.raises(ProviderError) as error:
        await adapter.discover(DiscoveryQuery(text="water"))
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE


@pytest.mark.parametrize(
    "status,reason",
    [
        (400, ProviderFailure.INVALID_REQUEST),
        (401, ProviderFailure.AUTHENTICATION),
        (403, ProviderFailure.AUTHENTICATION),
        (404, ProviderFailure.NOT_FOUND),
        (410, ProviderFailure.UNAVAILABLE),
        (429, ProviderFailure.RATE_LIMITED),
        (500, ProviderFailure.UNAVAILABLE),
        (503, ProviderFailure.UNAVAILABLE),
        (302, ProviderFailure.UNAVAILABLE),
    ],
)
async def test_http_errors_sanitized_without_retry_or_redirect(
    adapter, globalgiving_environment, status, reason, caplog
) -> None:
    route = globalgiving_environment.get(LIST).respond(
        status,
        text=f"secret echoed: {KEY}",
        headers={"Location": f"https://evil.example/?api_key={KEY}"},
    )
    with caplog.at_level(logging.DEBUG), pytest.raises(ProviderError) as error:
        await adapter.discover()
    assert error.value.reason is reason
    assert route.call_count == 1
    assert KEY not in str(error.value)
    assert KEY not in "".join(traceback.format_exception(error.value))
    assert KEY not in caplog.text


@pytest.mark.parametrize(
    "exception,reason",
    [
        (httpx.ReadTimeout, ProviderFailure.TIMEOUT),
        (httpx.ConnectTimeout, ProviderFailure.TIMEOUT),
        (httpx.ConnectError, ProviderFailure.NETWORK),
        (httpx.ReadError, ProviderFailure.NETWORK),
        (httpx.DecodingError, ProviderFailure.INVALID_RESPONSE),
    ],
)
async def test_transport_errors_sanitized(
    adapter, globalgiving_environment, exception, reason, caplog
) -> None:
    def fail(request):
        raise exception(f"secret URL {request.url}", request=request)

    globalgiving_environment.get(LIST).mock(side_effect=fail)
    with caplog.at_level(logging.DEBUG), pytest.raises(ProviderError) as error:
        await adapter.discover()
    assert error.value.reason is reason
    assert KEY not in "".join(traceback.format_exception(error.value))
    assert KEY not in caplog.text


@pytest.mark.parametrize(
    "body", [b"not json", b'{"secret": "test-globalgiving-key"', b"\xff\xfeinvalid"]
)
async def test_invalid_json_sanitized(adapter, globalgiving_environment, body) -> None:
    globalgiving_environment.get(LIST).respond(200, content=body)
    with pytest.raises(ProviderError) as error:
        await adapter.discover()
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE
    assert KEY not in "".join(traceback.format_exception(error.value))


async def test_response_size_is_bounded(adapter, globalgiving_environment) -> None:
    globalgiving_environment.get(LIST).respond(
        200, content=b" " * (2 * 1024 * 1024 + 1)
    )
    with pytest.raises(ProviderError) as error:
        await adapter.discover()
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE


async def test_overall_deadline() -> None:
    entered = asyncio.Event()

    async def slow(request):
        entered.set()
        await asyncio.sleep(0.1)
        return httpx.Response(200, json=listing([]))

    async with GlobalGivingDiscoveryAdapter(
        timeout=0.01, transport=httpx.MockTransport(slow)
    ) as instance:
        with pytest.raises(ProviderError) as error:
            await instance.discover()
    assert error.value.reason is ProviderFailure.TIMEOUT
    assert entered.is_set()


async def test_continuation_bound_to_instance_query_size_and_mode(
    adapter, globalgiving_environment
) -> None:
    route = globalgiving_environment.get(LIST).respond(
        200, json=listing({"id": 1}, hasNext=True, nextProjectId=2)
    )
    first = await adapter.discover()
    assert first.continuation is not None
    for query in [DiscoveryQuery(text="water"), DiscoveryQuery(page_size=1)]:
        with pytest.raises(ValueError, match="continuation"):
            await adapter.discover(query, first.continuation)
    async with GlobalGivingDiscoveryAdapter() as other:
        with pytest.raises(ValueError, match="continuation"):
            await other.discover(continuation=first.continuation)
    for token in ["invalid", "", first.continuation.token[:-2] + "xx", "x" * 4097]:
        with pytest.raises(ValueError, match="continuation"):
            await adapter.discover(continuation=Continuation(token))
    assert route.call_count == 1


async def test_nonadvancing_listing_cursor_rejected(
    adapter, globalgiving_environment
) -> None:
    globalgiving_environment.get(LIST).respond(
        200, json=listing({"id": 1}, hasNext=True, nextProjectId=2)
    )
    first = await adapter.discover()
    with pytest.raises(ProviderError) as error:
        await adapter.discover(continuation=first.continuation)
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE


@pytest.mark.parametrize(
    "query", [DiscoveryQuery(theme="Education"), DiscoveryQuery(country="Brazil")]
)
async def test_filters_rejected_not_silently_ignored(adapter, query) -> None:
    with pytest.raises(ValueError, match="filters"):
        await adapter.discover(query)


@pytest.mark.parametrize(
    "base_url",
    [
        "http://api.example/",
        "https://user:pass@api.example/",
        "https://api.example/?api_key=bad",
        "https://api.example/#fragment",
    ],
)
def test_unsafe_configuration_rejected(base_url) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        GlobalGivingDiscoveryAdapter(base_url=base_url)


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_timeout_rejected(timeout) -> None:
    with pytest.raises(ValueError, match="timeout"):
        GlobalGivingDiscoveryAdapter(timeout=timeout)


def test_missing_backend_key(monkeypatch) -> None:
    monkeypatch.delenv("GLOBALGIVING_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GLOBALGIVING_API_KEY"):
        GlobalGivingDiscoveryAdapter()


async def test_http_library_logging_scoped_to_adapter(
    adapter, globalgiving_environment, caplog
) -> None:
    async def respond(request):
        for name in [
            "httpx",
            "httpcore.connection",
            "httpcore.http11",
            "httpcore.http_proxy",
        ]:
            logging.getLogger(name).debug("credential-bearing trace %s", request.url)
        return httpx.Response(200, json=listing([]))

    globalgiving_environment.get(LIST).mock(side_effect=respond)
    globalgiving_environment.get("https://unrelated.example/").respond(200)
    with caplog.at_level(logging.DEBUG):
        async with httpx.AsyncClient() as unrelated:
            await asyncio.gather(
                adapter.discover(), unrelated.get("https://unrelated.example/")
            )
        logging.getLogger("httpx").info("after request")
    assert KEY not in caplog.text
    assert "api_key" not in caplog.text
    assert "unrelated.example" in caplog.text
    assert "after request" in caplog.text


async def test_owned_client_transport_closed() -> None:
    class Transport(httpx.AsyncBaseTransport):
        closed = False

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            assert request.extensions["timeout"]["read"] == 10.0
            return httpx.Response(200, json=listing([]))

        async def aclose(self) -> None:
            self.closed = True

    transport = Transport()
    async with GlobalGivingDiscoveryAdapter(
        transport=transport, base_url="https://test.example/api/"
    ) as instance:
        assert await instance.discover() == DiscoveryResult()
    assert transport.closed


@pytest.mark.parametrize("status", [200, 503])
async def test_response_stream_closed_even_on_failure(status) -> None:
    class Stream(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            yield b"not json"

        async def aclose(self) -> None:
            self.closed = True

    stream = Stream()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, stream=stream)
    )
    async with GlobalGivingDiscoveryAdapter(transport=transport) as instance:
        with pytest.raises(ProviderError):
            await instance.discover()
    assert stream.closed


async def test_cancelled_request_remains_cancelled(caplog) -> None:
    entered = asyncio.Event()

    async def pending(request):
        entered.set()
        await asyncio.Event().wait()
        return httpx.Response(200, json=listing([]))

    async with GlobalGivingDiscoveryAdapter(
        transport=httpx.MockTransport(pending)
    ) as instance:
        task = asyncio.create_task(instance.discover())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    with caplog.at_level(logging.INFO):
        logging.getLogger("httpx").info("logging after cancellation")
    assert "logging after cancellation" in caplog.text


async def test_changed_listing_cannot_silently_skip_past_page(
    adapter, globalgiving_environment
) -> None:
    globalgiving_environment.get(LIST).mock(
        side_effect=[
            httpx.Response(200, json=listing([{"id": 1}, {"id": 2}])),
            httpx.Response(200, json=listing([{"id": 1}])),
        ]
    )
    query = DiscoveryQuery(page_size=1)
    first = await adapter.discover(query)
    with pytest.raises(ProviderError) as error:
        await adapter.discover(query, first.continuation)
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE


async def test_deeply_nested_json_is_controlled(
    adapter, globalgiving_environment
) -> None:
    globalgiving_environment.get(LIST).respond(200, content=b"[" * 2000 + b"]" * 2000)
    with pytest.raises(ProviderError) as error:
        await adapter.discover()
    assert error.value.reason is ProviderFailure.INVALID_RESPONSE

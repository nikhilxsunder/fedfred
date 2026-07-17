# filepath: /tests/_internals_tests/_transport_test.py
#
# Copyright (c) 2026 Nikhil Sunder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio

import httpx
import orjson
import pytest
from cachetools.keys import hashkey

import fedfred._internals._transport as transport
from fedfred._core._specs import EndpointSpec
from fedfred._internals._caching import _CACHE
from fedfred.exceptions import (
    ConnectTimeoutError,
    HTTPClientError,
    HTTPServerError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    RequestPreparationError,
    ResponseDecodingError,
    TransportConnectionError,
    TransportError,
    TransportReadError,
    TransportRequestError,
    UnexpectedHTTPStatusError,
)

_REQ = httpx.Request("GET", "https://api.stlouisfed.org/x")


class _FakeResp:
    """Minimal stand-in for httpx.Response: content bytes + raise_for_status."""

    def __init__(self, content=b'{"ok": true}', raise_exc=None):
        self.content = content
        self._raise = raise_exc

    def raise_for_status(self):
        if self._raise is not None:
            raise self._raise


def _status_error(code, text="body"):
    resp = httpx.Response(code, request=_REQ, text=text)
    return httpx.HTTPStatusError("m", request=_REQ, response=resp)


# --------------------------------------------------------------------------- #
# exception detail extractors                                                  #
# --------------------------------------------------------------------------- #
def test_request_url():
    assert transport._request_url(httpx.ConnectError("b", request=_REQ)) == "https://api.stlouisfed.org/x"

    class Bare(Exception):
        pass

    assert transport._request_url(Bare()) is None    # no `request` attribute


def test_request_method():
    assert transport._request_method(httpx.ConnectError("b", request=_REQ)) == "GET"

    class Bare(Exception):
        pass

    assert transport._request_method(Bare()) is None


def test_safe_response_text():
    assert transport._safe_response_text(_status_error(404, "Not Found")) == "Not Found"

    # no `.response` -> AttributeError swallowed -> None
    class Bare(Exception):
        pass

    assert transport._safe_response_text(Bare()) is None

    # undecodable body -> UnicodeDecodeError swallowed -> None
    class Undecodable(Exception):
        class _R:
            @property
            def text(self):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "bad")

        response = _R()

    assert transport._safe_response_text(Undecodable()) is None


def test_map_http_status_error():
    err = transport._map_http_status_error(_status_error(404, "body"))
    assert isinstance(err, NotFoundError)
    assert err.status_code == 404
    assert err.url == "https://api.stlouisfed.org/x"
    assert err.method == "GET"
    assert err.response_text == "body"

    assert isinstance(transport._map_http_status_error(_status_error(429)), RateLimitError)
    assert isinstance(transport._map_http_status_error(_status_error(500)), InternalServerError)
    # unmapped 4xx / 5xx / other -> family fallbacks
    assert isinstance(transport._map_http_status_error(_status_error(418)), HTTPClientError)
    assert isinstance(transport._map_http_status_error(_status_error(599)), HTTPServerError)
    assert isinstance(transport._map_http_status_error(_status_error(302)), UnexpectedHTTPStatusError)


def test_resolve_httpx_exception_class():
    # exact class in the map
    assert transport._resolve_httpx_exception_class(httpx.ConnectTimeout("t", request=_REQ)) is ConnectTimeoutError
    assert transport._resolve_httpx_exception_class(httpx.ReadError("r", request=_REQ)) is TransportReadError
    # MRO walk: CloseError -> NetworkError -> TransportError -> RequestError (mapped)
    assert transport._resolve_httpx_exception_class(httpx.CloseError("c", request=_REQ)) is TransportRequestError
    # nothing in the MRO is mapped -> TransportError fallback
    assert transport._resolve_httpx_exception_class(httpx.HTTPError("x")) is TransportError


def test_map_httpx_exception():
    # status error routes to the status mapper
    assert isinstance(transport._map_httpx_exception(_status_error(404)), NotFoundError)
    # request error routes to the class resolver, carrying url/method
    mapped = transport._map_httpx_exception(httpx.ConnectTimeout("t", request=_REQ))
    assert isinstance(mapped, ConnectTimeoutError)
    assert mapped.url == "https://api.stlouisfed.org/x"
    assert mapped.method == "GET"


# --------------------------------------------------------------------------- #
# cache key                                                                    #
# --------------------------------------------------------------------------- #
def test_request_cache_key(monkeypatch):
    spec = EndpointSpec(service="fred", url="https://api.stlouisfed.org/fred/x")
    monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)

    key = transport._request_cache_key("fred", "get_x", (("a", "b"),), "PI")
    assert key == hashkey("https://api.stlouisfed.org/fred/x", (("a", "b"),), "PI")

    # unresolvable endpoint -> RequestPreparationError (during key computation)
    def _boom(s, e):
        raise ValueError("no endpoint")

    monkeypatch.setattr(transport, "_resolve_endpoint", _boom)
    with pytest.raises(RequestPreparationError) as exc:
        transport._request_cache_key("fred", "bad")
    assert isinstance(exc.value.__cause__, ValueError)


# --------------------------------------------------------------------------- #
# async client lifecycle                                                       #
# --------------------------------------------------------------------------- #
def test_get_async_client():
    transport._ASYNC_CLIENT_STATE = None

    # outside a running loop -> RuntimeError
    with pytest.raises(RuntimeError):
        transport._get_async_client()

    async def _inner():
        transport._ASYNC_CLIENT_STATE = None
        c1 = transport._get_async_client()
        assert isinstance(c1, httpx.AsyncClient)
        assert transport._get_async_client() is c1          # same loop -> cached
        await c1.aclose()
        c3 = transport._get_async_client()                  # cached client closed -> new
        assert c3 is not c1
        await transport._aclose_async_client()

    asyncio.run(_inner())


def test_aclose_async_client():
    async def _inner():
        transport._ASYNC_CLIENT_STATE = None
        c = transport._get_async_client()
        assert not c.is_closed
        await transport._aclose_async_client()
        assert transport._ASYNC_CLIENT_STATE is None
        assert c.is_closed
        await transport._aclose_async_client()              # idempotent no-op

    asyncio.run(_inner())


# --------------------------------------------------------------------------- #
# translating context manager                                                  #
# --------------------------------------------------------------------------- #
def test_translating_httpx():
    # clean pass-through
    with transport._translating_httpx("u", "GET"):
        pass

    # httpx error -> mapped transport error
    with pytest.raises(TransportConnectionError):
        with transport._translating_httpx("u", "GET"):
            raise httpx.ConnectError("boom", request=_REQ)

    # ValueError (e.g. JSON decode) -> ResponseDecodingError
    with pytest.raises(ResponseDecodingError) as exc:
        with transport._translating_httpx("u", "GET"):
            raise ValueError("bad json")
    assert isinstance(exc.value.__cause__, ValueError)


# --------------------------------------------------------------------------- #
# single-request send paths                                                    #
# --------------------------------------------------------------------------- #
def test_request_sync(monkeypatch):
    spec = EndpointSpec(service="fred", url="https://x", headers={"H": "v"})
    calls = {}

    def _fake(method, url, params=None, content=None, headers=None, timeout=None):
        calls.update(method=method, url=url, params=params, headers=headers)
        return _FakeResp()

    monkeypatch.setattr(transport._HTTP_CLIENT, "request", _fake)
    assert transport._request_sync(spec, "https://x/y", "GET", params={"p": "1"}) == {"ok": True}
    assert calls["method"] == "GET"
    assert calls["url"] == "https://x/y"
    assert calls["params"] == {"p": "1"}
    assert calls["headers"] == {"H": "v"}

    # spec with no headers -> headers kwarg is None
    transport._request_sync(EndpointSpec(service="fred", url="https://x"), "https://x", "GET")
    assert calls["headers"] is None

    # HTTP status error -> mapped
    monkeypatch.setattr(transport._HTTP_CLIENT, "request", lambda *a, **k: _FakeResp(raise_exc=_status_error(404)))
    with pytest.raises(NotFoundError):
        transport._request_sync(spec, "https://x", "GET")

    # undecodable body -> ResponseDecodingError
    monkeypatch.setattr(transport._HTTP_CLIENT, "request", lambda *a, **k: _FakeResp(content=b"not json"))
    with pytest.raises(ResponseDecodingError):
        transport._request_sync(spec, "https://x", "GET")

    # send-time transport error -> mapped
    def _send_err(*a, **k):
        raise httpx.ConnectError("boom", request=_REQ)

    monkeypatch.setattr(transport._HTTP_CLIENT, "request", _send_err)
    with pytest.raises(TransportConnectionError):
        transport._request_sync(spec, "https://x", "GET")


def test_request_async(monkeypatch):
    spec = EndpointSpec(service="fred", url="https://x", headers={"H": "v"})
    calls = {}

    class _FakeClient:
        def __init__(self, resp=None, exc=None):
            self._resp, self._exc = resp, exc

        async def request(self, method, url, params=None, content=None, headers=None, timeout=None):
            calls.update(method=method, url=url, params=params, headers=headers)
            if self._exc is not None:
                raise self._exc
            return self._resp

    async def _inner():
        monkeypatch.setattr(transport, "_get_async_client", lambda: _FakeClient(resp=_FakeResp()))
        assert await transport._request_async(spec, "https://x/y", "GET", params={"p": "1"}) == {"ok": True}
        assert calls["headers"] == {"H": "v"}

        monkeypatch.setattr(transport, "_get_async_client", lambda: _FakeClient(resp=_FakeResp(raise_exc=_status_error(404))))
        with pytest.raises(NotFoundError):
            await transport._request_async(spec, "https://x", "GET")

        monkeypatch.setattr(transport, "_get_async_client", lambda: _FakeClient(resp=_FakeResp(content=b"nope")))
        with pytest.raises(ResponseDecodingError):
            await transport._request_async(spec, "https://x", "GET")

        monkeypatch.setattr(transport, "_get_async_client", lambda: _FakeClient(exc=httpx.ConnectError("b", request=_REQ)))
        with pytest.raises(TransportConnectionError):
            await transport._request_async(spec, "https://x", "GET")

    asyncio.run(_inner())


# --------------------------------------------------------------------------- #
# GET/POST entry points                                                        #
# --------------------------------------------------------------------------- #
def test_get_request(monkeypatch):
    spec = EndpointSpec(service="fred", url="https://x/{}", params={"file_type": "json"})
    captured = {}
    monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)
    monkeypatch.setattr(transport, "_resolve_preparation_function", lambda data, service: {"series_id": "GDP"})
    monkeypatch.setattr(transport, "_rate_limiter", lambda s: captured.__setitem__("rl", s))

    def _fake_sync(spec_, url, method, params=None, content=None):
        captured.update(url=url, method=method, params=params)
        return {"result": 1}

    monkeypatch.setattr(transport, "_request_sync", _fake_sync)

    # no path_injection -> raw url; spec defaults merged under prepared params
    assert transport._get_request("fred", "get_x", {"series_id": "GDP"}) == {"result": 1}
    assert captured["method"] == "GET"
    assert captured["url"] == "https://x/{}"
    assert captured["params"] == {"file_type": "json", "series_id": "GDP"}
    assert captured["rl"] == "fred"

    # path_injection -> url formatted
    transport._get_request("fred", "get_x", None, "TITLE")
    assert captured["url"] == "https://x/TITLE"


def test_post_request(monkeypatch):
    spec = EndpointSpec(
        service="fraser", url="https://x", auth="api_key_header",
        payload={"format": "json"}, headers={"Authorization": "k"},
    )
    captured = {}
    monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)
    monkeypatch.setattr(transport, "_rate_limiter", lambda s: captured.__setitem__("rl", s))

    def _fake_sync(spec_, url, method, params=None, content=None):
        captured.update(url=url, method=method, content=content)
        return {"ok": 1}

    monkeypatch.setattr(transport, "_request_sync", _fake_sync)

    assert transport._post_request("fraser", "post_key_request", {"role": "creator"}) == {"ok": 1}
    assert captured["method"] == "POST"
    assert captured["url"] == "https://x"
    assert orjson.loads(captured["content"]) == {"format": "json", "role": "creator"}
    assert captured["rl"] == "fraser"


def test_get_request_async(monkeypatch):
    spec = EndpointSpec(service="fred", url="https://x/{}", params={"file_type": "json"})
    captured = {}

    async def _fake_rl(s):
        captured["rl"] = s

    async def _fake_async(spec_, url, method, params=None, content=None):
        captured.update(url=url, method=method, params=params)
        return {"result": 1}

    async def _inner():
        monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)
        monkeypatch.setattr(transport, "_resolve_preparation_function", lambda data, service: {"series_id": "GDP"})
        monkeypatch.setattr(transport, "_rate_limiter_async", _fake_rl)
        monkeypatch.setattr(transport, "_request_async", _fake_async)

        assert await transport._get_request_async("fred", "get_x", {"series_id": "GDP"}) == {"result": 1}
        assert captured["method"] == "GET"
        assert captured["url"] == "https://x/{}"
        assert captured["params"] == {"file_type": "json", "series_id": "GDP"}
        assert captured["rl"] == "fred"

        await transport._get_request_async("fred", "get_x", None, "TITLE")
        assert captured["url"] == "https://x/TITLE"

    asyncio.run(_inner())


def test_post_request_async(monkeypatch):
    spec = EndpointSpec(service="fraser", url="https://x", auth="api_key_header", payload={"format": "json"})
    captured = {}

    async def _fake_rl(s):
        captured["rl"] = s

    async def _fake_async(spec_, url, method, params=None, content=None):
        captured.update(url=url, method=method, content=content)
        return {"ok": 1}

    async def _inner():
        monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)
        monkeypatch.setattr(transport, "_rate_limiter_async", _fake_rl)
        monkeypatch.setattr(transport, "_request_async", _fake_async)

        assert await transport._post_request_async("fraser", "post_key_request", {"role": "creator"}) == {"ok": 1}
        assert captured["method"] == "POST"
        assert captured["url"] == "https://x"
        assert orjson.loads(captured["content"]) == {"format": "json", "role": "creator"}
        assert captured["rl"] == "fraser"

    asyncio.run(_inner())


# --------------------------------------------------------------------------- #
# cached wrappers                                                              #
# --------------------------------------------------------------------------- #
def test_cached_get_request(monkeypatch):
    _CACHE.clear()
    spec = EndpointSpec(service="fred", url="https://x/cachetest")
    monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)   # used by the key function

    counter = {"n": 0}

    def _fake_get(service, endpoint, data, path_injection):
        counter["n"] += 1
        return {"call": counter["n"], "data": data}

    monkeypatch.setattr(transport, "_get_request", _fake_get)

    hd = (("series_id", "GDP"),)
    r1 = transport._cached_get_request("fred", "get_x", hd)
    r2 = transport._cached_get_request("fred", "get_x", hd)
    assert counter["n"] == 1                       # second call served from cache
    assert r1 is r2
    assert r1["data"] == {"series_id": "GDP"}      # hashable_data decoded to a dict

    # different params -> distinct key -> underlying invoked again
    transport._cached_get_request("fred", "get_x", (("series_id", "CPI"),))
    assert counter["n"] == 2
    _CACHE.clear()


def test_cached_get_request_async(monkeypatch):
    _CACHE.clear()
    spec = EndpointSpec(service="fred", url="https://x/cachetest_async")
    counter = {"n": 0}

    async def _fake_get(service, endpoint, data, path_injection):
        counter["n"] += 1
        return {"call": counter["n"], "data": data}

    async def _inner():
        monkeypatch.setattr(transport, "_resolve_endpoint", lambda s, e: spec)
        monkeypatch.setattr(transport, "_get_request_async", _fake_get)

        hd = (("series_id", "GDP"),)
        r1 = await transport._cached_get_request_async("fred", "get_x", hd)
        r2 = await transport._cached_get_request_async("fred", "get_x", hd)
        assert counter["n"] == 1
        assert r1["data"] == {"series_id": "GDP"}
        await transport._cached_get_request_async("fred", "get_x", (("series_id", "CPI"),))
        assert counter["n"] == 2

    asyncio.run(_inner())
    _CACHE.clear()
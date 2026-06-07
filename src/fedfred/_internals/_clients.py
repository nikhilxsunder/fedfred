# filepath: /src/fedfred/_internals/_clients.py
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
"""Internal scaffolding for the fedfred client hierarchy.

This module defines the abstract bases that the public client classes in
:mod:`fedfred.clients` inherit from. The hierarchy has one shared root and
two sync/async specializations::

    _ClientModel                            — config, identity, cache-protocol surface
    ├── _BaseClient                         — synchronous transport + context manager
    └── _AsyncBaseClient                    — asynchronous transport + async context manager

:class:`_ClientModel` carries everything common to both flavours: API-key
resolution, caching configuration, identity (:meth:`__repr__`, :meth:`__str__`,
:meth:`__eq__`, :meth:`__hash__`), and the dict-like cache-inspection surface
(:meth:`__len__`, :meth:`__contains__`, :meth:`__getitem__`,
:attr:`_ClientModel.keys`). It is also the structural type that response
model objects type their ``client`` attribute against, since either flavour
of client may be attached.

:class:`_BaseClient` and :class:`_AsyncBaseClient` add the transport layer
appropriate to their concurrency mode: a synchronous or asynchronous context
manager (forward-compatible seam for per-instance connection pooling, currently
a no-op) and a ``_client_get_request`` private helper that dispatches through
the module-global cache when ``caching_enabled`` is set, or straight through
to the rate-limited transport when it is not.

Classes:
    _ClientModel: Root base for sync and async FRED-family clients.
    _BaseClient: Synchronous client base.
    _AsyncBaseClient: Asynchronous client base.

Notes:
    All classes in this module are private internals. The names are exported
    only so the public client modules can subclass them; downstream users
    should depend on the concrete clients (``Fred``, ``Alfred``, ``Fraser``,
    ``AsyncFred``, ``AsyncAlfred``, ``AsyncFraser``).
"""

from collections.abc import Callable, KeysView
from types import NotImplementedType, TracebackType
from typing import Any, cast

from .._core import _hashable_type_converter
from ..settings import Service, _resolve_api_key, set_api_key
from ._caching import _retrieve_cache_instance, get_cache_maxsize, set_cache_maxsize
from ._transport import (
    _cached_get_request,
    _cached_get_request_async,
    _get_request,
    _get_request_async,
    _post_request,
    _post_request_async,
)

# TODO: Fix all docstrings post error design.

__all__ = [
    "_AsyncBaseClient",
    "_BaseClient",
    "_ClientModel",
]


class _ClientModel:
    """Root base for synchronous and asynchronous FRED-family clients.

    Provides everything common to both flavours: API-key resolution
    delegated to :mod:`fedfred.settings`, caching configuration delegated
    to :mod:`fedfred._internals._caching`, identity protocols
    (:meth:`__repr__`, :meth:`__str__`, :meth:`__eq__`, :meth:`__hash__`),
    and a dict-like cache-inspection surface (:meth:`__len__`,
    :meth:`__contains__`, :meth:`__getitem__`, :attr:`keys`).

    Concrete subclasses declare the four class variables below to describe
    the underlying service. Instances should never be constructed directly;
    use :class:`fedfred.Fred`, :class:`fedfred.Alfred`,
    :class:`fedfred.Fraser`, or one of their async counterparts.

    Attributes:
        _service_key (str): Lowercase service identifier used for API-key resolution and rate-limit bucket selection.
        _base_url (str): Base URL of the upstream FRED-family service.
        _service_path (str): Service-specific URL prefix appended to ``_base_url``.
        _max_requests_per_minute (int): The per-service rate limit applied by the transport layer.
        caching_enabled (bool): Whether the module-global cache is enabled for this instance.
        cache_size (int): The maximum number of cache entries when caching is enabled.

    Notes:
        :class:`_ClientModel` is also the structural type that response model objects type their ``client`` attribute against, since either flavour of concrete client may be attached.
    """

    _service_key: Service
    """Lowercase service identifier (e.g., ``"fred"``, ``"alfred"``, ``"fraser"``). Derived from the concrete class name at construction time."""

    _base_url: str
    """Base URL of the upstream FRED-family service. Declared by concrete subclasses."""

    _service_path: str
    """Service-specific URL prefix appended to ``_base_url``. Declared by concrete subclasses."""

    _max_requests_per_minute: int
    """The per-service rate limit applied by the transport layer. Declared by concrete subclasses."""


    # Dunder Methods
    def __init__(
        self,
        api_key: str | None = None,
        caching_enabled: bool = True,
        cache_size: int = 256
    ) -> None:
        """Initialize the client with an API key and caching configuration.

        Derives ``_service_key`` from the concrete class name, registers
        the supplied ``api_key`` (if any) through
        :func:`fedfred.settings.set_api_key` for the corresponding service,
        and configures the module-global cache via
        :func:`fedfred._internals._caching.set_cache_maxsize` when
        ``caching_enabled`` is ``True``.

        Args:
            api_key (str, optional): Your FRED-family API key. If omitted, the API key is resolved from the global setting or the service's environment variable at request time.
            caching_enabled (bool, optional): Whether to enable the module-global cache for this client's requests. Defaults to ``True``.
            cache_size (int, optional): The maximum number of cache entries when caching is enabled. Defaults to 256.

        Raises:
            RuntimeError: If ``api_key`` is supplied but cannot be
                registered, or if a downstream request fails to resolve
                an API key from the explicit argument, global setting,
                or environment variable.

        Notes:
            API keys can be set globally via :func:`fedfred.set_api_key`
            or provided explicitly per-client. If neither is provided,
            the client falls back to the service's environment variable
            (``FRED_API_KEY`` for FRED/ALFRED/GeoFRED, ``FRASER_API_KEY``
            for FRASER) at request time.

        Examples:
            >>> import fedfred as fd
            >>> fd.set_api_key("your_api_key")  # optional global
            >>> fred = fd.Fred()                 # uses global/env key
            >>> fred_explicit = fd.Fred(api_key="your_api_key")
        """
        self._service_key = cast(Service, type(self).__name__.lower())

        if api_key:
            set_api_key(api_key, service=self._service_key)

        if caching_enabled:
            set_cache_maxsize(cache_size)

        self.caching_enabled: bool = caching_enabled

        self.cache_size: int = get_cache_maxsize() if caching_enabled else cache_size

    def __repr__(self) -> str:
        """Return a compact developer representation.

        Resolves the API-key presence without exposing the key itself —
        either ``<set>`` or ``None`` is shown — and reports the caching
        configuration. Suitable for logs and ``__repr__`` chains.

        Returns:
            str: A string of the form ``"<ClassName>(api_key=<set>|None,
            caching_enabled=<bool>, cache_size=<int>)"``.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> repr(fred)
            "Fred(api_key=<set>, caching_enabled=True, cache_size=256)"
        """
        try:
            has_key = bool(_resolve_api_key(service=self._service_key))  # TODO: Typing alias logic rewrite origination point.

        except ClientError:                        # TODO: Add custom exception for missing API key and catch that instead.
            has_key = False

        auth = "<set>" if has_key else "None"

                                                    # TODO: include size of instance object in the repr string for debugging purposes (can use sys.getsizeof() for that).

        return (
            f"{type(self).__name__}("
            f"api_key={auth}, "
            f"caching_enabled={self.caching_enabled}, "
            f"cache_size={self.cache_size}"
            f")"
        )

    def __str__(self) -> str:
        """Return a human-readable multi-line summary of the client's configuration.

        Reports the service identifier and resolved upstream URL, whether
        an API key is configured, the cache mode and capacity, and the
        rate-limit budget. Suitable for interactive inspection and for
        the ``print(client)`` idiom.

        Returns:
            str: A multi-line summary string.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> print(fred)
            Fred Instance:
              Service: Fred (https://api.stlouisfed.org/fred)
              API Key: configured
              Cache: enabled (FIFO, maxsize=256)
              Rate Limit: 120 req/min
        """
        try:
            has_key = bool(_resolve_api_key(service=self._service_key))
        except SettingsError:                           # TODO: Add custom exception for missing API key and catch that instead.
            has_key = False

        auth_line = "configured" if has_key else "not configured"

        cache_line = (
            f"enabled (FIFO, maxsize={self.cache_size})"
            if self.caching_enabled
            else "disabled"
        )

        return (
            f"{type(self).__name__} Instance:\n"
            f"  Service: {type(self).__name__} ({self._base_url}{self._service_path})\n"
            f"  API Key: {auth_line}\n"
            f"  Cache: {cache_line}\n"
            f"  Rate Limit: {self._max_requests_per_minute} req/min\n"
        )

    def __eq__(
        self,
        other: object
    ) -> bool | NotImplementedType:
        """Compare for equality against another client of the same concrete type.

        Two clients compare equal when they are the same concrete class and
        share the same observable configuration (``caching_enabled`` and
        ``cache_size``). API keys are not compared because they are stored
        out-of-band in the global settings registry. Returns
        :data:`NotImplemented` rather than ``False`` for cross-type
        comparisons so Python can attempt the reflected operation on the
        other operand.

        Args:
            other (object): The value to compare against.

        Returns:
            bool | NotImplementedType: ``True`` if ``other`` is the same
            concrete type and shares configuration; ``False`` if the
            configuration differs; :data:`NotImplemented` if ``other`` is
            a different type.

        Examples:
            >>> import fedfred as fd
            >>> fred1 = fd.Fred('your_api_key')
            >>> fred2 = fd.Fred('your_api_key')
            >>> fred1 == fred2
            True
        """
        try:
            assert isinstance(other, type(self))
        except AssertionError:
            return NotImplemented

        return (
            self.caching_enabled == other.caching_enabled
            and self.cache_size == other.cache_size
        )

    def __hash__(self) -> int:
        """Return a hash incorporating the concrete type name and configuration.

        Including ``type(self).__name__`` ensures that a ``Fred`` and an
        ``AsyncFred`` with the same caching configuration do not collide.
        API keys are not hashed, matching the :meth:`__eq__` contract.

        Returns:
            int: A stable hash for the client instance.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> isinstance(hash(fred), int)
            True
        """
        return hash((type(self).__name__, self.caching_enabled, self.cache_size))

    def __len__(self) -> int:
        """Return the number of entries in the module-global cache.

        Returns ``0`` when caching is disabled. The reported count is
        currently shared across all live clients regardless of service
        because the cache is module-global; once per-service cache
        partitioning lands this method will scope to the calling client's
        service.

        Returns:
            int: The current cache entry count, or ``0`` when caching is disabled.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key', caching_enabled=True)
            >>> len(fred)
            0
        """
        return len(_retrieve_cache_instance()) if self.caching_enabled else 0

    def __contains__(
        self,
        key: str
    ) -> bool:
        """Return whether a key is present in the module-global cache.

        Returns ``False`` when caching is disabled. Like :meth:`__len__`,
        the lookup is currently shared across all live clients.

        Args:
            key (str): The cache key to check for membership.

        Returns:
            bool: ``True`` if the key is cached, ``False`` if it is missing or caching is disabled.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> ('get_category', (('category_id', 125),)) in fred
            False
        """
        return self.caching_enabled and key in _retrieve_cache_instance()

    def __getitem__(
        self,
        key: str
    ) -> object:
        """Return the cached response for a key from the module-global cache.

        Provides dict-like read access to cached responses for inspection
        and debugging. Raises :class:`KeyError` when caching is disabled
        or the key is missing.

        Args:
            key (str): The cache key to retrieve.

        Returns:
            object: The cached response payload.

        Raises:
            KeyError: If caching is disabled or the key is not present in the cache.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key')
            >>> _ = fred.get_category(125)  # populate cache
            >>> # fred[('get_category', (('category_id', 125),))]
        """
        if not self.caching_enabled:
            raise ClientError(key)         # TODO: Add custom exception for cache disabled and catch that instead.

        return _retrieve_cache_instance().cache[key]

    # Properties
    @property
    def keys(self) -> KeysView[tuple[Any, ...]] | None:
        """The view of cache keys, or ``None`` when caching is disabled.

        Returns:
            KeysView[tuple[Any, ...]] | None: A live view of the module-global cache keys, or ``None`` if this client has caching disabled.

        Examples:
            >>> import fedfred as fd
            >>> fred = fd.Fred('your_api_key', caching_enabled=False)
            >>> fred.keys is None
            True
        """
        return _retrieve_cache_instance().keys() if self.caching_enabled else None


class _BaseClient(_ClientModel):
    """Synchronous client base.

    Adds the synchronous transport layer and a context-manager surface to
    :class:`_ClientModel`. Concrete synchronous clients (:class:`fedfred.Fred`,
    :class:`fedfred.Alfred`, :class:`fedfred.Fraser`) inherit from this
    class.

    The context-manager methods are currently no-ops — the underlying
    :mod:`httpx` transport opens and closes a :class:`httpx.Client` per
    request, and the cache and rate-limit buckets are module-global — but
    they exist as ergonomic parity with other Python HTTP libraries and
    as a forward-compatible seam for per-instance connection pooling.

    See Also:
        - :class:`_ClientModel`: The shared root base.
        - :class:`_AsyncBaseClient`: The asynchronous counterpart.
    """

    # Dunder Methods
    def __enter__(self) -> "_BaseClient":
        """Enter the synchronous runtime context.

        Returns:
            _BaseClient: This instance, for use as the ``as`` target in a ``with`` statement.

        Notes:
            The client does not currently own per-instance resources
            requiring explicit cleanup. The transport opens and closes
            :class:`httpx.Client` per request, and the cache and rate-limit
            buckets are module-global. This method exists for ergonomic
            parity with :mod:`httpx` and :mod:`requests` and as a forward-
            compatible seam for future per-instance connection pooling.

        Examples:
            >>> import fedfred as fd
            >>> with fd.Fred("your_api_key") as fred:
            ...     categories = fred.get_category(125)
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the synchronous runtime context.

        No-op. Does not clear the cache or rate-limit buckets — those are
        shared across all live sync and async clients, so clearing them
        here would corrupt other clients.

        Args:
            exc_type (type[BaseException] | None): Exception type if one was raised inside the ``with`` block, otherwise ``None``.
            exc (BaseException | None): Exception instance, if any.
            tb (TracebackType | None): Traceback, if any.

        Returns:
            None: This method does not suppress exceptions.
        """
        return None

    # Private Methods
    def _client_get_request(
        self,
        endpoint_name: str,
        data: dict[str, Any] | None = None,
        path_injection: str | None = None
    ) -> dict[str, Any]:
        """Perform a synchronous GET request to the FRED-family API.

        Dispatches through the cached transport
        (:func:`fedfred._internals._transport._cached_get_request`) when
        ``self.caching_enabled`` is ``True``, hashing the query parameters
        via :func:`fedfred._core._hashable_type_converter` so they form a
        stable cache key. Falls through to the uncached transport
        (:func:`fedfred._internals._transport._get_request`) when caching
        is disabled.

        Args:
            endpoint_name (str): The FRED API endpoint name to query. Resolved against the endpoint specifications in :mod:`fedfred._core._endpoints`.
            data (dict[str, Any] | None, optional): The query parameters to send with the request. ``None`` values are dropped by the transport layer. Defaults to ``None``.
            path_injection (str | None, optional): An optional string to inject into the endpoint path, for endpoints that require it. Defaults to ``None``.

        Returns:
            dict[str, Any]: The parsed JSON response from the API.

        Raises:
            httpx.HTTPError: If the underlying HTTP request fails.
            FedFredAPIError: If the upstream service returns an error payload.

        Warning:
            Caching applies only when ``caching_enabled`` is ``True``. The ``data`` parameter must be hashable through
            :func:`fedfred._core._hashable_type_converter` for caching to function correctly; list-valued parameters are flattened
            into tuples by that helper.
        """
        if self.caching_enabled:
            return _cached_get_request(self._service_key, endpoint_name, _hashable_type_converter(data), path_injection)

        else:
            return _get_request(self._service_key, endpoint_name, data, path_injection)

    def _client_post_request(
        self,
        endpoint_name: str,
        data: dict[str, str | int | None] | None = None
    ) -> dict[str, Any]:
        """Reserved hook for synchronous POST requests.

        Placeholder for the v4 design pass; no FRED-family endpoint
        currently requires a POST body, but the slot exists so the
        public client surface remains stable when one does.
        """
        return _post_request(self._service_key, endpoint_name, data)


class _AsyncBaseClient(_ClientModel):
    """Asynchronous client base.

    Adds the asynchronous transport layer and an async context-manager
    surface to :class:`_ClientModel`. Concrete asynchronous clients
    (:class:`fedfred.AsyncFred`, :class:`fedfred.AsyncAlfred`,
    :class:`fedfred.AsyncFraser`) inherit from this class.

    The async context-manager methods are currently no-ops — the underlying
    :mod:`httpx` transport opens and closes an :class:`httpx.AsyncClient`
    per request, and the cache and rate-limit buckets are module-global —
    but they exist as ergonomic parity with :class:`httpx.AsyncClient` and
    as a forward-compatible seam for per-instance connection pooling.

    See Also:
        - :class:`_ClientModel`: The shared root base.
        - :class:`_BaseClient`: The synchronous counterpart.
    """

    # Dunder Methods
    async def __aenter__(self) -> "_AsyncBaseClient":
        """Enter the asynchronous runtime context.

        Returns:
            _AsyncBaseClient: This instance, for use as the ``as`` target in an ``async with`` statement.

        Notes:
            The async client does not currently own per-instance resources
            requiring explicit cleanup. The transport opens and closes
            :class:`httpx.AsyncClient` per request, and the cache and
            rate-limit buckets are module-global. This method exists for
            ergonomic parity with :class:`httpx.AsyncClient` and as a
            forward-compatible seam for future per-instance connection
            pooling.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> async def main():
            ...     async with fd.AsyncFred("your_api_key") as fred:
            ...         categories = await fred.get_category(125)
            >>> asyncio.run(main())
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the asynchronous runtime context.

        No-op. Does not clear the cache or rate-limit buckets — those are
        shared across all live sync and async clients, so clearing them
        here would corrupt other clients.

        Args:
            exc_type (type[BaseException] | None): Exception type if one was raised inside the ``async with`` block, otherwise ``None``.
            exc (BaseException | None): Exception instance, if any.
            tb (TracebackType | None): Traceback, if any.

        Returns:
            None: This method does not suppress exceptions.
        """
        return None

    # Private Methods
    async def _client_get_request(
        self,
        endpoint_name: str,
        data: dict[str, str | int | None] | None = None,
        path_injection: str | None = None
    ) -> dict[str, Any]:
        """Perform an asynchronous GET request to the FRED-family API.

        Dispatches through the cached transport
        (:func:`fedfred._internals._transport._cached_get_request_async`)
        when ``self.caching_enabled`` is ``True``, hashing the query
        parameters via
        :func:`fedfred._core._hashable_type_converter_async` so they form
        a stable cache key. Falls through to the uncached transport
        (:func:`fedfred._internals._transport._get_request_async`) when
        caching is disabled.

        Args:
            endpoint_name (str): The FRED API endpoint name or path to query.
            data (dict[str, str | int | None] | None, optional): The query parameters to send with the request. ``None`` values are dropped by the transport layer. Defaults to ``None``.
            path_injection (str | None, optional): An optional string to inject into the endpoint path, for endpoints that require it. Defaults to ``None``.

        Returns:
            dict[str, Any]: The parsed JSON response from the API.

        Raises:
            httpx.HTTPError: If the underlying HTTP request fails.
            FedFredAPIError: If the upstream service returns an error payload.

        Warning:
            Caching applies only when ``caching_enabled`` is ``True`` on
            this instance. The ``data`` parameter must be hashable through
            :func:`fedfred._core._hashable_type_converter_async` for
            caching to function correctly; list-valued parameters are
            flattened into tuples by that helper.
        """
        if self.caching_enabled:
            return await _cached_get_request_async(
                self._service_key, endpoint_name, _hashable_type_converter(data), path_injection
            )

        else:
            return await _get_request_async(self._service_key, endpoint_name, data, path_injection)

    async def _client_post_request(
        self,
        endpoint_name: str,
        data: dict[str, str | int | None] | None = None
    ) -> dict[str, Any]:
        """Reserved hook for asynchronous POST requests.

        Placeholder for the v4 design pass; no FRED-family endpoint
        currently requires a POST body, but the slot exists so the
        public async client surface remains stable when one does.
        """
        return await _post_request_async(self._service_key, endpoint_name, data)

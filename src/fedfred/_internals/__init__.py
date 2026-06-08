# filepath: /src/fedfred/_internals/__init__.py
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
"""Internal subpackage of fedfred.

Aggregates the private building blocks that the public package surface is
composed from and re-exports them under a single namespace for internal use:
the runtime-adjustable cache and its accessors from :mod:`._caching`, the
synchronous and asynchronous client bases and the ``_ClientModel`` typing
contract from :mod:`._clients`, and the response-model and sequence bases from
:mod:`._models`.

These names are private implementation details. They are exported only so that
sibling internal modules and the public model classes can import them from one
place; downstream users should depend on the public ``fedfred`` surface
(``Fred``, ``Category``, ``Series``, etc.) rather than on anything here.

See Also:
    - :mod:`fedfred._internals._caching`: Runtime-adjustable FIFO cache.
    - :mod:`fedfred._internals._clients`: Client bases and the ``_ClientModel`` contract.
    - :mod:`fedfred._internals._models`: Response-model and sequence bases.
"""

from .._core import (
    _coerce_lower,
    _ResponseShape,
)
from ._caching import (
    AdjustableFIFOCache,
    _retrieve_cache_instance,
    get_cache_maxsize,
    set_cache_maxsize,
)
from ._clients import (
    _AsyncBaseClient,
    _BaseClient,
    _ClientModel,
)
from ._models import (
    _DateBase,
    _DateSequence,
    _ModelBase,
    _ModelSequence,
)

__all__ = [
    "AdjustableFIFOCache",
    "_AsyncBaseClient",
    "_BaseClient",
    "_ClientModel",
    "_DateBase",
    "_DateSequence",
    "_ModelBase",
    "_ModelSequence",
    "_ResponseShape",
    "_coerce_lower",
    "_retrieve_cache_instance",
    "get_cache_maxsize",
    "set_cache_maxsize",
]

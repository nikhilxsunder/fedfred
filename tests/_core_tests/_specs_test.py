# filepath: /tests/_core_tests/_specs_test.py
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

import dataclasses

import pytest

from fedfred._core._specs import EndpointSpec, ParameterSpec
from fedfred._core._types import _VALID_AUTH_STYLES, _VALID_SERVICES
from fedfred.exceptions import (
    EndpointAuthError,
    EndpointFieldTypeError,
    EndpointServiceError,
    EndpointURLError,
)


def test_endpoint_spec():
    # --- minimal valid spec: defaults applied --------------------------------
    spec = EndpointSpec(service="fred", url="https://api.stlouisfed.org/fred")
    assert spec.service == "fred"
    assert spec.url == "https://api.stlouisfed.org/fred"
    assert spec.auth == "api_key_param"       # default
    assert spec.params is None
    assert spec.payload is None
    assert spec.headers is None

    # --- fully specified valid spec ------------------------------------------
    full = EndpointSpec(
        service="fraser",
        url="https://api.stlouisfed.org/fraser/title/{}",
        auth="api_key_header",
        params={"format": "json"},
        payload={"body": "x"},
        headers={"Authorization": "..."},
    )
    assert full.auth == "api_key_header"
    assert full.params == {"format": "json"}
    assert full.payload == {"body": "x"}
    assert full.headers == {"Authorization": "..."}

    # --- frozen + slots ------------------------------------------------------
    assert not hasattr(spec, "__dict__")          # slots=True
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.url = "https://elsewhere"            # frozen=True

    # --- __post_init__: invalid service --------------------------------------
    with pytest.raises(EndpointServiceError) as exc:
        EndpointSpec(service="frd", url="https://api.stlouisfed.org/fred")
    assert exc.value.field == "service"
    assert exc.value.received == "frd"
    assert exc.value.valid == tuple(sorted(_VALID_SERVICES))

    # --- __post_init__: url empty / whitespace / non-string ------------------
    for bad_url in ("", "   ", 123):
        with pytest.raises(EndpointURLError) as exc:
            EndpointSpec(service="fred", url=bad_url)
        assert exc.value.field == "url"

    # --- __post_init__: url present but not https:// -------------------------
    with pytest.raises(EndpointURLError) as exc:
        EndpointSpec(service="fred", url="http://api.stlouisfed.org/fred")
    assert exc.value.field == "url"

    # --- __post_init__: invalid auth -----------------------------------------
    with pytest.raises(EndpointAuthError) as exc:
        EndpointSpec(service="fred", url="https://x", auth="magic")
    assert exc.value.field == "auth"
    assert exc.value.received == "magic"
    assert exc.value.valid == tuple(sorted(_VALID_AUTH_STYLES))

    # --- __post_init__: params/payload/headers set but not a dict ------------
    with pytest.raises(EndpointFieldTypeError) as exc:
        EndpointSpec(service="fred", url="https://x", params="nope")
    assert exc.value.field == "params"
    assert exc.value.received == "str"

    with pytest.raises(EndpointFieldTypeError) as exc:
        EndpointSpec(service="fred", url="https://x", payload=123)
    assert exc.value.field == "payload"
    assert exc.value.received == "int"

    with pytest.raises(EndpointFieldTypeError) as exc:
        EndpointSpec(service="fred", url="https://x", headers=[1])
    assert exc.value.field == "headers"
    assert exc.value.received == "list"


def test_parameter_spec():
    # --- defaults ------------------------------------------------------------
    spec = ParameterSpec()
    assert spec.converter is None
    assert spec.validator is None
    assert spec.required is False

    # --- fully specified -----------------------------------------------------
    def _conv(name, value):
        return value

    def _val(name, value):
        return None

    full = ParameterSpec(converter=_conv, validator=_val, required=True)
    assert full.converter is _conv
    assert full.validator is _val
    assert full.required is True

    # --- frozen + slots (no validation, but same dataclass guarantees) -------
    assert not hasattr(spec, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.required = True
# filepath: /src/fedfred/_core/_parsers.py
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
"""Response-shape parsers for FRED-family API payloads.

This module provides the internal helpers that extract and validate the
list-shaped data inside FRED, GeoFRED, and FRASER responses before it is handed
to the model layer. The helpers normalize the inconsistencies in FRED's payload
shapes — singular vs. plural container keys, elements returned as an
id-keyed dict instead of a list — and raise
:class:`~fedfred.exceptions.parsing.ParsingError` on any unexpected structure so
malformed responses fail loudly at the boundary rather than deep in parsing.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from ..exceptions.parsing import ParsingError

__all__ = [
    "_ResponseShape",
    "_extract_objects",
    "_observation_columns",
    "_region_type_parser",
]

def _region_type_parser(response: dict[str, Any]) -> str:
    """Extract the region type from a GeoFRED response.

    Args:
        response (dict[str, Any]): The GeoFRED response payload.

    Returns:
        str: The region type (e.g. ``"state"``), read from ``response["meta"]["region"]``.

    Raises:
        ParsingError: If the response has no ``meta`` section, or the ``meta`` section has no ``region`` value.

    Examples:
        >>> from fedfred._core._parsers import _region_type_parser
        >>> _region_type_parser({"meta": {"region": "state"}, "data": {"observations": []}})
        'state'

    Notes:
        GeoFRED reports the region type under the ``region`` key of the ``meta``
        section; despite the function name, the underlying payload key is
        ``region``, not ``region_type``.
    """
    meta_data = response.get('meta', {})

    if not meta_data:
        raise ParsingError(
            message="No meta data found in the response"
            )

    region_type = meta_data.get('region')

    if not region_type:
        raise ParsingError(
            message="No region type found in the response meta data"
            )

    return region_type

def _require_first_list(
    response: dict[str, Any],
    keys: tuple[str, ...]
) -> list[Any]:
    """Return the list under the first key in ``keys`` that is present.

    Args:
        response (dict[str, Any]): The response to read from.
        keys (tuple[str, ...]): Candidate keys, tried in order; the first present key wins.

    Returns:
        list[Any]: The list found under the first matching key.

    Raises:
        ParsingError: If ``response`` is not a dict, none of ``keys`` are present, or the value under the first matching key is not a list.

    Examples:
        >>> from fedfred._core._parsers import _require_first_list
        >>> _require_first_list({"seriess": [{"id": "GDP"}]}, ("seriess", "series"))
        [{'id': 'GDP'}]

    Notes:
        FRED's ``series`` and ``release`` endpoints sometimes return data under
        the plural key (``seriess`` / ``releases``) and sometimes the singular
        (``series`` / ``release``); passing both lets a single parser handle
        either shape.
    """
    if not isinstance(response, dict):
        raise ParsingError(
            f"Invalid API response: expected a mapping, got {type(response).__name__}"
        )

    for key in keys:
        if key in response:
            raw = response[key]
            if not isinstance(raw, list):
                raise ParsingError(f"Invalid API response: {key!r} must be a list")

            return raw

    pretty = " or ".join(repr(k) for k in keys)

    raise ParsingError(f"Invalid API response: missing {pretty} field")

def _objects_iter_dict_or_list(
    response: dict[str, Any],
    key: str
) -> list[dict[str, Any]]:
    """Return the objects under ``key`` as a list, accepting either a list or an id-keyed dict.

    Args:
        response (dict[str, Any]): The response to read from.
        key (str): The key expected to point to either a list of objects or a dict mapping ids to objects.

    Returns:
        list[dict[str, Any]]: The objects as a list. If the value was a dict, its values are returned (keys discarded).

    Raises:
        ParsingError: If ``response`` is not a dict, ``key`` is missing, or the value under ``key`` is neither a dict nor a list.

    Examples:
        >>> from fedfred._core._parsers import _objects_iter_dict_or_list
        >>> _objects_iter_dict_or_list({"elements": {"1": {"id": 1}}}, "elements")
        [{'id': 1}]
        >>> _objects_iter_dict_or_list({"elements": [{"id": 1}]}, "elements")
        [{'id': 1}]

    Notes:
        FRED's category ``related_tags``/``elements`` payloads return the objects
        as a dict keyed by id rather than a list; this normalizes both shapes to
        a list so the model layer sees one form.
    """
    if not isinstance(response, dict) or key not in response:
        raise ParsingError(f"Invalid API response: missing {key!r} field")

    raw = response[key]

    if isinstance(raw, dict):
        return list(raw.values())

    if isinstance(raw, list):
        return raw

    raise ParsingError(f"Invalid API response: {key!r} must be a dict or list")

type _ResponseShape = Literal["list", "dict_or_list"]

def _extract_objects(
    response: dict[str, Any],
    keys: tuple[str, ...],
    shape: _ResponseShape,
) -> list[Any]:
    """Extract the raw object list from a response per the declared shape.

    Args:
        response (dict[str, Any]): The raw FRED API response payload.
        keys (tuple[str, ...]): Candidate payload keys, tried in order.
        shape (_ResponseShape): ``"list"`` for a plain list under the first
            matching key, or ``"dict_or_list"`` for FRED's id-keyed-dict
            element payloads.

    Returns:
        list[Any]: The extracted object list.

    Raises:
        ParsingError: If ``response`` is not a mapping, none of ``keys`` are
            present, or the value has the wrong shape.
    """
    if shape == "dict_or_list":
        return _objects_iter_dict_or_list(response, keys[0])

    return _require_first_list(response, keys)

def _observation_columns(observations: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Bulk-parse the observations array into (dates, values) columns.

    Single O(n) pass: dates parsed vectorized as datetime64[D], FRED "." → NaN.
    Defensive — missing keys raise ParsingError rather than KeyError.
    """
    try:
        dates = np.array([o["date"] for o in observations], dtype="datetime64[D]")

        values = np.array(
            [np.nan if o["value"] == "." else o["value"] for o in observations],
            dtype="float64",
        )

    except KeyError as e:
        raise ParsingError(f"observation missing required key {e}.") from e

    return dates, values

def _date_column(rows: list[dict], key: str) -> np.ndarray:
    """Vectorized parse of one ISO-date field into a datetime64[D] column."""
    try:
        return np.array([r[key] for r in rows], dtype="datetime64[D]")
    except KeyError as e:
        raise ParsingError(f"observation missing required key {e}.") from e


def _observation_columns(observations: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Bulk parse the observations array into (dates, values); '.' -> NaN."""
    dates = _date_column(observations, "date")
    try:
        values = np.array(
            [np.nan if o["value"] == "." else o["value"] for o in observations],
            dtype="float64",
        )
    except KeyError as e:
        raise ParsingError(f"observation missing required key {e}.") from e
    return dates, values
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
"""Response parsers for FRED-family API payloads.

Internal parsers that turn a decoded JSON response into the structures the model layer
consumes, absorbing FRED's shape inconsistencies at one boundary. Three groups live here:

List-shape extractors
    :func:`_extract_objects` and its backends (:func:`_require_first_list`,
    :func:`_objects_iter_dict_or_list`) pull the list-shaped data out of FRED, GeoFRED, and
    FRASER responses, normalizing FRED's irregularities — singular vs. plural container keys
    (``series`` / ``seriess``), and elements returned as an id-keyed dict instead of a list —
    to a single list form.

Columnar observation parsers
    :func:`_observation_columns` and :func:`_date_column` bulk-parse a series-observations
    array into the numpy ``datetime64[D]`` / ``float64`` columns the observation model stores,
    mapping FRED's ``"."`` missing sentinel to ``NaN`` in one O(n) pass.

Field extractor
    :func:`_region_type_parser` reads the GeoFRED region type out of the ``meta`` section.

Every parser fails at the boundary rather than deep in the model layer, raising a
:class:`~fedfred.exceptions.parsing.ParsingError` subclass on any unexpected structure:
:class:`~fedfred.exceptions.parsing.MissingFieldError` when a required key is absent, and
:class:`~fedfred.exceptions.parsing.ResponseShapeError` when a present value has the wrong type
(a list where a dict was expected, and so on). Catch ``ParsingError`` to handle either.

Functions:
    _region_type_parser: GeoFRED region type from ``meta.region``.
    _require_first_list: List under the first present candidate key.
    _objects_iter_dict_or_list: Objects under a key, normalizing dict-or-list to a list.
    _extract_objects: Shape-dispatched object extraction over candidate keys.
    _date_column: One ISO-date field across rows to a ``datetime64[D]`` column.
    _observation_columns: An observations array to parallel ``(dates, values)`` columns.

See Also:
    - :mod:`fedfred._core._converters`: Consumes the observation columns to build backend frames.
    - :class:`fedfred._internals._models._ObservationSequence`: Stores the columns this produces.
    - :mod:`fedfred.exceptions.parsing`: The ``ParsingError`` hierarchy raised here.

References:
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..exceptions import MissingFieldError, ResponseShapeError
from ._types import _ResponseShape


def _region_type_parser(response: dict[str, Any]) -> str:
    """Extract the region type from a GeoFRED response.

    Args:
        response (dict[str, Any]): The GeoFRED response payload.

    Returns:
        str: The region type (e.g. ``"state"``), read from ``response["meta"]["region"]``.

    Raises:
        MissingFieldError: If the response has no (truthy) ``meta`` section, or the ``meta``
            section has no (truthy) ``region`` value.

    Examples:
        >>> from fedfred._core._parsers import _region_type_parser
        >>> _region_type_parser({"meta": {"region": "state"}, "data": {"observations": []}})
        'state'

    Notes:
        GeoFRED reports the region type under the ``region`` key of the ``meta`` section;
        despite the function name, the underlying payload key is ``region``, not
        ``region_type``. Both checks are truthiness checks, so an empty ``meta`` (``{}``) or an
        empty ``region`` (``""``) is treated as missing.
    """
    meta_data = response.get("meta", {})

    if not meta_data:
        raise MissingFieldError(
            message="No meta section found in the GeoFRED response.",
            field="meta",
        )

    region_type = meta_data.get("region")

    if not region_type:
        raise MissingFieldError(
            message="No region type found in the GeoFRED response meta section.",
            field="region",
        )

    return region_type


def _require_first_list(response: dict[str, Any], keys: tuple[str, ...]) -> list[Any]:
    """Return the list under the first key in ``keys`` that is present.

    Args:
        response (dict[str, Any]): The response to read from.
        keys (tuple[str, ...]): Candidate keys, tried in order; the first present key wins, even
            if its list is empty.

    Returns:
        list[Any]: The list found under the first matching key (may be empty).

    Raises:
        ResponseShapeError: If ``response`` is not a dict, or the value under the first matching
            key is not a list.
        MissingFieldError: If none of ``keys`` are present in ``response``.

    Examples:
        >>> from fedfred._core._parsers import _require_first_list
        >>> _require_first_list({"seriess": [{"id": "GDP"}]}, ("seriess", "series"))
        [{'id': 'GDP'}]

    Notes:
        FRED's ``series`` and ``release`` endpoints sometimes return data under the plural key
        (``seriess`` / ``releases``) and sometimes the singular (``series`` / ``release``);
        passing both lets one parser handle either shape. Both raised errors subclass
        ``ParsingError``, so a caller may catch that base to handle either.
    """
    if not isinstance(response, dict):
        raise ResponseShapeError(
            message="Invalid API response: expected a mapping.",
            expected="mapping",
            received=type(response).__name__,
        )

    for key in keys:
        if key in response:
            raw = response[key]

            if not isinstance(raw, list):
                raise ResponseShapeError(
                    message=f"Invalid API response: {key!r} must be a list.",
                    field=key,
                    expected="list",
                    received=type(raw).__name__,
                )

            return raw

    raise MissingFieldError(
        message=f"Invalid API response: missing {' or '.join(repr(k) for k in keys)} field.",
        candidates=keys,
    )


def _objects_iter_dict_or_list(response: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return the objects under ``key`` as a list, accepting either a list or an id-keyed dict.

    Args:
        response (dict[str, Any]): The response to read from.
        key (str): The key expected to point to either a list of objects or a dict mapping ids
            to objects.

    Returns:
        list[dict[str, Any]]: The objects as a list. If the value was a dict, its values are
        returned in insertion order and the id keys are discarded.

    Raises:
        MissingFieldError: If ``response`` is not a dict, or ``key`` is missing.
        ResponseShapeError: If the value under ``key`` is neither a dict nor a list.

    Examples:
        >>> from fedfred._core._parsers import _objects_iter_dict_or_list
        >>> _objects_iter_dict_or_list({"elements": {"1": {"id": 1}}}, "elements")
        [{'id': 1}]
        >>> _objects_iter_dict_or_list({"elements": [{"id": 1}]}, "elements")
        [{'id': 1}]

    Notes:
        FRED's category ``related_tags`` / ``elements`` payloads return the objects as a dict
        keyed by id rather than a list; this normalizes both shapes to a list so the model layer
        sees one form. When the id keys carry information the model needs, read them before
        calling — they are dropped here.
    """
    if not isinstance(response, dict) or key not in response:
        raise MissingFieldError(
            message=f"Invalid API response: missing {key!r} field.",
            field=key,
        )

    raw = response[key]

    if isinstance(raw, dict):
        return list(raw.values())

    if isinstance(raw, list):
        return raw

    raise ResponseShapeError(
        message=f"Invalid API response: {key!r} must be a dict or list.",
        field=key,
        expected="dict or list",
        received=type(raw).__name__,
    )


def _extract_objects(
    response: dict[str, Any],
    keys: tuple[str, ...],
    shape: _ResponseShape,
) -> list[Any]:
    """Extract the raw object list from a response per the declared shape.

    Dispatches on ``shape`` to the matching low-level parser: ``"dict_or_list"`` routes to
    :func:`_objects_iter_dict_or_list` (consulting only ``keys[0]``), and ``"list"`` routes to
    :func:`_require_first_list` (trying every key in order).

    Args:
        response (dict[str, Any]): The raw FRED API response payload.
        keys (tuple[str, ...]): Candidate payload keys. All are tried in order for the ``"list"``
            shape; only ``keys[0]`` is used for ``"dict_or_list"``.
        shape (_ResponseShape): ``"list"`` for a plain list under the first matching key, or
            ``"dict_or_list"`` for FRED's id-keyed-dict element payloads.

    Returns:
        list[Any]: The extracted object list (may be empty).

    Raises:
        ResponseShapeError: If ``response`` is not a mapping, or the value has the wrong shape
            (propagated from the dispatched parser).
        MissingFieldError: If the required key(s) are absent (propagated from the dispatched
            parser).

    See Also:
        - :func:`_require_first_list`: The ``"list"`` branch.
        - :func:`_objects_iter_dict_or_list`: The ``"dict_or_list"`` branch.
    """
    if shape == "dict_or_list":
        return _objects_iter_dict_or_list(response, keys[0])

    return _require_first_list(response, keys)


def _date_column(rows: list[dict], key: str) -> np.ndarray:
    """Vectorized parse of one ISO-date field across rows into a ``datetime64[D]`` column.

    Args:
        rows (list[dict]): The observation rows.
        key (str): The date field to read from each row (e.g. ``"date"``, ``"realtime_start"``,
            ``"realtime_end"``).

    Returns:
        numpy.ndarray: A 1-D ``datetime64[D]`` array of the parsed dates, one per row, in row
        order.

    Raises:
        MissingFieldError: If any row is missing ``key``.

    Examples:
        >>> from fedfred._core._parsers import _date_column
        >>> _date_column([{"date": "2020-01-01"}, {"date": "2020-02-01"}], "date").tolist()
        [datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)]

    Notes:
        numpy parses the strings at day resolution. A missing key is caught and re-raised as
        :class:`MissingFieldError` (a ``ParsingError`` subclass) rather than a bare ``KeyError``,
        so malformed payloads fail at the parse boundary with structured context. Shared by the
        date, realtime-start, and realtime-end column parses.
    """
    try:
        return np.array([r[key] for r in rows], dtype="datetime64[D]")

    except KeyError as exc:
        raise MissingFieldError(
            message=f"Observation missing required key {exc}.",
            field=str(exc.args[0]),
            original_exception=exc,
        ) from exc


def _observation_columns(observations: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Bulk-parse the observations array into parallel (dates, values) columns.

    Single O(n) pass that turns a FRED ``observations`` list into the two numpy columns the
    observation model stores: dates as ``datetime64[D]`` (via :func:`_date_column`) and values as
    ``float64`` with FRED's missing sentinel ``"."`` mapped to ``NaN``.

    Args:
        observations (list[dict]): The ``observations`` array from a FRED series-observations
            response; each row must carry ``"date"`` and ``"value"`` keys.

    Returns:
        tuple[numpy.ndarray, numpy.ndarray]: ``(dates, values)`` — a ``datetime64[D]`` date
        column and a ``float64`` value column of equal length, aligned row-for-row.

    Raises:
        MissingFieldError: If any observation is missing ``"date"`` or ``"value"``.

    Examples:
        >>> from fedfred._core._parsers import _observation_columns
        >>> dates, values = _observation_columns(
        ...     [{"date": "2020-01-01", "value": "1.5"}, {"date": "2020-02-01", "value": "."}]
        ... )
        >>> dates.tolist()
        [datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)]
        >>> values.tolist()
        [1.5, nan]

    Notes:
        The single parse boundary for observations: these columns feed the columnar
        ``_ObservationSequence`` directly, and the ``"."`` -> ``NaN`` mapping here is what the
        object layer later surfaces as ``None`` (see :func:`._accessors._cell_value`).
    """
    dates = _date_column(observations, "date")

    try:
        values = np.array(
            [np.nan if o["value"] == "." else o["value"] for o in observations],
            dtype="float64",
        )

    except KeyError as exc:
        raise MissingFieldError(
            message=f"Observation missing required key {exc}.",
            field=str(exc.args[0]),
            original_exception=exc,
        ) from exc

    return dates, values

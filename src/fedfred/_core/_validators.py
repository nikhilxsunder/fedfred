# filepath: /src/fedfred/_core/_validators.py
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
"""Validation for the fedfred core package.

Pure, stateless validators — each returns ``None`` on success or raises
:class:`~fedfred.exceptions.TypeValidationError` (wrong type) or
:class:`~fedfred.exceptions.ValueValidationError` (wrong value). No I/O, no runtime state: value
membership is checked against the type-derived sets in :mod:`._choices`, keeping validation
independent of the stateful registries. Four families live here.

Request-parameter validators
    The ``(name, value) -> None`` :data:`ParameterValidator` family plugged into a
    :class:`ParameterSpec` and run by the preparers: scalar type checks (:func:`_validate_type`,
    :func:`_validate_nonnegative_int`, :func:`_validate_bool`, :func:`_validate_str`,
    :func:`_validate_nonempty_str`), string-format checks (:func:`_validate_yyyy_mm_dd`,
    :func:`_validate_hh_mm`, :func:`_validate_semicolon_list_string`,
    :func:`_validate_comma_date_list_string`, :func:`_validate_series_id`), and the choice
    factories :func:`_validate_choice` / :func:`_validate_str_choice`, which return callable
    :class:`_choice_validator` / :class:`_str_choice_validator` instances (the functor pattern —
    a frozen dataclass closing over its allowed set).

Configuration validators
    :func:`_validate_service`, :func:`_validate_api_key`, :func:`_validate_dataframe_backend`,
    :func:`_validate_geodataframe_backend` — single-argument validators (not the ``(name, value)``
    shape) consulted by the config mutators and resolvers so an invalid identity or backend never
    reaches global state.

Model-column validator
    :func:`_validate_observation_columns` — a ``**columns`` validator checking the parallel numpy
    arrays behind an observation sequence for ndarray-ness, 1-D shape, per-column dtype kind (via
    :data:`_EXPECTED_KIND`), and equal length. The construction-time gate the columnar
    comparators and accessors rely on.

Note the three families do **not** share one call signature: the request-parameter validators
take ``(name, value)``, the configuration validators take a single value, and the column
validator takes keyword arrays. Only the first family conforms to :data:`ParameterValidator`.

See Also:
    - :mod:`fedfred._core._choices`: The type-derived ``_VALID_*`` sets membership is checked
    against.
    - :mod:`fedfred._core._specs`: :class:`ParameterSpec` pairs a validator with a converter.
    - :mod:`fedfred._core._preparers`: Runs the request-parameter validators.
    - :mod:`fedfred._core._mutators` / :mod:`fedfred._core._resolvers`: Run the config validators.
    - :mod:`fedfred._core._schemas`: Provides :data:`_EXPECTED_KIND` for the column validator.

References:
    - FRED API documentation. https://fred.stlouisfed.org/docs/api/fred/
    - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

import numpy as np

from ..exceptions import (
    TypeValidationError,
    ValueValidationError,
)
from ._choices import (
    _VALID_DATAFRAME_BACKENDS,
    _VALID_GEODATAFRAME_BACKENDS,
    _VALID_SERVICES,
)
from ._schemas import _EXPECTED_KIND
from ._types import DataFrameBackend, GeoDataFrameBackend, ParameterValidator, Service


def _validate_observation_columns(**columns: np.ndarray) -> None:
    """Validate the parallel arrays backing an observation sequence.

    Each keyword names a column and supplies its array. Every column is checked, in order, to be
    a :class:`numpy.ndarray`, one-dimensional, and — if its name appears in :data:`_EXPECTED_KIND`
    — of the expected dtype kind (``"M"`` datetime / ``"f"`` float). After the per-column checks,
    all columns must share one length. Returns ``None`` on success; raises on the first failure.

    Args:
        **columns (numpy.ndarray): Column name -> array. Names present in :data:`_EXPECTED_KIND`
            (``date``, ``realtime_start``, ``realtime_end``, ``value``) also have their dtype kind
            enforced; any other name is checked for ndarray-ness, 1-D shape, and length only.

    Raises:
        TypeValidationError: If a column is not a :class:`numpy.ndarray`, or (for a known column)
            its dtype kind does not match :data:`_EXPECTED_KIND`.
        ValueValidationError: If a column is not 1-D, or the columns are not all the same length.

    Examples:
        >>> import numpy as np
        >>> from fedfred._core._validators import _validate_observation_columns
        >>> _validate_observation_columns(
        ...     date=np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]"),
        ...     value=np.array([1.5, np.nan]),
        ... )
        >>> try:
        ...     _validate_observation_columns(
        ...         date=np.array(["2020-01-01", "2020-02-01"], dtype="datetime64[D]"),
        ...         value=np.array([1.5]),
        ...     )
        ... except Exception as exc:
        ...     print(type(exc).__name__)
        ValueValidationError

    Notes:
        The dtype-kind check is skipped for any column name not in :data:`_EXPECTED_KIND`, so an
        unexpected column passes the type gate on shape and length alone — validation is an
        allowlist for *known* columns, not a rejection of unknown ones. Called with no columns it
        is a no-op (vacuously valid). This is the construction-time gate that lets the columnar
        comparators and accessors branch on ``arr.dtype.kind`` without re-checking; a column that
        passes here is guaranteed to satisfy the kind those branches assume.

    See Also:
        - :data:`_EXPECTED_KIND`: The column-name -> dtype-kind contract enforced here.
    """
    lengths: dict[str, int] = {}

    for name, arr in columns.items():
        if not isinstance(arr, np.ndarray):
            raise TypeValidationError(f"{name} must be a numpy.ndarray, got {type(arr)!r}.")

        if arr.ndim != 1:
            raise ValueValidationError(f"{name} must be 1-D, got {arr.ndim} dimensions.")

        kind = _EXPECTED_KIND.get(name)

        if kind is not None and arr.dtype.kind != kind:
            raise TypeValidationError(f"{name} must have dtype kind {kind!r}, got {arr.dtype!r}.")

        lengths[name] = arr.shape[0]

    if len(set(lengths.values())) > 1:
        raise ValueValidationError(f"columns must be equal length, got {lengths}.")


@dataclass(frozen=True, slots=True)
class _choice_validator:
    """A parameter validator that accepts only values in a fixed allowed set.

    A callable value object (the functor pattern): constructed once by :func:`_validate_choice`
    with its allowed set, then invoked per parameter with the :data:`ParameterValidator`
    signature ``(name, value) -> None``. ``frozen=True, slots=True`` makes each instance an
    immutable, low-overhead closure over ``choices`` — cheaper and more introspectable than a
    nested function. Membership is an ``in`` test against a :class:`frozenset`, so checking is
    O(1) but every candidate value (and every allowed choice) must be hashable.

    Attributes:
        choices (frozenset[object]): The allowed values for the parameter.

    See Also:
        - :func:`_validate_choice`: The factory that builds these instances.
        - :func:`_validate_str_choice`: The string-typed variant.
    """

    choices: frozenset[object]
    """The allowed values for the parameter — the set membership is tested against."""

    def __call__(self, parameter: str, value: object) -> None:
        """Validate ``value`` against the allowed choices.

        Args:
            parameter (str): The name of the parameter being validated, used for error context.
            value (object): The value to validate. Must be hashable (it is tested for membership
                in a :class:`frozenset`).

        Raises:
            ValueValidationError: If ``value`` is not one of the allowed choices. The error
                carries the offending value and the sorted allowed set in its ``context``.

        Examples:
            >>> from fedfred._core._validators import _validate_choice
            >>> validate = _validate_choice({1, 2, 3})
            >>> validate("output_type", 2) is None
            True
            >>> try:
            ...     validate("output_type", 9)
            ... except Exception as exc:
            ...     print(type(exc).__name__)
            ValueValidationError
        """
        if value not in self.choices:
            raise ValueValidationError(
                message=f"Invalid value for parameter {parameter!r}.",
                parameter=parameter,
                reason="Value is not one of the allowed choices.",
                context={
                    "value": value,
                    "choices": tuple(sorted(self.choices, key=str)),
                },
            )


@dataclass(frozen=True, slots=True)
class _str_choice_validator:
    """A parameter validator that accepts only strings in a fixed allowed set.

    The string-typed sibling of :class:`_choice_validator`: a callable value object (functor)
    constructed once by :func:`_validate_str_choice` and invoked per parameter with the
    :data:`ParameterValidator` signature ``(name, value) -> None``. ``frozen=True, slots=True``
    makes each instance an immutable, low-overhead closure over ``choices``. It type-checks the
    value as a ``str`` *before* the membership test, so — unlike :class:`_choice_validator` — a
    non-string (hence possibly unhashable) value fails cleanly with a typed
    :class:`TypeValidationError` rather than a bare ``TypeError`` from the ``in`` test. Prefer
    this over :class:`_choice_validator` for any parameter whose valid values are strings.

    Attributes:
        choices (frozenset[str]): The allowed string values for the parameter.

    See Also:
        - :func:`_validate_str_choice`: The factory that builds these instances.
        - :class:`_choice_validator`: The untyped variant, for non-string choice sets.
    """

    choices: frozenset[str]
    """The allowed string values for the parameter — the set membership is tested against."""

    def __call__(self, parameter: str, value: object) -> None:
        """Validate ``value`` is a string and one of the allowed choices.

        Args:
            parameter (str): The name of the parameter being validated, used for error context.
            value (object): The value to validate.

        Raises:
            TypeValidationError: If ``value`` is not a ``str`` (from :func:`_validate_str`,
                checked first).
            ValueValidationError: If ``value`` is a string but not one of the allowed choices.
                The error carries the offending value and the sorted allowed set in its
                ``context``.

        Examples:
            >>> from fedfred._core._validators import _validate_str_choice
            >>> validate = _validate_str_choice({"asc", "desc"})
            >>> validate("sort_order", "asc") is None
            True
            >>> try:
            ...     validate("sort_order", "sideways")
            ... except Exception as exc:
            ...     print(type(exc).__name__)
            ValueValidationError
            >>> try:
            ...     validate("sort_order", 1)
            ... except Exception as exc:
            ...     print(type(exc).__name__)
            TypeValidationError
        """
        _validate_str(parameter, value)

        if value not in self.choices:
            raise ValueValidationError(
                message=f"Invalid value for parameter {parameter!r}.",
                parameter=parameter,
                reason="Value is not one of the allowed choices.",
                context={
                    "value": value,
                    "choices": tuple(sorted(self.choices)),
                },
            )


# Scalar Validators
def _validate_type(parameter: str, value: object, expected_type: type | tuple[type, ...]) -> None:
    """Validate that a parameter value is an instance of an expected type.

    The shared type-check primitive the other scalar validators build on. Raises a structured
    :class:`TypeValidationError` naming the expected and received type names, so a mismatch fails
    with context rather than a bare :func:`isinstance` ``False``.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.
        expected_type (type | tuple[type, ...]): The expected type, or a tuple of acceptable
            types (any match passes).

    Raises:
        TypeValidationError: If ``value`` is not an instance of ``expected_type``. The message
            renders a tuple of types as ``"a | b"``.

    Examples:
        >>> from fedfred._core._validators import _validate_type
        >>> _validate_type("limit", 100, int)
        >>> _validate_type("limit", "100", int)  # doctest: +SKIP
    """
    if not isinstance(value, expected_type):
        expected = (
            " | ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )

        raise TypeValidationError(
            message=f"Invalid type for parameter {parameter!r}.",
            parameter=parameter,
            reason="Type mismatch",
            expected=expected,
            received=type(value).__name__,
        )


def _validate_nonnegative_int(parameter: str, value: object) -> None:
    """Validate that a parameter value is a non-negative integer.

    Booleans are rejected even though :class:`bool` subclasses :class:`int`: ``True``/``False``
    pass the ``int`` type check but are never valid integer parameters, so they are caught
    explicitly after it.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not an ``int``, or is a ``bool``.
        ValueValidationError: If ``value`` is a negative integer.

    Examples:
        >>> from fedfred._core._validators import _validate_nonnegative_int
        >>> _validate_nonnegative_int("limit", 100)
        >>> _validate_nonnegative_int("limit", 0)
        >>> _validate_nonnegative_int("limit", -5)     # doctest: +SKIP
        >>> _validate_nonnegative_int("limit", "100")  # doctest: +SKIP
        >>> _validate_nonnegative_int("limit", True)   # doctest: +SKIP
    """
    _validate_type(parameter, value, int)

    if isinstance(value, bool):
        raise TypeValidationError(
            message=f"Invalid type for parameter {parameter!r}.",
            parameter=parameter,
            reason="Boolean is not accepted where integer is required.",
            expected="int",
            received="bool",
        )

    value_int = cast(int, value)

    if value_int < 0:
        raise ValueValidationError(
            message=f"Invalid value for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected non-negative integer.",
            context={"value": value_int},
        )


def _validate_bool(parameter: str, value: object) -> None:
    """Validate that a parameter value is a boolean.

    An ``int`` (even ``0`` or ``1``) is rejected: :func:`isinstance(1, bool)` is ``False``, so
    only true :class:`bool` instances pass. This is the mirror of
    :func:`_validate_nonnegative_int`'s bool rejection.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a ``bool``.

    Examples:
        >>> from fedfred._core._validators import _validate_bool
        >>> _validate_bool("flag", True)
        >>> _validate_bool("flag", False)
        >>> _validate_bool("flag", "True")  # doctest: +SKIP
        >>> _validate_bool("flag", 1)       # doctest: +SKIP
    """
    _validate_type(parameter, value, bool)


def _validate_str(parameter: str, value: object) -> None:
    """Validate that a parameter value is a string.

    Accepts any :class:`str`, including the empty string — emptiness is a separate constraint
    (see :func:`_validate_nonempty_str`).

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a ``str``.

    Examples:
        >>> from fedfred._core._validators import _validate_str
        >>> _validate_str("name", "GDP")
        >>> _validate_str("name", "")
        >>> _validate_str("name", 123)  # doctest: +SKIP
    """
    _validate_type(parameter, value, str)


def _validate_nonempty_str(parameter: str, value: object) -> None:
    """Validate that a parameter value is a non-empty string.

    Type-checks as a ``str`` first, then rejects the empty string. Emptiness is tested by
    truthiness (``not value``), so only ``""`` is rejected — a whitespace-only string such as
    ``"   "`` is **not** stripped and passes.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a ``str``.
        ValueValidationError: If ``value`` is the empty string.

    Examples:
        >>> from fedfred._core._validators import _validate_nonempty_str
        >>> _validate_nonempty_str("name", "GDP")
        >>> _validate_nonempty_str("name", "")     # doctest: +SKIP
        >>> _validate_nonempty_str("name", "   ")  # passes: whitespace is not empty
        >>> _validate_nonempty_str("name", 123)    # doctest: +SKIP
    """
    _validate_str(parameter, value)

    if not value:
        raise ValueValidationError(
            message=f"Invalid value for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected non-empty string.",
            context={"value": value},
        )


def _validate_choice(choices: set[int]) -> ParameterValidator:
    """Build a validator that checks a value is one of ``choices`` (non-string variant).

    Returns a :class:`_choice_validator` bound to a frozen copy of ``choices``. Use this for
    non-string choice sets (e.g. ``output_type``'s ``{1, 2, 3, 4}``); for string choices prefer
    :func:`_validate_str_choice`, which type-checks the value as a ``str`` first.

    Args:
        choices (set[int]): The allowed values for the parameter. Copied into a
            :class:`frozenset`, so members must be hashable.

    Returns:
        ParameterValidator: A validator that raises :class:`ValueValidationError` if a value is
        not in ``choices``.

    Examples:
        >>> from fedfred._core._validators import _validate_choice
        >>> validate_output_type = _validate_choice({1, 2, 3, 4})
        >>> validate_output_type("output_type", 1)
        >>> validate_output_type("output_type", 9)  # doctest: +SKIP
    """
    return _choice_validator(frozenset(choices))


def _validate_str_choice(choices: set[str]) -> ParameterValidator:
    """Build a validator that checks a value is a string in ``choices``.

    Returns a :class:`_str_choice_validator` bound to a frozen copy of ``choices``. Type-checks
    the value as a ``str`` before the membership test, so a non-string fails with
    :class:`TypeValidationError` rather than a bare ``TypeError``. The string counterpart of
    :func:`_validate_choice`.

    Args:
        choices (set[str]): The allowed string values for the parameter.

    Returns:
        ParameterValidator: A validator that raises if a value is not a string
        (:class:`TypeValidationError`) or not in ``choices`` (:class:`ValueValidationError`).

    Examples:
        >>> from fedfred._core._validators import _validate_str_choice
        >>> validate_sort_order = _validate_str_choice({"asc", "desc"})
        >>> validate_sort_order("sort_order", "asc")
        >>> validate_sort_order("sort_order", "ascending")  # doctest: +SKIP
    """
    return _str_choice_validator(frozenset(choices))


def _validate_yyyy_mm_dd(parameter: str, value: object) -> None:
    """Validate that a parameter value is a ``YYYY-MM-DD`` date string.

    Type-checks as a ``str``, then parses with ``datetime.strptime(value, "%Y-%m-%d")`` — the
    real accept/reject contract. Note that ``strptime`` accepts non-zero-padded fields, so
    ``"2020-1-1"`` is valid too; only the ordering and separators are strictly enforced.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` does not parse as ``%Y-%m-%d`` (wrong format,
            impossible date such as ``"2020-13-01"``, or extra content).

    Examples:
        >>> from fedfred._core._validators import _validate_yyyy_mm_dd
        >>> _validate_yyyy_mm_dd("realtime_start", "2020-01-01")
        >>> _validate_yyyy_mm_dd("realtime_start", "2020-13-01")  # doctest: +SKIP
        >>> _validate_yyyy_mm_dd("realtime_start", "01-01-2020")  # doctest: +SKIP
        >>> _validate_yyyy_mm_dd("realtime_start", 20200101)      # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    try:
        datetime.strptime(value_str, "%Y-%m-%d")

    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid date string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected YYYY-MM-DD date string.",
            context={
                "value": value_str,
                "expected_format": "YYYY-MM-DD",
            },
            original_exception=exc,
        ) from exc


def _validate_hh_mm(parameter: str, value: object) -> None:
    """Validate that a parameter value is an ``HH:MM`` 24-hour time string.

    Type-checks as a ``str``, then parses with ``datetime.strptime(value, "%H:%M")``. As with the
    date validator, ``strptime`` accepts non-zero-padded hours (``"1:30"`` is valid); the range
    is 24-hour (``00``-``23`` hours, ``00``-``59`` minutes).

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` does not parse as ``%H:%M`` (out-of-range, 12-hour
            with meridiem, or wrong format).

    Examples:
        >>> from fedfred._core._validators import _validate_hh_mm
        >>> _validate_hh_mm("start_time", "14:30")
        >>> _validate_hh_mm("start_time", "25:00")    # doctest: +SKIP
        >>> _validate_hh_mm("start_time", "14:60")    # doctest: +SKIP
        >>> _validate_hh_mm("start_time", "2:30 PM")  # doctest: +SKIP
        >>> _validate_hh_mm("start_time", 1430)       # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    try:
        datetime.strptime(value_str, "%H:%M")

    except ValueError as exc:
        raise ValueValidationError(
            message=f"Invalid time string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Expected HH:MM time string.",
            context={
                "value": value_str,
                "expected_format": "HH:MM",
            },
            original_exception=exc,
        ) from exc


def _validate_semicolon_list_string(parameter: str, value: object) -> None:
    """Validate a semicolon-separated list of non-empty terms.

    Type-checks as a ``str``, rejects the empty string, then splits on ``;`` and rejects any
    empty term (so leading, trailing, or doubled ``;`` fail). Note terms are checked only for
    emptiness by exact ``== ""`` — a whitespace-only term such as ``"tag1; ;tag2"`` is not
    stripped and passes.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is the empty string, or any ``;``-separated term is
            empty.

    Examples:
        >>> from fedfred._core._validators import _validate_semicolon_list_string
        >>> _validate_semicolon_list_string("tag_names", "tag1;tag2;tag3")
        >>> _validate_semicolon_list_string("tag_names", "")            # doctest: +SKIP
        >>> _validate_semicolon_list_string("tag_names", "tag1;;tag3")  # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    if value_str == "":
        raise ValueValidationError(
            message=f"Invalid list-string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Value cannot be empty.",
            context={"value": value_str},
        )

    terms = value_str.split(";")

    if any(term == "" for term in terms):
        raise ValueValidationError(
            message=f"Invalid list-string for parameter {parameter!r}.",
            parameter=parameter,
            reason="Empty terms are not permitted.",
            context={"value": value_str, "separator": ";"},
        )


def _validate_comma_date_list_string(parameter: str, value: object) -> None:
    """Validate a comma-separated list of ``YYYY-MM-DD`` dates.

    Type-checks as a ``str``, rejects the empty string, splits on ``,`` and rejects empty terms,
    then validates every term as a ``%Y-%m-%d`` date — collecting *all* invalid terms into one
    error rather than failing on the first. Same non-zero-padding leniency as
    :func:`_validate_yyyy_mm_dd`.

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is empty, contains an empty term, or contains any term
            that is not a valid ``YYYY-MM-DD`` date (the invalid terms are listed in ``context``).

    Examples:
        >>> from fedfred._core._validators import _validate_comma_date_list_string
        >>> _validate_comma_date_list_string("vintage_dates", "2020-01-01,2020-02-01,2020-03-01")
        >>> _validate_comma_date_list_string("vintage_dates", "") # doctest: +SKIP
        >>> _validate_comma_date_list_string(
        ...     "vintage_dates", "2020-01-01,,2020-03-01"
        ... ) # doctest: +SKIP
        >>> _validate_comma_date_list_string("vintage_dates", "2020-01-01,nope") # doctest: +SKIP
    """
    _validate_str(parameter, value)

    value_str = cast(str, value)

    if value_str == "":
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="Value cannot be empty.",
            context={"value": value_str},
        )

    terms = value_str.split(",")

    if any(term == "" for term in terms):
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="Empty date terms are not permitted.",
            context={"value": value_str, "separator": ","},
        )

    invalid_terms: list[str] = []

    for term in terms:
        try:
            datetime.strptime(term, "%Y-%m-%d")
        except ValueError:
            invalid_terms.append(term)

    if invalid_terms:
        raise ValueValidationError(
            message=f"Invalid vintage_dates for parameter {parameter!r}.",
            parameter=parameter,
            reason="One or more date terms are invalid.",
            context={
                "value": value_str,
                "invalid_terms": tuple(invalid_terms),
                "expected_format": "YYYY-MM-DD",
            },
        )


def _validate_series_id(parameter: str, value: object) -> None:
    """Validate a non-empty series identifier containing no spaces.

    Requires a non-empty string, then rejects any value containing a space. Note the check is for
    the literal space character (``" " in value``), **not** general whitespace — a tab or newline
    is not caught (see Notes).

    Args:
        parameter (str): The name of the parameter being validated, used for error context.
        value (object): The value to validate.

    Raises:
        TypeValidationError: If ``value`` is not a string.
        ValueValidationError: If ``value`` is the empty string or contains a space character.

    Examples:
        >>> from fedfred._core._validators import _validate_series_id
        >>> _validate_series_id("series_id", "GDP")
        >>> _validate_series_id("series_id", "GDP2020")
        >>> _validate_series_id("series_id", "")          # doctest: +SKIP
        >>> _validate_series_id("series_id", "GDP 2020")  # doctest: +SKIP
        >>> _validate_series_id("series_id", 12345)       # doctest: +SKIP

    Notes:
        Only the space character is rejected; tabs, newlines, and other whitespace pass. If a
        series id must be entirely whitespace-free, widen the check (see the code-level note).
    """
    _validate_nonempty_str(parameter, value)

    value_str = cast(str, value)

    if " " in value_str:
        raise ValueValidationError(
            message=f"Invalid series_id for parameter {parameter!r}.",
            parameter=parameter,
            reason="Series ID cannot contain whitespace.",
            context={"value": value_str},
        )


def _validate_api_key(api_key: str) -> None:
    """Validate that ``api_key`` is a non-blank string.

    Type-checks as a ``str``, then rejects a blank value using ``.strip()`` — so a whitespace-only
    key (``"   "``) is rejected, not just the empty string. This is the "non-blank" contract, and
    it matches how :func:`_set_api_key` stores the key (stripped). Extracted so the key-setting
    mutator and any other caller share one validation.

    Args:
        api_key (str): The API key to validate.

    Raises:
        TypeValidationError: If ``api_key`` is not a string.
        ValueValidationError: If ``api_key`` is empty or whitespace-only.

    Examples:
        >>> from fedfred._core._validators import _validate_api_key
        >>> _validate_api_key("abc123")
        >>> _validate_api_key("   ")  # doctest: +SKIP
    """
    if not isinstance(api_key, str):
        raise TypeValidationError(
            message="Invalid type for api_key.",
            parameter="api_key",
            reason="API key must be a string.",
            context={"value": api_key},
        )

    if not api_key.strip():
        raise ValueValidationError(
            message="Invalid api_key.",
            parameter="api_key",
            reason="API key must be a non-empty string.",
            context={"value": api_key},
        )


def _validate_service(service: Service) -> None:
    """Validate that ``service`` is a recognized service identity.

    Membership is checked against :data:`_VALID_SERVICES` (derived from the :data:`Service` type
    via ``get_args``), not the runtime API-key store, so the pure validation layer stays
    independent of stateful registries. Because the set is type-derived, it can never drift from
    :data:`Service`.

    Args:
        service (Service): The service identity to validate.

    Raises:
        TypeValidationError: If ``service`` is not a string.
        ValueValidationError: If ``service`` is not one of the known services.

    Examples:
        >>> from fedfred._core._validators import _validate_service
        >>> _validate_service("fred")
        >>> _validate_service("bogus")  # doctest: +SKIP
    """
    if not isinstance(service, str):
        raise TypeValidationError(
            message="Invalid type for service.",
            parameter="service",
            reason="Service must be a string.",
            context={"value": service},
        )

    if service not in _VALID_SERVICES:
        raise ValueValidationError(
            message=f"Unknown service: {service!r}.",
            parameter="service",
            reason=f"Expected: {sorted(_VALID_SERVICES)}.",
            context={"value": service},
        )


def _validate_dataframe_backend(backend: DataFrameBackend) -> None:
    """Validate that ``backend`` is a recognized DataFrame backend.

    Type-checks as a ``str``, then checks membership against :data:`_VALID_DATAFRAME_BACKENDS`.
    Consulted by :func:`_set_dataframe_backend` and :func:`_resolve_dataframe_backend` so an
    invalid backend never reaches the global state or a conversion.

    Args:
        backend (DataFrameBackend): The DataFrame backend name to validate.

    Raises:
        TypeValidationError: If ``backend`` is not a string.
        ValueValidationError: If ``backend`` is not one of :data:`_VALID_DATAFRAME_BACKENDS`.

    Examples:
        >>> from fedfred._core._validators import _validate_dataframe_backend
        >>> _validate_dataframe_backend("pandas")
        >>> _validate_dataframe_backend("numpy")  # doctest: +SKIP
    """
    if not isinstance(backend, str):
        raise TypeValidationError(
            message="Invalid type for backend.",
            parameter="backend",
            reason="Backend must be a string.",
            context={"value": backend},
        )

    if backend not in _VALID_DATAFRAME_BACKENDS:
        raise ValueValidationError(
            message=f"Unknown DataFrame backend: {backend!r}.",
            parameter="backend",
            reason=f"Expected one of: {list(_VALID_DATAFRAME_BACKENDS)}.",
            context={"value": backend},
        )


def _validate_geodataframe_backend(backend: GeoDataFrameBackend) -> None:
    """Validate that ``backend`` is a recognized GeoDataFrame backend.

    Type-checks as a ``str``, then checks membership against :data:`_VALID_GEODATAFRAME_BACKENDS`.
    Consulted by :func:`_set_geodataframe_backend` and :func:`_resolve_geodataframe_backend` so an
    invalid backend never reaches the global state or a conversion.

    Args:
        backend (GeoDataFrameBackend): The GeoDataFrame backend name to validate.

    Raises:
        TypeValidationError: If ``backend`` is not a string.
        ValueValidationError: If ``backend`` is not one of :data:`_VALID_GEODATAFRAME_BACKENDS`.

    Examples:
        >>> from fedfred._core._validators import _validate_geodataframe_backend
        >>> _validate_geodataframe_backend("geopandas")
        >>> _validate_geodataframe_backend("shapely")  # doctest: +SKIP
    """
    if not isinstance(backend, str):
        raise TypeValidationError(
            message="Invalid type for backend.",
            parameter="backend",
            reason="Backend must be a string.",
            context={"value": backend},
        )

    if backend not in _VALID_GEODATAFRAME_BACKENDS:
        raise ValueValidationError(
            message=f"Unknown GeoDataFrame backend: {backend!r}.",
            parameter="backend",
            reason=f"Expected one of: {list(_VALID_GEODATAFRAME_BACKENDS)}.",
            context={"value": backend},
        )

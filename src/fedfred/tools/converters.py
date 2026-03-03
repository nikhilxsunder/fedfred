
import asyncio
from typing import TYPE_CHECKING, Union
import pandas as pd
from ..__about__ import __title__, __version__, __author__, __email__, __license__, __copyright__, __description__, __docs__, __repository__
from ._converter_mappings import _FREQUENCIES_MAP

if TYPE_CHECKING:
    import polars as pl # pragma: no cover

def _pandas_frequency_converter(frequency: str) -> str:
    """Convert FRED native frequency strings to pandas compatible ones.

    Args:
        frequency (str): Input frequency string.

    Returns:
        str: Coerced frequency string compatible with pandas.

    Raises:
        ValueError: If the input frequency is not recognized.

    Examples:
        >>> import fedfred as fd
        >>> freq = "a"
        >>> pd_freq = fd.Helpers.pd_frequency_conversion(freq)
        >>> print(pd_freq)
        Y

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.pd_frequency_conversion.html

    See Also:
        - :meth:`Helpers.to_pd_series`: Convert a Series or DataFrame to a pandas Series with DatetimeIndex.
    """

    frequency = frequency.upper()
    if frequency in _FREQUENCIES_MAP:
        return _FREQUENCIES_MAP[frequency]
    else:
        raise ValueError(f"Frequency '{frequency}' is not recognized.")

def _pandas_series_converter(data: Union[pd.Series, pd.DataFrame], name: str) -> pd.Series:
    """Accepts a Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.

    Args:
        data (pandas.Series | pandas.DataFrame): Input data to be converted.
        name (str): Name to assign to the resulting Series.

    Returns:
        pandas.Series: A float Series with DatetimeIndex and the given `name`.

    Raises:
        TypeError: If the input is neither a pandas.Series nor a pandas.DataFrame.

    Examples:
        >>> import fedfred as fd
        >>> import pandas as pd
        >>> data = pd.DataFrame({
        >>>     "date": ["2020-01-01", "2020-02-01"],
        >>>     "value": [100, 200]
        >>> })
        >>> series = fd.Helpers.to_pd_series(data, name="My Series")
        >>> print(series)
        2020-01-01    100.0
        2020-02-01    200.0
        Name: My Series, dtype: float64

    Notes:
        This method handles both Series and DataFrame inputs, ensuring the output is a properly formatted pandas Series.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pd_series.html

    See Also:
        - :meth:`Helpers.pd_frequency_conversion`: Convert FRED native frequency strings to pandas compatible ones.
    """

    if isinstance(data, pd.Series):
        s = data.copy()
        s.index = pd.to_datetime(s.index)
        s = s.astype(float)
        s.name = name
        return s

    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pd.Series or pd.DataFrame")

    df: pd.DataFrame = data.copy()
    assert isinstance(df.index.name, str)
    if df.index.name and df.index.name.lower() == "date":
        idx: Union[pd.DatetimeIndex, pd.Series] = pd.to_datetime(df.index)
    elif "date" in df.columns:
        idx = pd.to_datetime(df["date"])
    else:
        cand = next((c for c in df.columns if "date" in c.lower()), None)
        if cand is not None:
            idx = pd.to_datetime(df[cand])
        else:
            idx = pd.to_datetime(df.index)
    if "value" in df.columns:
        vals = pd.to_numeric(df["value"], errors="coerce")
    else:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            vals = pd.to_numeric(df.iloc[:, -1], errors="coerce")
        else:
            vals = pd.to_numeric(df[num_cols[0]], errors="coerce")

    s = pd.Series(vals.values, index=idx, name=name).astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.index = pd.to_datetime(s.index)
    return s

def _polars_series_converter() -> 'pl.Series': # Add this helpers logic before release
    """Accepts a Polars Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.
    
    Args:
        data (polars.Series | polars.DataFrame): Input data to be converted.
        name (str): Name to assign to the resulting Series.

    Returns:
        polars.Series: A float Series with DatetimeIndex and the given `name`.

    Raises:
        TypeError: If the input is neither a polars.Series nor a polars.DataFrame

    Examples:

    Notes:

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pl_series.html
    
    See Also:
        - :meth:`Helpers.to_pd_series`: Convert a Series or DataFrame to a pandas Series with DatetimeIndex.
    """

    return None

async def _pandas_frequency_converter_async(frequency: str) -> str:
    """Asynchronously convert FRED native frequency strings to pandas compatible ones.

    Args:
        frequency (str): Input frequency string.

    Returns:
        str: Coerced frequency string compatible with pandas.

    Raises:
        None

    Examples:
        >>> import asyncio
        >>> import fedfred as fd
        >>> frequency = "WEF"
        >>> async def main():
        >>>     result = await fd.AsyncHelpers.pd_frequency_conversion(frequency)
        >>>     print(result)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        W-FRI

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.pd_frequency_conversion.html

    See Also:
        - :meth:`AsyncHelpers.pd_frequency_conversion`: Convert FRED native frequency strings to pandas compatible ones asynchronously.
    """

    return await asyncio.to_thread(_pandas_frequency_converter, frequency)

async def _pandas_series_converter_async(data: Union[pd.Series, pd.DataFrame], name: str) -> pd.Series:
    """Asynchronously accepts a Series or a DataFrame with 'date' and 'value' columns (fedfred style) and returns a float Series with DatetimeIndex and the given name.

    Args:
        data (pandas.Series | pandas.DataFrame): Input data to be converted.
        name (str): Name to assign to the resulting Series.

    Returns:
        pandas.Series: A float Series with DatetimeIndex and the given `name`.

    Raises:
        TypeError: If the input is neither a pandas.Series nor a pandas.DataFrame.

    Examples:
        >>> import asyncio
        >>> import pandas as pd
        >>> import fedfred as fd
        >>> data = pd.DataFrame({
        >>>     "date": ["2020-01-01", "2020-02-01"],
        >>>     "value": [100, 200]
        >>> })
        >>> async def main():
        >>>     series = await fd.AsyncHelpers.to_pd_series(data, name="My Series")
        >>>     print(series)
        >>> if __name__ == "__main__":
        >>>     asyncio.run(main())
        2020-01-01    100.0
        2020-02-01    200.0
        Name: My Series, dtype: float64

    Notes:
        This method handles both Series and DataFrame inputs, ensuring the output is a properly formatted pandas Series.

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.to_pd_series.html

    See Also:
        - :meth:`AsyncHelpers.pd_frequency_conversion`: Asynchronously convert FRED native frequency strings to pandas compatible ones.
    """

    return await asyncio.to_thread(_pandas_series_converter, data, name)

async def _polars_series_converter_async() -> 'pl.Series': # Add this helpers logic before release
    """Asynchronously accepts a Polars Series or a DataFrame with 'date' and 'value' columns and returns a float Series with DatetimeIndex and the given name.
    
    Args:
        data (polars.Series | polars.DataFrame): Input data to be converted.
        name (str): Name to assign to the resulting Series.

    Returns:
        polars.Series: A float Series with DatetimeIndex and the given `name`.

    Raises:
        TypeError: If the input is neither a polars.Series nor a polars.DataFrame

    Examples:

    Notes:

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.Helpers.to_pl_series.html
    
    See Also:
        - :meth:`AsyncHelpers.to_pd_series`: Convert a Series or DataFrame to a pandas Series with DatetimeIndex.
    """

    return await asyncio.to_thread(_polars_series_converter)



from typing import List, Dict
from dataclasses import dataclass
import asyncio

@dataclass(slots=True)
class SeriesGroup:
    """A class used to represent a SeriesGroup.

    Represents a single series group in the Federal Reserve Economic Data (FRED) database. A series group is a collection of related
    economic data series that share common characteristics, such as region type, seasonality, units, and frequency. Each series group has a title, region type, series group identifier,
    seasonality, units, frequency, and date range.

    Attributes:
        title (str): The title of the series group.
        region_type (str): The region type of the series group.
        series_group (str): The identifier of the series group.
        season (str): The seasonality of the series group.
        units (str): The units of the series group.
        frequency (str): The frequency of the series group.
        min_date (str): The minimum date of the series group.
        max_date (str): The maximum date of the series group.

    Examples:
        >>> import fedfred as fd
        >>> fred_client = fd.Fred('your_api_key')
        >>> series_groups = fred_client.get_series_group('GDP')
        >>> for series_group in series_groups:
        >>>     print(series_group.title)
        'Gross Domestic Product'
        'Real Gross Domestic Product'...

    References:
        - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.SeriesGroup.html

    See Also:
        - :class:`fedfred.Series`: For the object representation of a FRED series.
        - :meth:`fedfred.Fred.get_series_group`: For retrieving series group information from the FRED API.
    """
    title: str
    """The title of the series group."""

    region_type: str
    """The region type of the series group."""

    series_group: str
    """The identifier of the series group."""

    season: str
    """The seasonality of the series group."""

    units: str
    """The units of the series group."""

    frequency: str
    """The frequency of the series group."""

    min_date: str
    """The minimum date of the series group."""

    max_date: str
    """The maximum date of the series group."""

    @classmethod
    def to_object(cls, response: Dict) -> List["SeriesGroup"]:
        """Parses the FRED API response and returns a list of SeriesGroup objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[SeriesGroup]: A list of SeriesGroup objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "series_group": [
            >>>         {
            >>>             "title": "Gross Domestic Product",
            >>>             "region_type": "NATIONAL",
            >>>             "series_group": "GDP",
            >>>             "season": "SA",
            >>>             "units": "Billions of Dollars",
            >>>             "frequency": "Quarterly",
            >>>             "min_date": "1947-01-01",
            >>>             "max_date": "2024-06-01"
            >>>         }
            >>>     ]
            >>> }
            >>> series_groups = fd.SeriesGroup.to_object(response)
            >>> for series_group in series_groups:
            >>>     print(series_group.title)
            'Gross Domestic Product'

        Notes:
            This method assumes that the input response dictionary contains a 'series_group' key with a list of series group data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.SeriesGroup.to_object.html
        """

        if "series_group" not in response:
            raise ValueError("Invalid API response: Missing 'series_group' field")
        series_group_data = response["series_group"]
        if isinstance(series_group_data, dict):
            series_group_data = [series_group_data]
        series_groups = [
            cls(
                title=series_group["title"],
                region_type=series_group["region_type"],
                series_group=series_group["series_group"],
                season=series_group["season"],
                units=series_group["units"],
                frequency=series_group["frequency"],
                min_date=series_group["min_date"],
                max_date=series_group["max_date"]
            )
            for series_group in series_group_data
        ]
        if not series_groups:
            raise ValueError("No series groups found in the response")
        return series_groups

    @classmethod
    async def to_object_async(cls, response: Dict) -> List["SeriesGroup"]:
        """Asynchronously parses the FRED API response and returns a list of SeriesGroup objects.

        Args:
            response (Dict): The FRED API response.

        Returns:
            List[SeriesGroup]: A list of SeriesGroup objects.

        Raises:
            ValueError: If the response does not contain the expected data.

        Examples:
            >>> import fedfred as fd
            >>> response = {
            >>>     "series_group": [
            >>>         {
            >>>             "title": "Gross Domestic Product",
            >>>             "region_type": "NATIONAL",
            >>>             "series_group": "GDP",
            >>>             "season": "SA",
            >>>             "units": "Billions of Dollars",
            >>>             "frequency": "Quarterly",
            >>>             "min_date": "1947-01-01",
            >>>             "max_date": "2024-06-01"
            >>>         }
            >>>     ]
            >>> }
            >>> async def main():
            >>>     series_groups = await fd.SeriesGroup.to_object_async(response)
            >>>     for series_group in series_groups:
            >>>         print(series_group.title)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            'Gross Domestic Product'

        Notes:
            This method assumes that the input response dictionary contains a 'series_group' key with a list of series group data.

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.objects.SeriesGroup.to_object_async.html
        """

        return await asyncio.to_thread(cls.to_object, response)

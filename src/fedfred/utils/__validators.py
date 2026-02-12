from typing import Optional
from datetime import datetime
import asyncio

class __Validators:

    @staticmethod
    def __datestring_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate date-string formatted parameters.

        Args:
            param (str): Date string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid date string in YYYY-MM-DD format.

        Examples:
            >>> import fedfred as fd
            >>> param = "2020-01-01"
            >>> result = fd.__datestring_validation(param)
            >>> print(result)
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____datestring_validation.html

        See Also:
            - :meth:`__datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format.
        """

        try:
            datetime.strptime(param, "%Y-%m-%d")
            return None
        except ValueError as e:
            raise ValueError(f"Value Error: {e}" ) from e

    @staticmethod
    def __liststring_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate list-string formatted parameters.

        Args:
            param (str): Semicolon-separated string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid semicolon-separated string.

        Examples:
            >>> import fedfred as fd
            >>> param = "tag1;tag2;tag3"
            >>> result = fd.__liststring_validation(param)
            >>> print(result)
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____liststring_validation.html

        See Also:
            - :meth:`__liststring_conversion`: Convert a list of strings to a semicolon-separated string.
        """

        if not isinstance(param, str):
            raise ValueError("Parameter must be a string")
        terms = param.split(';')
        if any(term == '' for term in terms):
            raise ValueError("Semicolon-separated list cannot contain empty terms")
        if not all(term.isalnum() for term in terms):
            raise ValueError("Each term must be alphanumeric and contain no whitespace")
        else:
            return None

    @staticmethod
    def __vintage_dates_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate vintage_dates parameters.

        Args:
            param (str): Comma-separated string of vintage dates.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid vintage_dates string.

        Examples:
            >>> import fedfred as fd
            >>> param = "2020-01-01"
            >>> result = fd.__vintage_dates_validation(param)
            >>> print(result)
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____vintage_dates_validation.html

        See Also:
            - :meth:`__vintage_dates_type_conversion`: Convert a vintage_dates parameter to a string.
        """

        if not isinstance(param, str):
            raise ValueError("Parameter must be a string")
        if param == '':
            raise ValueError("vintage_dates cannot be empty")
        terms = param.split(',')
        for term in terms:
            try:
                datetime.strptime(term, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Value Error: {e}" ) from e
        return None

    @staticmethod
    def __hh_mm_datestring_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate hh:mm formatted parameters.

        Args:
            param (str): Time string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid time string in HH:MM format.

        Examples:
            >>> import fedfred as fd
            >>> param = "15:30"
            >>> result = fd.__hh_mm_datestring_validation(param)
            >>> print(result)
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.____hh_mm_datestring_validation.html

        See Also:
            - :meth:`__datetime_hh_mm_conversion`: Convert a datetime object to a string in HH:MM format.
        """

        if not isinstance(param, str):
            raise ValueError("Parameter must be a string")
        try:
            datetime.strptime(param, "%H:%M")
            return None
        except ValueError as e:
            raise ValueError(f"Value Error: {e}" ) from e

class __AsyncValidators:
    @staticmethod
    async def __datestring_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate date-string formatted parameter asynchronously.

        Args:
            param (str): Date string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid date string in YYYY-MM-DD format.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> param = "2020-01-01"
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.datestring_validation(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.datestring_validation.html

        See Also:
            - :meth:`AsyncHelpers.datetime_conversion`: Convert a datetime object to a string in YYYY-MM-DD format asynchronously.
        """

        return await asyncio.to_thread(__Validators.__datestring_validation, param)

    @staticmethod
    async def __liststring_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate list-string formatted parameters asynchronously.

        Args:
            param (str): Semicolon-separated string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid semicolon-separated string.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> param = "GDP;CPI;UNRATE"
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.liststring_validation(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None
        
        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.liststring_validation.html

        See Also:
            - :meth:`AsyncHelpers.liststring_conversion`: Convert a list of strings to a semicolon-separated string asynchronously.
        """

        return await asyncio.to_thread(__Validators.__liststring_validation, param)

    @staticmethod
    async def __vintage_dates_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate vintage_dates parameters asynchronously.

        Args:
            param (str): Comma-separated string of vintage dates.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid vintage_dates string.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> param = "2020-01-01"
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.vintage_dates_validation(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.vintage_dates_validation.html

        See Also:
            - :meth:`AsyncHelpers.vintage_dates_type_conversion`: Convert a vintage_dates parameter to a string asynchronously.
        """

        return await asyncio.to_thread(__Validators.__vintage_dates_validation, param)

    @staticmethod
    async def __hh_mm_datestring_validation(param: str) -> Optional[ValueError]:
        """Helper method to validate hh:mm formatted parameters asynchronously.

        Args:
            param (str): Time string to validate.

        Returns:
            None

        Raises:
            ValueError: If param is not a valid time string in HH:MM format.

        Examples:
            >>> import asyncio
            >>> import fedfred as fd
            >>> param = "14:30"
            >>> async def main():
            >>>     result = await fd.AsyncHelpers.hh_mm_datestring_validation(param)
            >>>     print(result)
            >>> if __name__ == "__main__":
            >>>     asyncio.run(main())
            None

        References:
            - fedfred package documentation. https://nikhilxsunder.github.io/fedfred/api/_autosummary/fedfred.helpers.AsyncHelpers.hh_mm_datestring_validation.html

        See Also:
            - :meth:`AsyncHelpers.datetime_hh_mm_conversion`: Convert a datetime object to a string in HH:MM format asynchronously.
        """

        return await asyncio.to_thread(__Validators.__hh_mm_datestring_validation, param)

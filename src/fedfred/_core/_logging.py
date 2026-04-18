"""fedfred._core._logging

This module provides internal logging abstractions for the fedfred core package.
"""

from dataclasses import dataclass
import logging
from typing import Optional, Any

@dataclass(slots=True, frozen=True)
class LoggingConfig:
    """Configuration for a fedfred logger instance.

    Attributes:
        enabled (bool): Whether logging is enabled for the owning client instance.
        level (int): Logging level to apply to the resolved logger.
        logger (Optional[logging.Logger]): User-supplied logger. If ``None``, the default
            ``fedfred`` package logger is used.

    Notes:
        This configuration is intended to be stored per-client-instance rather than globally.
        This allows one :class:`FredAPI` instance to emit logs while another remains silent.
    """

    enabled: bool = False
    """Whether logging is enabled for the owning client instance."""

    level: int = logging.INFO
    """Logging level to apply to the resolved logger."""

    logger: Optional[logging.Logger] = None
    """Optional user-supplied logger instance."""


@dataclass(slots=True)
class FedFredLogger:
    """Thin instance-scoped logging wrapper for fedfred internals.

    This wrapper provides a minimal-overhead logging surface for internal modules. When
    logging is disabled, all methods return immediately without emitting records.

    Attributes:
        enabled (bool): Whether this logger emits records.
        logger (logging.Logger): Underlying standard-library logger.

    Notes:
        This class is intentionally small and dependency-free. It should be passed through
        internal layers instead of relying on mutable global logging state.
    """

    enabled: bool
    """Whether this logger emits records."""

    logger: logging.Logger
    """Underlying standard-library logger."""

    def debug(self, message: str, **extra: Any) -> None:
        """Emit a DEBUG log record if logging is enabled.

        Args:
            message (str): Log message.
            **extra (Any): Structured metadata attached to the record.
        """
        if not self.enabled:
            return
        self.logger.debug(message, extra=extra if extra else None)

    def info(self, message: str, **extra: Any) -> None:
        """Emit an INFO log record if logging is enabled.

        Args:
            message (str): Log message.
            **extra (Any): Structured metadata attached to the record.
        """
        if not self.enabled:
            return
        self.logger.info(message, extra=extra if extra else None)

    def warning(self, message: str, **extra: Any) -> None:
        """Emit a WARNING log record if logging is enabled.

        Args:
            message (str): Log message.
            **extra (Any): Structured metadata attached to the record.
        """
        if not self.enabled:
            return
        self.logger.warning(message, extra=extra if extra else None)

    def error(self, message: str, **extra: Any) -> None:
        """Emit an ERROR log record if logging is enabled.

        Args:
            message (str): Log message.
            **extra (Any): Structured metadata attached to the record.
        """
        if not self.enabled:
            return
        self.logger.error(message, extra=extra if extra else None)

    def exception(self, message: str, **extra: Any) -> None:
        """Emit an ERROR log record with exception information if logging is enabled.

        Args:
            message (str): Log message.
            **extra (Any): Structured metadata attached to the record.
        """
        if not self.enabled:
            return
        self.logger.exception(message, extra=extra if extra else None)


def _coerce_log_level(level: int | str) -> int:
    """Normalize a log level input to a standard-library logging level integer.

    Args:
        level (int | str): Logging level as either a standard integer constant or a
            case-insensitive string such as ``"DEBUG"``, ``"INFO"``, or ``"WARNING"``.

    Returns:
        int: Resolved logging level integer.

    Raises:
        TypeError: If ``level`` is not an ``int`` or ``str``.
        ValueError: If ``level`` is a string that does not map to a valid logging level.
    """
    if isinstance(level, int):
        return level

    if not isinstance(level, str):
        raise TypeError("level must be an int or str")

    normalized = level.strip().upper()

    mapping = {
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.FATAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    if normalized not in mapping:
        raise ValueError(
            "Invalid log level string. Expected one of: "
            "'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'."
        )

    return mapping[normalized]


def _get_default_logger() -> logging.Logger:
    """Return the default fedfred package logger.

    Returns:
        logging.Logger: Default package logger.

    Notes:
        A :class:`logging.NullHandler` is attached only if the logger has no handlers.
        This avoids noisy library-side configuration while remaining safe for users who
        have not configured logging themselves.
    """
    logger = logging.getLogger("fedfred")

    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger


def _build_logger(config: LoggingConfig) -> FedFredLogger:
    """Build an instance-scoped fedfred logger wrapper from configuration.

    Args:
        config (LoggingConfig): Logging configuration for the owning client instance.

    Returns:
        FedFredLogger: Bound logging wrapper.

    Notes:
        This function does not attach stream/file handlers and does not globally configure
        the logging subsystem. Library-side logging should remain non-invasive.
    """
    logger = config.logger if config.logger is not None else _get_default_logger()
    logger.setLevel(config.level)
    return FedFredLogger(enabled=config.enabled, logger=logger)
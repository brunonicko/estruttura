"""Estruttura exceptions."""

__all__ = [
    "ProcessingError",
    "ConversionError",
    "ValidationError",
    "InvalidTypeError",
    "SerializationError",
]


class ProcessingError(Exception):
    """Error while processing a value through a relationship."""


class ConversionError(ProcessingError):
    """Error while converting a value through a relationship."""


class ValidationError(ProcessingError):
    """Error while validating a value through a relationship."""


class InvalidTypeError(ProcessingError):
    """Invalid type found when checking a value through a relationship."""


class SerializationError(Exception):
    """Could not serialize/deserialize value."""

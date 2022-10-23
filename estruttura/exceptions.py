"""Estruttura exceptions."""

__all__ = [
    "EstrutturaException",
    "ProcessingError",
    "ConversionError",
    "ValidationError",
    "InvalidTypeError",
    "SerializationError",
]


class EstrutturaException(Exception):
    """Base estruttura package exception."""


class ProcessingError(EstrutturaException):
    """Error while processing a value through a relationship."""


class ConversionError(ProcessingError):
    """Error while converting a value through a relationship."""


class ValidationError(ProcessingError):
    """Error while validating a value through a relationship."""


class InvalidTypeError(ProcessingError):
    """Invalid type found when checking a value through a relationship."""


class SerializationError(EstrutturaException):
    """Could not serialize/deserialize value."""

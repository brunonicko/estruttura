__all__ = [
    "EstrutturaException",
    "ProcessingError",
    "ConversionError",
    "ValidationError",
    "InvalidTypeError",
]


class EstrutturaException(Exception):
    pass


class ProcessingError(EstrutturaException):
    pass


class ConversionError(ProcessingError):
    pass


class ValidationError(ProcessingError):
    pass


class InvalidTypeError(ProcessingError):
    pass

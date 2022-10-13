"""Constants and sentinel values."""

from enum import Enum

import six
from tippo import final

__all__ = [
    "MissingType",
    "MISSING",
    "DeletedType",
    "DELETED",
    "DefaultType",
    "DEFAULT",
    "BASIC_TYPES",
]


@final
class MissingType(Enum):
    MISSING = "MISSING"


MISSING = MissingType.MISSING


@final
class DeletedType(Enum):
    DELETED = "DELETED"


DELETED = DeletedType.DELETED


@final
class DefaultType(Enum):
    DEFAULT = "DEFAULT"


DEFAULT = DefaultType.DEFAULT


BASIC_TYPES = (bool, float, type(None)) + six.integer_types + six.string_types

"""Constants and sentinel values."""

from enum import Enum

import six
from tippo import TypeVar, final

KT = TypeVar("KT")
VT_co = TypeVar("VT_co", covariant=True)


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

"""Constants and sentinel values."""

from enum import Enum

from tippo import TypeVar, final

KT = TypeVar("KT")  # key type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type


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

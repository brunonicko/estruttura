"""Constants and sentinel values."""

from enum import Enum

import six
from basicco.type_checking import TEXT_TYPES
from tippo import Tuple, cast, final

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
    """Enum type for `MISSING` sentinel."""

    MISSING = "MISSING"


MISSING = MissingType.MISSING
"""`MISSING` sentinel value."""


@final
class DeletedType(Enum):
    """Enum type for `DELETED` sentinel."""

    DELETED = "DELETED"


DELETED = DeletedType.DELETED
"""`DELETED` sentinel value."""


@final
class DefaultType(Enum):
    """Enum type for `DEFAULT` sentinel."""

    DEFAULT = "DEFAULT"


DEFAULT = DefaultType.DEFAULT
"""`DEFAULT` sentinel value."""


BASIC_TYPES = cast(Tuple[type, ...], (bool, float, type(None)) + six.integer_types + TEXT_TYPES)
"""Basic immutable types."""

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
    """Enum type for `MISSING`_ sentinel."""

    MISSING = "MISSING"


MISSING = MissingType.MISSING
"""`MISSING` sentinel value."""


@final
class DeletedType(Enum):
    """Enum type for `DELETED`_ sentinel."""

    DELETED = "DELETED"


DELETED = DeletedType.DELETED
"""`DELETED` sentinel value."""


@final
class DefaultType(Enum):
    """Enum type for `DEFAULT`_ sentinel."""

    DEFAULT = "DEFAULT"


DEFAULT = DefaultType.DEFAULT
"""`DEFAULT` sentinel value."""


BASIC_TYPES = (bool, float, type(None)) + six.integer_types + six.string_types
"""Basic immutable types."""

"""Serializers."""

import enum

from tippo import Any, Tuple, Type, TypeVar, cast

from ._relationship import Relationship, Serializer, TypedSerializer
from .exceptions import SerializationError

__all__ = ["Serializer", "TypedSerializer", "EnumSerializer"]


T = TypeVar("T")


class EnumSerializer(Serializer):
    """Serializer for enum types."""

    __slots__ = ("_by_name", "_fallback")

    def __init__(self, by_name=False, fallback=None):
        # type: (bool, Serializer[T] | None) -> None
        """
        :param by_name: Whether to serialize by name instead of value.
        :param fallback: Fallback serializer (in case value is not an enum).
        """
        self._by_name = bool(by_name)
        self._fallback = fallback

    def serialize(self, relationship, value):
        # type: (Relationship[T], T) -> Any
        """
        Serialize value.

        :param relationship: Relationship.
        :param value: Value.
        :return: Serialized value.
        :raises SerializationError: Error while serializing.
        """
        if isinstance(value, enum.Enum):
            return value.name if self.by_name else value.value
        elif self._fallback is not None:
            return self._fallback.serialize(relationship, value)
        else:
            error = "{!r} object is not an enum value".format(type(value).__name__)
            raise SerializationError(error)

    def deserialize(self, relationship, serialized):
        # type: (Relationship[T], Any) -> T
        """
        Deserialize value.

        :param relationship: Relationship.
        :param serialized: Serialized value.
        :return: Value.
        :raises SerializationError: Error while deserializing.
        """
        enum_types = cast(
            Tuple[Type[enum.Enum], ...],
            tuple(t for t in relationship.types_info.complex_types if issubclass(t, enum.Enum)),
        )
        for enum_cls in enum_types:
            items = list(enum_cls)  # type: list[enum.Enum]
            for item in items:
                if self.by_name and item.name == serialized or item.value == serialized:
                    return cast(T, item)

        if self._fallback is not None:
            return self._fallback.deserialize(relationship, serialized)

        if not enum_types:
            error = "no enum types defined"
        elif self.by_name:
            error = "no enum type with value named {!r}".format(serialized)
        else:
            error = "no enum type with value {!r}".format(serialized)
        raise SerializationError(error)

    @property
    def by_name(self):
        # type: () -> bool
        """Whether to serialize by name instead of value."""
        return self._by_name

    @property
    def fallback(self):
        # type: () -> Serializer[T] | None
        """Fallback serializer (in case value is not an enum)."""
        return self._fallback

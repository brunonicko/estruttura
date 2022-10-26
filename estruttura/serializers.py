"""Serializers."""

import enum

from tippo import Any, Tuple, Type, TypeVar, cast

from ._relationship import Relationship, Serializer, TypedSerializer
from .exceptions import SerializationError

__all__ = ["Serializer", "TypedSerializer", "EnumSerializer"]


T = TypeVar("T")


class EnumSerializer(Serializer):
    """Serializer for enum types."""

    __slots__ = ("_by_name",)

    def __init__(self, by_name=False):
        # type: (bool) -> None
        """
        :param by_name: Whether to serialize by name instead of value.
        """
        self._by_name = bool(by_name)

    def serialize(self, relationship, value):
        # type: (Relationship[T], T) -> Any
        """
        Serialize value.

        :param relationship: Relationship.
        :param value: Value.
        :return: Serialized value.
        :raises SerializationError: Error while serializing.
        """
        assert isinstance(value, enum.Enum)
        return value.name if self.by_name else value.value

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

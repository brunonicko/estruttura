"""Serializers and deserializers."""

import abc
import enum

import six
from basicco import Base, import_path, type_checking
from tippo import Any, Generic, Iterable, Type, TypeVar, cast

from .constants import BASIC_TYPES
from .exceptions import SerializationError

__all__ = ["TypedSerializer", "Serializer", "Deserializer"]


T = TypeVar("T")


class TypedSerializer(Base, Generic[T]):
    """Abstract class for typed serializers and deserializers."""

    __slots__ = (
        "_types",
        "_subtypes",
        "_resolved_types",
        "_basic_types",
        "_complex_types",
        "_extra_paths",
        "_builtin_paths",
    )

    def __init__(
        self,
        types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
        subtypes=False,  # type: bool
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param types: Available types.
        :param subtypes: Whether to accept subtypes.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """
        self._types = type_checking.format_types(types)
        self._subtypes = bool(subtypes)
        self._resolved_types = None  # type: tuple[Type[T], ...] | None
        self._basic_types = None  # type: tuple[Type[T], ...] | None
        self._complex_types = None  # type: tuple[Type[T], ...] | None
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

    @abc.abstractmethod
    def __call__(self, value):
        # type: (Any) -> Any
        """
        Perform deserialization/serialization.

        :param value: Serialized/value.
        :return: Value/serialized.
        """
        raise NotImplementedError()

    @property
    def types(self):
        # type: () -> tuple[Type[T] | str | None, ...]
        """Available types."""
        return self._types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self._subtypes

    @property
    def resolved_types(self):
        # type: () -> tuple[Type[T], ...]
        """Resolved types."""
        if self._resolved_types is None:
            self._resolved_types = type_checking.import_types(
                self._types,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        return self._resolved_types

    @property
    def basic_types(self):
        # type: () -> tuple[Type[T], ...]
        """Basic types."""
        if self._basic_types is None:
            self._basic_types = tuple(t for t in self.resolved_types if t in BASIC_TYPES)
        return self._basic_types

    @property
    def complex_types(self):
        # type: () -> tuple[Type[T], ...]
        """Complex types."""
        if self._complex_types is None:
            self._complex_types = tuple(t for t in self.resolved_types if t not in BASIC_TYPES)
        return self._complex_types

    @property
    def extra_paths(self):
        # type: () -> tuple[str, ...]
        """Extra module paths in fallback order."""
        return self._extra_paths

    @property
    def builtin_paths(self):
        # type: () -> tuple[str, ...] | None
        """Builtin module paths in fallback order."""
        return self._builtin_paths


class Serializer(TypedSerializer[T]):
    """Typed serializer."""

    __slots__ = ()

    def __call__(self, value):
        # type: (T) -> Any
        """
        Perform serialization.

        :param value: Value.
        :return: Serialized.
        """

        # Pass through basic types.
        if isinstance(value, BASIC_TYPES):
            return value

        # Get whether value is a class.
        is_type = isinstance(value, type)
        if is_type:

            # Serialize class as a path.
            serialized = import_path.get_path(
                value, extra_paths=self.extra_paths, builtin_paths=self.builtin_paths
            )  # type: Any

            # Ambiguous types, wrap the path in a dictionary with a '__class__' key.
            if len(self.complex_types) > 1:
                serialized = {"__class__": serialized}
            elif not self.complex_types:
                error = "can't serialize {!r} without a type definition".format(value)
                raise SerializationError(error)

        else:

            # Use serialize method if present.
            serializer = getattr(value, "serialize", None)
            if callable(serializer):

                # Use serializer method if applicable.
                try:
                    serialized = serializer()
                except (TypeError, ValueError) as e:
                    exc = SerializationError("{!r}; {}".format(type(e).__name__, e))
                    six.raise_from(exc, None)
                    raise exc

            elif isinstance(value, enum.Enum):

                # Serialize enum value by name.
                serialized = value.name

            else:

                # Unsupported non-serializable type.
                error = "{!r} object does not implement a 'serialize()' method".format(type(value).__name__)
                raise SerializationError(error)

            # Ambiguous types, wrap the serialized value in a dictionary with a path to the class and the state.
            if self.subtypes or len(self.complex_types) > 1:
                cls = type(value)
                cls_path = import_path.get_path(cls, extra_paths=self.extra_paths, builtin_paths=self.builtin_paths)
                serialized = {
                    "__class__": cls_path,
                    "__state__": serialized,
                }
            elif not self.complex_types:
                error = "can't serialize {!r} without a type definition".format(value)
                raise SerializationError(error)

        return serialized


class Deserializer(TypedSerializer[T]):
    """Typed deserializer."""

    __slots__ = ()

    def __call__(self, serialized):
        # type: (Any) -> T
        """
        Perform deserialization.

        :param serialized: Serialized.
        :return: Value.
        """

        # Pass through basic types.
        if isinstance(serialized, BASIC_TYPES):
            return cast(T, serialized)

        # Ambiguous types, use serialized class path and state.
        if self.subtypes or len(self.complex_types) > 1:

            # Ambiguous types, require the class and the state to be in the serialized dictionary.
            if isinstance(serialized, dict) and "__class__" in serialized:

                # Import class from path.
                cls = import_path.import_path(
                    serialized["__class__"], extra_paths=self.extra_paths, builtin_paths=self.builtin_paths
                )

                # No state, value is a class.
                if "__state__" not in serialized:
                    return cls

                # Get state.
                state = serialized["__state__"]

            else:
                error = "ambiguous types while deserializing {!r}".format(serialized)
                raise SerializationError(error)

        elif not self.complex_types:

            # No complex types defined to deserialize.
            error = "not enough types defined to deserialize {!r}".format(serialized)
            raise SerializationError(error)

        else:
            cls = self.complex_types[0]
            state = serialized

        # Get deserializer method if any.
        deserializer = getattr(cls, "deserialize", None)
        if callable(deserializer):

            # Use deserializer method.
            try:
                value = deserializer(state)
            except (TypeError, ValueError) as e:
                exc = SerializationError("{!r}; {}".format(type(e).__name__, e))
                six.raise_from(exc, None)
                raise exc

        elif issubclass(cls, enum.Enum):

            # Deserialize enum serialized by name.
            for enum_name, enum_value in six.iteritems(cls.__members__):
                if enum_name == state:
                    value = enum_value
                    break
            else:
                error = "could not find matching {!r} enum value for {!r}".format(cls.__name__, serialized)
                raise SerializationError(error)

        else:
            error = "{!r} object does not implement a 'deserialize()' method".format(type(serialized).__name__)
            raise SerializationError(error)

        return value

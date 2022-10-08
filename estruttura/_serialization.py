import abc
import enum

import six
from basicco import Base, import_path, type_checking
from tippo import Any, Generic, Iterable, Type, TypeVar, cast

from ._constants import BASIC_TYPES

T = TypeVar("T")


class BaseSerializer(Base, Generic[T]):
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
        raise NotImplementedError()

    @property
    def types(self):
        # type: () -> tuple[Type[T] | str | None, ...]
        """Types."""
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


class Serializer(BaseSerializer[T]):
    __slots__ = ()

    def __call__(self, value):
        # type: (T) -> Any

        # Pass through basic types.
        if isinstance(value, BASIC_TYPES):
            return value

        # Get serializer method if any.
        # TODO: check arg spec for func()
        serializer = getattr(value, "serialize", None)

        if callable(serializer):

            # Use serializer method.
            serialized = serializer()

        elif isinstance(value, enum.Enum):  # TODO: tuple, list, dict, etc

            # Serialize enum value by name.
            serialized = value.name

        else:
            error = "{!r} does not implement a 'serialize()' method".format(value)
            raise TypeError(error)

        # Ambiguous types, wrap the serialized value in a dictionary with a path to the class and the state.
        if self.subtypes or len(self.complex_types) > 1:
            cls = type(value)
            serialized = {
                "__class__": import_path.get_path(cls, extra_paths=self.extra_paths, builtin_paths=self.builtin_paths),
                "__state__": serialized,
            }
            # TODO: support for typing.Type
        elif not self.complex_types:
            error = "can't serialize {!r} without a type definition".format(value)
            raise TypeError(error)

        return serialized


class Deserializer(BaseSerializer[T]):
    __slots__ = ()

    def __call__(self, value):
        # type: (Any) -> T

        # Pass through basic types.
        if isinstance(value, BASIC_TYPES):
            return cast(T, value)

        if self.subtypes or len(self.complex_types) > 1:

            # Ambiguous types, require the class and the state to be in the serialized dictionary.
            if isinstance(value, dict) and "__class__" in value:
                cls = import_path.import_path(
                    value["__class__"], extra_paths=self.extra_paths, builtin_paths=self.builtin_paths
                )
                state = value["__state__"]
            else:
                error = "ambiguous types while deserializing {!r}".format(value)
                raise TypeError(error)

        elif not self.complex_types:

            # No complex types defined to deserialize.
            error = "not enough types defined to deserialize {!r}".format(value)
            raise TypeError(error)

        else:
            cls = self.complex_types[0]
            state = value

        # Get deserializer method if any.
        # TODO: check arg spec for func(serialized)
        # TODO: check if it's a classmethod
        deserializer = getattr(cls, "deserialize", None)

        if callable(deserializer):

            # Use deserializer method.
            deserialized = deserializer(state)

        elif issubclass(cls, enum.Enum):  # TODO: tuple, list, dict, etc

            # Deserialize enum value by name.
            for n, v in six.iteritems(cls.__members__):
                if n == state:
                    deserialized = v
                    break
            else:
                error = "could not find matching {!r} enum value for {!r}".format(cls.__name__, value)
                raise TypeError(error)

        else:
            error = "{!r} does not implement a 'deserialize()' method".format(value)
            raise TypeError(error)

        return deserialized

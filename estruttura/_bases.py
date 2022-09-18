import abc

import six
from basicco import type_checking, recursive_repr, fabricate_value, custom_repr, runtime_final
from tippo import Any, Callable, Type, Iterable, Generic, TypeVar, Hashable, cast

from .bases import (
    Base,
    BaseHashable,
    BaseCollectionMeta,
    BaseCollection,
    BaseProtectedCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
)


T = TypeVar("T")  # contained value type
T_co = TypeVar("T_co", covariant=True)  # contained covariant value type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type
LT = TypeVar("LT", bound=Hashable)  # location type
IT = TypeVar("IT")  # internal type


class BaseState(BaseHashable, BaseInteractiveCollection[T], Generic[T, IT]):
    """Base immutable state."""

    __slots__ = ("__hash", "__internal")

    @staticmethod
    def __new__(cls, initial=None):
        if type(initial) is cls:
            return initial
        else:
            return super(BaseState, cls).__new__(cls)

    @classmethod
    @runtime_final.final
    def _make(cls, internal):
        # type: (Type[BST], IT) -> BST
        """
        Build new state by directly setting the internal value.

        :param internal: Internal state.
        :return: State.
        """
        self = cast(BST, cls.__new__(cls))
        self.__internal = internal
        self.__hash = None
        return self

    @staticmethod
    @abc.abstractmethod
    def _init_internal(initial):
        # type: (Any) -> IT
        """Initialize internal."""
        raise NotImplementedError()

    @abc.abstractmethod
    def __init__(self, initial=None):
        self.__internal = self._init_internal(initial=initial)
        self.__hash = None  # type: int | None

    @runtime_final.final
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(self._internal)
        return self.__hash

    @runtime_final.final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if isinstance(other, type(self)):
            return self.__internal == other.__internal
        try:
            hash(other)
        except TypeError:
            return self.__internal == other
        else:
            return False

    @runtime_final.final
    def __copy__(self):
        # type: (BST) -> BST
        """
        Get itself.

        :return: Itself.
        """
        return self

    @property
    @runtime_final.final
    def _internal(self):
        # type: () -> Any
        """Internal values."""
        return self.__internal


BST = TypeVar("BST", bound=BaseState)  # base state type


class BaseRelationship(Base, Generic[T]):
    """Describes a relationship between a structure and its values."""

    __slots__ = (
        "__converter",
        "__types",
        "__subtypes",
        "__repr",
        "__eq",
        "__hash",
        "__serializer",
        "__deserializer",
        "__metadata",
        "__extra_paths",
        "__builtin_paths",
    )

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        types=(),  # type: Iterable[Type[T] | Type | str | None] | Type[T] | Type | str | None
        subtypes=False,  # type: bool
        repr=True,  # type: bool
        eq=True,  # type: bool
        hash=None,  # type: bool | None
        serializer=None,  # type: Callable[[T], Any] | str | None
        deserializer=None,  # type: Callable[[Any], T] | str | None
        metadata=None,  # type: Any
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param converter: Callable value converter.
        :param types: Types for runtime checking.
        :param subtypes: Whether to accept subtypes.
        :param repr: Whether to include in the `__repr__` method.
        :param eq: Whether to include in the `__eq__` method.
        :param hash: Whether to include in the `__hash__` method.
        :param serializer: Callable value serializer.
        :param deserializer: Callable value deserializer.
        :param metadata: User metadata.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """

        # Ensure safe hash.
        if hash is None:
            hash = eq
        if hash and not eq:
            error = "can't contribute to the hash if it's not contributing to the eq"
            raise ValueError(error)

        self.__converter = fabricate_value.format_factory(converter)
        self.__types = type_checking.format_types(types)
        self.__subtypes = bool(subtypes)
        self.__repr = bool(repr)
        self.__eq = bool(eq)
        self.__hash = bool(hash)
        self.__serializer = fabricate_value.format_factory(serializer)
        self.__deserializer = fabricate_value.format_factory(deserializer)
        self.__metadata = metadata
        self.__extra_paths = tuple(extra_paths)
        self.__builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

    @recursive_repr.recursive_repr
    def __repr__(self):
        items = self.to_items()
        return custom_repr.mapping_repr(
            mapping=dict(items),
            prefix="{}(".format(type(self).__name__),
            template="{key}={value}",
            separator=", ",
            suffix=")",
            sorting=True,
            sort_key=lambda i, _s=self, _i=items: next(iter(zip(*_i))).index(i[0]),
            key_repr=str,
        )

    def __hash__(self):
        return hash(self.to_items())

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.to_items() == other.to_items()

    def convert(self, value):
        # type: (Any) -> T
        return fabricate_value.fabricate_value(
            self.__converter,
            value,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def accepts_type(self, value):
        # type: (Any) -> bool
        return type_checking.is_instance(
            value,
            self.__types,
            subtypes=self.__subtypes,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def check_type(self, value):
        # type: (Any) -> T
        if self.__types:
            return type_checking.assert_is_instance(
                value,
                self.__types,
                subtypes=self.__subtypes,
                extra_paths=self.__extra_paths,
                builtin_paths=self.__builtin_paths,
            )
        else:
            return value

    def process(self, value):
        # type: (Any) -> T
        return self.check_type(self.convert(value))

    def serialize(self, value, *args, **kwargs):
        # type: (T, *Any, **Any) -> Any
        return fabricate_value.fabricate_value(
            self.__serializer,
            value,
            args=args,
            kwargs=kwargs,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def deserialize(self, serialized, *args, **kwargs):
        # type: (Any, *Any, **Any) -> T
        return fabricate_value.fabricate_value(
            self.__deserializer,
            serialized,
            args=args,
            kwargs=kwargs,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("converter", self.converter),
            ("types", self.types),
            ("subtypes", self.subtypes),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("serializer", self.serializer),
            ("deserializer", self.deserializer),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        )

    def to_dict(self):
        # type: () -> dict[str, Any]
        return dict(self.to_items())

    def update(self, *args, **kwargs):
        # type: (RT, **Any) -> RT
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(RT, type(self)(**updated_kwargs))

    @property
    def converter(self):
        # type: () -> Callable[[Any], T] | Type[T] | str | None
        return self.__converter

    @property
    def types(self):
        # type: () -> tuple[Type | str, ...]
        """Types for runtime checking."""
        return self.__types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self.__subtypes

    @property
    def repr(self):
        # type: () -> bool
        """Whether to include in the `__repr__` method."""
        return self.__repr

    @property
    def eq(self):
        # type: () -> bool
        """Whether to include in the `__eq__` method."""
        return self.__eq

    @property
    def hash(self):
        # type: () -> bool
        """Whether to include in the `__hash__` method."""
        return self.__hash

    @property
    def serializer(self):
        # type: () -> Callable[[T], Any] | str | None
        """Callable value serializer."""
        return self.__serializer

    @property
    def deserializer(self):
        # type: () -> Callable[[Any], T] | str | None
        """Callable value deserializer."""
        return self.__deserializer

    @property
    def metadata(self):
        # type: () -> Any
        """User metadata."""
        return self.__metadata

    @property
    def extra_paths(self):
        # type: () -> tuple[str, ...]
        """Extra module paths in fallback order."""
        return self.__extra_paths

    @property
    def builtin_paths(self):
        # type: () -> tuple[str, ...] | None
        """Builtin module paths in fallback order."""
        return self.__builtin_paths


RT = TypeVar("RT", bound=BaseRelationship)  # relationship type


class BaseStructureMeta(BaseCollectionMeta):
    """Metaclass for :class:`BaseStructure`."""


class BaseStructure(six.with_metaclass(BaseStructureMeta, BaseCollection[T_co], Generic[T_co, VT_co, BST, LT, RT])):
    """Base structure."""

    __slots__ = ()

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, serialized):
        # type: (Type[BS], Any) -> BS
        """
        Deserialize.

        :return: Deserialized.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def serialize(self):
        # type: () -> Any
        """
        Serialize.

        :return: Serialized.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_state(self):
        # type: () -> BST
        """
        Get state.

        :return: State.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_relationship(self, location):
        # type: (LT) -> RT
        """
        Get relationship at location.

        :param location: Location.
        :return: Relationship.
        :raises KeyError: No relationship at location.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_value(self, location):
        # type: (LT) -> VT_co
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        raise NotImplementedError()


BS = TypeVar("BS", bound=BaseStructure)


# noinspection PyAbstractClass
class BaseProtectedStructure(BaseStructure[T_co, VT_co, BST, LT, RT], BaseProtectedCollection[T_co]):
    """Base interactive structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveStructure(BaseProtectedStructure[T_co, VT_co, BST, LT, RT], BaseInteractiveCollection[T_co]):
    """Base interactive structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableStructure(BaseProtectedStructure[T_co, VT_co, BST, LT, RT], BaseMutableCollection[T_co]):
    """Base mutable structure."""

    __slots__ = ()

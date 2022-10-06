import abc

import six
from basicco import runtime_final, obj_state
from tippo import Any, Type, Generic, TypeVar, Hashable, cast

from estruttura import (
    StructureMeta,
    HashableStructure,
    UniformStructureMeta,
    UniformStructure,
    PrivateUniformStructure,
    InteractiveUniformStructure,
)

from ._relationship import DataRelationship


T_co = TypeVar("T_co", covariant=True)  # covariant value type
IT = TypeVar("IT", bound=Hashable)  # internal type


class BaseDataMeta(StructureMeta):
    """Metaclass for :class:`BaseData`."""


class BaseData(HashableStructure):
    """Base data."""

    __slots__ = ()

    @abc.abstractmethod
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()

    @abc.abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        raise NotImplementedError()

    def __copy__(self):
        cls = type(self)
        new_self = cls.__new__(cls)
        obj_state.update_state(new_self, obj_state.get_state(self))
        return new_self


class UniformDataMeta(BaseDataMeta, UniformStructureMeta):
    """Metaclass for :class:`UniformData`."""

    __relationship_type__ = DataRelationship  # type: Type[DataRelationship]


class UniformData(six.with_metaclass(UniformDataMeta, BaseData, UniformStructure[T_co], Generic[IT, T_co])):
    """Uniform data."""

    __slots__ = ("__hash", "__internal")
    __relationship__ = None  # type: DataRelationship | None

    @staticmethod
    @runtime_final.final
    def __new__(cls, initial=None, *args, **kwargs):
        if type(initial) is cls and not args and not kwargs:
            return initial
        else:
            return super(UniformData, cls).__new__(cls)

    @classmethod
    @runtime_final.final
    def _make(cls, internal):
        # type: (Type[UD], IT) -> UD
        """
        Build new uniform data by directly setting the internal value.

        :param internal: Internal state.
        :return: Uniform data.
        """
        self = cast(UD, cls.__new__(cls))
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
        if type(self) is type(other):
            return self.__internal == other.__internal  # type: ignore  # noqa
        try:
            hash(other)
        except TypeError:
            return self.__internal == other
        else:
            return False

    @property
    @runtime_final.final
    def _internal(self):
        # type: () -> IT
        """Internal values."""
        return self.__internal


UD = TypeVar("UD", bound=UniformData)


# noinspection PyAbstractClass
class PrivateUniformData(UniformData[IT, T_co], PrivateUniformStructure[T_co]):
    """Private uniform data."""

    def _clear(self):
        # type: (PUD) -> PUD
        """
        Clear.

        :return: Transformed.
        """
        return self._make(self._init_internal(initial=None))


PUD = TypeVar("PUD", bound=PrivateUniformData)


# noinspection PyAbstractClass
class InteractiveUniformData(PrivateUniformData[IT, T_co], InteractiveUniformStructure[T_co]):
    """Interactive uniform data."""

    __slots__ = ()

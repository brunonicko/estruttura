import abc

import six
from tippo import Any, Type, Generic, TypeVar
from basicco import runtime_final

from .bases import (
    BaseCollectionMeta,
    BaseCollection,
    BasePrivateCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
)
from ._relationship import Relationship


RT = TypeVar("RT", bound=Relationship, covariant=True)  # covariant relationship type
LT = TypeVar("LT")  # location type
CT_co = TypeVar("CT_co")  # covariant collected value type
VT_co = TypeVar("VT_co")  # covariant value type


class StructureMeta(BaseCollectionMeta):
    """Metaclass for :class:`Structure`."""


class Structure(six.with_metaclass(StructureMeta, BaseCollection[CT_co], Generic[CT_co, RT, LT, VT_co])):
    """Structure."""

    __slots__ = ()

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, serialized):
        # type: (Type[S], Any) -> S
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
    def get_value(self, location):
        # type: (LT) -> VT_co
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_relationship(self, location):
        # type: (LT) -> RT
        """
        Get relationship at location.

        :param location: Location.
        :return: Relationship.
        :raises KeyError: Invalid location.
        """
        raise NotImplementedError()


S = TypeVar("S", bound=Structure)


# noinspection PyAbstractClass
class PrivateStructure(Structure[CT_co, RT, LT, VT_co], BasePrivateCollection[CT_co]):
    """Private structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class InteractiveStructure(PrivateStructure[CT_co, RT, LT, VT_co], BaseInteractiveCollection[CT_co]):
    """Interactive structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class MutableStructure(PrivateStructure[CT_co, RT, LT, VT_co], BaseMutableCollection[CT_co]):
    """Mutable structure."""

    __slots__ = ()


class UniformStructure(Structure[CT_co, RT, LT, VT_co]):
    """Structure with a single relationship for all locations."""

    __slots__ = ()

    @runtime_final.final
    def get_relationship(self, location=None):
        # type: (Any) -> RT
        return self.relationship

    @property
    @abc.abstractmethod
    def relationship(self):
        # type: () -> RT
        raise NotImplementedError()


# noinspection PyAbstractClass
class PrivateUniformStructure(UniformStructure[CT_co, RT, LT, VT_co], PrivateStructure[CT_co, RT, LT, VT_co]):
    """Private structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class InteractiveUniformStructure(
    PrivateUniformStructure[CT_co, RT, LT, VT_co], InteractiveStructure[CT_co, RT, LT, VT_co]
):
    """Interactive structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class MutableUniformStructure(PrivateUniformStructure[CT_co, RT, LT, VT_co], MutableStructure[CT_co, RT, LT, VT_co]):
    """Mutable structure."""

    __slots__ = ()

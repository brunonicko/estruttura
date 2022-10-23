import basicco
import six
import slotted
from basicco.abstract_class import abstract, is_abstract
from basicco.explicit_hash import set_to_none
from basicco.runtime_final import final
from tippo import Any, Type, TypeVar

from ._relationship import Relationship
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class StructureMeta(basicco.SlottedBaseMeta):
    """Metaclass for :class:`Structure`."""


class Structure(six.with_metaclass(StructureMeta, basicco.SlottedBase)):
    """Forces the implementation of `__hash__` and `__eq__`."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()

    @abstract
    def __eq__(self, other):
        # type: (object) -> bool
        raise NotImplementedError()

    @abstract
    def serialize(self):
        # type: () -> Any
        raise NotImplementedError()

    @classmethod
    @abstract
    def deserialize(cls, serialized):
        # type: (Type[S], Any) -> S
        raise NotImplementedError()


S = TypeVar("S")  # structure self type


class ImmutableStructureMeta(StructureMeta):
    """Metaclass for :class:`ImmutableStructure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        cls = super(ImmutableStructureMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)
        if cls.__hash__ is None:
            error = "{!r} in {!r} can't be None".format(cls.__hash__, name)
            raise TypeError(error)
        return cls


class ImmutableStructure(six.with_metaclass(ImmutableStructureMeta, Structure, slotted.SlottedHashable)):
    """Forces an implementation of `__hash__` that is not None."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()


class MutableStructureMeta(StructureMeta):
    """Metaclass for :class:`MutableStructure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        if "__eq__" in dct and "__hash__" not in dct:
            dct = dict(dct)
            dct["__hash__"] = None
        cls = super(MutableStructureMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)
        if cls.__hash__ is not None and not is_abstract(cls.__hash__):
            error = "'__hash__' in {!r} needs to be None".format(name)
            raise TypeError(error)
        return cls


# noinspection PyAbstractClass
class MutableStructure(six.with_metaclass(MutableStructureMeta, Structure)):
    """Non-hashable."""

    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)


# noinspection PyAbstractClass
class CollectionStructure(Structure, slotted.SlottedCollection[T_co]):
    __slots__ = ()
    relationship = Relationship()  # type: Relationship[T_co]

    def __init_subclass__(cls, relationship=MISSING, **kwargs):
        # type: (Relationship[T_co] | MissingType, **Any) -> None

        # Relationship.
        if relationship is not MISSING:
            cls.relationship = relationship

        super(CollectionStructure, cls).__init_subclass__(**kwargs)  # noqa

    @abstract
    def _do_clear(self):
        # type: (BC) -> BC
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @final
    def _clear(self):
        # type: (BC) -> BC
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        return self._do_clear()


BC = TypeVar("BC", bound=CollectionStructure)


# noinspection PyAbstractClass
class ImmutableCollectionStructure(CollectionStructure[T_co], ImmutableStructure):

    __slots__ = ()

    @final
    def clear(self):
        # type: (BIC) -> BIC
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


BIC = TypeVar("BIC", bound=ImmutableCollectionStructure)


# noinspection PyAbstractClass
class MutableCollectionStructure(CollectionStructure[T_co], MutableStructure):
    """Mutable collection structure."""

    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

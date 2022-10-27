import basicco
import six
import slotted
from basicco import explicit_hash, recursive_repr, safe_repr
from basicco.runtime_final import final
from basicco.abstract_class import abstract
from tippo import Any, Type, Iterator, TypeVar

from ._relationship import Relationship
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseStructureMeta(basicco.SlottedBaseMeta):
    """Metaclass for :class:`BaseStructure`."""


class BaseStructure(six.with_metaclass(BaseStructureMeta, basicco.SlottedBase)):
    """Base structure class."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()

    @abstract
    def __eq__(self, other):
        # type: (object) -> bool
        raise NotImplementedError()

    @final
    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        return self._repr()

    @final
    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self._str()

    @abstract
    def _repr(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        raise NotImplementedError()

    def _str(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self._repr()

    @abstract
    def serialize(self):
        # type: () -> Any
        """
        Serialize.

        :return: Serialized.
        :raises SerializationError: Error while serializing.
        """
        raise NotImplementedError()

    @classmethod
    @abstract
    def deserialize(cls, serialized):
        # type: (Type[S], Any) -> S
        """
        Deserialize.

        :param serialized: Serialized.
        :return: Structure.
        :raises SerializationError: Error while deserializing.
        """
        raise NotImplementedError()


S = TypeVar("S")  # structure self type


class BaseImmutableStructureMeta(BaseStructureMeta):
    """Metaclass for :class:`BaseImmutableStructure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        cls = super(BaseImmutableStructureMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)

        # Force hashable.
        if cls.__hash__ is None:
            error = "'__hash__' in {!r} can't be None".format(name)
            raise TypeError(error)

        return cls


class BaseImmutableStructure(six.with_metaclass(BaseImmutableStructureMeta, BaseStructure, slotted.SlottedHashable)):
    """Base immutable structure class."""

    __slots__ = ()

    @final
    def __hash__(self):
        # type: () -> int
        return self._hash()

    @abstract
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()


class BaseMutableStructureMeta(BaseStructureMeta):
    """Metaclass for :class:`BaseMutableStructure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa

        # If '__eq__' is declared but not '__hash__', force it to be None.
        if "__eq__" in dct and "__hash__" not in dct:
            dct = dict(dct)
            dct["__hash__"] = None

        cls = super(BaseMutableStructureMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)

        # Error out if for some reason '__hash__' is not set to None.
        if cls.__hash__ is not None:
            error = "'__hash__' in {!r} needs to be None".format(name)
            raise TypeError(error)

        return cls


# noinspection PyAbstractClass
class BaseMutableStructure(six.with_metaclass(BaseMutableStructureMeta, BaseStructure)):
    """Base mutable structure class."""

    __slots__ = ()

    @explicit_hash.set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)


# noinspection PyAbstractClass
class BaseCollectionStructure(BaseStructure, slotted.SlottedCollection[T_co]):
    """Base collection structure class."""

    __slots__ = ()

    relationship = Relationship()  # type: Relationship[T_co]
    """Relationship with values."""

    def __init_subclass__(cls, relationship=MISSING, **kwargs):
        # type: (Relationship[T_co] | MissingType, **Any) -> None
        """
        Initialize subclass with parameters.

        :param relationship: Relationship.
        """
        if relationship is not MISSING:
            cls.relationship = relationship
        super(BaseCollectionStructure, cls).__init_subclass__(**kwargs)  # noqa

    @final
    def __contains__(self, item):
        # type: (object) -> bool
        return self._contains(item)

    @final
    def __iter__(self):
        # type: () -> Iterator[T_co]
        return self._iter()

    @final
    def __len__(self):
        # type: () -> int
        return self._len()

    @abstract
    def _contains(self, item):
        # type: (object) -> bool
        """
        Get whether contains item.

        :param item: Item.
        :return: True if contains.
        """
        raise NotImplementedError()

    @abstract
    def _iter(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over collection contents.

        :return: Iterator.
        """
        raise NotImplementedError()

    @abstract
    def _len(self):
        # type: () -> int
        """
        Get length.

        :return: Length.
        """
        raise NotImplementedError()

    @abstract
    def _do_clear(self):
        # type: (BC) -> BC
        """
        Clear (internal).

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


BC = TypeVar("BC", bound=BaseCollectionStructure)


# noinspection PyAbstractClass
class BaseImmutableCollectionStructure(BaseCollectionStructure[T_co], BaseImmutableStructure):
    """Immutable collection structure class."""

    __slots__ = ()

    @final
    def clear(self):
        # type: (BICS) -> BICS
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


BICS = TypeVar("BICS", bound=BaseImmutableCollectionStructure)


# noinspection PyAbstractClass
class BaseMutableCollectionStructure(BaseCollectionStructure[T_co], BaseMutableStructure):
    """Base mutable collection structure."""

    __slots__ = ()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

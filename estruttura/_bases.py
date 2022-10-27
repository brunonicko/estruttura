"""Base abstract classes."""

import basicco
import six
import slotted
from basicco import recursive_repr, safe_repr
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Type, TypeVar

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

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        return self._eq(other)

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
    def _eq(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

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


class BaseImmutableStructure(BaseStructure, slotted.SlottedHashable):
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


# noinspection PyAbstractClass
class BaseMutableStructure(BaseStructure):
    """Base mutable structure class."""

    __slots__ = ()

    @final
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)


# Add descriptor that forces final 'None' hash.
type.__setattr__(
    BaseMutableStructure,
    "__hash__",
    type("NullHash", (object,), {"__is_final_method__": True, "__get__": lambda *_: None})(),
)


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

    @abstract
    def _do_clear(self):
        # type: (BCS) -> BCS
        """
        Clear (internal).

        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @final
    def _clear(self):
        # type: (BCS) -> BCS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        return self._do_clear()


BCS = TypeVar("BCS", bound=BaseCollectionStructure)


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

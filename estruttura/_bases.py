import contextlib

import basicco
import six
import slotted
from basicco import recursive_repr, safe_repr
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Iterator, Type, TypeVar

from ._relationship import Relationship
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseStructureMeta(basicco.SlottedBaseMeta):
    """Metaclass for :class:`BaseStructure`."""


# noinspection PyAbstractClass
class BaseStructure(six.with_metaclass(BaseStructureMeta, basicco.SlottedBase)):
    """Base structure."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Other object.
        :return: True if equal.
        """
        return self._eq(other)

    @final
    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
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

    @contextlib.contextmanager
    @abstract
    def __change_context__(self):
        # type: (BS) -> Iterator[BS]
        raise NotImplementedError()

    def __post_init__(self):
        # type: () -> None
        """
        Called after initialization.
        The default implementation does nothing.
        """
        pass

    def __post_deserialize__(self):
        # type: () -> None
        """
        Called after deserialization.
        The default implementation calls `__post_init__`.
        """
        self.__post_init__()

    def __post_change__(self):
        # type: () -> None
        """
        Called after change.
        The default implementation does nothing.
        """
        pass

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
        # type: (Type[BS], Any) -> BS
        """
        Deserialize.

        :param serialized: Serialized.
        :return: Structure.
        :raises SerializationError: Error while deserializing.
        """
        raise NotImplementedError()


BS = TypeVar("BS", bound=BaseStructure)  # base structure self type


# noinspection PyAbstractClass
class BaseUserStructure(BaseStructure):
    """Base user structure."""

    __slots__ = ()


BUS = TypeVar("BUS", bound=BaseUserStructure)  # base user structure self type


# noinspection PyAbstractClass
class BaseImmutableStructure(BaseStructure, slotted.SlottedHashable):
    """Base immutable structure."""

    __slots__ = ()

    @final
    def __hash__(self):
        # type: () -> int
        hash_ = self.__retrieve_hash__()
        if hash_ is None:
            hash_ = self._hash()
            assert hash_ is not None
            self.__cache_hash__(hash_)
            hash_ = self.__retrieve_hash__()
            assert hash_ is not None, "hash was not cached properly"
        return hash_

    @abstract
    def __cache_hash__(self, hash_):
        # type: (int | None) -> None
        """
        Cache hash.

        :param hash_: Calculated hash (to be cached) or None (to clear the cache).
        """
        raise NotImplementedError()

    @abstract
    def __retrieve_hash__(self):
        # type: () -> int | None
        """
        Retrieve cached hash.

        :return: Cached hash or None.
        """
        raise NotImplementedError()

    @contextlib.contextmanager
    @final
    def __change_context__(self):
        # type: (BIS) -> Iterator[BIS]
        _self = self._do_copy()
        _self.__cache_hash__(None)
        yield _self
        _self.__post_change__()

    def __post_change__(self):
        # type: () -> None
        """
        Called after change.
        The default implementation calls `__post_init__`.
        """
        self.__post_init__()

    @abstract
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @abstract
    def _do_copy(self):
        # type: (BIS) -> BIS
        """
        Perform a shallow copy prior to internal mutation.
        The result is passed to the respective `_do_...` methods for mutation.

        :return: Shallow copy.
        """
        raise NotImplementedError()


BIS = TypeVar("BIS", bound=BaseImmutableStructure)  # base immutable structure self type


# noinspection PyAbstractClass
class BaseUserImmutableStructure(BaseImmutableStructure, BaseUserStructure):
    """Base user immutable structure."""

    __slots__ = ()


BUIS = TypeVar("BUIS", bound=BaseUserImmutableStructure)  # base user immutable structure self type


# noinspection PyAbstractClass
class BaseMutableStructure(BaseStructure):
    """Base mutable structure."""

    __slots__ = ()

    @final
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    @contextlib.contextmanager
    @final
    def __change_context__(self):
        # type: (BMS) -> Iterator[BMS]
        yield self
        self.__post_change__()


# Add descriptor that forces final 'None' hash.
type.__setattr__(
    BaseMutableStructure,
    "__hash__",
    type("NullHash", (object,), {"__is_final_method__": True, "__get__": lambda *_: None})(),
)


BMS = TypeVar("BMS", bound=BaseMutableStructure)  # base mutable structure self type


# noinspection PyAbstractClass
class BaseUserMutableStructure(BaseMutableStructure, BaseUserStructure):
    """Base user mutable structure."""

    __slots__ = ()


BUMS = TypeVar("BUMS", bound=BaseUserMutableStructure)  # base user mutable structure self type


# noinspection PyAbstractClass
class BaseCollectionStructure(BaseStructure, slotted.SlottedCollection[T_co]):
    """Base collection structure."""

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


BCS = TypeVar("BCS", bound=BaseCollectionStructure)  # base collection structure self type


# noinspection PyAbstractClass
class BaseUserCollectionStructure(BaseCollectionStructure[T_co], BaseUserStructure):
    """Base user collection structure."""

    __slots__ = ()

    @abstract
    def _do_clear(self):
        # type: () -> None
        """Clear (internal)."""
        raise NotImplementedError()

    @final
    def _clear(self):
        # type: (BUCS) -> BUCS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        with self.__change_context__() as _self:
            _self._do_clear()
            return _self


BUCS = TypeVar("BUCS", bound=BaseUserCollectionStructure)  # base user collection structure self type


# noinspection PyAbstractClass
class BaseImmutableCollectionStructure(BaseCollectionStructure[T_co], BaseImmutableStructure):
    """Immutable collection structure."""

    __slots__ = ()


BICS = TypeVar("BICS", bound=BaseImmutableCollectionStructure)  # base immutable collection structure self type


# noinspection PyAbstractClass
class BaseUserImmutableCollectionStructure(BaseImmutableCollectionStructure[T_co], BaseUserCollectionStructure[T_co]):
    """Base user immutable collection structure."""

    __slots__ = ()

    @final
    def clear(self):
        # type: (BUICS) -> BUICS
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


BUICS = TypeVar(
    "BUICS", bound=BaseUserImmutableCollectionStructure
)  # base user immutable collection structure self type


# noinspection PyAbstractClass
class BaseMutableCollectionStructure(BaseCollectionStructure[T_co], BaseMutableStructure):
    """Base mutable collection structure."""

    __slots__ = ()


BMCS = TypeVar("BMCS", bound=BaseMutableCollectionStructure)  # base mutable collection structure self type


# noinspection PyAbstractClass
class BaseUserMutableCollectionStructure(BaseMutableCollectionStructure[T_co], BaseUserCollectionStructure[T_co]):
    """Base user mutable collection structure."""

    __slots__ = ()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()


BUMCS = TypeVar("BUMCS", bound=BaseUserMutableCollectionStructure)  # base user mutable collection structure self type

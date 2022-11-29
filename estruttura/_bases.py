"""Base abstract classes."""

import weakref

import basicco
import six
import slotted
from basicco import recursive_repr, safe_repr
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Generic, Iterator, Mapping, Type, TypeVar

from ._relationship import Relationship
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseStructureMeta(basicco.SlottedBaseMeta):
    """Metaclass for :class:`BaseStructure`."""


# noinspection PyAbstractClass
class BaseStructure(six.with_metaclass(BaseStructureMeta, basicco.SlottedBase)):
    """Base structure."""

    __slots__ = ("__proxies",)

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

    @final
    def __register_proxy__(self, proxy):
        # type: (BaseProxyStructure) -> None
        """
        Register a new proxy.

        :param proxy: Proxy.
        """
        try:
            proxies = self.__proxies  # type: ignore
        except AttributeError:
            proxies = self.__proxies = weakref.WeakValueDictionary()  # type: ignore
        proxies[id(proxy)] = proxy

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

    @property
    @final
    def _proxies(self):
        # type: (BS) -> list[BaseProxyStructure[BS]]
        """Proxy structures."""
        proxies_dict = self.__proxies  # type: Mapping[int, BaseProxyStructure]
        return [i[1] for i in sorted(six.iteritems(proxies_dict), key=lambda p: p[0])]


BS = TypeVar("BS", bound=BaseStructure)  # base structure self type


# noinspection PyAbstractClass
class BaseUserStructure(BaseStructure):
    """Base user structure."""

    __slots__ = ()


BUS = TypeVar("BUS", bound=BaseUserStructure)  # base user structure self type


# noinspection PyAbstractClass
class BaseProxyStructure(BaseStructure, Generic[BS]):
    """Base proxy structure."""

    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (BS) -> None
        """
        :param wrapped: Structure to wrap.
        """
        self.__wrapped = wrapped
        wrapped.__register_proxy__(self)

    def _repr(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return "{}({!r})".format(type(self).__name__, self._wrapped)

    def _eq(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        return type(self) is type(other) and self._wrapped == other._wrapped  # type: ignore  # noqa

    @property
    def _wrapped(self):
        # type: () -> BS
        """Wrapped structure."""
        return self.__wrapped  # type: ignore


BPS = TypeVar("BPS", bound=BaseProxyStructure)  # base proxy structure self type


# noinspection PyAbstractClass
class BaseProxyUserStructure(BaseProxyStructure[BUS], BaseUserStructure):
    """Base proxy user structure."""

    __slots__ = ()


BPUS = TypeVar("BPUS", bound=BaseProxyUserStructure)  # base proxy user structure type


# noinspection PyAbstractClass
class BaseImmutableStructure(BaseStructure, slotted.SlottedHashable):
    """Base immutable structure."""

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
class BaseProxyImmutableStructure(BaseProxyStructure[BIS], BaseImmutableStructure):
    """Base proxy immutable structure."""

    __slots__ = ()

    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(self._wrapped)


BPIS = TypeVar("BPIS", bound=BaseProxyImmutableStructure)  # base proxy immutable structure self type


# noinspection PyAbstractClass
class BaseProxyUserImmutableStructure(BaseProxyImmutableStructure[BUIS], BaseUserImmutableStructure):
    """Base proxy user immutable structure."""

    __slots__ = ()


BPUIS = TypeVar("BPUIS", bound=BaseProxyUserImmutableStructure)  # base proxy user immutable structure self type


# noinspection PyAbstractClass
class BaseProxyMutableStructure(BaseProxyStructure[BMS], BaseMutableStructure):
    """Base proxy mutable structure."""

    __slots__ = ()


BPMS = TypeVar("BPMS", bound=BaseProxyMutableStructure)  # base proxy mutable structure self type


# noinspection PyAbstractClass
class BaseProxyUserMutableStructure(BaseProxyMutableStructure[BUMS], BaseUserMutableStructure):
    """Base proxy user mutable structure."""

    __slots__ = ()


BPUMS = TypeVar("BPUMS", bound=BaseProxyUserMutableStructure)  # base proxy user mutable structure self type


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
        # type: (BUCS) -> BUCS
        """
        Clear (internal).

        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @final
    def _clear(self):
        # type: (BUCS) -> BUCS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        return self._do_clear()


BUCS = TypeVar("BUCS", bound=BaseUserCollectionStructure)  # base user collection structure self type


# noinspection PyAbstractClass
class BaseProxyCollectionStructure(BaseProxyStructure[BCS], BaseCollectionStructure[T_co]):
    """Base proxy collection structure."""

    __slots__ = ()

    def __iter__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for i in self._wrapped:
            yield i

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._wrapped)

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether value is in the collection or not.

        :param value: Value.
        :return: True if contained.
        """
        return value in self._wrapped


# noinspection PyAbstractClass
class BaseProxyUserCollectionStructure(BaseProxyCollectionStructure[BUCS, T_co], BaseUserCollectionStructure[T_co]):
    """Base proxy user collection structure."""

    __slots__ = ()


BPUCS = TypeVar("BPUCS", bound=BaseProxyUserCollectionStructure)  # base proxy user collection structure self type


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
class BaseProxyImmutableCollectionStructure(
    BaseProxyCollectionStructure[BICS, T_co], BaseProxyImmutableStructure[BICS], BaseImmutableCollectionStructure[T_co]
):
    """Base proxy immutable collection structure."""

    __slots__ = ()


BPICS = TypeVar(
    "BPICS", bound=BaseProxyImmutableCollectionStructure
)  # base proxy immutable collection structure self type


# noinspection PyAbstractClass
class BaseProxyUserImmutableCollectionStructure(
    BaseProxyImmutableCollectionStructure[BUICS, T_co], BaseProxyUserCollectionStructure[BUICS, T_co]
):
    """Base proxy user immutable collection structure."""

    __slots__ = ()

    def _do_clear(self):
        # type: (BPUICS) -> BPUICS
        """
        Clear (internal).

        :return: Transformed.
        """
        return type(self)(self._wrapped.clear())


BPUICS = TypeVar(
    "BPUICS", bound=BaseProxyUserImmutableCollectionStructure
)  # base proxy user immutable collection structure self type


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


# noinspection PyAbstractClass
class BaseProxyMutableCollectionStructure(
    BaseProxyCollectionStructure[BMCS, T_co], BaseProxyMutableStructure[BMCS], BaseMutableCollectionStructure[T_co]
):
    """Base proxy mutable collection structure."""

    __slots__ = ()


BPMCS = TypeVar("BPMCS", bound=BaseProxyMutableCollectionStructure)  # base proxy mutable collection structure self type


# noinspection PyAbstractClass
class BaseProxyUserMutableCollectionStructure(
    BaseProxyMutableCollectionStructure[BUMCS, T_co], BaseProxyUserCollectionStructure[BUMCS, T_co]
):
    """Base proxy user mutable collection structure."""

    __slots__ = ()

    def _do_clear(self):
        # type: (BPUMCS) -> BPUMCS
        """
        Clear (internal).

        :return: Self.
        """
        self._wrapped.clear()
        return self


BPUMCS = TypeVar(
    "BPUMCS", bound=BaseProxyUserMutableCollectionStructure
)  # base proxy user mutable collection structure self type

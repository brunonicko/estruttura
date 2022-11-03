"""Base abstract classes."""

import weakref

import basicco
import six
import slotted
from basicco import recursive_repr, safe_repr, import_path
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Type, Mapping, TypeVar, Iterator, Generic

from ._relationship import Relationship
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseStructureMeta(basicco.SlottedBaseMeta):
    """Metaclass for :class:`BaseStructure`."""


class BaseStructure(six.with_metaclass(BaseStructureMeta, basicco.SlottedBase)):
    """Base structure class."""

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
class BaseProxyStructure(BaseStructure, Generic[BS]):
    """Base proxy structure."""

    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (BS) -> None
        """
        :param wrapped: Structure to wrap.
        """
        wrapped.__register_proxy__(self)
        self.__wrapped = wrapped

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

    def serialize(self):
        # type: () -> dict[str, Any]
        """
        Serialize.

        :return: Serialized proxy.
        :raises SerializationError: Error while serializing.
        """
        return {
            "__class__": import_path.get_path(type(self._wrapped)),
            "__state__": self._wrapped.serialize(),
        }

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[BPS], dict[str, Any]) -> BPS
        """
        Deserialize.

        :param serialized: Serialized proxy.
        :return: Proxy structure.
        :raises SerializationError: Error while deserializing.
        """
        wrapped_cls, wrapped_state = serialized["__class__"], serialized["__state__"]
        wrapped = wrapped_cls.deserialize(wrapped_state)
        return cls(wrapped)

    @property
    def _wrapped(self):
        # type: () -> BS
        """Wrapped structure."""
        return self.__wrapped


BPS = TypeVar("BPS", bound=BaseProxyStructure)  # base proxy structure self type


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


BIS = TypeVar("BIS", bound=BaseImmutableStructure)  # base immutable structure self type


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


BMS = TypeVar("BMS", bound=BaseMutableStructure)  # base mutable structure self type


class BaseProxyImmutableStructure(BaseProxyStructure[BIS], BaseImmutableStructure):
    """Base proxy immutable structure class."""
    __slots__ = ()

    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(self._wrapped)


class BaseProxyMutableStructure(BaseProxyStructure[BMS], BaseMutableStructure):
    """Base proxy mutable structure class."""
    __slots__ = ()


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


BCS = TypeVar("BCS", bound=BaseCollectionStructure)  # base collection structure self type


# noinspection PyAbstractClass
class BaseProxyCollectionStructure(BaseProxyStructure[BCS], BaseCollectionStructure[T_co]):
    """Base proxy collection structure class."""

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


BICS = TypeVar("BICS", bound=BaseImmutableCollectionStructure)  # base immutable collection structure self type


class BaseProxyImmutableCollectionStructure(
    BaseProxyCollectionStructure[BICS, T_co], BaseProxyImmutableStructure[BICS], BaseImmutableCollectionStructure[T_co]
):
    """Base proxy immutable collection structure class."""

    __slots__ = ()

    @abstract
    def _do_clear(self):
        # type: (BPICS) -> BPICS
        """
        Clear (internal).

        :return: Transformed.
        """
        return type(self)(self._wrapped.clear())


BPICS = TypeVar(
    "BPICS", bound=BaseProxyImmutableCollectionStructure
)  # base proxy immutable collection structure self type


# noinspection PyAbstractClass
class BaseMutableCollectionStructure(BaseCollectionStructure[T_co], BaseMutableStructure):
    """Base mutable collection structure."""

    __slots__ = ()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()


BMCS = TypeVar("BMCS", bound=BaseMutableCollectionStructure)  # base mutable collection structure self type


class BaseProxyMutableCollectionStructure(
    BaseProxyCollectionStructure[BMCS, T_co], BaseProxyMutableStructure[BMCS], BaseMutableCollectionStructure[T_co]
):
    """Base proxy mutable collection structure class."""

    __slots__ = ()

    @abstract
    def _do_clear(self):
        # type: (BPMCS) -> BPMCS
        """
        Clear (internal).

        :return: Self.
        """
        self._wrapped.clear()
        return self


BPMCS = TypeVar("BPMCS", bound=BaseProxyMutableCollectionStructure)  # base proxy mutable collection structure self type

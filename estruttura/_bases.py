import abc
import weakref

import six
import slotted
from basicco import (
    Base,
    BaseMeta,
    recursive_repr,
    runtime_final,
    safe_repr,
    type_checking,
)
from tippo import Any, Iterator, Type, TypeVar, cast

from ._relationship import Relationship

T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class BaseStructureMeta(BaseMeta, slotted.SlottedABCGenericMeta):
    """Metaclass for :class:`BaseStructure`."""


class BaseStructure(six.with_metaclass(BaseStructureMeta, Base)):
    """Non-hashable by default."""

    __slots__ = ()

    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__qualname__)
        raise TypeError(error)


# Set as non-hashable by default.
type.__setattr__(BaseStructure, "__hash__", None)


class HashableStructure(BaseStructure, slotted.SlottedHashable):
    """Forces implementation of `__hash__` method."""

    __slots__ = ()

    @abc.abstractmethod
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()


class SizedStructure(BaseStructure, slotted.SlottedSized):
    """Forces implementation of `__len__` method."""

    __slots__ = ()

    # noinspection PyProtocol
    @abc.abstractmethod
    def __len__(self):
        # type: () -> int
        raise NotImplementedError()


class IterableStructure(BaseStructure, slotted.SlottedIterable[T_co]):
    """Forces implementation of `__iter__` method."""

    __slots__ = ()

    @abc.abstractmethod
    def __iter__(self):
        # type: () -> Iterator[T_co]
        raise NotImplementedError()


class ContainerStructure(BaseStructure, slotted.SlottedContainer[T_co]):
    """Forces implementation of `__contains__` method."""

    __slots__ = ()

    @abc.abstractmethod
    def __contains__(self, content):
        # type: (object) -> bool
        raise NotImplementedError()


class CollectionStructureMeta(BaseStructureMeta):
    """Metaclass for :class:`CollectionStructure`."""


SlottedCollection = slotted.SlottedCollection  # trick static type checking.
if SlottedCollection is None:
    globals()["SlottedCollection"] = object
assert SlottedCollection is not None


# noinspection PyAbstractClass
class CollectionStructure(
    six.with_metaclass(
        CollectionStructureMeta, SizedStructure, IterableStructure[T_co], ContainerStructure[T_co], SlottedCollection
    )
):
    """Collection structure."""

    __slots__ = ()


class UniformStructureMeta(CollectionStructureMeta):
    """Metaclass for :class:`UniformStructure`."""

    __relationship_type__ = Relationship  # type: Type[Relationship]


# noinspection PyAbstractClass
class UniformStructure(six.with_metaclass(UniformStructureMeta, CollectionStructure[T_co])):
    """Container structure with a single relationship."""

    __slots__ = ("__proxy_refs",)
    __relationship__ = Relationship()  # type: Relationship | None

    def __init_subclass__(cls, relationship=None, **kwargs):
        # type: (Relationship | None, **Any) -> None
        """
        :param relationship: Relationship.
        """
        if relationship is not None:
            type_checking.assert_is_instance(relationship, cls.__relationship_type__)
            cls.__relationship__ = relationship
        super(UniformStructure, cls).__init_subclass__(**kwargs)  # noqa

    def __register_proxy__(self, proxy):
        # type: (ProxyUniformStructure) -> None
        try:
            _ = self.__proxy_refs  # type: ignore
        except AttributeError:
            proxies = weakref.WeakValueDictionary()  # type: weakref.WeakValueDictionary[int, ProxyUniformStructure]
            self.__proxy_refs = proxies  # type: ignore
        else:
            proxies = self.__proxy_refs
        proxies[id(proxy)] = proxy

    @property
    @runtime_final.final
    def __proxies__(self):
        # type: () -> tuple[ProxyUniformStructure, ...]

        # Get proxies from weak value dictionary.
        try:
            proxy_refs = self.__proxy_refs  # type: ignore
        except AttributeError:
            proxy_refs = weakref.WeakValueDictionary()  # type: ignore

        # Remove invalid proxies.
        self.__proxy_refs = weakref.WeakValueDictionary(
            dict((i, p) for i, p in six.iteritems(proxy_refs) if p.__wrapped__ is self)
        )  # type: ignore

        return tuple(self.__proxy_refs.values())

    @property
    def _proxies(self):
        # type: () -> tuple[ProxyUniformStructure, ...]
        return self.__proxies__


class PrivateUniformStructure(UniformStructure[T_co]):
    """Has private transformation methods which return a transformed version (immutable) or self (mutable)."""

    __slots__ = ()

    @abc.abstractmethod
    def _clear(self):
        # type: (PUS) -> PUS
        """
        Clear.

        :return: Transformed.
        """
        raise NotImplementedError()


PUS = TypeVar("PUS", bound=PrivateUniformStructure)


# noinspection PyAbstractClass
class InteractiveUniformStructure(PrivateUniformStructure[T_co]):
    """Has public transformation methods which return a transformed version (immutable) or self (mutable)."""

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: (IUS) -> IUS
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


IUS = TypeVar("IUS", bound=InteractiveUniformStructure)


# noinspection PyAbstractClass
class MutableUniformStructure(PrivateUniformStructure[T_co]):
    """Has public mutable transformation methods."""

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()


class ProxyUniformStructure(UniformStructure[T_co]):
    """Wraps a uniform structure."""

    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (PrivateUniformStructure[T_co]) -> None
        """
        :param wrapped: Structure to be wrapped.
        """
        self.__wrapped = wrapped
        wrapped.__register_proxy__(self)

    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        return "{}({!r})".format(type(self).__qualname__, self._wrapped)

    @runtime_final.final
    def __iter__(self):
        # type: () -> Iterator[T_co]
        for v in iter(self._wrapped):
            yield v

    @runtime_final.final
    def __contains__(self, content):
        # type: (object) -> bool
        return content in self._wrapped

    @runtime_final.final
    def __len__(self):
        # type: () -> int
        return len(self._wrapped)

    @property
    @runtime_final.final
    def __wrapped__(self):
        # type: () -> PrivateUniformStructure[T_co]
        return self.__wrapped

    @property
    def _wrapped(self):
        # type: () -> PrivateUniformStructure[T_co]
        return self.__wrapped__


class PrivateProxyUniformStructure(ProxyUniformStructure[T_co], PrivateUniformStructure[T_co]):
    """Has private transformation methods which return a transformed version (immutable) or self (mutable)."""

    __slots__ = ()

    @runtime_final.final
    def _transform_wrapped(self, new_wrapped):
        # type: (PPUS, PrivateUniformStructure[T_co]) -> PPUS
        if new_wrapped is self._wrapped or new_wrapped is None:
            return self
        else:
            return type(self)(new_wrapped)

    @runtime_final.final
    def _clear(self):
        # type: (PPUS) -> PPUS
        """
        Clear.

        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._clear())  # noqa


PPUS = TypeVar("PPUS", bound=PrivateProxyUniformStructure)


class InteractiveProxyUniformStructure(PrivateProxyUniformStructure[T_co], InteractiveUniformStructure[T_co]):
    """Has public transformation methods which return a transformed version (immutable) or self (mutable)."""

    __slots__ = ()


class MutableProxyUniformStructure(PrivateProxyUniformStructure[T_co], MutableUniformStructure[T_co]):
    """Has public mutable transformation methods."""

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (MutableUniformStructure[T_co]) -> None
        """
        :param wrapped: Mutable structure.
        """
        super(MutableProxyUniformStructure, self).__init__(wrapped)

    @property
    def _wrapped(self):
        # type: () -> MutableUniformStructure[T_co]
        """Wrapped mutable structure."""
        return cast(MutableUniformStructure[T_co], super(MutableProxyUniformStructure, self)._wrapped)

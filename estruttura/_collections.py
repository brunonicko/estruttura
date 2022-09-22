import abc

import six
import slotted
from basicco import runtime_final, type_checking
from tippo import Any, Type, TypeVar, Iterator, cast

from ._bases import BaseMeta, BaseSized, BaseIterable, BaseContainer
from ._relationship import Relationship


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class BaseCollectionMeta(BaseMeta):
    """Metaclass for :class:`BaseCollection`."""

    __relationship_type__ = Relationship  # type: Type[Relationship]


# Trick static type checking.
SlottedCollection = slotted.SlottedCollection
if SlottedCollection is None:
    globals()["SlottedCollection"] = object
assert SlottedCollection is not None


# noinspection PyAbstractClass
class BaseCollection(
    six.with_metaclass(BaseCollectionMeta, BaseSized, BaseIterable[T_co], BaseContainer[T_co], SlottedCollection)
):
    """
    Base collection.

    Features:
      - Sized iterable container.
      - Optional relationship.
    """

    __slots__ = ()
    __relationship__ = None  # type: Relationship | None

    def __init_subclass__(cls, relationship=None, **kwargs):
        # type: (Relationship | None, **Any) -> None
        if relationship is not None:
            type_checking.assert_is_instance(relationship, cls.__relationship_type__)
            cls.__relationship__ = relationship
        super(BaseCollection, cls).__init_subclass__(**kwargs)  # noqa

    def __hash__(self):
        """Non-hashable by default."""
        error = "{!r} object is not hashable".format(type(self).__fullname__)
        raise TypeError(error)

    @abc.abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()


# Set as non-hashable.
type.__setattr__(BaseCollection, "__hash__", None)


class BasePrivateCollection(BaseCollection[T_co]):
    """
    Base private collection.

    Features:
      - Has private transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @abc.abstractmethod
    def _clear(self):
        # type: (BPC) -> BPC
        """
        Clear.

        :return: Transformed.
        """
        raise NotImplementedError()


BPC = TypeVar("BPC", bound=BasePrivateCollection)  # base private collection type


# noinspection PyAbstractClass
class BaseInteractiveCollection(BasePrivateCollection[T_co]):
    """
    Base interactive collection.

    Features:
      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: (BIC) -> BIC
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


BIC = TypeVar("BIC", bound=BaseInteractiveCollection)  # base interactive collection type


# noinspection PyAbstractClass
class BaseMutableCollection(BasePrivateCollection[T_co]):
    """
    Base mutable collection.

    Features:
      - Has public mutable transformation methods.
    """

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()


class ProxyCollection(BaseCollection[T_co]):
    """
    Proxy collection.

    Features:
      - Wraps a private/interactive/mutable collection.
    """

    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (BasePrivateCollection[T_co]) -> None
        """
        :param wrapped: Base private/interactive/mutable collection.
        """
        self.__wrapped = wrapped

    def __repr__(self):
        return "{}({})".format(type(self).__fullname__, self._wrapped)

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
    def _wrapped(self):
        # type: () -> BasePrivateCollection[T_co]
        """Wrapped base private/interactive/mutable collection."""
        return self.__wrapped


class PrivateProxyCollection(ProxyCollection[T_co], BasePrivateCollection[T_co]):
    """
    Private proxy collection.

    Features:
      - Has private transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @runtime_final.final
    def _transform_wrapped(self, new_wrapped):
        # type: (PPC, BasePrivateCollection[T_co]) -> PPC
        if new_wrapped is self._wrapped:
            return self
        else:
            return type(self)(new_wrapped)

    @runtime_final.final
    def _clear(self):
        # type: (PPC) -> PPC
        """
        Clear.

        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._clear())  # noqa


PPC = TypeVar("PPC", bound=PrivateProxyCollection)  # private proxy collection type


class InteractiveProxyCollection(PrivateProxyCollection[T_co], BaseInteractiveCollection[T_co]):
    """
    Proxy interactive collection.

    Features:
      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()


class MutableProxyCollection(PrivateProxyCollection[T_co], BaseMutableCollection[T_co]):
    """
    Proxy mutable collection.

    Features:
      - Has public mutable transformation methods.
    """

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (BaseMutableCollection[T_co]) -> None
        """
        :param wrapped: Base mutable collection.
        """
        super(MutableProxyCollection, self).__init__(wrapped)

    @property
    def _wrapped(self):
        # type: () -> BaseMutableCollection[T_co]
        """Wrapped base mutable collection."""
        return cast(BaseMutableCollection[T_co], super(MutableProxyCollection, self)._wrapped)

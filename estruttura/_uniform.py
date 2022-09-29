import abc

import six
import slotted
from basicco import runtime_final, type_checking, safe_repr, recursive_repr
from tippo import Any, Type, TypeVar, Iterator, cast

from ._bases import StructureMeta, CollectionStructure
from ._relationship import Relationship


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class UniformStructureMeta(StructureMeta):
    """Metaclass for :class:`UniformStructure`."""

    __relationship_type__ = Relationship  # type: Type[Relationship]


# Trick static type checking.
SlottedCollection = slotted.SlottedCollection
if SlottedCollection is None:
    globals()["SlottedCollection"] = object
assert SlottedCollection is not None


# noinspection PyAbstractClass
class UniformStructure(six.with_metaclass(UniformStructureMeta, CollectionStructure[T_co])):
    """Container structure with a single relationship."""

    __slots__ = ()
    __relationship__ = None  # type: Relationship | None

    def __init_subclass__(cls, relationship=None, **kwargs):
        # type: (Relationship | None, **Any) -> None
        """
        :param relationship: Relationship.
        """
        if relationship is not None:
            type_checking.assert_is_instance(relationship, cls.__relationship_type__)
            cls.__relationship__ = relationship
        super(UniformStructure, cls).__init_subclass__(**kwargs)  # noqa


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
    """Wraps a private/interactive/mutable uniform structure."""

    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (PrivateUniformStructure[T_co]) -> None
        """
        :param wrapped: Structure private/interactive/mutable collection.
        """
        self.__wrapped = wrapped

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
    def _wrapped(self):
        # type: () -> PrivateUniformStructure[T_co]
        """Wrapped base private/interactive/mutable collection."""
        return self.__wrapped


class PrivateProxyUniformStructure(ProxyUniformStructure[T_co], PrivateUniformStructure[T_co]):
    """Has private transformation methods which return a transformed version (immutable) or self (mutable)."""

    __slots__ = ()

    @runtime_final.final
    def _transform_wrapped(self, new_wrapped):
        # type: (PPUS, PrivateUniformStructure[T_co]) -> PPUS
        if new_wrapped is self._wrapped:
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
        :param wrapped: Structure mutable collection.
        """
        super(MutableProxyUniformStructure, self).__init__(wrapped)

    @property
    def _wrapped(self):
        # type: () -> MutableProxyUniformStructure[T_co]
        """Wrapped base mutable collection."""
        return cast(MutableProxyUniformStructure[T_co], super(MutableProxyUniformStructure, self)._wrapped)

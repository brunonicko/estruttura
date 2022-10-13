from basicco.recursive_repr import recursive_repr
from basicco.explicit_hash import set_to_none
from basicco.safe_repr import safe_repr
from basicco.runtime_final import final
from basicco.type_checking import assert_is_instance
from tippo import Any, TypeVar, Type, Union, cast

from ..structures import (
    Structure,
    ImmutableStructure,
    MutableStructure,
    CollectionStructure,
    ImmutableCollectionStructure,
    MutableCollectionStructure,
)


T_co = TypeVar("T_co", covariant=True)

BST = TypeVar("BST", bound=Structure)  # base state type
ST = TypeVar("ST", bound=Union[ImmutableStructure, MutableStructure])  # state type


class Proxy(Structure[BST]):
    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (BST) -> None
        """
        :param wrapped: Structure to be wrapped.
        """
        self.__wrapped = wrapped
        wrapped.__register_proxy__(self)

    def __hash__(self):
        # type: () -> int
        return hash(self._state)

    def __eq__(self, other):
        # type: (P, object) -> bool
        return type(self) is type(other) and self._state == cast(P, other)._state

    @safe_repr
    @recursive_repr
    def __repr__(self):
        return "{}({!r})".format(type(self).__qualname__, self.__wrapped__)

    @property
    def __wrapped__(self):
        # type: () -> BST
        return self.__wrapped

    @__wrapped__.setter
    @final
    def __wrapped__(self, new_wrapped):
        # type: (BST | None) -> None
        if new_wrapped is not None and new_wrapped is not self.__wrapped:
            self.__wrapped.__deregister_proxy__(self)
            self.__wrapped = new_wrapped
            new_wrapped.__register_proxy__(self)

    def _transform(self, new_state):
        # type: (P, BST | None) -> P
        return type(self)(new_state)

    def serialize(self):
        # type: () -> Any
        return None  # TODO

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[P], Any) -> P
        return cls(cast(BST, None))  # TODO

    @property
    def _state(self):
        # type: () -> BST
        return self.__wrapped__


P = TypeVar("P", bound=Proxy)

IST = TypeVar("IST", bound=ImmutableStructure)


class ImmutableProxy(Proxy[IST], ImmutableStructure[IST]):
    __slots__ = ()

    def __init__(self, wrapped):
        # type: (IST) -> None
        """
        :param wrapped: Structure to be wrapped.
        """
        assert_is_instance(wrapped, ImmutableStructure)
        super(ImmutableProxy, self).__init__(wrapped)


IP = TypeVar("IP", bound=ImmutableProxy)


class MutableProxy(Proxy[ST], MutableStructure[ST]):
    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def _transform(self, new_state):
        # type: (MP, ST | None) -> MP
        self.__wrapped__ = new_state
        return self


MP = TypeVar("MP", bound=MutableProxy)


CST = TypeVar("CST", bound=Union[ImmutableCollectionStructure, MutableCollectionStructure])


class ProxyCollection(Proxy[CST], CollectionStructure[CST, T_co]):
    """Wraps a collection."""
    __slots__ = ()


ICST = TypeVar("ICST", bound=ImmutableCollectionStructure)


class ProxyImmutableCollection(
    ProxyCollection[ICST, T_co],
    ImmutableProxy[ICST],
    ImmutableCollectionStructure[ICST, T_co],
):
    __slots__ = ()


class ProxyMutableCollection(
    ProxyCollection[CST, T_co],
    MutableProxy[CST],
    MutableCollectionStructure[CST, T_co],
):
    __slots__ = ()

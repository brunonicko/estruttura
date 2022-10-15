import weakref

from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Generic, TypeVar, Type, Iterator, Union, cast

from ..base import Base, BaseCollection, BaseImmutable, BaseMutable, BaseImmutableCollection, BaseMutableCollection
from ._relationship import Relationship


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

BST = TypeVar("BST", bound=Base)  # base state type
ST = TypeVar("ST", bound=Union[BaseImmutable, BaseMutable])  # state type


class Structure(Base, Generic[BST]):
    __slots__ = ("__proxy_refs",)

    def __register_proxy__(self, proxy):
        # type: (S, Structure[S]) -> None
        try:
            _ = self.__proxy_refs  # type: ignore
        except AttributeError:
            proxies = weakref.WeakValueDictionary()  # type: weakref.WeakValueDictionary[int, Structure[S]]
            self.__proxy_refs = proxies
        else:
            proxies = self.__proxy_refs
        proxies[id(proxy)] = proxy

    def __deregister_proxy__(self, proxy):
        # type: (S, Structure[S]) -> None
        try:
            _ = self.__proxy_refs  # type: ignore
        except AttributeError:
            proxies = weakref.WeakValueDictionary()  # type: weakref.WeakValueDictionary[int, Structure[S]]
            self.__proxy_refs = proxies
        else:
            proxies = self.__proxy_refs
        del proxies[id(proxy)]

    @abstract
    def _transform(self, new_state):
        # type: (S, BST | None) -> S
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

    @property
    @final
    def __proxies__(self):
        # type: (S) -> tuple[Structure[S], ...]
        try:
            proxy_refs = self.__proxy_refs  # type: ignore
        except AttributeError:
            proxy_refs = self.__proxy_refs = weakref.WeakValueDictionary()  # type: ignore
        return tuple(proxy_refs.values())

    @property
    @abstract
    def _state(self):
        # type: () -> BST
        raise NotImplementedError()

    @property
    def _proxies(self):
        # type: (S) -> tuple[Structure[S], ...]
        return self.__proxies__


S = TypeVar("S", bound=Structure)  # structure self type

IST = TypeVar("IST", bound=BaseImmutable)  # immutable state type


# noinspection PyAbstractClass
class ImmutableStructure(Structure[IST], BaseImmutable):
    __slots__ = ()

    def __hash__(self):
        # type: () -> int
        return hash(self._state)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._state == cast(ImmutableStructure, other)._state


# noinspection PyAbstractClass
class MutableStructure(Structure[ST], BaseMutable):
    __slots__ = ()

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._state == cast(MutableStructure, other)._state


CST = TypeVar("CST", bound=Union[BaseImmutableCollection, BaseMutableCollection])  # collection state type


# noinspection PyAbstractClass
class CollectionStructure(Structure[CST], BaseCollection[T_co]):
    __slots__ = ()
    relationship = None  # type: Relationship | None

    def __len__(self):
        # type: () -> int
        return len(self._state)

    def __iter__(self):
        # type: () -> Iterator[T_co]
        for value in self._state:
            yield value

    def __contains__(self, item):
        # type: (object) -> bool
        return item in self._state

    def _clear(self):
        # type: (CS) -> CS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        return self._transform(self._state.clear())


CS = TypeVar("CS", bound=CollectionStructure)  # collection structure self type


ICST = TypeVar("ICST", bound=BaseImmutableCollection)  # immutable collection state type


# noinspection PyAbstractClass
class ImmutableCollectionStructure(
    CollectionStructure[ICST, T_co],
    ImmutableStructure[ICST],
    BaseImmutableCollection[T_co],
):
    __slots__ = ()


# noinspection PyAbstractClass
class MutableCollectionStructure(
    CollectionStructure[CST, T_co],
    MutableStructure[CST],
    BaseMutableCollection[T_co],
):
    __slots__ = ()

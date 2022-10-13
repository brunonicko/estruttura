from basicco.explicit_hash import set_to_none
from tippo import TypeVar

from ..base import Base, BaseImmutable, BaseMutable, BaseCollection, BaseImmutableCollection, BaseMutableCollection


T_co = TypeVar("T_co", covariant=True)


class State(Base):
    __slots__ = ()


class ImmutableState(State, BaseImmutable):
    __slots__ = ()


class MutableState(State, BaseMutable):
    __slots__ = ()


class CollectionState(State, BaseCollection[T_co]):
    __slots__ = ()


class ImmutableCollectionState(ImmutableState, CollectionState[T_co], BaseImmutableCollection[T_co]):
    __slots__ = ()


class MutableCollectionState(MutableState, CollectionState[T_co], BaseMutableCollection[T_co]):
    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

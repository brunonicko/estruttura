import itertools

import pyrsistent
from six import moves
from basicco.abstract_class import abstract
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import iterable_repr
from basicco.explicit_hash import set_to_none
from tippo import Any, overload, MutableSequence, Iterable, Iterator, TypeVar, Type, AbstractSet, cast
from pyrsistent.typing import PSet

from ..base import BaseSet, BaseImmutableSet, BaseMutableSet


T = TypeVar("T")


_PSET_TYPE = type(pyrsistent.pset())  # type: Type[PSet]


class SetState(BaseSet[T]):
    __slots__ = ()

    @abstract
    def __init__(self, initial=()):  # noqa
        # type: (Iterable[T]) -> None
        raise NotImplementedError()

    @property
    @abstract
    def _internal(self):
        # type: () -> AbstractSet[T]
        raise NotImplementedError()


class ImmutableSetState(SetState[T], BaseImmutableSet[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        if type(initial) is _PSET_TYPE:
            internal = cast(PSet[T], initial)
        else:
            internal = pyrsistent.pset(initial)
        self.__internal = internal  # type: PSet[T]

    def __hash__(self):
        # type: () -> int
        return hash(self._internal)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(ImmutableSetState, other)._internal

    @property
    def _internal(self):
        # type: () -> PSet[T]
        return self.__internal


ISS = TypeVar("ISS", bound=ImmutableSetState)


class MutableSetState(SetState[T], BaseMutableSet[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        self.__internal = set(initial)  # type: set[T]

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(MutableSetState, other)._internal

    @property
    def _internal(self):
        # type: () -> set[T]
        return self.__internal


MSS = TypeVar("MSS", bound=MutableSetState)

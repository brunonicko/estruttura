import itertools

import pyrsistent
from six import moves
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import iterable_repr
from basicco.explicit_hash import set_to_none
from tippo import Any, overload, MutableSequence, Iterable, Iterator, TypeVar, Type, cast
from pyrsistent.typing import PVector

from ._base import CollectionState, ImmutableCollectionState, MutableCollectionState
from ..base import BaseList, BaseImmutableList, BaseMutableList


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


_PVECTOR_TYPE = type(pyrsistent.pvector())  # type: Type[PVector]


class ListState(CollectionState[T], BaseList[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        if type(initial) is _PVECTOR_TYPE:
            self.__internal = initial
        else:
            self.__internal = pyrsistent.pvector(initial)  # type: PVector[T]

    def __hash__(self):
        # type: () -> int
        return hash(self.__internal)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self.__internal == cast(ListState, other).__internal

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return iterable_repr(
            self.__internal,
            prefix="{}([".format(type(self).__qualname__),
            suffix="])",
        )

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self.__internal)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self.__internal[index]

    def __iter__(self):
        # type: () -> Iterator[T]
        for v in iter(self.__internal):
            yield v

    def __contains__(self, content):
        # type: (object) -> bool
        return content in self.__internal

    def __len__(self):
        # type: () -> int
        return len(self.__internal)

    def _insert(self, index, *values):
        # type: (LS, int, T) -> LS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        index = self.resolve_index(index, clamp=True)
        if index == len(self.__internal):
            return self._extend(values)
        elif index == 0:
            return type(self)(pyrsistent.pvector(values) + self.__internal)
        else:
            return type(self)(self.__internal[:index] + pyrsistent.pvector(values) + self.__internal[index:])

    def _clear(self):
        # type: (LS) -> LS
        """
        Clear.

        :return: Transformed.
        """
        return type(self)()

    def _move(self, item, target_index):
        # type: (LS, slice | int, int) -> LS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        result = self.pre_move(item, target_index)
        if result is None:
            return self
        index, stop, target_index, post_index = result

        values = self.__internal[index:stop]
        internal = self.__internal.delete(index, stop)

        if post_index == len(internal):
            return type(self)(internal.extend(values))
        elif post_index == 0:
            return type(self)(pyrsistent.pvector(values) + internal)
        else:
            return type(self)(internal[:post_index] + pyrsistent.pvector(values) + internal[post_index:])

    def _delete(self, item):
        # type: (LS, slice | int) -> LS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            return type(self)(self.__internal.delete(index, stop))
        else:
            index = self.resolve_index(item)
            stop = index + 1
            return type(self)(self.__internal.delete(index, stop))

    @overload
    def _update(self, item, value):
        # type: (LS, int, T) -> LS
        pass

    @overload
    def _update(self, item, value):
        # type: (LS, slice, Iterable[T]) -> LS
        pass

    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            values = value
        else:
            index = self.resolve_index(item)
            stop = index + 1
            values = (value,)

        if not values:
            error = "no values provided"
            raise ValueError(error)

        pairs = itertools.chain.from_iterable(zip(moves.xrange(index, stop), values))
        return type(self)(self.__internal.mset(*pairs))

    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return self.__internal.count(value)

    def index(self, value, start=None, stop=None):
        # type: (Any, int | None, int | None) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        if start is None and stop is None:
            args = (value,)  # type: tuple[Any, ...]
        elif start is not None and stop is None:
            args = (value, start)
        elif start is not None and stop is not None:
            args = (value, start, stop)
        else:
            error = "provided 'stop' argument but did not provide 'start'"
            raise ValueError(error)
        return self.__internal.index(*args)


LS = TypeVar("LS", bound=ListState)


class ImmutableListState(
    ListState[T_co],
    ImmutableCollectionState[T_co],
    BaseImmutableList[T_co],
):
    __slots__ = ()


class MutableListState(
    ListState[T_co],
    MutableCollectionState[T_co],
    BaseMutableList[T_co],
):
    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

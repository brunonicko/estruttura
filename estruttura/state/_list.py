import itertools

import pyrsistent
from six import moves
from basicco.abstract_class import abstract
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import iterable_repr
from basicco.explicit_hash import set_to_none
from tippo import Any, overload, MutableSequence, Iterable, Iterator, TypeVar, Type, Sequence, cast
from pyrsistent.typing import PVector

from ..base import BaseList, BaseImmutableList, BaseMutableList


T = TypeVar("T")


_PVECTOR_TYPE = type(pyrsistent.pvector())  # type: Type[PVector]


class ListState(BaseList[T]):
    __slots__ = ()

    @abstract
    def __init__(self, initial=()):  # noqa
        # type: (Iterable[T]) -> None
        raise NotImplementedError()

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__qualname__),
            suffix="])",
        )

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._internal)

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
        return self._internal[index]

    def __iter__(self):
        # type: () -> Iterator[T]
        for v in iter(self._internal):
            yield v

    def __contains__(self, content):
        # type: (object) -> bool
        return content in self._internal

    def __len__(self):
        # type: () -> int
        return len(self._internal)

    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return self._internal.count(value)

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
        return self._internal.index(*args)

    @property
    @abstract
    def _internal(self):
        # type: () -> Sequence[T]
        raise NotImplementedError()


class ImmutableListState(ListState[T], BaseImmutableList[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        if type(initial) is _PVECTOR_TYPE:
            internal = cast(PVector[T], initial)
        else:
            internal = pyrsistent.pvector(initial)
        self.__internal = internal  # type: PVector[T]

    def __hash__(self):
        # type: () -> int
        return hash(self._internal)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(ImmutableListState, other)._internal

    def _insert(self, index, *values):
        # type: (ILS, int, T) -> ILS
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
        if index == len(self._internal):
            return self._extend(values)
        elif index == 0:
            return type(self)(pyrsistent.pvector(values) + self._internal)
        else:
            return type(self)(self._internal[:index] + pyrsistent.pvector(values) + self._internal[index:])

    def _clear(self):
        # type: (ILS) -> ILS
        """
        Clear.

        :return: Transformed.
        """
        return type(self)()

    def _move(self, item, target_index):
        # type: (ILS, slice | int, int) -> ILS
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

        values = self._internal[index:stop]
        internal = self._internal.delete(index, stop)

        if post_index == len(internal):
            return type(self)(internal.extend(values))
        elif post_index == 0:
            return type(self)(pyrsistent.pvector(values) + internal)
        else:
            return type(self)(internal[:post_index] + pyrsistent.pvector(values) + internal[post_index:])

    def _delete(self, item):
        # type: (ILS, slice | int) -> ILS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            return type(self)(self._internal.delete(index, stop))
        else:
            index = self.resolve_index(item)
            stop = index + 1
            return type(self)(self._internal.delete(index, stop))

    @overload
    def _update(self, item, value):
        # type: (ILS, int, T) -> ILS
        pass

    @overload
    def _update(self, item, value):
        # type: (ILS, slice, Iterable[T]) -> ILS
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
        return type(self)(self._internal.mset(*pairs))

    @property
    def _internal(self):
        # type: () -> PVector[T]
        return self.__internal


ILS = TypeVar("ILS", bound=ImmutableListState)


class MutableListState(ListState[T], BaseMutableList[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        self.__internal = list(initial)  # type: list[T]

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(MutableListState, other)._internal

    def _insert(self, index, *values):
        # type: (MLS, int, T) -> MLS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Self.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        index = self.resolve_index(index, clamp=True)
        self._internal[index:index] = values
        return self

    def _clear(self):
        # type: (MLS) -> MLS
        """
        Clear.

        :return: Self.
        """
        self._internal.clear()
        return self

    def _move(self, item, target_index):
        # type: (MLS, slice | int, int) -> MLS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Self.
        """
        result = self.pre_move(item, target_index)
        if result is None:
            return self
        index, stop, target_index, post_index = result

        values = self._internal[index:stop]
        del self._internal[index:stop]
        self._internal[post_index:post_index] = values

        return self

    def _delete(self, item):
        # type: (MLS, slice | int) -> MLS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Self.
        """
        del self._internal[item]
        return self

    @overload
    def _update(self, item, value):
        # type: (MLS, int, T) -> MLS
        pass

    @overload
    def _update(self, item, value):
        # type: (MLS, slice, Iterable[T]) -> MLS
        pass

    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Self.
        """
        self._internal[item] = value
        return self

    @property
    def _internal(self):
        # type: () -> list[T]
        return self.__internal


MLS = TypeVar("MLS", bound=MutableListState)

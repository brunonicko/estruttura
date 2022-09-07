import itertools

import pyrsistent
import six
from basicco import runtime_final, recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Iterator, overload
from pyrsistent.typing import PVector

from .bases import BaseList, BaseProtectedList, BaseInteractiveList, BaseMutableList
from .utils import resolve_index, resolve_continuous_slice, pre_move
from ._bases import (
    BaseState,
    BaseRelationship,
    BaseStructure,
    BaseProtectedStructure,
    BaseInteractiveStructure,
    BaseMutableStructure,
)


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type
RT = TypeVar("RT", bound=BaseRelationship)  # relationship type


@runtime_final.final
class ListState(BaseState[T, PVector[T]], BaseInteractiveList[T]):
    """Immutable list state."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Iterable[T]) -> PVector[T]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pvector(initial)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        super(ListState, self).__init__(initial)

    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._internal

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._internal:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._internal)

    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__fullname__),
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
        # type: (slice) -> list[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.
        :param index: Index/slice.
        :return: Value/values.
        """
        if isinstance(index, slice):
            return list(self._internal[index])
        else:
            return self._internal[index]

    def _clear(self):
        # type: (LS) -> LS
        """
        Clear.

        :return: Transformed.
        """
        return self._make(pyrsistent.pvector())

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
        if index == len(self._internal):
            return self.extend(values)
        elif index == 0:
            return self._make(pyrsistent.pvector(values) + self._internal)
        else:
            return self._make(self._internal[:index] + pyrsistent.pvector(values) + self._internal[index:])

    def _append(self, value):
        # type: (LS, T) -> LS
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.append(value))

    def _extend(self, iterable):
        # type: (LS, Iterable[T]) -> LS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._make(self._internal.extend(iterable))

    def _remove(self, value):
        # type: (LS, T) -> LS
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._make(self._internal.remove(value))

    def _reverse(self):
        # type: (LS) -> LS
        """
        Reverse values.

        :return: Transformed.
        """
        return self._make(pyrsistent.pvector(reversed(self._internal)))

    def _move(self, item, target_index):
        # type: (LS, slice | int, int) -> LS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        result = pre_move(len(self._internal), item, target_index)
        if result is None:
            return self
        index, stop, target_index, post_index = result

        values = self._internal[index:stop]
        internal = self._internal.delete(index, stop)

        if post_index == len(internal):
            return self._make(internal.extend(values))
        elif post_index == 0:
            return self._make(pyrsistent.pvector(values) + internal)
        else:
            return self._make(internal[:post_index] + pyrsistent.pvector(values) + internal[post_index:])

    def _delete(self, item):
        # type: (LS, slice | int) -> LS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            return self._make(self._internal.delete(index, stop))
        else:
            index = self.resolve_index(item)
            return self._make(self._internal.delete(index, None))

    def _update(self, index, *values):
        # type: (LS, int, T) -> LS
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        index = self.resolve_index(index)
        stop = self.resolve_index(index + len(values) - 1) + 1
        pairs = itertools.chain.from_iterable(zip(range(index, stop), values))
        new_internal = self._internal.mset(*pairs)  # type: ignore
        return self._make(new_internal)

    def count(self, value):
        # type: (Any) -> int
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

    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return resolve_index(len(self._internal), index, clamp=clamp)

    def resolve_continuous_slice(self, slc):
        # type: (slice) -> tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self._internal), slc)


LS = TypeVar("LS", bound=ListState)


# noinspection PyAbstractClass
class BaseListStructure(BaseStructure[T_co, T_co, ListState[T_co], int, RT], BaseList[T_co]):
    """Base list structure."""

    __slots__ = ()

    @runtime_final.final
    def get_value(self, location):
        # type: (int) -> T_co
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        try:
            return self[location]
        except IndexError as e:
            exc = KeyError(e)
            six.raise_from(exc, None)
            raise exc


# noinspection PyAbstractClass
class BaseProtectedListStructure(
    BaseListStructure[T_co, RT],
    BaseProtectedStructure[T_co, T_co, ListState[T_co], int, RT],
    BaseProtectedList[T_co],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveListStructure(
    BaseProtectedListStructure[T_co, RT],
    BaseInteractiveStructure[T_co, T_co, ListState[T_co], int, RT],
    BaseInteractiveList[T_co],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableListStructure(
    BaseProtectedListStructure[T_co, RT],
    BaseMutableStructure[T_co, T_co, ListState[T_co], int, RT],
    BaseMutableList[T_co],
):
    """Base mutable list structure."""

    __slots__ = ()

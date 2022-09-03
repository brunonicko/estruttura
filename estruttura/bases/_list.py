import abc

import slotted
from basicco import runtime_final
from tippo import Any, TypeVar, Iterator, Sequence, MutableSequence, Iterable, overload

from ._bases import BaseCollection, BaseInteractiveCollection, BaseMutableCollection, BaseProtectedCollection


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class BaseList(BaseCollection[T_co], slotted.SlottedSequence[T_co]):
    """Base list collection."""

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: {!r}".format(type(self).__name__)
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

    @abc.abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        raise NotImplementedError()

    @overload
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> Sequence[T_co]
        pass

    @abc.abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        raise NotImplementedError()

    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        raise NotImplementedError()


# noinspection PyCallByClass
type.__setattr__(BaseList, "__hash__", None)  # force non-hashable


class BaseProtectedList(BaseList[T], BaseProtectedCollection[T]):
    """Base protected list collection."""

    __slots__ = ()

    @abc.abstractmethod
    def _insert(self, index, *values):
        # type: (BPL, int, T) -> BPL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _append(self, value):
        # type: (BPL, T) -> BPL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _extend(self, iterable):
        # type: (BPL, Iterable[T]) -> BPL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _remove(self, value):
        # type: (BPL, T) -> BPL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _reverse(self):
        # type: (BPL) -> BPL
        """
        Reverse values.

        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _move(self, item, target_index):
        # type: (BPL, slice | int, int) -> BPL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _delete(self, item):
        # type: (BPL, slice | int) -> BPL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _update(self, index, *values):
        # type: (BPL, int, T) -> BPL
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()


BPL = TypeVar("BPL", bound=BaseProtectedList)


# noinspection PyAbstractClass
class BaseInteractiveList(BaseProtectedList[T], BaseInteractiveCollection[T]):
    """Base interactive list collection."""

    __slots__ = ()

    @runtime_final.final
    def insert(self, index, *values):
        # type: (BIL, int, T) -> BIL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._insert(index, *values)

    @runtime_final.final
    def append(self, value):
        # type: (BIL, T) -> BIL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._append(value)

    @runtime_final.final
    def extend(self, iterable):
        # type: (BIL, Iterable[T]) -> BIL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._extend(iterable)

    @runtime_final.final
    def remove(self, value):
        # type: (BIL, T) -> BIL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._remove(value)

    @runtime_final.final
    def reverse(self):
        # type: (BIL) -> BIL
        """
        Reverse values.

        :return: Transformed.
        """
        return self._reverse()

    @runtime_final.final
    def move(self, item, target_index):
        # type: (BIL, slice | int, int) -> BIL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._move(item, target_index)

    @runtime_final.final
    def delete(self, item):
        # type: (BIL, slice | int) -> BIL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._delete(item)

    @runtime_final.final
    def update(self, index, *values):
        # type: (BIL, int, T) -> BIL
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._update(index, *values)


BIL = TypeVar("BIL", bound=BaseInteractiveList)


class BaseMutableList(BaseProtectedList[T], BaseMutableCollection[T], slotted.SlottedMutableSequence[T]):
    """Base mutable list collection."""

    __slots__ = ()

    @runtime_final.final
    def __iadd__(self, iterable):
        """
        In place addition.

        :param iterable: Another iterable.
        :return: Added list.
        """
        self._extend(iterable)
        return self

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    @abc.abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @overload
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @abc.abstractmethod
    def __setitem__(self, item, value):
        # type: (slice | int, T | Iterable[T]) -> None
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        raise NotImplementedError()

    @overload
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @abc.abstractmethod
    def __delitem__(self, item):
        # type: (slice | int) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :return: Value.
        """
        raise NotImplementedError()

    @runtime_final.final
    def insert(self, index, *values):
        # type: (int, T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._insert(index, *values)

    @runtime_final.final
    def append(self, value):
        # type: (T) -> None
        """
        Append value at the end.

        :param value: Value.
        """
        self._append(value)

    @runtime_final.final
    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        """
        self._extend(iterable)

    @runtime_final.final
    def remove(self, value):
        # type: (T) -> None
        """
        Remove first occurrence of value.

        :param value: Value.
        :raises ValueError: Value is not present.
        """
        self._remove(value)

    @runtime_final.final
    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    @runtime_final.final
    def move(self, item, target_index):
        # type: (slice | int, int) -> None
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        """
        self._move(item, target_index)

    @runtime_final.final
    def delete(self, item):
        # type: (slice | int) -> None
        """
        Delete values at index/slice.

        :param item: Index/slice.
        """
        self._delete(item)

    @runtime_final.final
    def update(self, index, *values):
        # type: (int, T) -> None
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._update(index, *values)

import slotted
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, overload, MutableSequence, Iterable, TypeVar

from ._base import BaseUniformCollection, BaseImmutableUniformCollection, BaseMutableUniformCollection
from ..utils import resolve_index, resolve_continuous_slice, pre_move


T = TypeVar("T")


class BaseList(BaseUniformCollection[T], slotted.SlottedSequence[T]):
    __slots__ = ()

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    @abstract
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @final
    def _append(self, value):
        # type: (BL, T) -> BL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._insert(len(self), value)

    @final
    def _extend(self, iterable):
        # type: (BL, Iterable[T]) -> BL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._insert(len(self), *iterable)

    @final
    def _remove(self, value):
        # type: (BL, T) -> BL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        :raises ValueError: Value is not present.
        """
        return self._delete(self.index(value))

    @final
    def _reverse(self):
        # type: (BL) -> BL
        """
        Reverse values.

        :return: Transformed (immutable) or self (mutable).
        """
        return self._update(slice(0, len(self)), reversed(self))

    @abstract
    def _insert(self, index, *values):
        # type: (BL, int, T) -> BL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed (immutable) or self (mutable).
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abstract
    def _move(self, item, target_index):
        # type: (BL, slice | int, int) -> BL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @abstract
    def _delete(self, item):
        # type: (BL, slice | int) -> BL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @final
    def _set(self, index, value):
        # type: (BL, int, T) -> BL
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        :raises IndexError: Invalid index.
        """
        index = self.resolve_index(index)
        return self._update(index, value)

    @overload
    def _update(self, item, value):
        # type: (BL, int, T) -> BL
        pass

    @overload
    def _update(self, item, value):
        # type: (BL, slice, Iterable[T]) -> BL
        pass

    @abstract
    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

    @abstract
    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        raise NotImplementedError()

    @abstract
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

    @final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return resolve_index(len(self), index, clamp=clamp)

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self), slc)

    @final
    def pre_move(self, item, target_index):
        # type: (slice | int, int) -> tuple[int, int, int, int] | None
        """
        Perform checks before moving values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: None or (index, stop, target index, post index).
        """
        return pre_move(len(self), item, target_index)


BL = TypeVar("BL", bound=BaseList)


# noinspection PyAbstractClass
class BaseImmutableList(BaseList[T], BaseImmutableUniformCollection[T]):
    __slots__ = ()

    @final
    def append(self, value):
        # type: (BIL, T) -> BIL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._append(value)

    @final
    def extend(self, iterable):
        # type: (BIL, Iterable[T]) -> BIL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._extend(iterable)

    @final
    def remove(self, value):
        # type: (BIL, T) -> BIL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._remove(value)

    @final
    def reverse(self):
        # type: (BIL) -> BIL
        """
        Reverse values.

        :return: Transformed.
        """
        return self._reverse()

    @final
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

    @final
    def move(self, item, target_index):
        # type: (BIL, slice | int, int) -> BIL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._move(item, target_index)

    @final
    def delete(self, item):
        # type: (BIL, slice | int) -> BIL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._delete(item)

    @final
    def set(self, index, value):
        # type: (BIL, int, T) -> BIL
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        return self._set(index, value)

    @overload
    def update(self, item, value):
        # type: (BIL, int, T) -> BIL
        pass

    @overload
    def update(self, item, value):
        # type: (BIL, slice, Iterable[T]) -> BIL
        pass

    @final
    def update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        return self._update(item, value)


BIL = TypeVar("BIL", bound=BaseImmutableList)


# noinspection PyAbstractClass
class BaseMutableList(BaseList[T], BaseMutableUniformCollection[T], slotted.SlottedMutableSequence[T]):
    __slots__ = ()

    @final
    def __iadd__(self, iterable):
        """
        In place addition.

        :param iterable: Another iterable.
        :return: Added list.
        """
        self._extend(iterable)
        return self

    @overload
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @final
    def __setitem__(self, item, value):
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        self._update(item, value)

    @overload
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @final
    def __delitem__(self, item):
        # type: (slice | int) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        self._delete(item)

    @final
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :return: Value.
        """
        value = self[index]
        del self[index]
        return value

    @final
    def insert(self, index, *values):
        # type: (int, T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._insert(index, *values)

    @final
    def append(self, value):
        # type: (T) -> None
        """
        Append value at the end.

        :param value: Value.
        """
        self._append(value)

    @final
    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        """
        self._extend(iterable)

    @final
    def remove(self, value):
        # type: (T) -> None
        """
        Remove first occurrence of value.

        :param value: Value.
        :raises ValueError: Value is not present.
        """
        self._remove(value)

    @final
    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    @final
    def move(self, item, target_index):
        # type: (slice | int, int) -> None
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        """
        self._move(item, target_index)

    @final
    def delete(self, item):
        # type: (slice | int) -> None
        """
        Delete values at index/slice.

        :param item: Index/slice.
        """
        self._delete(item)

    @final
    def set(self, index, value):
        # type: (int, T) -> None
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        self._set(index, value)

    @overload
    def update(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def update(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    @final
    def update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        self._update(item, value)

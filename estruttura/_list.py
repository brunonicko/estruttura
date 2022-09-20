import abc

import slotted
from basicco import runtime_final
from tippo import Any, TypeVar, Iterator, MutableSequence, Iterable, overload, cast

from ._bases import (
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BasePrivateCollection,
    ProxyCollection,
    InteractiveProxyCollection,
    MutableProxyCollection,
    PrivateProxyCollection,
)


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
        # type: (slice) -> MutableSequence[T_co]
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


class BasePrivateList(BaseList[T], BasePrivateCollection[T]):
    """Base private list collection."""

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


BPL = TypeVar("BPL", bound=BasePrivateList)  # base private list type


# noinspection PyAbstractClass
class BaseInteractiveList(BasePrivateList[T], BaseInteractiveCollection[T]):
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


BIL = TypeVar("BIL", bound=BaseInteractiveList)  # base interactive list type


class BaseMutableList(BasePrivateList[T], BaseMutableCollection[T], slotted.SlottedMutableSequence[T]):
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
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @abc.abstractmethod
    def __setitem__(self, item, value):
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


class ProxyList(BaseList[T_co], ProxyCollection[T_co]):
    """
    Proxy list.

    Features:
      - Wraps a private/interactive/mutable list.
    """

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (BasePrivateList[T_co]) -> None
        """
        :param wrapped: Base private/interactive/mutable list.
        """
        super(ProxyList, self).__init__(wrapped)

    @runtime_final.final
    def __hash__(self):
        """
        Get hash.

        :raises TypeError: Not hashable.
        """
        return hash((type(self), self._wrapped))

    @runtime_final.final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        return isinstance(other, type(self)) and self._wrapped == other._wrapped

    @runtime_final.final
    def __reversed__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._wrapped)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T_co]
        pass

    @runtime_final.final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._wrapped[index]

    @runtime_final.final
    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return len(self._wrapped)

    @runtime_final.final
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
        return self._wrapped.index(value, start=start, stop=stop)

    @runtime_final.final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return self._wrapped.resolve_index(index, clamp=clamp)

    @runtime_final.final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return self._wrapped.resolve_continuous_slice(slc)

    @property
    def _wrapped(self):
        # type: () -> BasePrivateList[T_co]
        """Wrapped base private/interactive/mutable list."""
        return cast(BasePrivateList[T_co], super(ProxyList, self)._wrapped)


class ProxyPrivateList(ProxyList[T], BasePrivateList[T], PrivateProxyCollection[T]):
    """
    Private proxy list.

    Features:
      - Has private transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @runtime_final.final
    def _insert(self, index, *values):
        # type: (PPL, int, T) -> PPL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._transform_wrapped(self._wrapped._insert(index, *values))

    @runtime_final.final
    def _append(self, value):
        # type: (PPL, T) -> PPL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._append(value))

    @runtime_final.final
    def _extend(self, iterable):
        # type: (PPL, Iterable[T]) -> PPL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._extend(iterable))

    @runtime_final.final
    def _remove(self, value):
        # type: (PPL, T) -> PPL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._transform_wrapped(self._wrapped._remove(value))

    @runtime_final.final
    def _reverse(self):
        # type: (PPL) -> PPL
        """
        Reverse values.

        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._reverse())

    @runtime_final.final
    def _move(self, item, target_index):
        # type: (PPL, slice | int, int) -> PPL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._move(item, target_index))

    @runtime_final.final
    def _delete(self, item):
        # type: (PPL, slice | int) -> PPL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._delete(item))

    @runtime_final.final
    def _update(self, index, *values):
        # type: (PPL, int, T) -> PPL
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._transform_wrapped(self._wrapped._update(index, *values))


PPL = TypeVar("PPL", bound=ProxyPrivateList)  # private proxy list type


class ProxyInteractiveList(ProxyPrivateList[T], BaseInteractiveList[T], InteractiveProxyCollection[T]):
    """
    Proxy interactive list.

    Features:
      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()


class ProxyMutableList(ProxyPrivateList[T], BaseMutableList[T], MutableProxyCollection[T]):
    """
    Proxy mutable list.

    Features:
      - Has public mutable transformation methods.
    """

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (BaseMutableList[T]) -> None
        """
        :param wrapped: Base mutable list.
        """
        super(ProxyMutableList, self).__init__(wrapped)

    @overload
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @runtime_final.final
    def __setitem__(self, item, value):
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        self._wrapped[item] = value

    @overload
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @runtime_final.final
    def __delitem__(self, item):
        # type: (slice | int) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        del self._wrapped[item]

    @runtime_final.final
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :return: Value.
        """
        return self._wrapped.pop(index)

    @property
    def _wrapped(self):
        # type: () -> BaseMutableList[T]
        """Wrapped base mutable list."""
        return cast(BaseMutableList[T], super(MutableProxyCollection, self)._wrapped)


def resolve_index(length, index, clamp=False):
    # type: (int, int, bool) -> int
    """
    Resolve index to a positive number.

    :param length: Length of the list.
    :param index: Input index.
    :param clamp: Whether to clamp between zero and the length.
    :return: Resolved index.
    :raises IndexError: Index out of range.
    """
    if index < 0:
        index += length
    if clamp:
        if index < 0:
            index = 0
        elif index > length:
            index = length
    elif index < 0 or index >= length:
        error = "index out of range"
        raise IndexError(error)
    return index


def resolve_continuous_slice(length, slc):
    # type: (int, slice) -> tuple[int, int]
    """
    Resolve continuous slice according to length.

    :param length: Length of the list.
    :param slc: Continuous slice.
    :return: Index and stop.
    :raises IndexError: Slice is noncontinuous.
    """
    index, stop, step = slc.indices(length)
    if step != 1 or stop < index:
        error = "slice {} is noncontinuous".format(slc)
        raise IndexError(error)
    return index, stop


def pre_move(length, item, target_index):
    # type: (int, slice | int, int) -> tuple[int, int, int, int] | None
    """
    Perform checks before moving values internally.

    :param length: Length of the list.
    :param item: Index/slice.
    :param target_index: Target index.
    :return: None or (index, stop, target index, post index).
    """

    # Resolve slice/index.
    if isinstance(item, slice):
        index, stop = resolve_continuous_slice(length, item)
        if index == stop:
            return None
    else:
        index = resolve_index(length, item)
        stop = index + 1

    # Calculate target index and post index.
    target_index = resolve_index(length, target_index, clamp=True)
    if index <= target_index <= stop:
        return None
    elif target_index > stop:
        post_index = target_index - (stop - index)
    else:
        post_index = target_index

    return index, stop, target_index, post_index

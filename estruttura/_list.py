from basicco import abstract
from basicco.custom_repr import iterable_repr
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from slotted import SlottedMutableSequence, SlottedSequence
from tippo import Any, Callable, Hashable, Iterable, MutableSequence, Self, Sequence
from tippo import TypeVar, Union, overload

from ._base import CollectionStructure, ImmutableCollectionStructure
from ._base import MutableCollectionStructure

__all__ = ["ListStructure", "ImmutableListStructure", "MutableListStructure"]


T = TypeVar("T")
_T = TypeVar("_T")


class ListStructure(CollectionStructure[T], SlottedSequence[T]):
    """List Structure."""

    __slots__ = ()

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return iterable_repr(
            self,
            prefix="{}([".format(type(self).__name__),
            suffix="])",
        )

    @abstract
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if not isinstance(other, Sequence):
            return False
        if type(self) is not type(other):
            return (
                not isinstance(self, Hashable) or not isinstance(other, Hashable)
            ) and list(self) == list(other)
        return list(self) == list(other)  # noqa

    @overload
    def __getitem__(self, item):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, item):
        # type: (slice) -> Sequence[T]
        pass

    @abstract
    def __getitem__(self, item):
        # type: (Any) -> Any
        """
        Get value/values at index/slice.

        :param item: Index/slice.
        :return: Value/values.
        :raises IndexError: Invalid index/slice.
        """
        raise NotImplementedError()

    @abstract
    def __add__(self, other):
        # type: (Iterable[T]) -> Sequence[T]
        """
        Concatenate: (self + other).

        :param other: Another iterable.
        :return: Merged sequence.
        """
        raise NotImplementedError()

    @abstract
    def __mul__(self, times):
        # type: (int) -> Sequence[T]
        """
        Repeat: (self * times).

        :param times: How many times to repeat values.
        :return: Repeated sequence.
        """
        raise NotImplementedError()

    def __rmul__(self, times):
        # type: (int) -> Sequence[T]
        """
        Repeat: (times * self).

        :param times: How many times to repeat values.
        :return: Repeated sequence.
        """
        return self * times

    @overload
    def get(self, index):
        # type: (int) -> Union[T, None]
        pass

    @overload
    def get(self, index, default):  # noqa
        # type: (int, _T) -> Union[T, _T]
        pass

    def get(self, index, default=None):
        # type: (Any, Any) -> Any
        """
        Get value at index, return default value if index is invalid.

        :param index: Index.
        :param default: Default value.
        :return: Value or default value.
        """
        try:
            return self[index]
        except IndexError:
            return default

    def count(self, value):
        # type: (T) -> int
        """
        Get number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return sum(1 for v in self if v == value)

    def index(self, value, start=None, stop=None, identity=False):
        # type: (Any, Union[int, None], Union[int, None], bool) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :param identity: Whether to compare by identity.
        :return: Index of value.
        :raises ValueError: Value is not present.
        :raises TypeError: Provided stop but did not provide start.
        """
        start = start or 0
        if start < 0:
            start += len(self)
        if start < 0:
            start = 0
        for i, v in enumerate(self[start:stop]):
            if (identity and v is value) or (not identity and v == value):
                return i + start
        raise ValueError("{!r} is not in {}".format(value, type(self).__name__))


class ImmutableListStructure(ImmutableCollectionStructure[T], ListStructure[T]):
    """Immutable List Structure."""

    __slots__ = ()

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(tuple(self))

    @abstract
    def __add__(self, other):
        # type: (Iterable[T]) -> Self
        """
        Concatenate: (self + other).

        :param other: Another iterable.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstract
    def insert(self, index, *value):
        # type: (int, *T) -> Self
        """
        Insert value(s) at index.

        :param index: Index.
        :param value: Value(s).
        :return: Transformed.
        """
        raise NotImplementedError()

    @overload
    def set(self, item, value):
        # type: (int, T) -> Self
        pass

    @overload
    def set(self, item, value):
        # type: (slice, Iterable[T]) -> Self
        pass

    @abstract
    def set(self, item, value):
        # type: (Any, Any) -> Any
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        raise NotImplementedError()

    @overload
    def delete(self, item):
        # type: (int) -> Self
        pass

    @overload
    def delete(self, item):
        # type: (slice) -> Self
        pass

    @abstract
    def delete(self, item):
        # type: (Any) -> Any
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        :raises IndexError: Invalid index/slice.
        """
        raise NotImplementedError()

    @abstract
    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> Self
        """
        Move value/values from index/slice to a target index.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        :raises IndexError: Invalid index/slice.
        """
        raise NotImplementedError()

    def extend(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Extend with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self.insert(len(self), *iterable)

    def append(self, value):
        # type: (T) -> Self
        """
        Append value.

        :param value: Value.
        :return: Transformed.
        """
        return self.insert(len(self), value)

    def reverse(self):
        # type: () -> Self
        """
        Reverse values.

        :return: Transformed.
        """
        return self.set(slice(0, len(self)), reversed(self))

    def sort(self, key=None, reverse=False):
        # type: (Union[Callable[[T], Any], None], bool) -> Self
        """
        Sort values.

        :param key: Sorting key function.
        :param reverse: Whether to reverse sorting order.
        :return: Transformed.
        """
        sorted_values = sorted(self, key=key, reverse=reverse)  # type: ignore
        return self.set(slice(0, len(self)), sorted_values)

    def remove(self, value, start=None, stop=None, identity=False):
        # type: (T, Union[int, None], Union[int, None], bool) -> Self
        """
        Remove value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :param identity: Whether to compare by identity.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self.delete(self.index(value, start=start, stop=stop, identity=identity))


class MutableListStructure(
    MutableCollectionStructure[T],
    ListStructure[T],
    SlottedMutableSequence[T],
):
    """Mutable List Structure."""

    __slots__ = ()
    __hash__ = None  # type: ignore

    @overload
    def __getitem__(self, item):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, item):
        # type: (slice) -> MutableSequence[T]
        pass

    @abstract
    def __getitem__(self, item):
        # type: (Any) -> Any
        """
        Get value/values at index/slice.

        :param item: Index/slice.
        :return: Value/values.
        :raises IndexError: Invalid index/slice.
        """
        raise NotImplementedError()

    @overload
    def __setitem__(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    def __setitem__(self, item, value):
        # type: (Any, Any) -> Any
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        self.set(item, value)

    @overload
    def __delitem__(self, item):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, item):
        # type: (slice) -> None
        pass

    def __delitem__(self, item):
        # type: (Any) -> Any
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        self.delete(item)

    def __iadd__(self, other):
        # type: (Iterable[T]) -> Self
        """
        Concatenate in place: (self += other).

        :param other: Another iterable.
        :return: Self.
        """
        self.extend(other)
        return self

    def __imul__(self, times):
        # type: (int) -> Self
        """
        Repeat in place: (self *= times).

        :param times: How many times to repeat values.
        :return: Self.
        """
        if times <= 0:
            self.clear()
        elif times > 1:
            self.extend(self * (times - 1))
        return self

    @abstract
    def insert(self, index, *value):
        # type: (int, *T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param value: Value(s).
        """
        raise NotImplementedError()

    @overload
    def set(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def set(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    @abstract
    def set(self, item, value):
        # type: (Any, Any) -> Any
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Invalid index.
        """
        raise NotImplementedError()

    @overload
    def delete(self, item):
        # type: (int) -> None
        pass

    @overload
    def delete(self, item):
        # type: (slice) -> None
        pass

    @abstract
    def delete(self, item):
        # type: (Any) -> Any
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Invalid index/slice.
        """
        raise NotImplementedError()

    @abstract
    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> None
        """
        Move value/values from index/slice to a target index.

        :param item: Index/slice.
        :param target_index: Target index.
        :raises IndexError: Invalid index/slice.
        """
        raise NotImplementedError()

    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend with iterable.

        :param iterable: Iterable.
        """
        self.insert(len(self), *iterable)

    def append(self, value):
        # type: (T) -> None
        """
        Append value.

        :param value: Value.
        """
        self.insert(len(self), value)

    def reverse(self):
        # type: () -> None
        """
        Reverse values.

        """
        self.set(slice(0, len(self)), reversed(self))

    def sort(self, key=None, reverse=False):
        # type: (Union[Callable[[T], Any], None], bool) -> None
        """
        Sort values.

        :param key: Sorting key function.
        :param reverse: Whether to reverse sorting order.
        """
        sorted_values = sorted(self, key=key, reverse=reverse)  # type: ignore
        self.set(slice(0, len(self)), sorted_values)

    def remove(self, value, start=None, stop=None, identity=False):
        # type: (T, Union[int, None], Union[int, None], bool) -> None
        """
        Remove value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :param identity: Whether to compare by identity.
        :raises ValueError: Value is not present.
        """
        self.delete(self.index(value, start=start, stop=stop, identity=identity))

    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index and return it.

        :param index: Index.
        :return: Value
        """
        value = self[index]
        self.delete(index)
        return value

import pyrsistent
from tippo import Any, Iterable, Iterator, List, Self, Sequence, Type, TypeVar, Union
from tippo import cast, overload

from .._list import ImmutableListStructure, MutableListStructure
from ..utils import pre_move, resolve_continuous_slice, resolve_index

__all__ = ["ImmutableList", "MutableList"]


T = TypeVar("T")


_PVector = type(pyrsistent.pvector())  # type: Type[pyrsistent.PVector[Any]]


class ImmutableList(ImmutableListStructure[T]):
    """Immutable list."""

    __slots__ = ("__pvector",)

    def __init__(self, initial=pyrsistent.pvector()):
        # type: (Iterable[T]) -> None
        """
        :param initial: Initial values.
        """
        if type(initial) is _PVector:
            self.__pvector = cast("pyrsistent.PVector[T]", initial)
        else:
            self.__pvector = pyrsistent.pvector(initial)

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether has value.

        :param value: Value.
        :return: True if has value.
        """
        return value in self.__pvector

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for value in self.__pvector:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self.__pvector)

    @overload
    def __getitem__(self, item):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, item):
        # type: (slice) -> Self
        pass

    def __getitem__(self, item):
        # type: (Any) -> Any
        """
        Get value/values at index/slice.

        :param item: Index/slice.
        :return: Value/values.
        :raises IndexError: Invalid index/slice.
        """
        if isinstance(item, slice):
            return type(self)(self.__pvector[item])
        else:
            return self.__pvector[item]

    def __add__(self, other):
        # type: (Iterable[T]) -> Self
        """
        Concatenate: (self + other).

        :param other: Another iterable.
        :return: Transformed.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return type(self)(self.__pvector.extend(other))

    def __mul__(self, times):
        # type: (int) -> Self
        """
        Repeat: (self * times).

        :param times: How many times to repeat values.
        :return: Repeated sequence.
        """
        return type(self)(self.__pvector * times)  # type: ignore

    def insert(self, index, *value):
        # type: (int, *T) -> Self
        """
        Insert value(s) at index.

        :param index: Index.
        :param value: Value(s).
        :return: Transformed.
        """
        pvector = self.__pvector
        length = len(self)
        index = resolve_index(length, index, clamp=True)
        if index == 0:
            return type(self)(pyrsistent.pvector(value) + pvector)
        if index == length:
            return type(self)(pvector + pyrsistent.pvector(value))
        return type(self)(pvector[:index] + pyrsistent.pvector(value) + pvector[index:])

    @overload
    def set(self, item, value):
        # type: (int, T) -> Self
        pass

    @overload
    def set(self, item, value):
        # type: (slice, Iterable[T]) -> Self
        pass

    def set(self, item, value):
        # type: (Any, Any) -> Any
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        pvector = self.__pvector
        if not isinstance(item, slice):
            return type(self)(pvector.set(item, value))
        length = len(self)
        start, stop = resolve_continuous_slice(length, item)
        return type(self)(pvector[:start] + pyrsistent.pvector(value) + pvector[stop:])

    @overload
    def delete(self, item):
        # type: (int) -> Self
        pass

    @overload
    def delete(self, item):
        # type: (slice) -> Self
        pass

    def delete(self, item):
        # type: (Any) -> Any
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        :raises IndexError: Invalid index/slice.
        """
        pvector = self.__pvector
        if not isinstance(item, slice):
            return type(self)(pvector.delete(item))
        length = len(self)
        start, stop = resolve_continuous_slice(length, item)
        return type(self)(pvector[:start] + pvector[stop:])

    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> Self
        """
        Move value/values from index/slice to a target index.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        :raises IndexError: Invalid index/slice.
        """
        length = len(self)
        pre_move_data = pre_move(length, item, target_index)
        if pre_move_data is None:
            return self
        target_index, index, stop, post_index, post_stop = pre_move_data
        pvector = self.__pvector
        values = pvector[index:stop]
        pvector = pvector[:index] + pvector[stop:]
        pvector = pvector[:post_index] + values + pvector[post_index:]
        return type(self)(pvector)

    def clear(self):
        # type: () -> Self
        """
        Clear contents.

        :return: Transformed.
        """
        return type(self)()


class MutableList(MutableListStructure[T]):
    """Mutable List."""

    __slots__ = ("__list",)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        """
        :param initial: Initial values.
        """
        self.__list = list(initial)  # type: List[T]

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether has value.

        :param value: Value.
        :return: True if has value.
        """
        return value in self.__list

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for value in self.__list:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self.__list)

    @overload
    def __getitem__(self, item):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, item):
        # type: (slice) -> Self
        pass

    def __getitem__(self, item):
        # type: (Any) -> Any
        """
        Get value/values at index/slice.

        :param item: Index/slice.
        :return: Value/values.
        :raises IndexError: Invalid index/slice.
        """
        if isinstance(item, slice):
            return type(self)(self.__list[item])
        else:
            return self.__list[item]

    def __add__(self, other):
        # type: (Iterable[T]) -> Sequence[T]
        """
        Concatenate: (self + other).

        :param other: Another iterable.
        :return: Merged sequence.
        """
        return type(self)(self.__list + list(other))

    def __mul__(self, times):
        # type: (int) -> Sequence[T]
        """
        Repeat: (self * times).

        :param times: How many times to repeat values.
        :return: Repeated sequence.
        """
        return type(self)(self.__list * times)

    @overload
    def set(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def set(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    def set(self, item, value):
        # type: (Any, Any) -> None
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Invalid index.
        """
        self.__list[item] = value

    @overload
    def delete(self, item):
        # type: (int) -> None
        pass

    @overload
    def delete(self, item):
        # type: (slice) -> None
        pass

    def delete(self, item):
        # type: (Any) -> Any
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Invalid index/slice.
        """
        del self.__list[item]

    def clear(self):
        # type: () -> None
        """Clear contents."""
        del self.__list[:]

    def insert(self, index, *value):
        # type: (int, *T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param value: Value(s).
        """
        self.__list[index:index] = value

    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> None
        """
        Move value/values from index/slice to a target index.

        :param item: Index/slice.
        :param target_index: Target index.
        :raises IndexError: Invalid index/slice.
        """
        length = len(self)
        pre_move_data = pre_move(length, item, target_index)
        if pre_move_data is None:
            return
        target_index, index, stop, post_index, post_stop = pre_move_data
        values = self.__list[index:stop]
        del self.__list[index:stop]
        self.__list[post_index:post_index] = values

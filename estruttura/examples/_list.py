import pyrsistent
from tippo import Any, Iterable, List, Self, Type, TypeVar, Union, overload

from .._list import ImmutableListStructure, MutableListStructure
from ..utils import pre_move, resolve_continuous_slice, resolve_index

__all__ = ["ImmutableList", "MutableList"]


T = TypeVar("T")


_PVector = type(pyrsistent.pvector())  # type: Type[pyrsistent.PVector[Any]]


class ImmutableList(ImmutableListStructure[T]):
    __slots__ = ("__pvector",)

    def __init__(self, initial=pyrsistent.pvector()):
        # type: (Iterable[T]) -> None
        if type(initial) is _PVector:
            self.__pvector = initial
        else:
            self.__pvector = pyrsistent.pvector(initial)

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
        if isinstance(item, slice):
            return type(self)(self.__pvector[item])
        else:
            return self.__pvector[item]

    def __len__(self):
        # type: () -> int
        return len(self.__pvector)

    def __add__(self, other):
        # type: (Iterable[T]) -> Self
        if not isinstance(other, Iterable):
            return NotImplemented
        return type(self)(self.__pvector.extend(other))

    def __mul__(self, times):
        # type: (int) -> Self
        return type(self)(self.__pvector * times)  # type: ignore

    def insert(self, index, *value):
        # type: (int, *T) -> Self
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
        # type: (slice, Iterable[T]) -> Self
        raise NotImplementedError()

    @overload
    def set(self, item, value):
        # type: (int, T) -> Self
        raise NotImplementedError()

    def set(self, item, value):
        # type: (Any, Any) -> Any
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
        pvector = self.__pvector
        if not isinstance(item, slice):
            return type(self)(pvector.delete(item))
        length = len(self)
        start, stop = resolve_continuous_slice(length, item)
        return type(self)(pvector[:start] + pvector[stop:])

    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> Self
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
        return type(self)()


class MutableList(MutableListStructure[T]):
    __slots__ = ("__list",)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        self.__list = list(initial)  # type: List[T]

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
        if isinstance(item, slice):
            return type(self)(self.__list[item])
        else:
            return self.__list[item]

    @overload
    def __setitem__(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    def __setitem__(self, item, value):
        # type: (Any, Any) -> None
        self.__list[item] = value

    def __delitem__(self, item):
        # type: (Union[slice, int]) -> None
        del self.__list[item]

    def __len__(self):
        # type: () -> int
        return len(self.__list)

    def __add__(self, other):
        # type: (Iterable[T]) -> Self
        if not isinstance(other, Iterable):
            return NotImplemented
        return type(self)(self.__list + list(other))

    def __mul__(self, times):
        # type: (int) -> Self
        return type(self)(self.__list * times)

    def clear(self):
        # type: () -> None
        del self.__list[:]

    def insert(self, index, *value):
        # type: (int, *T) -> None
        self.__list[index:index] = value

    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> None
        length = len(self)
        pre_move_data = pre_move(length, item, target_index)
        if pre_move_data is None:
            return
        target_index, index, stop, post_index, post_stop = pre_move_data
        values = self.__list[index:stop]
        del self.__list[index:stop]
        self.__list[post_index:post_index] = values

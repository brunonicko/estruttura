from basicco import abstract
from basicco.custom_repr import iterable_repr
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from slotted import SlottedMutableSequence, SlottedSequence
from tippo import Any, Callable, Hashable, Iterable, Self, Sequence, TypeVar, Union
from tippo import overload

from ._base import CollectionStructure, ImmutableCollectionStructure
from ._base import MutableCollectionStructure

__all__ = ["ListStructure", "ImmutableListStructure", "MutableListStructure"]


T = TypeVar("T")


class ListStructure(CollectionStructure[T], SlottedSequence[T]):
    __slots__ = ()

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        return iterable_repr(
            self,
            prefix="{}([".format(type(self).__name__),
            suffix="])",
        )

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()

    def __eq__(self, other):
        # type: (object) -> bool
        if not isinstance(other, Sequence):
            return False
        if type(self) is not type(other):
            return not isinstance(other, Hashable) and list(self) == list(other)  # noqa
        return list(self) == list(other)  # noqa

    @abstract
    def __add__(self, other):
        # type: (Iterable[T]) -> Self
        raise NotImplementedError()

    @abstract
    def __mul__(self, times):
        # type: (int) -> Self
        raise NotImplementedError()

    def __rmul__(self, times):
        # type: (int) -> Self
        return self * times


class ImmutableListStructure(ImmutableCollectionStructure[T], ListStructure[T]):
    __slots__ = ()

    def __hash__(self):
        # type: () -> int
        return hash(tuple(self))

    @abstract
    def insert(self, index, *value):
        # type: (int, *T) -> Self
        raise NotImplementedError()

    @overload
    def set(self, item, value):
        # type: (slice, Iterable[T]) -> Self
        raise NotImplementedError()

    @overload
    def set(self, item, value):
        # type: (int, T) -> Self
        raise NotImplementedError()

    @abstract
    def set(self, item, value):
        # type: (Any, Any) -> Any
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
        raise NotImplementedError()

    @abstract
    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> Self
        raise NotImplementedError()

    def extend(self, values):
        # type: (Iterable[T]) -> Self
        return self.insert(len(self), *values)

    def append(self, value):
        # type: (T) -> Self
        return self.insert(len(self), value)

    def reverse(self):
        # type: () -> Self
        return self.set(slice(0, len(self)), reversed(self))

    def sort(self, key=None, reverse=False):
        # type: (Union[Callable[[T], Any], None], bool) -> Self
        sorted_values = sorted(self, key=key, reverse=reverse)  # type: ignore
        return self.set(slice(0, len(self)), sorted_values)

    def remove(self, value):
        # type: (T) -> Self
        return self.delete(self.index(value))


class MutableListStructure(
    MutableCollectionStructure[T],
    ListStructure[T],
    SlottedMutableSequence[T],
):
    __slots__ = ()

    __hash__ = None  # type: ignore

    def __imul__(self, times):
        # type: (int) -> Self
        if times <= 0:
            self.clear()
        elif times > 1:
            self.extend(self * (times - 1))
        return self

    @abstract
    def insert(self, index, *value):
        # type: (int, *T) -> None
        raise NotImplementedError()

    @abstract
    def move(self, item, target_index):
        # type: (Union[int, slice], int) -> None
        raise NotImplementedError()

    def extend(self, values):
        # type: (Iterable[T]) -> None
        self.insert(len(self), *values)

    def sort(self, key=None, reverse=False):
        # type: (Union[Callable[[T], Any], None], bool) -> None
        sorted_values = sorted(self, key=key, reverse=reverse)  # type: ignore
        self[:] = sorted_values

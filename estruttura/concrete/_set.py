import pyrsistent
from tippo import Any, Iterable, Iterator, Self, Set, Type, TypeVar, cast

from .._set import ImmutableSetStructure, MutableSetStructure

__all__ = ["ImmutableSet", "MutableSet"]


T = TypeVar("T")


_PSet = type(pyrsistent.pset())  # type: Type[pyrsistent.PSet[Any]]


class ImmutableSet(ImmutableSetStructure[T]):
    """Immutable set."""

    __slots__ = ("__pset",)

    def __init__(self, initial=pyrsistent.pset()):
        # type: (Iterable[T]) -> None
        """
        :param initial: Initial values.
        """
        if type(initial) is _PSet:
            self.__pset = cast("pyrsistent.PSet[T]", initial)
        else:
            self.__pset = pyrsistent.pset(initial)

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether has value.

        :param value: Value.
        :return: True if has value.
        """
        return value in self.__pset

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for value in self.__pset:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self.__pset)

    def intersection(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return type(self)(self.__pset.intersection(iterable))

    def symmetric_difference(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return type(self)(self.__pset.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return type(self)(self.__pset.union(iterable))

    def difference(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return type(self)(self.__pset.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return type(self)(pyrsistent.pset(iterable).difference(self.__pset))

    def update(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return type(self)(self.__pset.update(iterable))

    def discard(self, *value):
        # type: (*T) -> Self
        """
        Discard value(s).

        :param value: Value(s).
        :return: Transformed.
        """
        return type(self)(self.__pset.difference(value))

    def clear(self):
        # type: () -> Self
        """
        Clear contents.

        :return: Transformed.
        """
        return type(self)()


class MutableSet(MutableSetStructure[T]):
    """Mutable Set."""

    __slots__ = ("__set",)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        """
        :param initial: Initial values.
        """
        self.__set = set(initial)  # type: Set[T]

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether has value.

        :param value: Value.
        :return: True if has value.
        """
        return value in self.__set

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for value in self.__set:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self.__set)

    def intersection(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return type(self)(self.__set.intersection(iterable))

    def symmetric_difference(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return type(self)(self.__set.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return type(self)(self.__set.union(iterable))

    def difference(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return type(self)(self.__set.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable[T]) -> Self
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return type(self)(set(iterable).difference(self.__set))

    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        self.__set.update(iterable)

    def discard(self, *value):
        # type: (*T) -> None
        """
        Discard value(s).

        :param value: Value(s).
        """
        self.__set.difference_update(value)

    def clear(self):
        # type: () -> None
        """Clear contents."""
        self.__set.clear()

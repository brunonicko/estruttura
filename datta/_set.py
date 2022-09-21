import pyrsistent
from basicco import recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Iterator
from pyrsistent.typing import PSet

from estruttura import BasePrivateSet, BaseInteractiveSet

from ._bases import BasePrivateDataCollection, BaseDataCollection


T = TypeVar("T")  # value type


class PrivateDataSet(BasePrivateDataCollection[PSet[T], T], BasePrivateSet[T]):
    """Private set data."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Iterable[T]) -> PSet[T]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pset(initial)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        super(PrivateDataSet, self).__init__(initial)

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
        for key in self._internal:
            yield key

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
            prefix="{}([".format(type(self).__name__),
            suffix="])",
            sorting=True,
            sort_key=lambda v: hash(v),
        )

    def _clear(self):
        # type: (PSD) -> PSD
        """
        Clear.

        :return: Transformed.
        """
        return self._make(pyrsistent.pset())

    def _add(self, value):
        # type: (PSD, T) -> PSD
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.add(value))

    def _discard(self, *values):
        # type: (PSD, T) -> PSD
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        return self._make(self._internal.discard(*values))

    def _remove(self, *values):
        # type: (PSD, T) -> PSD
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        return self._make(self._internal.difference(values))

    def _replace(self, old_value, new_value):
        # type: (PSD, T, T) -> PSD
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        return self._make(self._internal.remove(old_value).add(new_value))

    def _update(self, iterable):
        # type: (PSD, Iterable[T]) -> PSD
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._make(self._internal.update(iterable))

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._internal.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> PrivateDataSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return type(self)._make(self._internal.intersection(iterable))

    def difference(self, iterable):
        # type: (Iterable) -> PrivateDataSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return type(self)._make(self._internal.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable) -> PrivateDataSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return type(self)._make(pyrsistent.pset(iterable).difference(self._internal))

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> PrivateDataSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return type(self)._make(self._internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable) -> PrivateDataSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return type(self)._make(self._internal.union(iterable))


PSD = TypeVar("PSD", bound=PrivateDataSet)


class DataSet(PrivateDataSet[T], BaseDataCollection[PSet[T], T], BaseInteractiveSet[T]):
    """Set data."""

    __slots__ = ()

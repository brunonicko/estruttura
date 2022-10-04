import pyrsistent
from basicco import recursive_repr, custom_repr, safe_repr
from tippo import Any, TypeVar, Iterable, Iterator
from pyrsistent.typing import PSet

from estruttura import SetStructure, PrivateSetStructure, InteractiveSetStructure, relationship

from ._data import UniformData, PrivateUniformData, InteractiveUniformData


T = TypeVar("T")  # value type


class ProtectedDataSet(UniformData[PSet[T], T], SetStructure[T]):
    """Protected data set."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Iterable[T]) -> PSet[T]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pset(initial or ())

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None

        rel = relationship(self)
        if rel is not None:
            initial = tuple(rel.process(v) for v in initial)

        super(ProtectedDataSet, self).__init__(initial)

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

    @safe_repr.safe_repr
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
        # type: (Iterable) -> DataSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return DataSet(self._internal.intersection(iterable))

    def difference(self, iterable):
        # type: (Iterable) -> DataSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return DataSet(self._internal.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable) -> DataSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return DataSet(pyrsistent.pset(iterable).difference(self._internal))

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> DataSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return DataSet(self._internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable) -> DataSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return DataSet(self._internal.union(iterable))


class PrivateDataSet(ProtectedDataSet[T], PrivateUniformData[PSet[T], T], PrivateSetStructure[T]):
    """Private data set."""

    __slots__ = ()

    def _discard(self, *values):
        # type: (PDS, T) -> PDS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        return self._make(self._internal.difference(values))

    def _replace(self, old_value, new_value):
        # type: (PDS, T, T) -> PDS
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        rel = relationship(self)
        if rel is not None:
            new_value = rel.process(new_value)
        return self._make(self._internal.remove(old_value).add(new_value))

    def _update(self, iterable):
        # type: (PDS, Iterable[T]) -> PDS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        rel = relationship(self)
        if rel is not None:
            iterable = tuple(rel.process(v) for v in iterable)
        return self._make(self._internal.update(iterable))


PDS = TypeVar("PDS", bound=PrivateDataSet)


class DataSet(PrivateDataSet[T], InteractiveUniformData[PSet[T], T], InteractiveSetStructure[T]):
    """Data set."""

    __slots__ = ()

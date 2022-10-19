from tippo import AbstractSet, TypeVar, Iterable, Union

from ..base import BaseSet, BaseImmutableSet, BaseMutableSet
from ._base import CollectionStructure, ImmutableCollectionStructure, MutableCollectionStructure


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

SST = TypeVar("SST", bound=Union[BaseImmutableSet, BaseMutableSet])  # set state type


class SetStructure(CollectionStructure[SST, T], BaseSet[T]):
    __slots__ = ()

    def _discard(self, *values):
        # type: (SS, T) -> SS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._transform(self._state.discard(*values))

    def _update(self, iterable):
        # type: (SS, Iterable[T]) -> SS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        relationship = type(self).relationship
        if relationship is not None and relationship.will_process:
            iterable = tuple(relationship.process(v) for v in iterable)
        return self._transform(self._state.update(iterable))

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._state.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._state.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._state.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return self._state.intersection(iterable)

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return self._state.symmetric_difference(iterable)

    def union(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return self._state.union(iterable)

    def difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return self._state.difference(iterable)

    def inverse_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return self._state.inverse_difference(iterable)


SS = TypeVar("SS", bound=SetStructure)  # set structure self type


ISST = TypeVar("ISST", bound=BaseImmutableSet)  # immutable set state type


class ImmutableSetStructure(
    SetStructure[ISST, T_co],
    ImmutableCollectionStructure[ISST, T_co],
    BaseImmutableSet[T_co],
):
    __slots__ = ()


class MutableSetStructure(
    SetStructure[SST, T],
    MutableCollectionStructure[SST, T],
    BaseMutableSet[T],
):
    __slots__ = ()

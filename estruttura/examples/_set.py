"""Example set structures implementation."""

import copy

from tippo import TypeVar

import estruttura

T = TypeVar("T")


# noinspection PyAbstractClass
class BaseSet(estruttura.UserSetStructure[T]):
    """Base set."""

    __slots__ = ("_internal",)

    def __contains__(self, item):
        return item in self._internal

    def __len__(self):
        return len(self._internal)

    def __iter__(self):
        return iter(self._internal)

    def _eq(self, other):
        if isinstance(other, set):
            return self._internal == other
        else:
            return isinstance(other, type(self)) and self._internal == other._internal

    def _do_init(self, initial_values):
        self._internal = set(initial_values)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._internal = set(values)
        return self

    def isdisjoint(self, iterable):
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._internal.issuperset(iterable)

    def symmetric_difference(self, iterable):
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        new_internal = self._internal.symmetric_difference(iterable)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def union(self, iterable):
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        new_internal = self._internal.union(iterable)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def difference(self, iterable):
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        new_internal = self._internal.difference(iterable)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def inverse_difference(self, iterable):
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        new_internal = set(iterable).difference(self._internal)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def intersection(self, iterable):
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        new_internal = self._internal.intersection(iterable)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self


class ImmutableSet(BaseSet[T], estruttura.UserImmutableSetStructure[T]):
    """Immutable set."""

    def _hash(self):
        return hash(tuple(self._internal))

    def _do_clear(self):
        return type(self)()

    def _do_remove(self, old_values):
        new_internal = self._internal.difference(old_values)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def _do_update(self, new_values):
        new_internal = self._internal.union(new_values)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self


class MutableSet(BaseSet[T], estruttura.UserMutableSetStructure[T]):
    """Mutable set."""

    def _do_clear(self):
        self._internal.clear()
        return self

    def _do_remove(self, old_values):
        for value in old_values:
            self._internal.remove(value)

    def _do_update(self, new_values):
        self._internal.update(new_values)

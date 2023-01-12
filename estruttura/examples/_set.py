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

    def _do_init(self, initial_values):
        self._internal = set(initial_values)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._internal = set(values)
        return self

    def isdisjoint(self, iterable):
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        return self._internal.issuperset(iterable)

    def symmetric_difference(self, iterable):
        return self._internal.symmetric_difference(iterable)

    def union(self, iterable):
        return self._internal.union(iterable)

    def difference(self, iterable):
        return self._internal.difference(iterable)

    def inverse_difference(self, iterable):
        return set(iterable).difference(self._internal)

    def intersection(self, iterable):
        return self._internal.intersection(iterable)


class ImmutableSet(BaseSet[T], estruttura.UserImmutableSetStructure[T]):
    """Immutable set."""

    __slots__ = ("__hash",)

    def __cache_hash__(self, hash_):
        self.__hash = hash_

    def __retrieve_hash__(self):
        try:
            return self.__hash
        except AttributeError:
            return None

    def _do_copy(self):
        return copy.copy(self)

    def _do_clear(self):
        self._internal = set()

    def _do_remove(self, old_values):
        new_internal = self._internal.difference(old_values)
        self._internal = new_internal

    def _do_update(self, new_values):
        new_internal = self._internal.union(new_values)
        self._internal = new_internal


class MutableSet(BaseSet[T], estruttura.UserMutableSetStructure[T]):
    """Mutable set."""

    def _do_clear(self):
        self._internal.clear()

    def _do_remove(self, old_values):
        for value in old_values:
            self._internal.remove(value)

    def _do_update(self, new_values):
        self._internal.update(new_values)

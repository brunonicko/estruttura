"""Example list structures implementation."""

import copy

from tippo import TypeVar

import estruttura

T = TypeVar("T")


# noinspection PyAbstractClass
class BaseList(estruttura.UserListStructure[T]):
    """Base list."""

    __slots__ = ("_internal",)

    def __getitem__(self, item):
        return self._internal[item]

    def __len__(self):
        return len(self._internal)

    def _do_init(self, initial_values):
        self._internal = list(initial_values)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._internal = list(values)
        return self

    def count(self, value):
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return self._internal.count(value)

    def index(self, value, start=None, stop=None):
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._internal.index(value, start, stop)


class ImmutableList(BaseList[T], estruttura.UserImmutableListStructure[T]):
    """Immutable list."""

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
        self._internal = []

    def _do_insert(self, index, new_values):
        new_internal = list(self._internal)
        new_internal[index:index] = new_values
        self._internal = new_internal

    def _do_move(self, target_index, index, stop, post_index, post_stop, values):
        new_internal = list(self._internal)
        del new_internal[index:stop]
        new_internal[post_index:post_index] = values
        self._internal = new_internal

    def _do_delete(self, index, stop, old_values):
        new_internal = list(self._internal)
        del new_internal[index:stop]
        self._internal = new_internal

    def _do_update(self, index, stop, old_values, new_values):
        new_internal = list(self._internal)
        new_internal[index:stop] = new_values
        self._internal = new_internal


class MutableList(BaseList[T], estruttura.UserMutableListStructure[T]):
    """Mutable list."""

    def _do_clear(self):
        self._internal.clear()

    def _do_insert(self, index, new_values):
        self._internal[index:index] = new_values

    def _do_move(self, target_index, index, stop, post_index, post_stop, values):
        del self._internal[index:stop]
        self._internal[post_index:post_index] = values

    def _do_delete(self, index, stop, old_values):
        del self._internal[index:stop]

    def _do_update(self, index, stop, old_values, new_values):
        self._internal[index:stop] = new_values

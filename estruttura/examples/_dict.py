"""Example dictionary structures implementation."""

import copy

from tippo import TypeVar

import estruttura

KT = TypeVar("KT")
VT = TypeVar("VT")


# noinspection PyAbstractClass
class BaseDict(estruttura.UserDictStructure[KT, VT]):
    """Base dictionary."""

    __slots__ = ("_internal",)

    def __iter__(self):
        return iter(self._internal)

    def __len__(self):
        return len(self._internal)

    def __getitem__(self, key):
        return self._internal[key]

    def _do_init(self, initial_values):
        self._internal = dict(initial_values)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._internal = dict(values)
        return self


class ImmutableDict(BaseDict[KT, VT], estruttura.UserImmutableDictStructure[KT, VT]):
    """Immutable dictionary."""

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

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        new_internal = dict(
            (k, v) for k, v in self._internal.items() if k not in deletes and k not in updates_and_inserts
        )
        new_internal.update(updates_and_inserts)
        self._internal = new_internal

    def _do_clear(self):
        self._internal = {}


class MutableDict(BaseDict[KT, VT], estruttura.UserMutableDictStructure[KT, VT]):
    """Mutable dictionary."""

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        for key in deletes:
            del self._internal[key]
        self._internal.update(updates_and_inserts)

    def _do_clear(self):
        self._internal.clear()

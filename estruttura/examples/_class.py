"""Example attribute class structures implementation."""

import copy

import estruttura


# noinspection PyAbstractClass
class BaseClass(estruttura.UserStructure):
    """Base attribute class."""

    __slots__ = ("_internal",)

    def _contains(self, name):
        return name in self._internal

    def _get(self, name):
        try:
            return self._internal[name]
        except KeyError:
            pass
        raise AttributeError(name)

    def _do_init(self, initial_values):
        self._internal = dict(initial_values)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._internal = dict(values)
        return self


class ImmutableClass(estruttura.UserImmutableStructure, BaseClass):
    """Immutable attribute class."""

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


class MutableClass(estruttura.UserMutableStructure, BaseClass):
    """Mutable attribute class."""

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        for key in deletes:
            del self._internal[key]
        self._internal.update(updates_and_inserts)

    def _do_clear(self):
        self._internal.clear()

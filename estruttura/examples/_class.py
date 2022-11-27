"""Example attribute class structures implementation."""

import copy

import estruttura


# noinspection PyAbstractClass
class BaseClass(estruttura.UserStructure):
    """Base attribute class."""

    __slots__ = ("_internal",)

    def __contains__(self, name):
        return name in self._internal

    def __getitem__(self, key):
        return self._internal[key]

    def _do_init(self, initial_values):
        self._internal = dict(initial_values)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._internal = dict(values)
        return self


class ImmutableClass(BaseClass, estruttura.UserImmutableStructure):
    """Immutable attribute class."""

    def _hash(self):
        return hash(tuple(sorted(self._internal.items(), key=lambda i: id(i[0]))))

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        new_internal = dict((k, v) for k, v in self._internal.items() if k not in deletes)
        new_internal.update(updates_and_inserts)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def _do_clear(self):
        return type(self)()


class MutableClass(BaseClass, estruttura.UserMutableStructure):
    """Mutable attribute class."""

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        for key in deletes:
            del self._internal[key]
        self._internal.update(updates_and_inserts)
        return self

    def _do_clear(self):
        self._internal.clear()
        return self

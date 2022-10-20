import copy

import pyrsistent
from basicco.obj_state import get_state, update_state
from estruttura._dict import ImmutableDictStructure
from tippo import cast


class DataDict(ImmutableDictStructure):
    __slots__ = ("__internal",)

    def __copy__(self):
        cls = type(self)
        new_self = cls.__new__(cls)
        update_state(new_self, get_state(self))
        return new_self

    def __getitem__(self, key):
        return self.__internal[key]

    def _do_init(self, initial_values):
        self.__internal = pyrsistent.pmap(initial_values)

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts):
        internal = self.__internal
        if deletes:
            evolver = internal.evolver()
            for key in deletes:
                del evolver[key]
            internal = evolver.persistent()
        if updates_and_inserts:
            internal = internal.update(updates_and_inserts)

        new_self = copy.copy(self)
        new_self.__internal = internal
        return new_self

    def get(self, key, fallback=None):
        return self.__internal.get(key, fallback)

    def _do_clear(self):
        new_self = copy.copy(self)
        new_self.__internal = pyrsistent.pmap()
        return new_self

    def __hash__(self):
        return hash(self.__internal)

    def __eq__(self, other):
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        return self.__internal == cast(DataDict, other).__internal

    def __len__(self):
        return len(self.__internal)

    def __iter__(self):
        for key in self.__internal:
            yield key

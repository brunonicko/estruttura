import copy

from basicco import explicit_hash
from basicco.abstract_class import abstract
from tippo import TypeVar

import estruttura


T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


# noinspection PyAbstractClass
class Dict(estruttura.DictStructure[KT, VT]):
    __slots__ = ("_internal",)

    @abstract
    def __hash__(self):
        raise NotImplementedError()

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._internal == other
        else:
            return isinstance(other, type(self)) and self._internal == other._internal

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
        self = cls()
        self._internal = dict(values)
        return self


class ImmutableDict(Dict[KT, VT], estruttura.ImmutableDictStructure[KT, VT]):
    def __hash__(self):
        return hash(tuple(sorted(self._internal.items(), key=lambda i: id(i[0]))))

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts):
        new_internal = dict((k, v) for k, v in self._internal.items() if k not in deletes)
        new_internal.update(updates_and_inserts)
        new_self = copy.copy(self)
        new_self._internal = new_internal
        return new_self

    def _do_clear(self):
        return type(self)()


class MutableDict(Dict[KT, VT], estruttura.MutableDictStructure[KT, VT]):
    @explicit_hash.set_to_none
    def __hash__(self):
        raise TypeError()

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts):
        for key in deletes:
            del self._internal[key]
        self._internal.update(updates_and_inserts)
        return self

    def _do_clear(self):
        self._internal.clear()
        return self

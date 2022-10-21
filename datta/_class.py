import copy

import six
from basicco.mangling import unmangle
from estruttura import StructureAttribute, ImmutableClassStructureMeta, ImmutableClassStructure


class DataAttribute(StructureAttribute):
    __slots__ = ()


class DataClassMeta(ImmutableClassStructureMeta):
    __attribute_type__ = DataAttribute

    # noinspection PyUnusedLocal
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):

        # Convert attributes to slots.
        slots = list(dct.get("__slots__", ()))
        dct_copy = dict(dct)
        for attribute_name, attribute in six.iteritems(this_attribute_map):
            del dct_copy[attribute_name]
            slot_name = unmangle(attribute_name, name)
            slots.append(slot_name)
        dct_copy["__slots__"] = tuple(slots)

        return dct_copy


class DataClass(six.with_metaclass(DataClassMeta, ImmutableClassStructure)):
    __slots__ = ()

    def __getitem__(self, name):
        return getattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def _do_init(self, initial_values):
        for name, value in six.iteritems(initial_values):
            object.__setattr__(self, name, value)

    def _do_update(
        self,
        inserts,
        deletes,
        updates_old,
        updates_new,
        updates_and_inserts,
    ):
        self_copy = copy.copy(self)
        for name, value in six.iteritems(updates_and_inserts):
            object.__setattr__(self_copy, name, value)
        for name in deletes:
            object.__delattr__(self_copy, name)

        return self_copy

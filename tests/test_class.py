import copy

import pytest

from estruttura import ImmutableClassStructure, StructureAttribute, Relationship


class ImmutableClass(ImmutableClassStructure):
    __slots__ = ("__internal",)

    def __getitem__(self, name):
        return self.__internal[name]

    def __contains__(self, name):
        return name in self.__internal

    def _do_init(self, initial_values):
        self.__internal = initial_values

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts):
        new_internal = dict(self.__internal)
        new_internal.update(updates_and_inserts)
        for d in deletes:
            del new_internal[d]
        new_self = copy.copy(self)
        self.__internal = new_internal
        return new_self

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self.__internal = values
        return self


class Employee(ImmutableClass):
    name = StructureAttribute(relationship=Relationship(types=str))
    boss = StructureAttribute(
        default=None,
        relationship=Relationship(types=("Employee", None), extra_paths=(__name__,)),
        serialize_to="manager",
        deserialize_from="manager",
    )  # type: StructureAttribute[Employee] | None


def test_class():
    john = Employee("John")
    mark = Employee("Mark", boss=john)

    serialized_mark = mark.serialize()
    assert serialized_mark == {'manager': {'manager': None, 'name': 'John'}, 'name': 'Mark'}

    deserialized_mark = Employee.deserialize(serialized_mark)
    assert deserialized_mark == mark


if __name__ == "__main__":
    pytest.main()

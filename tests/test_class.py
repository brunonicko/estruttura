import copy

import pytest

from estruttura import ImmutableClassStructure, Relationship, StructureAttribute


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
        new_self.__internal = new_internal
        return new_self

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self.__internal = values
        return self


class Employee(ImmutableClass):
    company = StructureAttribute(
        "foobar", constant=True, relationship=Relationship(converter=str.upper)
    )  # type: StructureAttribute[str]
    name = StructureAttribute(relationship=Relationship(types=str))
    boss = StructureAttribute(
        default=None,
        relationship=Relationship(types=("Employee", None), extra_paths=(__name__,)),
        serialize_as="manager",
        serialize_default=False,
    )  # type: StructureAttribute[Employee] | None
    salary = StructureAttribute(100, serializable=False)  # type: StructureAttribute[int]


def test_class():
    john = Employee("John")
    mark = Employee("Mark", boss=john)

    assert Employee.company == "FOOBAR"
    assert john.company == "FOOBAR"
    assert mark.company == "FOOBAR"

    serialized_mark = mark.serialize()
    assert serialized_mark == {"name": "Mark", "manager": {"name": "John"}}

    deserialized_mark = Employee.deserialize(serialized_mark)
    assert deserialized_mark == mark


if __name__ == "__main__":
    pytest.main()

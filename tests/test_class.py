import copy
import enum

import pytest

from estruttura import ImmutableClassStructure, Relationship, StructureAttribute
from estruttura.serializers import EnumSerializer


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


class LightSwitch(enum.Enum):
    OFF = 0
    ON = 1


class Position(enum.Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Employee(ImmutableClass):
    light = StructureAttribute(relationship=Relationship(types=LightSwitch, serializer=EnumSerializer()))
    position = StructureAttribute(relationship=Relationship(types=Position, serializer=EnumSerializer(by_name=True)))
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
    john = Employee(LightSwitch.OFF, Position.RIGHT, "John")
    mark = Employee(LightSwitch.ON, Position.LEFT, "Mark", boss=john)

    assert Employee.company == "FOOBAR"
    assert john.company == "FOOBAR"
    assert mark.company == "FOOBAR"

    serialized_mark = mark.serialize()
    assert serialized_mark == {
        "light": 1,
        "position": "LEFT",
        "name": "Mark",
        "manager": {"light": 0, "position": "RIGHT", "name": "John"},
    }

    deserialized_mark = Employee.deserialize(serialized_mark)
    assert deserialized_mark == mark


if __name__ == "__main__":
    pytest.main()

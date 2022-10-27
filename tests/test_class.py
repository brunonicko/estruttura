import enum

import pytest

from estruttura import Attribute, Relationship
from estruttura.examples import ImmutableClass
from estruttura.serializers import EnumSerializer


class LightSwitch(enum.Enum):
    OFF = 0
    ON = 1


class Position(enum.Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Employee(ImmutableClass):
    light = Attribute(
        relationship=Relationship(types=LightSwitch, serializer=EnumSerializer())
    )  # type: Attribute[LightSwitch]

    position = Attribute(
        relationship=Relationship(types=Position, serializer=EnumSerializer(by_name=True))
    )  # type: Attribute[Position]

    company = Attribute("foobar", constant=True, relationship=Relationship(converter=str.upper))  # type: Attribute[str]

    name = Attribute(relationship=Relationship(types=str))  # type: Attribute[str]

    boss = Attribute(
        default=None,
        relationship=Relationship(
            types=("Employee", None),
            extra_paths=(__name__,),
        ),
        serialize_as="manager",
        serialize_default=False,
    )  # type: Attribute[Employee | None]

    salary = Attribute(100, serializable=False)  # type: Attribute[int]


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

import enum

import pytest

from estruttura.examples import ImmutableClass, attribute
from estruttura.serializers import EnumSerializer


class LightSwitch(enum.Enum):
    OFF = 0
    ON = 1


class Position(enum.Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Employee(ImmutableClass):
    light = attribute(types=LightSwitch, serializer=EnumSerializer())  # type: LightSwitch
    position = attribute(types=Position, serializer=EnumSerializer(by_name=True))  # type: Position
    company = attribute("foobar", constant=True, converter=str.upper)  # type: str
    name = attribute(types=str)  # type: str
    boss = attribute(
        default=None,
        types=("Employee", None),
        extra_paths=(__name__,),
        serialize_as="manager",
        serialize_default=False,
    )  # type: Employee | None
    salary = attribute(100, serializable=False)  # type: int


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

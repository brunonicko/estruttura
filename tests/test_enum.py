import copy
import enum

import pytest

from estruttura import ImmutableDictStructure, ImmutableListStructure, Relationship


class LightSwitch(enum.Enum):
    OFF = 0
    ON = 1


class Position(enum.Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


def test_enum():
    pass


if __name__ == "__main__":
    pytest.main()

# type: ignore

import pytest
from slotted import SlottedMutableSet, SlottedSet

from estruttura import CollectionStructure, ImmutableCollectionStructure
from estruttura import ImmutableSetStructure, MutableCollectionStructure
from estruttura import MutableSetStructure, SetStructure
from estruttura.concrete import ImmutableSet, MutableSet


def test_inheritance():
    assert issubclass(SetStructure, CollectionStructure)
    assert issubclass(SetStructure, SlottedSet)
    assert issubclass(ImmutableSetStructure, SetStructure)
    assert issubclass(ImmutableSetStructure, ImmutableCollectionStructure)
    assert issubclass(MutableSetStructure, SetStructure)
    assert issubclass(MutableSetStructure, MutableCollectionStructure)
    assert issubclass(MutableSetStructure, SlottedMutableSet)

    assert issubclass(ImmutableSet, ImmutableSetStructure)
    assert issubclass(MutableSet, MutableSetStructure)


if __name__ == "__main__":
    pytest.main()

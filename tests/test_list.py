# type: ignore

import pytest
from slotted import SlottedMutableSequence, SlottedSequence

from estruttura._base import CollectionStructure, ImmutableCollectionStructure
from estruttura._base import MutableCollectionStructure
from estruttura._list import ImmutableListStructure, ListStructure, MutableListStructure


def test_inheritance():
    assert issubclass(ListStructure, CollectionStructure)
    assert issubclass(ListStructure, SlottedSequence)
    assert issubclass(ImmutableListStructure, ListStructure)
    assert issubclass(ImmutableListStructure, ImmutableCollectionStructure)
    assert issubclass(MutableListStructure, ListStructure)
    assert issubclass(MutableListStructure, MutableCollectionStructure)
    assert issubclass(MutableListStructure, SlottedMutableSequence)


if __name__ == "__main__":
    pytest.main()

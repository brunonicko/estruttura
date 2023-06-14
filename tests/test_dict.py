# type: ignore

import pytest
from slotted import SlottedMapping, SlottedMutableMapping

from estruttura._base import CollectionStructure, ImmutableCollectionStructure
from estruttura._base import MutableCollectionStructure
from estruttura._dict import DictStructure, ImmutableDictStructure, MutableDictStructure


def test_inheritance():
    assert issubclass(DictStructure, CollectionStructure)
    assert issubclass(DictStructure, SlottedMapping)
    assert issubclass(ImmutableDictStructure, DictStructure)
    assert issubclass(ImmutableDictStructure, ImmutableCollectionStructure)
    assert issubclass(MutableDictStructure, DictStructure)
    assert issubclass(MutableDictStructure, MutableCollectionStructure)
    assert issubclass(MutableDictStructure, SlottedMutableMapping)


if __name__ == "__main__":
    pytest.main()

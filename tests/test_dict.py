import pytest
from slotted import SlottedMapping, SlottedMutableMapping

from estruttura._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseMutableCollectionStructure,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserMutableCollectionStructure,
)
from estruttura._dict import (
    DictStructure,
    ImmutableDictStructure,
    MutableDictStructure,
    UserDictStructure,
    UserImmutableDictStructure,
    UserMutableDictStructure,
)


def test_inheritance():
    assert issubclass(DictStructure, BaseCollectionStructure)
    assert issubclass(DictStructure, SlottedMapping)
    assert issubclass(UserDictStructure, DictStructure)
    assert issubclass(UserDictStructure, BaseUserCollectionStructure)
    assert issubclass(ImmutableDictStructure, DictStructure)
    assert issubclass(ImmutableDictStructure, BaseImmutableCollectionStructure)
    assert issubclass(UserImmutableDictStructure, ImmutableDictStructure)
    assert issubclass(UserImmutableDictStructure, UserDictStructure)
    assert issubclass(UserImmutableDictStructure, BaseUserImmutableCollectionStructure)
    assert issubclass(MutableDictStructure, DictStructure)
    assert issubclass(MutableDictStructure, BaseMutableCollectionStructure)
    assert issubclass(UserMutableDictStructure, MutableDictStructure)
    assert issubclass(UserMutableDictStructure, UserDictStructure)
    assert issubclass(UserMutableDictStructure, BaseUserMutableCollectionStructure)
    assert issubclass(UserMutableDictStructure, SlottedMutableMapping)


if __name__ == "__main__":
    pytest.main()

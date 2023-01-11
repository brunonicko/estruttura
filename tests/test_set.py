import pytest
from slotted import SlottedMutableSet, SlottedSet

from estruttura._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseMutableCollectionStructure,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserMutableCollectionStructure,
)
from estruttura._set import (
    ImmutableSetStructure,
    MutableSetStructure,
    SetStructure,
    UserImmutableSetStructure,
    UserMutableSetStructure,
    UserSetStructure,
)


def test_inheritance():
    assert issubclass(SetStructure, BaseCollectionStructure)
    assert issubclass(SetStructure, SlottedSet)
    assert issubclass(UserSetStructure, SetStructure)
    assert issubclass(UserSetStructure, BaseUserCollectionStructure)
    assert issubclass(ImmutableSetStructure, SetStructure)
    assert issubclass(ImmutableSetStructure, BaseImmutableCollectionStructure)
    assert issubclass(UserImmutableSetStructure, ImmutableSetStructure)
    assert issubclass(UserImmutableSetStructure, UserSetStructure)
    assert issubclass(UserImmutableSetStructure, BaseUserImmutableCollectionStructure)
    assert issubclass(MutableSetStructure, SetStructure)
    assert issubclass(MutableSetStructure, BaseMutableCollectionStructure)
    assert issubclass(UserMutableSetStructure, MutableSetStructure)
    assert issubclass(UserMutableSetStructure, UserSetStructure)
    assert issubclass(UserMutableSetStructure, BaseUserMutableCollectionStructure)
    assert issubclass(UserMutableSetStructure, SlottedMutableSet)


if __name__ == "__main__":
    pytest.main()

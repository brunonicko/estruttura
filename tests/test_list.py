import pytest
from slotted import SlottedMutableSequence, SlottedSequence

from estruttura._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseMutableCollectionStructure,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserMutableCollectionStructure,
)
from estruttura._list import (
    ImmutableListStructure,
    ListStructure,
    MutableListStructure,
    UserImmutableListStructure,
    UserListStructure,
    UserMutableListStructure,
    pre_move,
    resolve_continuous_slice,
    resolve_index,
)


def test_inheritance():
    assert issubclass(ListStructure, BaseCollectionStructure)
    assert issubclass(ListStructure, SlottedSequence)
    assert issubclass(UserListStructure, ListStructure)
    assert issubclass(UserListStructure, BaseUserCollectionStructure)
    assert issubclass(ImmutableListStructure, ListStructure)
    assert issubclass(ImmutableListStructure, BaseImmutableCollectionStructure)
    assert issubclass(UserImmutableListStructure, ImmutableListStructure)
    assert issubclass(UserImmutableListStructure, UserListStructure)
    assert issubclass(UserImmutableListStructure, BaseUserImmutableCollectionStructure)
    assert issubclass(MutableListStructure, ListStructure)
    assert issubclass(MutableListStructure, BaseMutableCollectionStructure)
    assert issubclass(UserMutableListStructure, MutableListStructure)
    assert issubclass(UserMutableListStructure, UserListStructure)
    assert issubclass(UserMutableListStructure, BaseUserMutableCollectionStructure)
    assert issubclass(UserMutableListStructure, SlottedMutableSequence)


def test_resolve_index():
    my_list = ["a", "b", "c", "c"]
    length = len(my_list)

    for i in range(-4, 4):
        assert my_list[resolve_index(length, i)] == my_list[i]

    with pytest.raises(IndexError):
        resolve_index(length, 5)

    with pytest.raises(IndexError):
        resolve_index(length, -5)

    assert resolve_index(length, 5, clamp=True) == 4
    assert resolve_index(length, -5, clamp=True) == 0


def test_resolve_continuous_slice():
    my_list = ["a", "b", "c", "c"]
    length = len(my_list)

    assert resolve_continuous_slice(length, slice(0, 4)) == (0, 4)
    assert resolve_continuous_slice(length, slice(-5, 5)) == (0, 4)

    with pytest.raises(IndexError):
        resolve_continuous_slice(length, slice(0, 4, 2))


def test_pre_move():
    my_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "a", "b", "c"]
    length = len(my_list)

    assert pre_move(length, 1, 2) is None
    assert pre_move(length, 2, 3) is None
    assert pre_move(length, 3, 0) == (0, 3, 4, 0, 1)
    assert pre_move(length, 1, 3) == (3, 1, 2, 2, 3)
    assert pre_move(length, slice(1, 3), 0) == (0, 1, 3, 0, 2)
    assert pre_move(length, slice(1, 3), 4) == (4, 1, 3, 2, 4)
    assert pre_move(length, slice(3, 5), 9) == (9, 3, 5, 7, 9)


if __name__ == "__main__":
    pytest.main()

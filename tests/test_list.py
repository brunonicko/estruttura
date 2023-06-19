# type: ignore

import pytest
from slotted import SlottedMutableSequence, SlottedSequence

from estruttura import CollectionStructure, ImmutableCollectionStructure
from estruttura import ImmutableListStructure, ListStructure
from estruttura import MutableCollectionStructure, MutableListStructure
from estruttura.concrete import ImmutableList, MutableList


def test_inheritance():
    assert issubclass(ListStructure, CollectionStructure)
    assert issubclass(ListStructure, SlottedSequence)
    assert issubclass(ImmutableListStructure, ListStructure)
    assert issubclass(ImmutableListStructure, ImmutableCollectionStructure)
    assert issubclass(MutableListStructure, ListStructure)
    assert issubclass(MutableListStructure, MutableCollectionStructure)
    assert issubclass(MutableListStructure, SlottedMutableSequence)

    assert issubclass(ImmutableList, ImmutableListStructure)
    assert issubclass(MutableList, MutableListStructure)


@pytest.mark.parametrize("cls", (MutableList, ImmutableList))
def test_getitem(cls):
    lst = cls(range(10))
    assert lst[1] == 1
    assert lst[2] == 2
    assert lst[3:6] == list(range(10))[3:6]
    assert lst[2:-2] == list(range(10))[2:-2]
    assert lst[-8:8] == list(range(10))[-8:8]
    assert lst[-6:-2] == list(range(10))[-6:-2]
    with pytest.raises(IndexError):
        _ = lst[11]


@pytest.mark.parametrize("cls", (MutableList, ImmutableList))
def test_get(cls):
    lst = cls(range(10))
    assert lst.get(15) is None
    assert lst.get(15, 15) == 15


@pytest.mark.parametrize("cls", (MutableList, ImmutableList))
def test_eq(cls):
    lst = cls(range(10))
    assert lst == lst
    assert lst == list(range(10))
    assert lst != list(range(4))


if __name__ == "__main__":
    pytest.main()

import pytest
from basicco import SlottedBase, SlottedBaseMeta
from slotted import SlottedCollection, SlottedHashable

from estruttura._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseImmutableStructure,
    BaseMutableCollectionStructure,
    BaseMutableStructure,
    BaseStructure,
    BaseStructureMeta,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserImmutableStructure,
    BaseUserMutableCollectionStructure,
    BaseUserMutableStructure,
    BaseUserStructure,
)


def test_inheritance():
    assert issubclass(BaseStructureMeta, SlottedBaseMeta)
    assert isinstance(BaseStructure, BaseStructureMeta)
    assert issubclass(BaseStructure, SlottedBase)
    assert issubclass(BaseUserStructure, BaseStructure)
    assert issubclass(BaseImmutableStructure, BaseStructure)
    assert issubclass(BaseImmutableStructure, SlottedHashable)
    assert issubclass(BaseUserImmutableStructure, BaseImmutableStructure)
    assert issubclass(BaseUserImmutableStructure, BaseUserStructure)
    assert issubclass(BaseMutableStructure, BaseStructure)
    assert issubclass(BaseUserMutableStructure, BaseMutableStructure)
    assert issubclass(BaseUserMutableStructure, BaseUserStructure)
    assert issubclass(BaseCollectionStructure, BaseStructure)
    assert issubclass(BaseCollectionStructure, SlottedCollection)
    assert issubclass(BaseUserCollectionStructure, BaseCollectionStructure)
    assert issubclass(BaseUserCollectionStructure, BaseUserStructure)
    assert issubclass(BaseImmutableCollectionStructure, BaseCollectionStructure)
    assert issubclass(BaseImmutableCollectionStructure, BaseImmutableStructure)
    assert issubclass(BaseUserImmutableCollectionStructure, BaseImmutableCollectionStructure)
    assert issubclass(BaseUserImmutableCollectionStructure, BaseUserCollectionStructure)
    assert issubclass(BaseMutableCollectionStructure, BaseCollectionStructure)
    assert issubclass(BaseMutableCollectionStructure, BaseMutableStructure)
    assert issubclass(BaseUserMutableCollectionStructure, BaseMutableCollectionStructure)
    assert issubclass(BaseUserMutableCollectionStructure, BaseUserCollectionStructure)


def test_unhashable_mutable():
    with pytest.raises(TypeError):

        class Foo(BaseMutableStructure):  # type: ignore  # noqa
            def __hash__(self):  # type: ignore  # noqa
                pass


if __name__ == "__main__":
    pytest.main()

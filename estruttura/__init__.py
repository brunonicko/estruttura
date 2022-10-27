"""Estruttura package."""

from ._attribute import (
    Attribute,
    MutableAttribute,
    getter,
    setter,
    deleter,
)
from ._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseImmutableStructure,
    BaseMutableCollectionStructure,
    BaseMutableStructure,
    BaseStructure,
    BaseStructureMeta,
)
from ._dict import (
    DictStructure,
    ImmutableDictStructure,
    MutableDictStructure,
)
from ._list import (
    ImmutableListStructure,
    ListStructure,
    MutableListStructure,
)
from ._relationship import (
    Relationship,
    RelationshipTypesInfo,
)
from ._set import (
    ImmutableSetStructure,
    MutableSetStructure,
    SetStructure,
)
from ._structure import (
    AttributeMap,
    ImmutableStructure,
    MutableStructure,
    Structure,
    StructureMeta,
)

__all__ = [
    "Attribute",
    "MutableAttribute",
    "getter",
    "setter",
    "deleter",
    "BaseStructureMeta",
    "BaseStructure",
    "BaseImmutableStructure",
    "BaseMutableStructure",
    "BaseCollectionStructure",
    "BaseImmutableCollectionStructure",
    "BaseMutableCollectionStructure",
    "AttributeMap",
    "Structure",
    "StructureMeta",
    "ImmutableStructure",
    "MutableStructure",
    "DictStructure",
    "ImmutableDictStructure",
    "MutableDictStructure",
    "ListStructure",
    "ImmutableListStructure",
    "MutableListStructure",
    "Relationship",
    "RelationshipTypesInfo",
    "SetStructure",
    "ImmutableSetStructure",
    "MutableSetStructure",
]

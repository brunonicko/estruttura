"""Estruttura package."""

from ._attribute import Attribute, MutableAttribute
from ._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseImmutableStructure,
    BaseMutableCollectionStructure,
    BaseMutableStructure,
    BaseStructure,
    BaseStructureMeta,
)
from ._dict import DictStructure, ImmutableDictStructure, MutableDictStructure
from ._list import ImmutableListStructure, ListStructure, MutableListStructure
from ._make import attribute, deleter, getter, relationship, setter
from ._relationship import Relationship, RelationshipTypesInfo
from ._set import ImmutableSetStructure, MutableSetStructure, SetStructure
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
    "relationship",
    "attribute",
    "getter",
    "setter",
    "deleter",
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

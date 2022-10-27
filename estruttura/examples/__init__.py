"""Example concrete implementations."""

from estruttura import attribute, deleter, getter, relationship, setter

from ._class import BaseClass, ImmutableClass, MutableClass
from ._dict import BaseDict, ImmutableDict, MutableDict
from ._list import BaseList, ImmutableList, MutableList
from ._set import BaseSet, ImmutableSet, MutableSet

__all__ = [
    "BaseDict",
    "ImmutableDict",
    "MutableDict",
    "BaseList",
    "ImmutableList",
    "MutableList",
    "BaseSet",
    "ImmutableSet",
    "MutableSet",
    "BaseClass",
    "ImmutableClass",
    "MutableClass",
    "relationship",
    "attribute",
    "getter",
    "setter",
    "deleter",
]

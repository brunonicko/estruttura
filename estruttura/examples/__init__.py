"""Example concrete implementations."""

from ._class import BaseClass, ImmutableClass, MutableClass
from ._dict import BaseDict, ImmutableDict, MutableDict
from ._list import BaseList, ImmutableList, MutableList
from ._set import BaseSet, ImmutableSet, MutableSet
from ._helpers import dict_attribute

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
    "dict_attribute",
]

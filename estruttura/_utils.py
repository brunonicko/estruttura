from tippo import Type

from ._relationship import Relationship
from ._collections import BaseCollection
from ._class import BaseClass, Attribute, AttributeMap


def relationship(cls):
    # type: (Type[BaseCollection]) -> Relationship | None
    return cls.__relationship__


def relationship_type(cls):
    # type: (Type[BaseCollection]) -> Type[Relationship]
    return cls.__relationship_type__


def attributes(cls):
    # type: (Type[BaseClass]) -> AttributeMap
    return cls.__attributes__


def attribute_type(cls):
    # type: (Type[BaseClass]) -> Type[Attribute]
    return cls.__attribute_type__

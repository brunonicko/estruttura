import six
from tippo import TypeVar

from ..base import (
    BaseClassMeta,
    BaseClass,
    BaseImmutableClassMeta,
    BaseImmutableClass,
    BaseMutableClassMeta,
    BaseMutableClass,
)
from ._attribute import StructureAttribute, MutableStructureAttribute


class ClassStructureMeta(BaseClassMeta):
    __attribute_type__ = StructureAttribute


# noinspection PyAbstractClass
class ClassStructure(six.with_metaclass(ClassStructureMeta, BaseClass)):
    __slots__ = ()


class ImmutableClassStructureMeta(ClassStructureMeta, BaseImmutableClassMeta):
    pass


# noinspection PyAbstractClass
class ImmutableClassStructure(six.with_metaclass(ImmutableClassStructureMeta, ClassStructure, BaseImmutableClass)):
    __slots__ = ()


ICS = TypeVar("ICS", bound=ImmutableClassStructure)


class MutableClassStructureMeta(ClassStructureMeta, BaseMutableClassMeta):
    __attribute_type__ = MutableStructureAttribute


# noinspection PyAbstractClass
class MutableClassStructure(six.with_metaclass(MutableClassStructureMeta, ClassStructure, BaseMutableClass)):
    __slots__ = ()


MCS = TypeVar("MCS", bound=MutableClassStructure)

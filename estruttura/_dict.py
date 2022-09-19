import six
import pyrsistent
from basicco import runtime_final, recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Mapping, Iterator, Union, overload
from pyrsistent.typing import PMap

from .bases import BaseDict, BasePrivateDict, BaseInteractiveDict, BaseMutableDict
from ._bases import (
    BaseState,
    BaseRelationship,
    BaseStructure,
    BasePrivateStructure,
    BaseInteractiveStructure,
    BaseMutableStructure,
)


KT = TypeVar("KT")  # key type
VT = TypeVar("VT")  # value type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type
RT = TypeVar("RT", bound=BaseRelationship)  # relationship type


# noinspection PyAbstractClass
class BaseDictStructure(BaseStructure[KT, VT_co, DictState[KT, VT_co], KT, RT], BaseDict[KT, VT_co]):
    """Base dict structure."""

    __slots__ = ()

    @runtime_final.final
    def get_value(self, location):
        # type: (KT) -> VT_co
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        return self[location]


# noinspection PyAbstractClass
class BasePrivateDictStructure(
    BaseDictStructure[KT, VT_co, RT],
    BasePrivateStructure[KT, VT_co, DictState[KT, VT_co], KT, RT],
    BasePrivateDict[KT, VT_co],
):
    """Base interactive dict structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveDictStructure(
    BasePrivateDictStructure[KT, VT_co, RT],
    BaseInteractiveStructure[KT, VT_co, DictState[KT, VT_co], KT, RT],
    BaseInteractiveDict[KT, VT_co],
):
    """Base interactive dict structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableDictStructure(
    BasePrivateDictStructure[KT, VT_co, RT],
    BaseMutableStructure[KT, VT_co, DictState[KT, VT_co], KT, RT],
    BaseMutableDict[KT, VT_co],
):
    """Base mutable dict structure."""

    __slots__ = ()

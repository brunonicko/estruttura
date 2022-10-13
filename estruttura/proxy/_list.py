from tippo import TypeVar, Union

from ._base import ProxyCollection, ProxyImmutableCollection, ProxyMutableCollection
from ..structures import ListStructure, ImmutableListStructure, MutableListStructure


T_co = TypeVar("T_co", covariant=True)


LST = TypeVar("LST", bound=Union[ImmutableListStructure, MutableListStructure])


class ProxyList(ListStructure[LST, T_co], ProxyCollection[LST, T_co]):
    __slots__ = ()


ILST = TypeVar("ILST", bound=ImmutableListStructure)


class ProxyImmutableList(
    ProxyList[ILST, T_co],
    ImmutableListStructure[ILST, T_co],
    ProxyImmutableCollection[ILST, T_co],
):
    __slots__ = ()


class ProxyMutableList(
    ProxyList[LST, T_co],
    MutableListStructure[LST, T_co],
    ProxyMutableCollection[LST, T_co],
):
    __slots__ = ()

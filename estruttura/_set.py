import pyrsistent
from basicco import runtime_final, recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Iterator
from pyrsistent.typing import PSet

from .bases import BaseSet, BaseProtectedSet, BaseInteractiveSet, BaseMutableSet
from ._bases import (
    BaseState,
    BaseRelationship,
    BaseStructure,
    BaseProtectedStructure,
    BaseInteractiveStructure,
    BaseMutableStructure,
)


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type
RT = TypeVar("RT", bound=BaseRelationship)  # relationship type


# noinspection PyAbstractClass
class BaseSetStructure(BaseStructure[T, T, SetState[T], int, RT], BaseSet[T]):
    """Base list structure."""

    __slots__ = ()

    @runtime_final.final
    def _get_value(self, location):
        # type: (T) -> T
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        if location not in self:
            raise KeyError("not in set")
        return location


# noinspection PyAbstractClass
class BaseProtectedSetStructure(
    BaseSetStructure[T_co, RT],
    BaseProtectedStructure[T_co, T_co, SetState[T_co], int, RT],
    BaseProtectedSet[T_co],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveSetStructure(
    BaseProtectedSetStructure[T_co, RT],
    BaseInteractiveStructure[T_co, T_co, SetState[T_co], int, RT],
    BaseInteractiveSet[T_co],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableSetStructure(
    BaseProtectedSetStructure[T_co, RT],
    BaseMutableStructure[T_co, T_co, SetState[T_co], int, RT],
    BaseMutableSet[T_co],
):
    """Base mutable list structure."""

    __slots__ = ()

import itertools

import pyrsistent
import six
from basicco import runtime_final, recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Iterator, overload
from pyrsistent.typing import PVector

from .bases import BaseList, BaseProtectedList, BaseInteractiveList, BaseMutableList
from .utils import resolve_index, resolve_continuous_slice, pre_move
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
class BaseListStructure(BaseStructure[T_co, T_co, ListState[T_co], int, RT], BaseList[T_co]):
    """Base list structure."""

    __slots__ = ()

    @runtime_final.final
    def get_value(self, location):
        # type: (int) -> T_co
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        try:
            return self[location]
        except IndexError as e:
            exc = KeyError(e)
            six.raise_from(exc, None)
            raise exc


# noinspection PyAbstractClass
class BaseProtectedListStructure(
    BaseListStructure[T_co, RT],
    BaseProtectedStructure[T_co, T_co, ListState[T_co], int, RT],
    BaseProtectedList[T_co],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveListStructure(
    BaseProtectedListStructure[T_co, RT],
    BaseInteractiveStructure[T_co, T_co, ListState[T_co], int, RT],
    BaseInteractiveList[T_co],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableListStructure(
    BaseProtectedListStructure[T_co, RT],
    BaseMutableStructure[T_co, T_co, ListState[T_co], int, RT],
    BaseMutableList[T_co],
):
    """Base mutable list structure."""

    __slots__ = ()

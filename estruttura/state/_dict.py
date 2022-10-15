import itertools

import pyrsistent
from six import moves
from basicco.abstract_class import abstract
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import iterable_repr
from basicco.explicit_hash import set_to_none
from tippo import Any, overload, MutableSequence, Iterable, SupportsKeysAndGetItem, TypeVar, Type, Mapping, cast
from pyrsistent.typing import PMap

from ..base import BaseDict, BaseImmutableDict, BaseMutableDict


KT = TypeVar("KT")
VT = TypeVar("VT")


_PMAP_TYPE = type(pyrsistent.pmap())  # type: Type[PMap]


class DictState(BaseDict[KT, VT]):
    __slots__ = ()

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**VT) -> None
        pass

    @abstract
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    @abstract
    def _internal(self):
        # type: () -> Mapping[KT, VT]
        raise NotImplementedError()


class ImmutableDictState(DictState[KT, VT], BaseImmutableDict[KT, VT]):
    __slots__ = ("__internal",)

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**VT) -> None
        pass

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and type(args[0]) is _PMAP_TYPE:
            internal = cast(PMap[KT, VT], args[0])
        else:
            internal = pyrsistent.pmap(dict(*args, **kwargs))
        self.__internal = internal  # type: PMap[KT, VT]

    def __hash__(self):
        # type: () -> int
        return hash(self._internal)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(ImmutableDictState, other)._internal

    @property
    def _internal(self):
        # type: () -> PMap[KT, VT]
        return self.__internal


ISS = TypeVar("ISS", bound=ImmutableDictState)


class MutableDictState(DictState[KT, VT], BaseMutableDict[KT, VT]):
    __slots__ = ("__internal",)

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**VT) -> None
        pass

    def __init__(self, *args, **kwargs):
        self.__internal = dict(*args, **kwargs)  # type: dict[KT, VT]

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(MutableDictState, other)._internal

    @property
    def _internal(self):
        # type: () -> dict[KT, VT]
        return self.__internal


MSS = TypeVar("MSS", bound=MutableDictState)

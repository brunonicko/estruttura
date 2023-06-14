import pyrsistent
from tippo import Any, Dict, Iterable, Iterator, Mapping, Self, SupportsKeysAndGetItem
from tippo import Tuple, Type, TypeVar, overload

from .._dict import ImmutableDictStructure, MutableDictStructure

__all__ = ["ImmutableDict", "MutableDict"]


KT = TypeVar("KT")
VT = TypeVar("VT")


_PMap = type(pyrsistent.pmap())  # type: Type[pyrsistent.PMap[Any, Any]]


class ImmutableDict(ImmutableDictStructure[KT, VT]):
    __slots__ = ("__pmap",)

    @classmethod
    def fromkeys(cls, keys, value):
        # type: (Type[Self], Iterable[KT], VT) -> Self
        return cls(dict.fromkeys(keys, value))

    def __init__(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        if len(args) == 1:
            if type(args[0]) is _PMap:
                self.__pmap = args[0]  # type: pyrsistent.PMap[KT, VT]
            else:
                self.__pmap = pyrsistent.pmap(args[0])
            if kwargs:
                self.__pmap = self.__pmap.update(kwargs)
        else:
            self.__pmap = pyrsistent.pmap(dict(*args, **kwargs))

    def __contains__(self, key):
        # type: (object) -> bool
        return key in self.__pmap

    def __iter__(self):
        # type: () -> Iterator[KT]
        for key in self.__pmap:
            yield key

    def __len__(self):
        # type: () -> int
        return len(self.__pmap)

    def __getitem__(self, key):
        # type: (KT) -> VT
        return self.__pmap[key]

    def clear(self):
        # type: () -> Self
        return type(self)()

    def discard(self, *keys):
        # type: (*KT) -> Self
        evolver = self.__pmap.evolver()
        for key in keys:
            if key in self.__pmap:
                del evolver[key]
        return type(self)(evolver.persistent())

    @overload
    def update(self, mapping, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> Self
        pass

    @overload
    def update(self, iterable, **kwargs):
        # type: (Iterable[Tuple[KT, VT]], **VT) -> Self
        pass

    @overload
    def update(self, **kwargs):
        # type: (**VT) -> Self
        pass

    def update(self, *args, **kwargs):
        # type: (*Any, **Any) -> Self
        if len(args) == 1:
            pmap = self.__pmap.update(args[0])  # type: pyrsistent.PMap[KT, VT]
        else:
            pmap = self.__pmap.update(*args)
        if kwargs:
            pmap = pmap.update(kwargs)
        return type(self)(pmap)


class MutableDict(MutableDictStructure[KT, VT]):
    __slots__ = ("__dict",)

    @classmethod
    def fromkeys(cls, keys, value):
        # type: (Type[Self], Iterable[KT], VT) -> Self
        return cls(dict.fromkeys(keys, value))

    def __init__(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        self.__dict = dict(*args, **kwargs)  # type: Dict[KT, VT]

    def __contains__(self, key):
        # type: (object) -> bool
        return key in self.__dict

    def __iter__(self):
        # type: () -> Iterator[KT]
        for key in self.__dict:
            yield key

    def __len__(self):
        # type: () -> int
        return len(self.__dict)

    def __or__(self, other):
        # type: (Mapping[KT, VT]) -> Self
        if not isinstance(other, Mapping):
            return NotImplemented
        merged = dict(self.__dict)
        merged.update(other)
        return type(self)(merged)

    def __getitem__(self, key):
        # type: (KT) -> VT
        return self.__dict[key]

    def clear(self):
        # type: () -> None
        self.__dict.clear()

    def discard(self, *keys):
        # type: (*KT) -> None
        for key in keys:
            if key in self.__dict:
                del self.__dict[key]

    @overload  # type: ignore
    def update(self, mapping, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def update(self, iterable, **kwargs):
        # type: (Iterable[Tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**VT) -> None
        pass

    def update(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        self.__dict.update(*args, **kwargs)

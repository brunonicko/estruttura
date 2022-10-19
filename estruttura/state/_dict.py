import pyrsistent
import six
from basicco.abstract_class import abstract
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import mapping_repr
from basicco.explicit_hash import set_to_none
from tippo import Any, overload, Iterator, Iterable, SupportsKeysAndGetItem, TypeVar, Type, Mapping, cast
from pyrsistent.typing import PMap

from ..base import BaseDict, BaseImmutableDict, BaseMutableDict
from ..constants import DeletedType, DELETED


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

    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        return self._internal[key]

    def __contains__(self, key):
        # type: (object) -> bool
        """
        Whether key is present.

        :param key: Key.
        :return: True if present.
        """
        return key in self._internal

    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in self._internal:
            yield key

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._internal)

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return mapping_repr(
            self._internal,
            prefix="{}({{".format(type(self).__qualname__),
            suffix="})",
            sorting=True,
            sort_key=lambda p: id(p[0])
        )

    def get(self, key, fallback=None):
        # type: (KT, Any) -> Any
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._internal.get(key, fallback)

    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        for item in six.iteritems(self._internal):
            yield item

    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in six.iterkeys(self._internal):
            yield key

    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in six.itervalues(self._internal):
            yield value

    @property
    @abstract
    def _internal(self):
        # type: () -> Mapping[KT, VT]
        """Internal mapping."""
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

    def _clear(self):
        # type: (IDS) -> IDS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        return type(self)()

    @overload
    def _update(self, __m, **kwargs):
        # type: (IDS, SupportsKeysAndGetItem[KT, VT | DeletedType], **VT) -> IDS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (IDS, Iterable[tuple[KT, VT | DeletedType]], **VT | DeletedType) -> IDS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (IDS, **VT | DeletedType) -> IDS
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        updates = dict(*args, **kwargs)
        deletes = set()
        for key, value in list(updates.items()):
            if value is DELETED:
                deletes.add(updates.pop(key))

        internal = self._internal.update(updates)
        if deletes:
            evolver = internal.evolver()
            for key in deletes:
                del evolver[key]
            internal = evolver.persistent()

        return type(self)(internal)

    @property
    def _internal(self):
        # type: () -> PMap[KT, VT]
        return self.__internal


IDS = TypeVar("IDS", bound=ImmutableDictState)


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

    def _clear(self):
        # type: (MDS) -> MDS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        self._internal.clear()
        return self

    @overload
    def _update(self, __m, **kwargs):
        # type: (MDS, SupportsKeysAndGetItem[KT, VT | DeletedType], **VT) -> MDS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (MDS, Iterable[tuple[KT, VT | DeletedType]], **VT | DeletedType) -> MDS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (MDS, **VT | DeletedType) -> MDS
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        updates = dict(*args, **kwargs)
        deletes = set()
        for key, value in list(updates.items()):
            if value is DELETED:
                deletes.add(updates.pop(key))

        self._internal.update(updates)
        for key in deletes:
            del self._internal[key]

        return self

    @property
    def _internal(self):
        # type: () -> dict[KT, VT]
        return self.__internal


MDS = TypeVar("MDS", bound=MutableDictState)

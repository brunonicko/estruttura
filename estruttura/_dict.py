import six
import pyrsistent
from basicco import runtime_final, recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Mapping, Iterator, Union, Protocol, overload
from pyrsistent.typing import PMap

from .bases import BaseDict, BaseProtectedDict, BaseInteractiveDict, BaseMutableDict
from ._bases import (
    BaseState,
    BaseRelationship,
    BaseStructure,
    BaseProtectedStructure,
    BaseInteractiveStructure,
    BaseMutableStructure,
)


KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # value type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type
RT = TypeVar("RT", bound=BaseRelationship)  # relationship type


class _SupportsKeysAndGetItem(Protocol[KT, VT_co]):
    def keys(self):
        # type: () -> Iterable[KT]
        pass

    def __getitem__(self, __k):
        # type: (KT) -> VT_co
        pass


@runtime_final.final
class DictState(BaseState[KT, PMap[KT, VT]], BaseInteractiveDict[KT, VT]):
    """Immutable dictionary state."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Union[Iterable[tuple[KT, VT]], Mapping[KT, VT]]) -> PMap[KT, VT]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pmap(initial)

    def __init__(self, initial=()):
        # type: (Union[Iterable[tuple[KT, VT]], Mapping[KT, VT]]) -> None
        super(DictState, self).__init__(initial)

    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :return: True if contains.
        """
        return key in self._internal

    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in six.iterkeys(self._internal):
            yield key

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._internal)

    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.mapping_repr(
            self._internal,
            prefix="{}({{".format(type(self).__fullname__),
            suffix="})",
            sorting=True,
            sort_key=lambda i: hash(i[0]),
        )

    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return reversed(list(self.__iter__()))

    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        return self._internal[key]

    def _clear(self):
        # type: (DS) -> DS
        """
        Clear.

        :return: Transformed.
        """
        return self._make(pyrsistent.pmap())

    def _discard(self, key):
        # type: (DS, KT) -> DS
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._make(self._internal.discard(key))

    def _remove(self, key):
        # type: (DS, KT) -> DS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._make(self._internal.remove(key))

    def _set(self, key, value):
        # type: (DS, KT, VT) -> DS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.set(key, value))

    @overload
    def _update(self, __m, **kwargs):
        # type: (DS, _SupportsKeysAndGetItem[KT, VT], VT) -> DS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (DS, Iterable[tuple[KT, VT]], VT) -> DS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (DS, VT) -> DS
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._make(self._internal.update(dict(*args, **kwargs)))

    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
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
        for key, value in six.iteritems(self._internal):
            yield key, value

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


DS = TypeVar("DS", bound=DictState)


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
class BaseProtectedDictStructure(
    BaseDictStructure[KT, VT_co, RT],
    BaseProtectedStructure[KT, VT_co, DictState[KT, VT_co], KT, RT],
    BaseProtectedDict[KT, VT_co],
):
    """Base interactive dict structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveDictStructure(
    BaseProtectedDictStructure[KT, VT_co, RT],
    BaseInteractiveStructure[KT, VT_co, DictState[KT, VT_co], KT, RT],
    BaseInteractiveDict[KT, VT_co],
):
    """Base interactive dict structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableDictStructure(
    BaseProtectedDictStructure[KT, VT_co, RT],
    BaseMutableStructure[KT, VT_co, DictState[KT, VT_co], KT, RT],
    BaseMutableDict[KT, VT_co],
):
    """Base mutable dict structure."""

    __slots__ = ()

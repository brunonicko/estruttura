import contextlib

import six
from tippo import Any, TypeVar, Iterator, SupportsKeysAndGetItem, Iterable, Union, overload

from ..base import BaseDict, BaseImmutableDict, BaseMutableDict
from ._base import CollectionStructure, ImmutableCollectionStructure, MutableCollectionStructure
from ..constants import DeletedType, DELETED


KT = TypeVar("KT")
VT = TypeVar("VT")
VT_co = TypeVar("VT_co", covariant=True)

DST = TypeVar("DST", bound=Union[BaseImmutableDict, BaseMutableDict])  # dict state type


class DictStructure(CollectionStructure[DST, KT], BaseDict[KT, VT]):
    __slots__ = ()

    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        return self._state[key]

    @contextlib.contextmanager
    def _update_context(self, updates):
        yield

    @overload
    def _update(self, __m, **kwargs):
        # type: (DS, SupportsKeysAndGetItem[KT, VT | DeletedType], **VT) -> DS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (DS, Iterable[tuple[KT, VT | DeletedType]], **VT | DeletedType) -> DS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (DS, **VT | DeletedType) -> DS
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        updates = dict(*args, **kwargs)
        relationship = type(self).relationship
        if relationship is not None and relationship.will_process:
            updates = dict((k, relationship.process(v) if v is not DELETED else v) for k, v in six.iteritems(updates))

        with self._update_context(updates):
            return self._transform(self._state.update(*args, **kwargs))

    def get(self, key, fallback=None):
        # type: (KT, Any) -> Any
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._state.get(key, fallback=fallback)

    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        # noinspection PyCompatibility
        return self._state.iteritems()

    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        # noinspection PyCompatibility
        return self._state.iterkeys()

    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        # noinspection PyCompatibility
        return self._state.itervalues()


DS = TypeVar("DS", bound=DictStructure)  # dict structure self type


IDST = TypeVar("IDST", bound=BaseImmutableDict)  # immutable dict state type


class ImmutableDictStructure(
    DictStructure[IDST, KT, VT_co],
    ImmutableCollectionStructure[IDST, KT],
    BaseImmutableDict[KT, VT_co],
):
    __slots__ = ()


class MutableDictStructure(
    DictStructure[DST, KT, VT_co],
    MutableCollectionStructure[DST, KT],
    BaseMutableDict[KT, VT_co],
):
    __slots__ = ()

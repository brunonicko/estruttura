import six
import slotted
from tippo import (
    Any,
    TypeVar,
    KeysView,
    ItemsView,
    ValuesView,
    Iterator,
    SupportsKeysAndGetItem,
    Iterable,
    MutableMapping,
    overload,
)
from basicco.runtime_final import final
from basicco.abstract_class import abstract

from ._base import CollectionStructure, ImmutableCollectionStructure, MutableCollectionStructure
from .constants import DeletedType, DELETED, MISSING


KT = TypeVar("KT")
VT = TypeVar("VT")


class DictStructure(CollectionStructure[KT], slotted.SlottedMapping[KT, VT]):
    __slots__ = ()

    @abstract
    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        raise NotImplementedError()

    @final
    def _discard(self, key):
        # type: (BD, KT) -> BD
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        try:
            return self._delete(key)
        except KeyError:
            return self

    @final
    def _delete(self, key):
        # type: (BD, KT) -> BD
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._update({key: DELETED})

    @final
    def _set(self, key, value):
        # type: (BD, KT, VT) -> BD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._update({key: value})

    @overload
    def _update(self, __m, **kwargs):
        # type: (BD, SupportsKeysAndGetItem[KT, VT | DeletedType], **VT) -> BD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BD, Iterable[tuple[KT, VT | DeletedType]], **VT | DeletedType) -> BD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BD, **VT | DeletedType) -> BD
        pass

    @abstract
    def _update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstract
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Any
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        raise NotImplementedError()

    @abstract
    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        raise NotImplementedError()

    @abstract
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        raise NotImplementedError()

    @abstract
    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        raise NotImplementedError()

    @final
    def items(self):
        # type: () -> ItemsView[KT, VT]
        """
        Items view.

        :return: Items.
        """
        return ItemsView(self)

    @final
    def keys(self):
        # type: () -> KeysView[KT]
        """
        Keys view.

        :return: Keys.
        """
        return KeysView(self)

    @final
    def values(self):
        # type: () -> ValuesView[VT]
        """
        Values view.

        :return: Values.
        """
        return ValuesView(self)


BD = TypeVar("BD", bound=DictStructure)


# noinspection PyAbstractClass
class ImmutableDictStructure(DictStructure[KT, VT], ImmutableCollectionStructure[KT]):
    __slots__ = ()

    @final
    def discard(self, key):
        # type: (IDS, KT) -> IDS
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._discard(key)

    @final
    def delete(self, key):
        # type: (IDS, KT) -> IDS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._delete(key)

    @final
    def set(self, key, value):
        # type: (IDS, KT, VT) -> IDS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (IDS, SupportsKeysAndGetItem[KT, VT], **VT) -> IDS
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (IDS, Iterable[tuple[KT, VT]], **VT) -> IDS
        pass

    @overload
    def update(self, **kwargs):
        # type: (IDS, **VT) -> IDS
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        return self._update(*args, **kwargs)


IDS = TypeVar("IDS", bound=ImmutableDictStructure)  # immutable dict structure self type


# noinspection PyAbstractClass
class MutableDictStructure(
    DictStructure[KT, VT],
    MutableCollectionStructure[KT],
    slotted.SlottedMutableMapping[KT, VT],
):
    __slots__ = ()

    @final
    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        self._set(key, value)

    @final
    def __delitem__(self, key):
        # type: (KT) -> None
        """
        Delete key.

        :param key: Key.
        :raises KeyError: Key is not preset.
        """
        self._delete(key)

    @final
    def pop(self, key, fallback=MISSING):
        # type: (KT, Any) -> Any
        """
        Get value for key and delete it, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        :raises KeyError: Key is not present and fallback value not provided.
        """
        try:
            value = self[key]
        except KeyError:
            if fallback is not MISSING:
                return fallback
            raise
        del self[key]
        return value

    @final
    def popitem(self):
        # type: () -> tuple[KT, VT]
        """
        Get item and discard key.

        :return: Item.
        :raises KeyError: Dictionary is empty.
        """
        try:
            key = next(iter(self))
        except StopIteration:
            exc = KeyError("{!r} is empty".format(type(self).__name__))
            six.raise_from(exc, None)
            raise exc
        return (key, self.pop(key))

    @overload
    def setdefault(self, key):  # noqa
        # type: (MutableMapping[KT, VT | None], KT) -> VT | None
        pass

    @overload
    def setdefault(self, key, default):  # noqa
        # type: (KT, VT) -> VT
        pass

    @final
    def setdefault(self, key, default=None):
        """
        Get the value for the specified key, insert key with default if not present.

        :param key: Key.
        :param default: Default value.
        :return: Existing or default value.
        """
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    @final
    def discard(self, key):
        # type: (KT) -> None
        """
        Discard key if it exists.

        :param key: Key.
        """
        self._discard(key)

    @final
    def delete(self, key):
        # type: (KT) -> None
        """
        Delete existing key.

        :param key: Key.
        :raises KeyError: Key is not present.
        """
        self._delete(key)

    @final
    def set(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**VT) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)

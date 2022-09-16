import abc

import slotted
from basicco import runtime_final
from tippo import (
    Any,
    TypeVar,
    Iterator,
    ItemsView,
    KeysView,
    ValuesView,
    Iterable,
    MutableMapping,
    Protocol,
    overload,
)

from ._bases import BaseCollection, BaseInteractiveCollection, BaseMutableCollection, BaseProtectedCollection


KT = TypeVar("KT")  # key type
VT = TypeVar("VT")  # value type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type


MISSING = object()


class _SupportsKeysAndGetItem(Protocol[KT, VT_co]):
    def keys(self):
        # type: () -> Iterable[KT]
        pass

    def __getitem__(self, __k):
        # type: (KT) -> VT_co
        pass


class BaseDict(BaseCollection[KT], slotted.SlottedMapping[KT, VT_co]):
    """Base dictionary collection."""

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: {!r}".format(type(self).__name__)
        raise TypeError(error)

    @abc.abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __getitem__(self, key):
        # type: (KT) -> VT_co
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Any
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT_co]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def itervalues(self):
        # type: () -> Iterator[VT_co]
        """
        Iterate over values.

        :return: Values iterator.
        """
        raise NotImplementedError()

    @runtime_final.final
    def items(self):
        # type: () -> ItemsView[KT, VT_co]
        """
        Get items.

        :return: Items.
        """
        return ItemsView(self)

    @runtime_final.final
    def keys(self):
        # type: () -> KeysView[KT]
        """
        Get keys.

        :return: Keys.
        """
        return KeysView(self)

    @runtime_final.final
    def values(self):
        # type: () -> ValuesView[VT_co]
        """
        Get values.

        :return: Values.
        """
        return ValuesView(self)


# noinspection PyCallByClass
type.__setattr__(BaseDict, "__hash__", None)  # force non-hashable


class BaseProtectedDict(BaseDict[KT, VT], BaseProtectedCollection[KT]):
    """Base protected dictionary collection."""

    __slots__ = ()

    @abc.abstractmethod
    def _discard(self, key):
        # type: (BPD, KT) -> BPD
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _remove(self, key):
        # type: (BPD, KT) -> BPD
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _set(self, key, value):
        # type: (BPD, KT, VT) -> BPD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        raise NotImplementedError()

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPD, _SupportsKeysAndGetItem[KT, VT], **VT) -> BPD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPD, Iterable[tuple[KT, VT]], **VT) -> BPD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BPD, **VT) -> BPD
        pass

    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        raise NotImplementedError()


BPD = TypeVar("BPD", bound=BaseProtectedDict)  # base protected dict type


# noinspection PyAbstractClass
class BaseInteractiveDict(BaseProtectedDict[KT, VT], BaseInteractiveCollection[KT]):
    """Base interactive dictionary collection."""

    __slots__ = ()

    @runtime_final.final
    def discard(self, key):
        # type: (BID, KT) -> BID
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._discard(key)

    @runtime_final.final
    def remove(self, key):
        # type: (BID, KT) -> BID
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._remove(key)

    @runtime_final.final
    def set(self, key, value):
        # type: (BID, KT, VT) -> BID
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (BID, _SupportsKeysAndGetItem[KT, VT], **VT) -> BID
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BID, Iterable[tuple[KT, VT]], **VT) -> BID
        pass

    @overload
    def update(self, **kwargs):
        # type: (BID, **VT) -> BID
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


BID = TypeVar("BID", bound=BaseInteractiveDict)  # base interactive dict type


class BaseMutableDict(BaseProtectedDict[KT, VT], BaseMutableCollection[KT], slotted.SlottedMutableMapping[KT, VT]):
    """Base mutable dictionary collection."""

    __slots__ = ()

    @runtime_final.final
    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        self._set(key, value)

    @runtime_final.final
    def __delitem__(self, key):
        # type: (KT) -> None
        """
        Delete key.

        :param key: Key.
        :raises KeyError: Key is not preset.
        """
        self._remove(key)

    @abc.abstractmethod
    def pop(self, key, fallback=MISSING):
        # type: (KT, Any) -> Any
        """
        Get value for key and remove it, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        :raises KeyError: Key is not present and fallback value not provided.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def popitem(self):
        # type: () -> tuple[KT, VT]
        """
        Get item and discard key.

        :return: Item.
        :raises KeyError: Dictionary is empty.
        """
        raise NotImplementedError()

    @overload
    def setdefault(self, key):
        # type: (MutableMapping[KT, VT | None], KT) -> None
        pass

    @overload
    def setdefault(self, key, default):  # noqa
        # type: (KT, VT) -> VT
        pass

    @abc.abstractmethod
    def setdefault(self, key, default=None):
        """
        Get the value for the specified key, insert key with default if not present.

        :param key: Key.
        :param default: Default value.
        :return: Existing or default value.
        """
        raise NotImplementedError()

    @runtime_final.final
    def discard(self, key):
        # type: (KT) -> None
        """
        Discard key if it exists.

        :param key: Key.
        """
        self._discard(key)

    @runtime_final.final
    def remove(self, key):
        # type: (KT) -> None
        """
        Delete existing key.

        :param key: Key.
        :raises KeyError: Key is not present.
        """
        self._remove(key)

    @runtime_final.final
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
        # type: (_SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**VT) -> None
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)

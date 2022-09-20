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
    overload,
    cast,
)

from ._constants import MISSING, SupportsKeysAndGetItem
from ._bases import (
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BasePrivateCollection,
    ProxyCollection,
    InteractiveProxyCollection,
    MutableProxyCollection,
    PrivateProxyCollection,
)


KT = TypeVar("KT")  # key type
VT = TypeVar("VT")  # value type
VT_co = TypeVar("VT_co", covariant=True)  # covariant value type


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
        Items view.

        :return: Items.
        """
        return ItemsView(self)

    @runtime_final.final
    def keys(self):
        # type: () -> KeysView[KT]
        """
        Keys view.

        :return: Keys.
        """
        return KeysView(self)

    @runtime_final.final
    def values(self):
        # type: () -> ValuesView[VT_co]
        """
        Values view.

        :return: Values.
        """
        return ValuesView(self)


# noinspection PyCallByClass
type.__setattr__(BaseDict, "__hash__", None)  # force non-hashable


class BasePrivateDict(BaseDict[KT, VT], BasePrivateCollection[KT]):
    """Base private dictionary collection."""

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
        # type: (BPD, SupportsKeysAndGetItem[KT, VT], **VT) -> BPD
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


BPD = TypeVar("BPD", bound=BasePrivateDict)  # base private dict type


# noinspection PyAbstractClass
class BaseInteractiveDict(BasePrivateDict[KT, VT], BaseInteractiveCollection[KT]):
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
        # type: (BID, SupportsKeysAndGetItem[KT, VT], **VT) -> BID
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


class BaseMutableDict(BasePrivateDict[KT, VT], BaseMutableCollection[KT], slotted.SlottedMutableMapping[KT, VT]):
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
    def setdefault(self, key):  # noqa
        # type: (MutableMapping[KT, VT | None], KT) -> VT | None
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

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)


class ProxyDict(BaseDict[KT, VT_co], ProxyCollection[KT]):
    """
    Proxy dictionary.

    Features:
      - Wraps a private/interactive/mutable dictionary.
    """

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (BasePrivateDict[KT, VT_co]) -> None
        """
        :param wrapped: Base private/interactive/mutable dictionary.
        """
        super(ProxyDict, self).__init__(wrapped)

    @runtime_final.final
    def __hash__(self):
        """
        Get hash.

        :raises TypeError: Not hashable.
        """
        return hash((type(self), self._wrapped))

    @runtime_final.final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        return isinstance(other, type(self)) and self._wrapped == other._wrapped

    @runtime_final.final
    def __getitem__(self, key):
        # type: (KT) -> VT_co
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        return self._wrapped[key]

    @runtime_final.final
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Any
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._wrapped.get(key, fallback=fallback)

    @runtime_final.final
    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT_co]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        for i in self._wrapped.iteritems():  # noqa
            yield i

    @runtime_final.final
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for k in self._wrapped.iterkeys():  # noqa
            yield k

    @runtime_final.final
    def itervalues(self):
        # type: () -> Iterator[VT_co]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for v in self._wrapped.itervalues():  # noqa
            yield v

    @property
    def _wrapped(self):
        # type: () -> BasePrivateDict[KT, VT_co]
        """Wrapped base private/interactive/mutable dictionary."""
        return cast(BasePrivateDict[KT, VT_co], super(ProxyDict, self)._wrapped)


class ProxyPrivateDict(ProxyDict[KT, VT], BasePrivateDict[KT, VT], PrivateProxyCollection[KT]):
    """
    Private proxy dictionary.

    Features:
      - Has private transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @runtime_final.final
    def _discard(self, key):
        # type: (PPD, KT) -> PPD
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._discard(key))  # noqa

    @runtime_final.final
    def _remove(self, key):
        # type: (PPD, KT) -> PPD
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._transform_wrapped(self._wrapped._remove(key))  # noqa

    @runtime_final.final
    def _set(self, key, value):
        # type: (PPD, KT, VT) -> PPD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._set(key, value))  # noqa

    @overload
    def _update(self, __m, **kwargs):
        # type: (PPD, SupportsKeysAndGetItem[KT, VT], **VT) -> PPD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (PPD, Iterable[tuple[KT, VT]], **VT) -> PPD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (PPD, **VT) -> PPD
        pass

    @runtime_final.final
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._update(*args, **kwargs))  # noqa


PPD = TypeVar("PPD", bound=ProxyPrivateDict)  # private proxy dictionary type


class ProxyInteractiveDict(ProxyPrivateDict[KT, VT], BaseInteractiveDict[KT, VT], InteractiveProxyCollection[KT]):
    """
    Proxy interactive dictionary.

    Features:
      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()


class ProxyMutableDict(ProxyPrivateDict[KT, VT], BaseMutableDict[KT, VT], MutableProxyCollection[KT]):
    """
    Proxy mutable dictionary.

    Features:
      - Has public mutable transformation methods.
    """

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (BaseMutableDict[KT, VT]) -> None
        """
        :param wrapped: Base mutable dict.
        """
        super(ProxyMutableDict, self).__init__(wrapped)

    @runtime_final.final
    def pop(self, key, fallback=MISSING):
        # type: (KT, Any) -> Any
        """
        Get value for key and remove it, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        :raises KeyError: Key is not present and fallback value not provided.
        """
        return self._wrapped.pop(key, fallback=fallback)

    @runtime_final.final
    def popitem(self):
        # type: () -> tuple[KT, VT]
        """
        Get item and discard key.

        :return: Item.
        :raises KeyError: Dictionary is empty.
        """
        return self._wrapped.popitem()

    @overload
    def setdefault(self, key):  # noqa
        # type: (MutableMapping[KT, VT | None], KT) -> VT | None
        pass

    @overload
    def setdefault(self, key, default):  # noqa
        # type: (KT, VT) -> VT
        pass

    @runtime_final.final
    def setdefault(self, key, default=None):
        """
        Get the value for the specified key, insert key with default if not present.

        :param key: Key.
        :param default: Default value.
        :return: Existing or default value.
        """
        return self._wrapped.setdefault(key, default=default)

    @property
    def _wrapped(self):
        # type: () -> BaseMutableDict[KT, VT]
        """Wrapped base mutable dict."""
        return cast(BaseMutableDict[KT, VT], super(MutableProxyCollection, self)._wrapped)

"""Dictionary structures."""

import abc

import six
import slotted
from basicco import runtime_final
from tippo import (
    Any,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    MutableMapping,
    SupportsKeysAndGetItem,
    TypeVar,
    ValuesView,
    cast,
    overload,
)

from ._bases import (
    InteractiveProxyUniformStructure,
    InteractiveUniformStructure,
    MutableProxyUniformStructure,
    MutableUniformStructure,
    PrivateProxyUniformStructure,
    PrivateUniformStructure,
    ProxyUniformStructure,
    UniformStructure,
)
from ._constants import DELETED, MISSING

KT = TypeVar("KT")
VT = TypeVar("VT")
VT_co = TypeVar("VT_co", covariant=True)


class DictStructure(UniformStructure[KT], slotted.SlottedMapping[KT, VT_co]):
    """Dictionary structure."""

    __slots__ = ()

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


class PrivateDictStructure(DictStructure[KT, VT], PrivateUniformStructure[KT]):
    """Private dictionary structure."""

    __slots__ = ()

    @runtime_final.final
    def _discard(self, key):
        # type: (PDS, KT) -> PDS
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        try:
            return self._remove(key)
        except KeyError:
            return self

    @runtime_final.final
    def _remove(self, key):
        # type: (PDS, KT) -> PDS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._update({key: DELETED})

    @runtime_final.final
    def _set(self, key, value):
        # type: (PDS, KT, VT) -> PDS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._update({key: value})

    @overload
    def _update(self, __m, **kwargs):
        # type: (PDS, SupportsKeysAndGetItem[KT, VT], **VT) -> PDS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (PDS, Iterable[tuple[KT, VT]], **VT) -> PDS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (PDS, **VT) -> PDS
        pass

    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        raise NotImplementedError()


PDS = TypeVar("PDS", bound=PrivateDictStructure)


# noinspection PyAbstractClass
class InteractiveDictStructure(PrivateDictStructure[KT, VT], InteractiveUniformStructure[KT]):
    """Interactive dictionary structure."""

    __slots__ = ()

    @runtime_final.final
    def discard(self, key):
        # type: (IDS, KT) -> IDS
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._discard(key)

    @runtime_final.final
    def remove(self, key):
        # type: (IDS, KT) -> IDS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._remove(key)

    @runtime_final.final
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

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


IDS = TypeVar("IDS", bound=InteractiveDictStructure)


# noinspection PyAbstractClass
class MutableDictStructure(
    PrivateDictStructure[KT, VT], MutableUniformStructure[KT], slotted.SlottedMutableMapping[KT, VT]
):
    """Mutable dictionary structure."""

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
        try:
            value = self[key]
        except KeyError:
            if fallback is not MISSING:
                return fallback
            raise
        del self[key]
        return value

    @runtime_final.final
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

    @runtime_final.final
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


class ProxyDict(DictStructure[KT, VT_co], ProxyUniformStructure[KT]):
    """Proxy dictionary."""

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (PrivateDictStructure[KT, VT_co]) -> None
        """
        :param wrapped: Dictionary structure to be wrapped.
        """
        super(ProxyDict, self).__init__(wrapped)

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
        # type: () -> PrivateDictStructure[KT, VT_co]
        """Wrapped dictionary collection."""
        return cast(PrivateDictStructure[KT, VT_co], super(ProxyDict, self)._wrapped)


class PrivateProxyDict(ProxyDict[KT, VT], PrivateDictStructure[KT, VT], PrivateProxyUniformStructure[KT]):
    """Private proxy dictionary."""

    __slots__ = ()

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


PPD = TypeVar("PPD", bound=PrivateProxyDict)


class InteractiveProxyDict(
    PrivateProxyDict[KT, VT], InteractiveDictStructure[KT, VT], InteractiveProxyUniformStructure[KT]
):
    """Interactive proxy dictionary."""

    __slots__ = ()


class MutableProxyDict(PrivateProxyDict[KT, VT], MutableDictStructure[KT, VT], MutableProxyUniformStructure[KT]):
    """Mutable proxy dictionary."""

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (MutableDictStructure[KT, VT]) -> None
        """
        :param wrapped: Mutable dictionary structure.
        """
        super(MutableProxyDict, self).__init__(wrapped)

    @property
    def _wrapped(self):
        # type: () -> MutableDictStructure[KT, VT]
        """Wrapped mutable dict structure."""
        return cast(MutableDictStructure[KT, VT], super(MutableProxyDict, self)._wrapped)

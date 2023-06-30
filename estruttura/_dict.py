from basicco import abstract
from basicco.custom_repr import mapping_repr
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from slotted import SlottedMapping, SlottedMutableMapping
from tippo import Any, Hashable, ItemsView, Iterable, KeysView, Mapping, Type
from tippo import SupportsKeysAndGetItem, Tuple, TypeVar, Union, ValuesView, overload

from ._base import CollectionStructure, ImmutableCollectionStructure
from ._base import MutableCollectionStructure

__all__ = ["DictStructure", "ImmutableDictStructure", "MutableDictStructure"]


KT = TypeVar("KT")
VT = TypeVar("VT")
_VT = TypeVar("_VT")


class DictStructure(CollectionStructure[KT], SlottedMapping[KT, VT]):
    """Dictionary Structure."""

    __slots__ = ()

    @classmethod
    @abstract
    def fromkeys(cls, keys, value):
        # type: (Type[DS], Iterable[KT], VT) -> DS
        """
        Build from keys and a single value.

        :param keys: Keys.
        :param value: Value.
        :return: New instance.
        """
        raise NotImplementedError()

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return mapping_repr(
            self.items(),
            prefix="{}({{".format(type(self).__name__),
            suffix="})",
        )

    @abstract
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if not isinstance(other, Mapping):
            return False
        if type(self) is not type(other):
            return (
                not isinstance(self, Hashable) or not isinstance(other, Hashable)
            ) and dict(self) == dict(other)
        return dict(self) == dict(other)  # noqa

    @abstract
    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key not present.
        """
        raise NotImplementedError()

    @abstract
    def __or__(self, other):
        # type: (Mapping[KT, VT]) -> Mapping[KT, VT]
        """
        Merge: (self | other).

        :param other: Another mapping.
        :return: Merged mapping.
        """
        raise NotImplementedError()

    @overload
    def get(self, key):
        # type: (KT) -> Union[VT, None]
        pass

    @overload
    def get(self, key, default):  # noqa
        # type: (KT, _VT) -> Union[VT, _VT]
        pass

    def get(self, key, default=None):
        # type: (Any, Any) -> Any
        """
        Get value for key, return default value if key not present.

        :param key: Key.
        :param default: Default value.
        :return: Value or default value.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        # type: () -> ItemsView[KT, VT]
        """
        Get items view.

        :return: Items view.
        """
        return ItemsView(self)

    def keys(self):
        # type: () -> KeysView[KT]
        """
        Get keys view.

        :return: Keys view.
        """
        return KeysView(self)

    def values(self):
        # type: () -> ValuesView[VT]
        """
        Get values view.

        :return: Values view.
        """
        return ValuesView(self)


DS = TypeVar("DS", bound=DictStructure[Any, Any])


class ImmutableDictStructure(ImmutableCollectionStructure[KT], DictStructure[KT, VT]):
    """Immutable Dictionary Structure."""

    __slots__ = ()

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(frozenset(self.items()))

    @abstract
    def __or__(self, other):
        # type: (IDS, Mapping[KT, VT]) -> IDS
        """
        Merge: (self | other).

        :param other: Another mapping.
        :return: Transformed.
        """
        raise NotImplementedError()

    @overload
    def update(self, mapping, **kwargs):
        # type: (IDS, SupportsKeysAndGetItem[KT, VT], **VT) -> IDS
        pass

    @overload
    def update(self, iterable, **kwargs):
        # type: (IDS, Iterable[Tuple[KT, VT]], **VT) -> IDS
        pass

    @overload
    def update(self, **kwargs):
        # type: (IDS, **VT) -> IDS
        pass

    @abstract
    def update(self, *args, **kwargs):
        # type: (IDS, *Any, **Any) -> IDS
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        raise NotImplementedError()

    @abstract
    def discard(self, *key):
        # type: (IDS, *KT) -> IDS
        """
        Discard key(s).

        :param: Key(s).
        :return: Transformed.
        """
        raise NotImplementedError()

    def remove(self, *key):
        # type: (IDS, *KT) -> IDS
        """
        Remove key(s).

        :param: Key(s).
        :return: Transformed.
        :raises KeyError: Key not present.
        """
        for k in key:
            if k not in self:
                raise KeyError(k)
        return self.discard(*key)

    def set(self, key, value):
        # type: (IDS, KT, VT) -> IDS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self.update({key: value})


IDS = TypeVar("IDS", bound=ImmutableDictStructure[Any, Any])


class MutableDictStructure(
    MutableCollectionStructure[KT],
    DictStructure[KT, VT],
    SlottedMutableMapping[KT, VT],
):
    """Mutable Dictionary Structure."""

    __slots__ = ()
    __hash__ = None  # type: ignore

    def __ior__(self, other):
        # type: (MDS, Mapping[KT, VT]) -> MDS
        """
        Merge in-place: (self |= other).

        :param other: Another mapping.
        :return: Self.
        """
        self.update(other)
        return self

    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        self.set(key, value)

    def __delitem__(self, key):
        # type: (KT) -> None
        """
        Delete value for key.

        :param key: Key.
        :raises KeyError: Key not present.
        """
        self.remove(key)

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

    @abstract
    def update(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        raise NotImplementedError()

    @abstract
    def discard(self, *keys):
        # type: (*KT) -> None
        """
        Discard key(s).

        :param: Key(s).
        """
        raise NotImplementedError()

    def remove(self, *key):
        # type: (*KT) -> None
        """
        Remove key(s).

        :param: Key(s).
        :raises KeyError: Key not present.
        """
        for k in key:
            if k not in self:
                raise KeyError(k)
        self.discard(*key)

    def set(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        self.update({key: value})

    def setdefault(self, key, value):  # noqa
        # type: (KT, VT) -> VT
        """
        Set value for key if it's not present.

        :param key: Key.
        :param value: Default value.
        :return: Value or default value.
        """
        try:
            return self[key]
        except KeyError:
            self[key] = value
            return value


MDS = TypeVar("MDS", bound=MutableDictStructure[Any, Any])

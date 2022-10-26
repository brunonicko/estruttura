import six
import slotted
from basicco.abstract_class import abstract
from basicco.custom_repr import mapping_repr
from basicco.mapping_proxy import MappingProxyType
from basicco.recursive_repr import recursive_repr
from basicco.runtime_final import final
from basicco.safe_repr import safe_repr
from tippo import (
    Any,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    MutableMapping,
    SupportsKeysAndGetItem,
    Type,
    TypeVar,
    ValuesView,
    overload,
)

from ._bases import (
    CollectionStructure,
    ImmutableCollectionStructure,
    MutableCollectionStructure,
)
from ._relationship import Relationship
from .constants import DELETED, MISSING, DeletedType, MissingType
from .exceptions import ProcessingError

KT = TypeVar("KT")
VT = TypeVar("VT")


class DictStructure(CollectionStructure[KT], slotted.SlottedMapping[KT, VT]):
    """Dictionary structure."""

    __slots__ = ()
    key_relationship = Relationship()  # type: Relationship[KT]

    def __init_subclass__(cls, key_relationship=MISSING, **kwargs):
        # type: (Relationship[KT] | MissingType, **Any) -> None

        # Key relationship.
        if key_relationship is not MISSING:
            cls.key_relationship = key_relationship

        super(DictStructure, cls).__init_subclass__(**kwargs)

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
        """
        Same parameters as :class:`dict`.
        """
        initial_values = dict(*args, **kwargs)
        if self.relationship.will_process:
            try:
                initial_values = dict(
                    (self.key_relationship.process_value(k), self.relationship.process_value(v, k))
                    for k, v in six.iteritems(initial_values)
                )
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        self._do_init(MappingProxyType(initial_values))

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

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.
        :return: Representation.
        """
        return mapping_repr(
            self,
            prefix="{}({{".format(type(self).__qualname__),
            suffix="})",
        )

    @abstract
    def _do_init(self, initial_values):
        # type: (MappingProxyType[KT, VT]) -> None
        """
        Initialize keys and values.

        :param initial_values: Initial values.
        """
        raise NotImplementedError()

    @final
    def _discard(self, key):
        # type: (DS, KT) -> DS
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed (immutable) or self (mutable).
        """
        if key in self:
            return self._update({key: DELETED})
        else:
            return self

    @final
    def _delete(self, key):
        # type: (DS, KT) -> DS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed (immutable) or self (mutable).
        :raises KeyError: Key is not present.
        """
        return self._update({key: DELETED})

    @final
    def _set(self, key, value):
        # type: (DS, KT, VT) -> DS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._update({key: value})

    @abstract
    def _do_update(
        self,  # type: DS
        inserts,  # type: MappingProxyType[KT, VT]
        deletes,  # type: MappingProxyType[KT, VT]
        updates_old,  # type: MappingProxyType[KT, VT]
        updates_new,  # type: MappingProxyType[KT, VT]
        updates_and_inserts,  # type: MappingProxyType[KT, VT]
    ):
        # type: (...) -> DS
        """
        Update keys and values.

        :param inserts: Keys and values being inserted.
        :param deletes: Keys and values being deleted.
        :param updates_old: Keys and values being updated (old values).
        :param updates_new: Keys and values being updated (new values).
        :param updates_and_inserts: Keys and values being updated or inserted.
        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()

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

    @final
    def _update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed (immutable) or self (mutable).
        """
        changes = dict(*args, **kwargs)
        inserts = {}
        deletes = {}
        updates_old = {}
        updates_new = {}
        updates_and_inserts = {}
        for key, value in six.iteritems(changes):
            key = self.key_relationship.process_value(key)

            if value is DELETED:
                if key not in self:
                    raise KeyError(key)
                deletes[key] = self[key]
                continue

            if self.relationship.will_process:
                try:
                    value = self.relationship.process_value(value, key)
                except ProcessingError as e:
                    exc = type(e)(e)
                    six.raise_from(exc, None)
                    raise exc

            updates_and_inserts[key] = value
            if key in self:
                updates_old[key] = self[key]
                updates_new[key] = value
            else:
                inserts[key] = value

        return self._do_update(
            MappingProxyType(inserts),
            MappingProxyType(deletes),
            MappingProxyType(updates_old),
            MappingProxyType(updates_new),
            MappingProxyType(updates_and_inserts),
        )

    @classmethod
    @abstract
    def _do_deserialize(cls, values):
        # type: (Type[DS], MappingProxyType[KT, VT]) -> DS
        raise NotImplementedError()

    def serialize(self):
        # type: () -> dict[KT, Any]
        return dict((n, type(self).relationship.serialize_value(v)) for n, v in six.iteritems(self))

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[DS], Mapping[KT, Any]) -> DS
        values = dict((n, cls.relationship.deserialize_value(s)) for n, s in six.iteritems(serialized))
        return cls._do_deserialize(MappingProxyType(values))

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

    @final
    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        for key in self:
            yield key, self[key]

    @final
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in self:
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for key in self:
            yield self[key]

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


DS = TypeVar("DS", bound=DictStructure)


# noinspection PyAbstractClass
class ImmutableDictStructure(DictStructure[KT, VT], ImmutableCollectionStructure[KT]):
    """Immutable dictionary structure."""

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
    """Mutable dictionary structure."""

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

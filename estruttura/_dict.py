"""Dictionary structures."""

import six
import slotted
from basicco import custom_repr, hash_cache_wrapper, mapping_proxy
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Iterable, Mapping, SupportsKeysAndGetItem, Type, TypeVar, overload

from ._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseMutableCollectionStructure,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserMutableCollectionStructure,
)
from ._relationship import Relationship
from .constants import DELETED, MISSING, DeletedType, MissingType
from .exceptions import ProcessingError

KT = TypeVar("KT")
VT = TypeVar("VT")


class DictStructure(BaseCollectionStructure[KT], slotted.SlottedMapping[KT, VT]):
    """Dictionary structure."""

    __slots__ = ()

    value_relationship = Relationship()  # type: Relationship[VT]
    """Value relationship."""

    def __init_subclass__(cls, value_relationship=MISSING, **kwargs):
        # type: (Relationship[KT] | MissingType, **Any) -> None
        """
        Initialize subclass with parameters.

        :param value_relationship: Value relationship.
        """
        if value_relationship is not MISSING:
            cls.value_relationship = value_relationship
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
        """Same parameters as :class:`dict`."""
        initial_values = dict(*args, **kwargs)
        if self.relationship.will_process or self.value_relationship.will_process:
            try:
                initial_values = dict(
                    (
                        self.relationship.process_value(k, "{!r} (key)".format(k)),
                        self.value_relationship.process_value(v, k),
                    )
                    for k, v in six.iteritems(initial_values)
                )
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        self._do_init(mapping_proxy.MappingProxyType(initial_values))
        self.__post_init__()

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
    def _eq(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if other is self:
            return True
        elif isinstance(other, dict):
            return dict(self) == other
        else:
            return isinstance(other, type(self)) and type(self) is type(other) and dict(self) == dict(other)

    def _repr(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.mapping_repr(self, prefix="{}({{".format(type(self).__qualname__), suffix="})")

    @abstract
    def _do_init(self, initial_values):
        # type: (mapping_proxy.MappingProxyType[KT, VT]) -> None
        """
        Initialize keys and values (internal).

        :param initial_values: Initial values.
        """
        raise NotImplementedError()

    @classmethod
    @abstract
    def _do_deserialize(cls, values):
        # type: (Type[DS], mapping_proxy.MappingProxyType[KT, VT]) -> DS
        """
        Deserialize (internal).

        :param values: Deserialized values.
        :return: Dictionary structure.
        :raises SerializationError: Error while deserializing.
        """
        raise NotImplementedError()

    def serialize(self):
        # type: () -> dict[KT, Any]
        """
        Serialize.

        :return: Serialized dictionary.
        :raises SerializationError: Error while serializing.
        """
        return dict(
            (type(self).relationship.serialize_value(k), type(self).value_relationship.serialize_value(v))
            for k, v in six.iteritems(self)
        )

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[DS], Mapping[KT, Any]) -> DS
        """
        Deserialize.

        :param serialized: Serialized mapping.
        :return: Dictionary structure.
        :raises SerializationError: Error while deserializing.
        """
        values = dict(
            (cls.relationship.deserialize_value(k), cls.value_relationship.deserialize_value(v))
            for k, v in six.iteritems(serialized)
        )
        self = cls._do_deserialize(mapping_proxy.MappingProxyType(values))
        self.__post_deserialize__()
        return self


DS = TypeVar("DS", bound=DictStructure)  # dictionary structure self type


# noinspection PyAbstractClass
class UserDictStructure(DictStructure[KT, VT], BaseUserCollectionStructure[KT]):
    """User dictionary structure."""

    __slots__ = ()

    @final
    def _discard(self, key):
        # type: (UDS, KT) -> UDS
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
        # type: (UDS, KT) -> UDS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed (immutable) or self (mutable).
        :raises KeyError: Key is not present.
        """
        return self._update({key: DELETED})

    @final
    def _set(self, key, value):
        # type: (UDS, KT, VT) -> UDS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._update({key: value})

    @abstract
    def _do_update(
        self,
        inserts,  # type: mapping_proxy.MappingProxyType[KT, VT]
        deletes,  # type: mapping_proxy.MappingProxyType[KT, VT]
        updates_old,  # type: mapping_proxy.MappingProxyType[KT, VT]
        updates_new,  # type: mapping_proxy.MappingProxyType[KT, VT]
        updates_and_inserts,  # type: mapping_proxy.MappingProxyType[KT, VT]
        all_updates,  # type: mapping_proxy.MappingProxyType[KT, VT | DeletedType]
    ):
        # type: (...) -> None
        """
        Update keys and values (internal).

        :param inserts: Keys and values being inserted.
        :param deletes: Keys and values being deleted.
        :param updates_old: Keys and values being updated (old values).
        :param updates_new: Keys and values being updated (new values).
        :param updates_and_inserts: Keys and values being updated or inserted.
        """
        raise NotImplementedError()

    @overload
    def _update(self, __m, **kwargs):
        # type: (UDS, SupportsKeysAndGetItem[KT, VT | DeletedType], **VT) -> UDS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (UDS, Iterable[tuple[KT, VT | DeletedType]], **VT | DeletedType) -> UDS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (UDS, **VT | DeletedType) -> UDS
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
        all_updates = {}
        for key, value in six.iteritems(changes):
            if self.relationship.will_process:
                key = self.relationship.process_value(key, "{!r} (key)".format(key))

            if value is DELETED:
                if key not in self:
                    raise KeyError(key)
                deletes[key] = self[key]
                all_updates[key] = DELETED
                continue

            if self.value_relationship.will_process:
                try:
                    value = self.value_relationship.process_value(value, key)
                except ProcessingError as e:
                    exc = type(e)(e)
                    six.raise_from(exc, None)
                    raise exc

            updates_and_inserts[key] = value
            all_updates[key] = value
            if key in self:
                updates_old[key] = self[key]
                updates_new[key] = value
            else:
                inserts[key] = value

        with self.__change_context__() as _self:
            _self._do_update(
                mapping_proxy.MappingProxyType(inserts),
                mapping_proxy.MappingProxyType(deletes),
                mapping_proxy.MappingProxyType(updates_old),
                mapping_proxy.MappingProxyType(updates_new),
                mapping_proxy.MappingProxyType(updates_and_inserts),
                mapping_proxy.MappingProxyType(all_updates),
            )
            return _self


UDS = TypeVar("UDS", bound=UserDictStructure)  # user dictionary structure self type


# noinspection PyAbstractClass
class ImmutableDictStructure(DictStructure[KT, VT], BaseImmutableCollectionStructure[KT]):
    """Immutable dictionary structure."""

    __slots__ = ()

    @final
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(frozenset(self.items()))


IDS = TypeVar("IDS", bound=ImmutableDictStructure)  # immutable dictionary structure self type


# noinspection PyAbstractClass
class UserImmutableDictStructure(
    ImmutableDictStructure[KT, VT],
    UserDictStructure[KT, VT],
    BaseUserImmutableCollectionStructure[KT],
):
    """User immutable dictionary structure."""

    __slots__ = ()

    @final
    def __or__(self, mapping):
        # type: (UIDS, Mapping[KT, VT]) -> UIDS
        """
        Update with another mapping.

        :param mapping: Another mapping.
        :return: Transformed.
        """
        return self.update(mapping)

    @final
    def discard(self, key):
        # type: (UIDS, KT) -> UIDS
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._discard(key)

    @final
    def delete(self, key):
        # type: (UIDS, KT) -> UIDS
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._delete(key)

    @final
    def set(self, key, value):
        # type: (UIDS, KT, VT) -> UIDS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (UIDS, SupportsKeysAndGetItem[KT, VT], **VT) -> UIDS
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (UIDS, Iterable[tuple[KT, VT]], **VT) -> UIDS
        pass

    @overload
    def update(self, **kwargs):
        # type: (UIDS, **VT) -> UIDS
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        return self._update(*args, **kwargs)


UIDS = TypeVar("UIDS", bound=UserImmutableDictStructure)  # user immutable dictionary structure self type


# noinspection PyAbstractClass
class MutableDictStructure(DictStructure[KT, VT], BaseMutableCollectionStructure[KT]):
    """Mutable dictionary structure."""

    __slots__ = ()


MDS = TypeVar("MDS", bound=MutableDictStructure)  # mutable dictionary structure self type


# noinspection PyAbstractClass
class UserMutableDictStructure(
    MutableDictStructure[KT, VT],
    UserDictStructure[KT, VT],
    BaseUserMutableCollectionStructure[KT],
    slotted.SlottedMutableMapping[KT, VT],
):
    """User mutable dictionary structure."""

    __slots__ = ()

    @final
    def __ior__(self, mapping):
        # type: (UMDS, Mapping[KT, VT]) -> UMDS
        """
        Update in place with another mapping.

        :param mapping: Another mapping.
        """
        self.update(mapping)
        return self

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
        return key, self.pop(key)

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


UMDS = TypeVar("UMDS", bound=UserMutableDictStructure)  # user mutable dictionary structure self type

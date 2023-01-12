"""Attribute class structures."""

import operator

import six
from basicco import get_mro, mapping_proxy
from basicco.abstract_class import abstract
from basicco.namespace import Namespace
from basicco.runtime_final import final
from tippo import Any, Callable, Iterable, Iterator, Mapping, SupportsKeysAndGetItem, Type, TypeVar, cast, overload

from ._attribute import Attribute, AttributeMap, MutableAttribute
from ._bases import (
    BaseImmutableStructure,
    BaseMutableStructure,
    BaseStructure,
    BaseStructureMeta,
    BaseUserImmutableStructure,
    BaseUserMutableStructure,
    BaseUserStructure,
)
from .constants import DELETED, MISSING
from .exceptions import ProcessingError


class StructureMeta(BaseStructureMeta):
    """Metaclass for :class:`Structure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        # type: (...) -> StructureMeta

        # Get/set attribute type for this class.
        dct = dict(dct)
        attribute_type = Attribute
        for base in reversed(get_mro.preview_mro(*bases)):
            if base is object:
                continue
            if "__attribute_type__" in base.__dict__:
                if isinstance(base, StructureMeta):
                    attribute_type = base.__dict__["__attribute_type__"]
                else:
                    error = "invalid base {!r} defines '__attribute_type__'".format(base.__name__)
                    raise TypeError(error)
        attribute_type = dct["__attribute_type__"] = dct.get("__kwargs__", {}).get(
            "attribute_type", kwargs.get("attribute_type", dct.get("__attribute_type__", attribute_type))
        )

        # Scrape bases for attributes.
        base_attributes = {}  # type: dict[str, Attribute]
        counter = {}  # type: dict[str, int]
        for base in reversed(get_mro.preview_mro(*bases)):
            if base is object:
                continue

            # Prevent overriding existing attributes with invalid ones.
            for attribute_name in base_attributes:
                if attribute_name in base.__dict__:
                    if isinstance(base, StructureMeta):
                        if attribute_name not in base.__this_attribute_map__ or not isinstance(
                            base.__this_attribute_map__[attribute_name], attribute_type
                        ):
                            error = "{!r} overrides {!r} attribute with {!r} object, expected {!r}".format(
                                base.__name__,
                                attribute_name,
                                type(base.__dict__[attribute_name]).__name__,
                                attribute_type.__name__,
                            )
                            raise TypeError(error)
                    else:
                        error = "invalid base {!r} overrides {!r} attribute".format(base.__name__, attribute_name)
                        raise TypeError(error)

            # Collect base's attributes.
            if isinstance(base, StructureMeta):
                for attribute_name, attribute in base.__attribute_map__.ordered_items():

                    # Attribute type changed and it's not compatible anymore.
                    if not isinstance(attribute, attribute_type):
                        error = "class {!r} defines '__attribute_type__' as {!r}, but base {!r} utilizes {!r}".format(
                            name,
                            attribute_type.__name__,
                            base.__qualname__,
                            getattr(base, "__attribute_type__", Attribute).__name__,
                        )
                        raise TypeError(error)

                    assert attribute.name == attribute_name

                    # Collect attribute and remember count only if not seen before.
                    base_attributes[attribute_name] = attribute
                    if attribute_name not in counter:
                        counter[attribute_name] = attribute.count

            else:
                for member_name, member in six.iteritems(base.__dict__):
                    if isinstance(member, attribute_type):
                        error = "invalid base {!r} defines {!r} attribute".format(base.__name__, member_name)
                        raise TypeError(error)

        # Collect attributes for this class.
        this_attributes = {}  # type: dict[str, Attribute]
        for member_name, member in six.iteritems(dct):
            if isinstance(member, Attribute):
                if not isinstance(member, attribute_type):
                    error = "invalid {!r} attribute type {!r}, expected {!r}".format(
                        member_name, type(member).__name__, attribute_type.__name__
                    )
                    raise TypeError(error)

                # Collect attribute.
                base_attributes[member_name] = this_attributes[member_name] = member
                if member_name not in counter:
                    counter[member_name] = member.count

            elif member_name in base_attributes:
                error = "{!r} overrides {!r} attribute with {!r} object, expected {!r}".format(
                    name,
                    member_name,
                    type(member).__name__,
                    attribute_type.__name__,
                )
                raise TypeError(error)

        # Build ordered attribute map.
        attribute_items = sorted(six.iteritems(base_attributes), key=lambda i: counter[i[0]])
        attribute_map = AttributeMap(attribute_items)  # type: AttributeMap[str, Attribute]

        this_attribute_items = [(n, a) for n, a in attribute_items if n in this_attributes]
        this_attribute_map = AttributeMap(this_attribute_items)  # type: AttributeMap[str, Attribute]

        # Hook to edit dct.
        dct_copy = dict(dct)
        dct_copy = mcs.__edit_dct__(this_attribute_map, attribute_map, name, bases, dct_copy, **kwargs)

        # Build class.
        cls = super(StructureMeta, mcs).__new__(mcs, name, bases, dct_copy, **kwargs)

        # Name and claim attributes.
        for attribute_name, attribute in six.iteritems(this_attributes):
            attribute.__set_name__(cls, attribute_name)
            assert attribute.owner is cls
            assert attribute.name == attribute_name

        # Final checks.
        seen_default = None
        initialization_map = {}  # type: dict[str, str]
        deserialization_map = {}  # type: dict[str, str]
        for attribute_name, attribute in attribute_map.ordered_items():

            # Check for non-default attributes declared after default ones.
            if not cls.__kw_only__ and attribute.init:
                if attribute.has_default:
                    seen_default = attribute_name
                elif seen_default is not None:
                    error = "non-default attribute {!r} declared after default attribute {!r}".format(
                        attribute_name, seen_default
                    )
                    raise TypeError(error)

            # Check for missing attribute dependencies.
            missing_dependencies = set(attribute.recursive_dependencies).difference(attribute_map.values())
            if missing_dependencies:
                error = "attribute {!r} depends on {}; not defined in {!r}".format(
                    attribute_name,
                    ", ".join(
                        "'{}.{}'".format(m.owner.__qualname__, m.name)
                        for m in sorted(missing_dependencies, key=lambda a: a.name)
                    ),
                    cls.__qualname__,
                )
                raise TypeError(error)

            # Check for initialization conflicts.
            if attribute.init:

                if isinstance(attribute.init_as, cls.__attribute_type__):
                    init_name = attribute.init_as.name
                elif isinstance(attribute.init_as, six.string_types):
                    init_name = attribute.init_as
                elif attribute.init_as is not None:
                    error = "invalid 'init_as' type {!r} for attribute {!r}".format(
                        type(attribute.init_as).__name__, attribute_name
                    )
                    raise TypeError(error)
                else:
                    init_name = attribute_name

                if init_name in initialization_map:
                    error = "attribute {!r} initializes as {!r}, which is also used by attribute {!r}".format(
                        attribute_name, init_name, initialization_map[init_name]
                    )
                    raise TypeError(error)
                initialization_map[init_name] = attribute_name

            # Check for serialization conflicts.
            if attribute.serializable:

                if isinstance(attribute.serialize_as, cls.__attribute_type__):
                    serialized_name = attribute.serialize_as.name
                elif isinstance(attribute.serialize_as, six.string_types):
                    serialized_name = attribute.serialize_as
                elif attribute.serialize_as is not None:
                    error = "invalid 'serialize_as' type {!r} for attribute {!r}".format(
                        type(attribute.serialize_as).__name__, attribute_name
                    )
                    raise TypeError(error)
                else:
                    serialized_name = attribute_name

                if serialized_name in deserialization_map:
                    error = "attribute {!r} serializes as {!r}, which is also used by attribute {!r}".format(
                        attribute_name, serialized_name, deserialization_map[serialized_name]
                    )
                    raise TypeError(error)
                deserialization_map[serialized_name] = attribute_name

        # Store attributes namespace, attributes map, and initialization/deserialization map.
        type.__setattr__(cls, "attributes", Namespace(attribute_map))
        type.__setattr__(cls, "__attribute_map__", attribute_map)
        type.__setattr__(cls, "__this_attribute_map__", this_attribute_map)
        type.__setattr__(cls, "__initialization_map__", mapping_proxy.MappingProxyType(initialization_map))
        type.__setattr__(cls, "__deserialization_map__", mapping_proxy.MappingProxyType(deserialization_map))

        # Run callbacks.
        for attribute in six.itervalues(this_attribute_map):
            attribute.__run_callback__()

        return cls

    # noinspection PyUnusedLocal
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]
        """
        Static method hook to edit the class dictionary.

        :param this_attribute_map: Attribute map for this class only.
        :param attribute_map: Attribute map with all attributes.
        :param name: Class name.
        :param bases: Class bases.
        :param dct: Class dictionary.
        :param kwargs: Class keyword arguments.
        :return: Edited class dictionary.
        """
        return dct


# noinspection PyAbstractClass
class Structure(six.with_metaclass(StructureMeta, BaseStructure)):
    """Attribute class structure."""

    __slots__ = ()

    attributes = Namespace()  # type: Namespace[Attribute[Any]]

    __attribute_map__ = AttributeMap()  # type: AttributeMap[str, Attribute[Any]]
    __this_attribute_map__ = AttributeMap()  # type: AttributeMap[str, Attribute[Any]]
    __initialization_map__ = mapping_proxy.MappingProxyType({})  # type: mapping_proxy.MappingProxyType[str, str]
    __deserialization_map__ = mapping_proxy.MappingProxyType({})  # type: mapping_proxy.MappingProxyType[str, str]

    __attribute_type__ = Attribute  # type: Type[Attribute[Any]]
    __kw_only__ = False  # type: bool

    def __init_subclass__(cls, attribute_type=None, kw_only=None, **kwargs):
        # type: (Type[Attribute] | None, bool | None, **Any) -> None
        """
        Initialize subclass with parameters.

        :param attribute_type: Attribute type.
        :param kw_only: Whether '__init__' should accept keyword arguments only.
        """
        # Attribute type (should be set by the metaclass).
        if attribute_type is not None:
            assert attribute_type is cls.__attribute_type__

        # Keyword arguments only.
        if kw_only is not None:
            if not kw_only and cls.__kw_only__:
                error = "class {!r} already set to use keyword arguments only, can't set it to False".format(
                    cls.__qualname__
                )
                raise TypeError(error)
            cls.__kw_only__ = bool(kw_only)

        super(Structure, cls).__init_subclass__(**kwargs)  # noqa

    def __init__(self, *args, **kwargs):
        cls = type(self)

        # Force keyword arguments only.
        if cls.__kw_only__ and args:
            error = "'{}.__init__' accepts keyword arguments only".format(cls.__qualname__)
            raise TypeError(error)

        # Translate kwargs using initialization map.
        try:
            kwargs = dict((cls.__initialization_map__[n], v) for n, v in six.iteritems(kwargs))
        except KeyError:
            invalid_names = set(kwargs).difference(cls.__initialization_map__)
            error = "invalid attribute name(s) {}".format(", ".join(repr(n) for n in invalid_names))
            exc = TypeError(error)
            six.raise_from(exc, None)
            raise exc

        # Initialize attribute values.
        try:
            initial_values = cls.__attribute_map__.get_initial_values(
                args,
                kwargs,
                init_property="init",
                init_method="__init__",
            )
            self._do_init(mapping_proxy.MappingProxyType(initial_values))
        except (ProcessingError, TypeError, ValueError) as e:
            exc = type(e)(e)
            six.raise_from(exc, None)
            raise exc

        self.__post_init__()

    def __order__(self, other, func):
        # type: (object, Callable[[Any, Any], bool]) -> bool

        # Require the exact same type for comparison.
        cls = type(self)
        if cls is not type(other):
            return NotImplemented
        assert isinstance(other, type(self))

        # Get attributes to compare.
        attributes = [n for n, a in cls.__attribute_map__.ordered_items() if a.order]
        if not attributes:
            return NotImplemented

        # Compare values.
        order_values = tuple(self._get(n) for n in attributes if n in self)
        other_order_values = tuple(other._get(n) for n in attributes if n in other)
        return func(order_values, other_order_values)

    def __lt__(self, other):
        # type: (object) -> bool
        return self.__order__(other, operator.lt)

    def __le__(self, other):
        # type: (object) -> bool
        return self.__order__(other, operator.le)

    def __gt__(self, other):
        # type: (object) -> bool
        return self.__order__(other, operator.gt)

    def __ge__(self, other):
        # type: (object) -> bool
        return self.__order__(other, operator.ge)

    @final
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute.

        :param name: Attribute name.
        :return: Attribute value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        _ = self.__attribute_map__[name]
        try:
            return self._get(name)
        except AttributeError as e:
            exc = KeyError(e)
            six.raise_from(exc, None)
            raise exc

    @final
    def __contains__(self, name):
        # type: (object) -> bool
        """
        Get whether there's a value for attribute.

        :param name: Attribute name.
        :return: True if has value.
        """
        if name not in self.__attribute_map__:
            return False
        return self._contains(cast(str, name))

    @final
    def __iter__(self):
        # type: () -> Iterator[tuple[str, Any]]
        """
        Iterate over attribute items (name, value).

        :return: Attribute item iterator.
        """
        for name in type(self).__attribute_map__:
            if name in self:
                yield name, self._get(name)

    @abstract
    def _contains(self, name):
        # type: (str) -> bool
        """
        Get whether there's a value for attribute.

        :param name: Attribute name.
        :return: True if has value.
        """
        raise NotImplementedError()

    @abstract
    def _get(self, name):
        # type: (str) -> Any
        """
        Get value for attribute.

        :param name: Attribute name.
        :return: Attribute value.
        :raises AttributeError: Attribute has no value.
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

        # Same object.
        if self is other:
            return True

        # Require the exact same type for comparison.
        cls = type(self)
        if cls is not type(other):
            return NotImplemented
        assert isinstance(other, type(self))

        # Get attributes to compare.
        attributes = [n for n, a in cls.__attribute_map__.ordered_items() if a.eq]

        # Compare values.
        eq_values = dict((n, self._get(n)) for n in attributes if n in self)
        other_eq_values = dict((n, other._get(n)) for n in attributes if n in other)
        return eq_values == other_eq_values

    def _repr(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        cls = type(self)

        args = []
        kwargs = []
        delegated = []
        reprs = {}  # type: dict[str, Callable[[Any], str]]
        values = {}  # type: dict[str, Any]
        translations = {}  # type: dict[str, str]
        for name, attribute in cls.__attribute_map__.ordered_items():
            if not attribute.repr:
                continue

            if name in self:
                values[name] = self._get(name)

            if isinstance(attribute.init_as, cls.__attribute_type__):
                assert attribute.init_as.name is not None
                translations[name] = attribute.init_as.name
            elif isinstance(attribute.init_as, six.string_types):
                translations[name] = attribute.init_as
            else:
                translations[name] = name

            reprs[name] = repr if not callable(attribute.repr) else attribute.repr
            if attribute.has_default and attribute.init:
                kwargs.append(name)
            elif (attribute.delegated and attribute.init_as is None) or not attribute.init:
                delegated.append(name)
            elif cls.__kw_only__:
                kwargs.append(name)
            else:
                args.append(name)

        parts = []
        for name, value in ((n, values[n]) for n in args if n in values):
            parts.append(reprs[name](value))
        for name, value in ((n, values[n]) for n in kwargs if n in values):
            parts.append("{}={}".format(translations[name], reprs[name](value)))
        for name, value in ((n, values[n]) for n in delegated if n in values):
            parts.append("<{}={}>".format(translations[name], reprs[name](value)))

        return "{}({})".format(cls.__qualname__, ", ".join(parts))

    @abstract
    def _do_init(self, initial_values):
        # type: (mapping_proxy.MappingProxyType[str, Any]) -> None
        """
        Initialize attribute values (internal).

        :param initial_values: Initial values.
        """
        raise NotImplementedError()

    @classmethod
    @abstract
    def _do_deserialize(cls, values):
        # type: (Type[S], mapping_proxy.MappingProxyType[str, Any]) -> S
        """
        Deserialize (internal).

        :param values: Deserialized values.
        :return: Structure.
        :raises SerializationError: Error while deserializing.
        """
        raise NotImplementedError()

    def serialize(self):
        # type: () -> dict[str, Any]
        """
        Serialize.

        :return: Serialized dictionary.
        :raises SerializationError: Error while serializing.
        """
        cls = type(self)
        serialized = {}  # type: dict[str, Any]
        for name, value in self:
            attribute = cls.__attribute_map__[name]
            if attribute.serializable:
                if not attribute.serialize_default and value == attribute.default:
                    continue

                if isinstance(attribute.serialize_as, cls.__attribute_type__):
                    serialized_name = attribute.serialize_as.name
                elif isinstance(attribute.serialize_as, six.string_types):
                    serialized_name = attribute.serialize_as
                else:
                    serialized_name = name

                serialized_value = attribute.relationship.serialize_value(value)
                if serialized_value is not MISSING:
                    assert serialized_name is not None
                    serialized[serialized_name] = serialized_value
        return serialized

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[S], Mapping[str, Any]) -> S
        """
        Deserialize.

        :param serialized: Serialized dictionary.
        :return: Structure.
        :raises SerializationError: Error while deserializing.
        """
        values = {}  # type: dict[str, Any]
        for serialized_name, serialized in six.iteritems(serialized):
            name = cls.__deserialization_map__[serialized_name]
            attribute = cls.__attribute_map__[name]
            if attribute.delegated and attribute.serializable and attribute.fset is None:
                continue
            values[name] = attribute.relationship.deserialize_value(serialized)
        values = cls.__attribute_map__.get_initial_values(
            (),
            values,
            init_property="serializable",
            init_method="deserialize",
        )
        self = cls._do_deserialize(mapping_proxy.MappingProxyType(values))
        self.__post_deserialize__()
        return self


S = TypeVar("S", bound=Structure)  # structure self type


class UserStructure(Structure, BaseUserStructure):
    """User attribute class structure."""

    __slots__ = ()

    @final
    def _discard(self, name):
        # type: (US, str) -> US
        """
        Discard attribute value if it's set.

        :param name: Attribute name.
        :return: Transformed (immutable) or self (mutable).
        """
        if name in self:
            return self._update({name: DELETED})
        else:
            return self

    @final
    def _delete(self, name):
        # type: (US, str) -> US
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed (immutable) or self (mutable).
        :raises KeyError: Key is not present.
        """
        return self._update({name: DELETED})

    @final
    def _set(self, name, value):
        # type: (US, str, Any) -> US
        """
        Set value for attribute.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._update({name: value})

    @abstract
    def _do_update(
        self,
        inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        deletes,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_old,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_new,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_and_inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        all_updates,  # type: mapping_proxy.MappingProxyType[str, Any]
    ):
        # type: (...) -> None
        """
        Update attribute values (internal).

        :param inserts: Keys and values being inserted.
        :param deletes: Keys and values being deleted.
        :param updates_old: Keys and values being updated (old values).
        :param updates_new: Keys and values being updated (new values).
        :param updates_and_inserts: Keys and values being updated or inserted.
        :param all_updates: All updates.
        """
        raise NotImplementedError()

    @overload
    def _update(self, __m, **kwargs):
        # type: (US, SupportsKeysAndGetItem[str, Any], **Any) -> US
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (US, Iterable[tuple[str, Any]], **Any) -> US
        pass

    @overload
    def _update(self, **kwargs):
        # type: (US, **Any) -> US
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed (immutable) or self (mutable).
        """
        try:
            new_values, old_values = type(self).__attribute_map__.get_update_values(dict(*args, **kwargs), self)
        except (ProcessingError, TypeError, ValueError) as e:
            exc = type(e)(e)
            six.raise_from(exc, None)
            raise exc

        # Compile inserts, deletes, updates.
        inserts = {}
        deletes = {}
        updates_old = {}
        updates_new = {}
        updates_and_inserts = {}
        all_updates = new_values
        for name, value in six.iteritems(new_values):
            if name in old_values:
                updates_new[name] = value
                updates_old[name] = old_values[name]
            else:
                inserts[name] = value
            updates_and_inserts[name] = value
        for name, value in six.iteritems(old_values):
            if name not in new_values:
                deletes[name] = value

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


US = TypeVar("US", bound=UserStructure)  # user structure self type


# noinspection PyAbstractClass
class ImmutableStructure(Structure, BaseImmutableStructure):
    """Immutable attribute class structure."""

    __slots__ = ()

    @final
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        cls = type(self)

        # Get hashable attributes.
        attributes = [n for n, a in cls.__attribute_map__.ordered_items() if a.hash]

        # Hash out a tuple containing the class + names and values.
        hash_values = (type(self),) + tuple((n, self._get(n)) for n in attributes if n in self)
        return hash(hash_values)


IS = TypeVar("IS", bound=ImmutableStructure)  # immutable structure self type


# noinspection PyAbstractClass
class UserImmutableStructure(ImmutableStructure, UserStructure, BaseUserImmutableStructure):
    """User immutable attribute class structure."""

    __slots__ = ()

    @final
    def discard(self, name):
        # type: (UIS, str) -> UIS
        """
        Discard attribute value if it's set.

        :param name: Attribute name.
        :return: Transformed.
        """
        return self._discard(name)

    @final
    def delete(self, name):
        # type: (UIS, str) -> UIS
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._delete(name)

    @final
    def set(self, name, value):
        # type: (UIS, str, Any) -> UIS
        """
        Set value for attribute.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (UIS, SupportsKeysAndGetItem[str, Any], **Any) -> UIS
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (UIS, Iterable[tuple[str, Any]], **Any) -> UIS
        pass

    @overload
    def update(self, **kwargs):
        # type: (UIS, **Any) -> UIS
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        return self._update(*args, **kwargs)


UIS = TypeVar("UIS", bound=UserImmutableStructure)  # user immutable structure self type


# noinspection PyAbstractClass
class MutableStructure(Structure, BaseMutableStructure):
    """Mutable attribute class structure."""

    __slots__ = ()
    __attribute_type__ = MutableAttribute  # type: Type[MutableAttribute[Any]]
    __attribute_map__ = AttributeMap()  # type: AttributeMap[str, MutableAttribute[Any]]


MS = TypeVar("MS", bound=MutableStructure)  # mutable structure self type


# noinspection PyAbstractClass
class UserMutableStructure(MutableStructure, UserStructure, BaseUserMutableStructure):
    """User mutable attribute class structure."""

    __slots__ = ()

    @final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Attribute value.
        """
        self._update({name: value})

    @final
    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        """
        self._update({name: DELETED})

    @final
    def discard(self, name):
        # type: (str) -> None
        """
        Discard attribute value if it's set.

        :param name: Attribute name.
        :return: Transformed.
        """
        self._discard(name)

    @final
    def delete(self, name):
        # type: (str) -> None
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self._delete(name)

    @final
    def set(self, name, value):
        # type: (str, Any) -> None
        """
        Set value for attribute.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**Any) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        self._update(*args, **kwargs)


UMS = TypeVar("UMS", bound=UserMutableStructure)  # user mutable structure self type

"""Attribute class structures."""

import collections
import contextlib
import operator
import weakref

import six
import slotted
from basicco import (
    SlottedBase,
    custom_repr,
    get_mro,
    mapping_proxy,
    recursive_repr,
    safe_repr,
)
from basicco.abstract_class import abstract
from basicco.namespace import Namespace
from basicco.runtime_final import final
from tippo import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Mapping,
    SupportsKeysAndGetItem,
    Type,
    TypeVar,
    cast,
    overload,
)

from ._attribute import Attribute, MutableAttribute
from ._bases import (
    BaseImmutableStructure,
    BaseMutableStructure,
    BaseProxyImmutableStructure,
    BaseProxyMutableStructure,
    BaseProxyStructure,
    BaseProxyUserImmutableStructure,
    BaseProxyUserMutableStructure,
    BaseProxyUserStructure,
    BaseStructure,
    BaseStructureMeta,
    BaseUserImmutableStructure,
    BaseUserMutableStructure,
    BaseUserStructure,
)
from .constants import DEFAULT, DELETED, MISSING
from .exceptions import ProcessingError, SerializationError

KT_str = TypeVar("KT_str", bound=str)
AT_co = TypeVar("AT_co", bound=Attribute, covariant=True)


@final
class AttributeMap(SlottedBase, slotted.SlottedHashable, slotted.SlottedMapping[KT_str, AT_co]):
    """Maps attributes by name."""

    __slots__ = ("__attribute_dict",)

    @overload
    def __init__(self, ordered_attributes):
        # type: (collections.OrderedDict[str, AT_co]) -> None
        pass

    @overload
    def __init__(self, ordered_attributes=()):
        # type: (Iterable[tuple[str, AT_co]]) -> None
        pass

    def __init__(self, ordered_attributes=()):
        # type: (collections.OrderedDict[str, AT_co] | Iterable[tuple[str, AT_co]]) -> None
        """
        :param ordered_attributes: Ordered attributes (ordered dict or items).
        """
        if isinstance(ordered_attributes, collections.OrderedDict):
            self.__attribute_dict = ordered_attributes  # type: collections.OrderedDict[str, AT_co]
        else:
            self.__attribute_dict = collections.OrderedDict()
            for name, attribute in ordered_attributes:
                self.__attribute_dict[name] = attribute

    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        return "{}({})".format(type(self).__name__, custom_repr.iterable_repr(self.items()))

    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    def __getitem__(self, name):
        # type: (str) -> AT_co
        return self.__attribute_dict[name]

    def __contains__(self, name):
        # type: (object) -> bool
        return name in self.__attribute_dict

    def __len__(self):
        # type: () -> int
        return len(self.__attribute_dict)

    def __iter__(self):
        # type: () -> Iterator[KT_str]
        for name in self.__attribute_dict:
            yield cast(KT_str, name)

    def get_initial_values(self, args, kwargs, init_property="init", init_method="__init__"):
        # type: (tuple, dict[str, Any], str, str) -> dict[str, Any]
        """
        Get initial/deserialized attribute values.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :param init_property: Which boolean attribute property to use when considering it a `init` attribute.
        :param init_method: The name of the initialization method receiving the values.
        :return: Initial attribute values.
        """

        # Go through each attribute.
        i = 0
        reached_kwargs = False
        required_names = set()
        constant_names = set()
        initial_values = {}  # type: dict[str, Any]
        for name, attribute in six.iteritems(self):

            # Keep track of required attribute names.
            if attribute.required:
                required_names.add(name)

            # Skip non-init attributes.
            if not getattr(attribute, init_property):

                # Can't get its value from the init method.
                if name in kwargs:
                    error = "attribute {!r} is not supported by the {!r} method".format(name, init_method)
                    raise TypeError(error)

                if attribute.has_default:

                    # Default value.
                    if attribute.constant:
                        constant_names.add(name)
                        initial_values[name] = attribute.default
                    else:
                        initial_values[name] = attribute.get_default_value()

                continue

            # Get value for positional argument.
            if not reached_kwargs:
                try:
                    value = args[i]
                except IndexError:
                    reached_kwargs = True
                else:
                    if value is DEFAULT:
                        if attribute.has_default:
                            value = attribute.get_default_value()
                        else:
                            error = "missing value for attribute {!r}".format(name)
                            raise ValueError(error)
                    i += 1
                    initial_values[name] = value
                    continue

            # Get value for keyword argument.
            try:
                value = kwargs[name]
                if value is DEFAULT:
                    raise KeyError()
            except KeyError:
                if attribute.has_default:
                    value = attribute.get_default_value()
                else:
                    continue

            # Set attribute value.
            initial_values[name] = value

        # Invalid kwargs.
        invalid_kwargs = set(kwargs).difference(self)
        if invalid_kwargs:
            error = "invalid keyword argument(s) {}".format(", ".join(repr(k) for k in invalid_kwargs))
            raise TypeError(error)

        # Invalid positional arguments.
        invalid_args = args[i:]
        if invalid_args:
            error = "invalid additional positional argument value(s) {}".format(
                ", ".join(repr(p) for p in invalid_args)
            )
            raise TypeError(error)

        # Compile updates.
        initial_values, _ = self.get_update_values(initial_values)

        # Remove constant values.
        for constant_name in constant_names:
            del initial_values[constant_name]

        # Check for required attributes.
        missing = required_names.difference(initial_values)
        if missing:
            sorted_missing = [n for n in self if n in missing]
            error = "missing values for required attributes {}".format(", ".join(repr(k) for k in sorted_missing))
            raise RuntimeError(error)

        return initial_values

    def get_update_values(self, updates, structure=None):
        # type: (Mapping[str, Any], Structure | None) -> tuple[dict[str, Any], dict[str, Any]]
        """
        Get values for an update.

        :param updates: Updated values.
        :param structure: Structure that owns attributes.
        :return: New values and old values.
        """

        # Compile update values.
        delegate_self = _DelegateSelf(self, structure)
        sorting_key = lambda i: len(self[i[0]].recursive_dependencies)
        for name, value in sorted(six.iteritems(updates), key=sorting_key, reverse=True):
            setattr(delegate_self, name, value)
        new_values, old_values = delegate_self.__.get_results()

        # Ensure no required attributes are being deleted.
        for name, value in six.iteritems(new_values):
            if value is DELETED and self[name].required:
                error = "can't delete required attribute {!r}".format(name)
                raise AttributeError(error)

        return new_values, old_values


class StructureMeta(BaseStructureMeta):
    """Metaclass for :class:`Structure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        # type: (...) -> StructureMeta

        # Get/set attribute type for this class.
        dct = dict(dct)
        attribute_type = dct["__attribute_type__"] = dct.get("__kwargs__", {}).get(
            "attribute_type", kwargs.get("attribute_type", dct.get("__attribute_type__", Attribute))
        )

        # Scrape bases for attributes.
        base_attributes = {}  # type: dict[str, Attribute]
        counter = {}  # type: dict[str, int]
        for base in reversed(get_mro.preview_mro(*bases)):
            if base is object:
                continue

            # Prevent overriding attributes with non-attributes.
            for attribute_name in base_attributes:
                if (isinstance(base, StructureMeta) and attribute_name not in base.__attributes__) or (
                    hasattr(base, attribute_name) and not isinstance(getattr(base, attribute_name), attribute_type)
                ):
                    error = "{!r} overrides {!r} attribute with {!r} object, expected {!r}".format(
                        base.__name__,
                        attribute_name,
                        type(getattr(base, attribute_name)).__name__,
                        attribute_type.__name__,
                    )
                    raise TypeError(error)

            # Collect base's attributes.
            if isinstance(base, StructureMeta):
                for attribute_name, attribute in six.iteritems(base.__attributes__):

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
        for attribute_name, attribute in six.iteritems(attribute_map):

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

        # Store attribute map, attribute namespace, and deserialization map.
        type.__setattr__(cls, "__attributes__", attribute_map)
        type.__setattr__(cls, "__attrs__", Namespace(attribute_map))
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

    __attributes__ = AttributeMap()  # type: AttributeMap[str, Attribute[Any]]
    __attrs__ = Namespace()  # type: Namespace[Attribute[Any]]
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
        kwargs = dict((cls.__initialization_map__[n], v) for n, v in six.iteritems(kwargs))

        # Initialize attribute values.
        try:
            initial_values = cls.__attributes__.get_initial_values(
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

    def __order__(self, other, func):
        # type: (object, Callable[[Any, Any], bool]) -> bool

        # Require the exact same type for comparison.
        cls = type(self)
        if cls is not type(other):
            return NotImplemented
        assert isinstance(other, type(self))

        # Get attributes to compare.
        attributes = [n for n, a in six.iteritems(cls.__attributes__) if a.order]
        if not attributes:
            return NotImplemented

        # Compare values.
        order_values = tuple(self[n] for n in attributes if n in self)
        other_order_values = tuple(other[n] for n in attributes if n in other)
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

    @abstract
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute.

        :param name: Attribute name.
        :return: Attribute value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        raise NotImplementedError()

    @abstract
    def __contains__(self, name):
        # type: (object) -> bool
        """
        Get whether there's a value for attribute.

        :param name: Attribute name.
        :return: True if has value.
        """
        raise NotImplementedError()

    @final
    def __iter__(self):
        # type: () -> Iterator[tuple[str, Any]]
        """
        Iterate over attribute items (name, value).

        :return: Attribute item iterator.
        """
        for name in type(self).__attributes__:
            if name in self:
                yield name, self[name]

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
        attributes = [n for n, a in six.iteritems(cls.__attributes__) if a.eq]

        # Compare values.
        eq_values = dict((n, self[n]) for n in attributes if n in self)
        other_eq_values = dict((n, other[n]) for n in attributes if n in other)
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
        for name, attribute in six.iteritems(cls.__attributes__):
            if not attribute.repr:
                continue

            if isinstance(attribute.init_as, cls.__attribute_type__):
                assert attribute.init_as.name is not None
                name = attribute.init_as.name
            elif isinstance(attribute.init_as, six.string_types):
                name = attribute.init_as

            reprs[name] = repr if not callable(attribute.repr) else attribute.repr
            if attribute.has_default:
                kwargs.append(name)
            elif attribute.delegated and attribute.init_as is None:
                delegated.append(name)
            elif cls.__kw_only__:
                kwargs.append(name)
            else:
                args.append(name)

        parts = []
        for name, value in six.iteritems(dict((n, self[n]) for n in args if n in self)):
            parts.append(reprs[name](value))
        for name, value in six.iteritems(dict((n, self[n]) for n in kwargs if n in self)):
            parts.append("{}={}".format(name, reprs[name](value)))
        for name, value in six.iteritems(dict((n, self[n]) for n in delegated if n in self)):
            parts.append("<{}={}>".format(name, reprs[name](value)))

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
            attribute = cls.__attributes__[name]
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
            attribute = cls.__attributes__[name]
            values[name] = attribute.relationship.deserialize_value(serialized)
        values = cls.__attributes__.get_initial_values(
            (),
            values,
            init_property="serializable",
            init_method="deserialize",
        )
        return cls._do_deserialize(mapping_proxy.MappingProxyType(values))


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
        self,  # type: US
        inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        deletes,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_old,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_new,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_and_inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        all_updates,  # type: mapping_proxy.MappingProxyType[str, Any]
    ):
        # type: (...) -> US
        """
        Update attribute values (internal).

        :param inserts: Keys and values being inserted.
        :param deletes: Keys and values being deleted.
        :param updates_old: Keys and values being updated (old values).
        :param updates_new: Keys and values being updated (new values).
        :param updates_and_inserts: Keys and values being updated or inserted.
        :param all_updates: All updates.
        :return: Transformed (immutable) or self (mutable).
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
            new_values, old_values = type(self).__attributes__.get_update_values(dict(*args, **kwargs), self)
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

        return self._do_update(
            mapping_proxy.MappingProxyType(inserts),
            mapping_proxy.MappingProxyType(deletes),
            mapping_proxy.MappingProxyType(updates_old),
            mapping_proxy.MappingProxyType(updates_new),
            mapping_proxy.MappingProxyType(updates_and_inserts),
            mapping_proxy.MappingProxyType(all_updates),
        )


US = TypeVar("US", bound=UserStructure)  # user structure self type


class ProxyStructureMeta(StructureMeta):
    """Metaclass for :class:`ProxyStructure`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        cls = super(ProxyStructureMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)
        delegated_attribute_names = [n for n, a in six.iteritems(cls.__attributes__) if a.delegated]
        if delegated_attribute_names:
            error = "proxy class {!r} can't have delegated attributes {}".format(
                name, ", ".join(repr(n) for n in delegated_attribute_names)
            )
            raise TypeError(error)
        return cls


# noinspection PyAbstractClass
class ProxyStructure(six.with_metaclass(ProxyStructureMeta, BaseProxyStructure[S], Structure)):
    """Proxy attribute class structure."""

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (S) -> None
        """
        :param wrapped: Structure to wrap.
        """

        # Check for attribute inconsistencies.
        for attribute_name, attribute in six.iteritems(type(wrapped).__attributes__):
            try:
                proxy_attribute = type(self).__attributes__[attribute_name]
            except KeyError:
                continue

            # Required.
            if proxy_attribute.required and not attribute.required:
                error = "'{}.{}' attribute is required but '{}.{}' is not".format(
                    type(self).__name__, attribute_name, type(wrapped).__name__, attribute_name
                )
                raise TypeError(error)

        super(ProxyStructure, self).__init__(wrapped)

    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute.

        :param name: Attribute name.
        :return: Attribute value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        return self._wrapped[name]

    def __contains__(self, name):
        # type: (object) -> bool
        """
        Get whether there's a value for attribute.

        :param name: Attribute name.
        :return: True if has value.
        """
        return name in self._wrapped

    @classmethod
    def _do_deserialize(cls, values):  # noqa
        """
        Deserialize (internal).

        :param values: Deserialized values.
        :return: Set structure.
        :raises SerializationError: Error while deserializing.
        """
        error = "can't deserialize proxy object {!r}".format(cls.__name__)
        raise SerializationError(error)

    def _do_init(self, initial_values):
        # type: (mapping_proxy.MappingProxyType[str, Any]) -> None
        """
        Initialize attribute values (internal).

        :param initial_values: Initial values.
        """
        error = "{!r} object already initialized".format(type(self).__name__)
        raise RuntimeError(error)


PS = TypeVar("PS", bound=ProxyStructure)  # proxy structure self type


# noinspection PyAbstractClass
class ProxyUserStructure(ProxyStructure[US], BaseProxyUserStructure[US], UserStructure):
    """Proxy user structure."""

    __slots__ = ()


PUS = TypeVar("PUS", bound=ProxyUserStructure)  # proxy user structure self type


# noinspection PyAbstractClass
class ImmutableStructure(Structure, BaseImmutableStructure):
    """Immutable attribute class structure."""

    __slots__ = ()

    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        cls = type(self)

        # Get hashable attributes.
        attributes = [n for n, a in six.iteritems(cls.__attributes__) if a.hash]

        # Hash out a tuple containing the class + names and values.
        hash_values = (type(self),) + tuple((n, self[n]) for n in attributes if n in self)
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
        """."""

    @overload
    def update(self, __m, **kwargs):
        # type: (UIS, Iterable[tuple[str, Any]], **Any) -> UIS
        """."""

    @overload
    def update(self, **kwargs):
        # type: (UIS, **Any) -> UIS
        """."""

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
class ProxyImmutableStructure(
    ProxyStructure[IS],
    BaseProxyImmutableStructure[IS],
    ImmutableStructure,
):
    """Proxy immutable class structure."""

    __slots__ = ()


PIS = TypeVar("PIS", bound=ProxyImmutableStructure)  # proxy immutable class structure self type


class ProxyUserImmutableStructure(
    ProxyImmutableStructure[UIS],
    BaseProxyUserImmutableStructure[UIS],
    UserImmutableStructure,
):
    """Proxy user immutable class structure."""

    __slots__ = ()

    def _do_update(
        self,  # type: PUIS
        inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        deletes,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_old,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_new,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_and_inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        all_updates,  # type: mapping_proxy.MappingProxyType[str, Any]
    ):
        # type: (...) -> PUIS
        """
        Update attribute values (internal).

        :param inserts: Keys and values being inserted.
        :param deletes: Keys and values being deleted.
        :param updates_old: Keys and values being updated (old values).
        :param updates_new: Keys and values being updated (new values).
        :param updates_and_inserts: Keys and values being updated or inserted.
        :param all_updates: All updates.
        :return: Transformed.
        """
        return type(self)(self._wrapped.update(all_updates))


PUIS = TypeVar("PUIS", bound=ProxyUserImmutableStructure)  # proxy user immutable class structure self type


# noinspection PyAbstractClass
class MutableStructure(Structure, BaseMutableStructure):
    """Mutable attribute class structure."""

    __slots__ = ()


MS = TypeVar("MS", bound=MutableStructure)  # mutable structure self type


# noinspection PyAbstractClass
class UserMutableStructure(MutableStructure, UserStructure, BaseUserMutableStructure):
    """User mutable attribute class structure."""

    __slots__ = ()
    __attribute_type__ = MutableAttribute  # type: Type[MutableAttribute[Any]]
    __attributes__ = AttributeMap()  # type: AttributeMap[str, MutableAttribute[Any]]

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
        """
        self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        """."""

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        """."""

    @overload
    def update(self, **kwargs):
        # type: (**Any) -> None
        """."""

    @final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        self._update(*args, **kwargs)


UMS = TypeVar("UMS", bound=UserMutableStructure)  # user mutable structure self type


# noinspection PyAbstractClass
class ProxyMutableStructure(
    ProxyStructure[MS],
    BaseProxyMutableStructure[MS],
    MutableStructure,
):
    """Proxy mutable class structure."""

    __slots__ = ()


PMS = TypeVar("PMS", bound=ProxyMutableStructure)  # proxy mutable class structure self type


class ProxyUserMutableStructure(
    ProxyMutableStructure[UMS],
    BaseProxyUserMutableStructure[UMS],
    UserMutableStructure,
):
    """Proxy user mutable class structure."""

    __slots__ = ()

    def _do_update(
        self,  # type: PUMS
        inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        deletes,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_old,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_new,  # type: mapping_proxy.MappingProxyType[str, Any]
        updates_and_inserts,  # type: mapping_proxy.MappingProxyType[str, Any]
        all_updates,  # type: mapping_proxy.MappingProxyType[str, Any]
    ):
        # type: (...) -> PUMS
        """
        Update attribute values (internal).

        :param inserts: Keys and values being inserted.
        :param deletes: Keys and values being deleted.
        :param updates_old: Keys and values being updated (old values).
        :param updates_new: Keys and values being updated (new values).
        :param updates_and_inserts: Keys and values being updated or inserted.
        :param all_updates: All updates.
        :return: Self.
        """
        self._wrapped.update(all_updates)
        return self


PUMS = TypeVar("PUMS", bound=ProxyUserMutableStructure)  # proxy user mutable class structure self type


@final
class _DelegateSelf(SlottedBase):
    """Intermediary `self` object provided to delegates."""

    __slots__ = ("__",)

    def __init__(self, attribute_map, structure=None):
        # type: (AttributeMap, Structure | None) -> None
        """
        :param attribute_map: Attribute map.
        :param structure: Structure that owns attributes.
        """
        internals = _DelegateSelfInternals(self, attribute_map, structure)
        object.__setattr__(self, "__", internals)

    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    def __dir__(self):
        # type: () -> list[str]
        """
        Get attribute names.

        :return: Attribute names.
        """
        if self.__.in_getter is not None:
            attribute = self.__.in_getter
            return sorted(n for n, a in six.iteritems(self.__.attribute_map) if a is attribute or a in a.dependencies)
        return sorted(self.__.attribute_map)

    def __getattr__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.
        :param name: Attribute name.
        :return: Value.
        """
        if name != "__" and name in self.__.attribute_map:
            return self[name]
        else:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.
        :param name: Attribute name.
        :param value: Value.
        """
        if name in self.__.attribute_map:
            self[name] = value
        else:
            super(_DelegateSelf, self).__setattr__(name, value)

    def __delattr__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.
        :param name: Attribute name.
        """
        if name in self.__.attribute_map:
            del self[name]
        else:
            super(_DelegateSelf, self).__delattr__(name)

    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.
        :param name: Attribute name.
        :return: Value.
        """
        return self.__.get_value(name)

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.
        :param name: Attribute name.
        :param value: Value.
        """
        self.__.set_value(name, value)

    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.
        :param name: Attribute name.
        """
        self.__.delete_value(name)


@final
class _DelegateSelfInternals(SlottedBase):
    """Internals for :class:`DelegateSelf`."""

    __slots__ = (
        "__delegate_self_ref",
        "__attribute_map",
        "__structure",
        "__dependencies",
        "__in_getter",
        "__new_values",
        "__old_values",
        "__dirty",
    )

    def __init__(self, delegate_self, attribute_map, structure):
        # type: (_DelegateSelf, AttributeMap, Structure | None) -> None
        """
        :param delegate_self: Internal object.
        :param attribute_map: Attribute map.
        :param structure: Structure that owns attributes.
        """
        self.__delegate_self_ref = weakref.ref(delegate_self)
        self.__attribute_map = attribute_map
        self.__structure = structure
        self.__dependencies = None  # type: tuple[Attribute, ...] | None
        self.__in_getter = None  # type: Attribute | None
        self.__new_values = {}  # type: dict[str, Any]
        self.__old_values = {}  # type: dict[str, Any]
        self.__dirty = set(attribute_map).difference(
            (list(zip(*(list(structure or [])))) or [[], []])[0]
        )  # type: set[str]

    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    def get_value(self, name):
        """
        Get current value for attribute.

        :param name: Attribute name.
        :return: Value.
        :raises NameError: Can't access attribute not declared as dependency.
        :raises AttributeError: Attribute has no value.
        """
        attribute = self.__get_attribute(name)
        if self.__dependencies is not None and attribute not in self.__dependencies:
            error = (
                "can't access {!r} attribute from {!r} getter delegate since it was " "not declared as a dependency"
            ).format(name, self.__in_getter.name)
            raise NameError(error)

        if name in self.__dirty:
            value = MISSING
        else:
            try:
                value = self.__new_values[name]
            except KeyError:
                try:
                    if self.__structure is None:
                        raise KeyError()
                    value = self.__structure[name]
                except KeyError:
                    value = MISSING

        if value in (MISSING, DELETED):
            if attribute.delegated:
                with self.__getter_context(attribute):
                    value = attribute.fget(self.delegate_self)
                try:
                    value = attribute.process_value(value, name)
                except (ProcessingError, TypeError, ValueError) as e:
                    exc = type(e)(e)
                    six.raise_from(exc, None)
                    raise exc
                self.__set_new_value(name, value)
                return value
            else:
                error = "attribute {!r} has no value".format(name)
                raise AttributeError(error)
        else:
            return value

    def set_value(self, name, value, process=True):
        # type: (str, Any, bool) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :param process: Whether to process value or not.
        :raises AttributeError: Can't set attributes while running getter delegate.
        :raises AttributeError: Attribute is read-only.
        :raises AttributeError: Attribute already has a value and can't be changed.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """

        if value is DELETED:
            self.delete_value(name)
            return

        if self.__in_getter is not None:
            error = "can't set attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.settable:
            if attribute.delegated:
                error = "attribute {!r} is read-only".format(name)
                raise AttributeError(error)
            try:
                self.get_value(name)
            except AttributeError:
                pass
            else:
                error = "attribute {!r} already has a value and can't be changed".format(name)
                raise AttributeError(error)

        if process:
            try:
                value = attribute.process_value(value, name)
            except (ProcessingError, TypeError, ValueError) as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        if attribute.delegated:
            attribute.fset(self.delegate_self, value)
        else:
            self.__set_new_value(name, value)

    def delete_value(self, name):
        """
        Delete attribute.

        :param name: Attribute name.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """
        if self.__in_getter is not None:
            error = "can't delete attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.deletable:
            error = "attribute {!r} is not deletable".format(name)
            raise AttributeError(error)

        if attribute.delegated:
            attribute.fdel(self.delegate_self)
        else:
            self.get_value(name)  # will error if it has no value, which we want
            self.__set_new_value(name, DELETED)

    @contextlib.contextmanager
    def __getter_context(self, attribute):
        # type: (Attribute) -> Iterator
        """
        Getter context.

        :param attribute: Attribute.
        :return: Getter context manager.
        """
        before = self.__in_getter
        before_dependencies = self.__dependencies

        self.__in_getter = attribute
        if attribute.delegated:
            self.__dependencies = attribute.dependencies
        else:
            self.__dependencies = None

        try:
            yield
        finally:
            self.__in_getter = before
            self.__dependencies = before_dependencies

    def __set_new_value(self, name, value):
        # type: (str, Any) -> None
        """
        Set new attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        try:
            if self.__structure is None:
                raise KeyError()
            old_value = self.__structure[name]
        except KeyError:
            old_value = DELETED

        if value is not old_value:
            self.__old_values[name] = old_value
            self.__new_values[name] = value
        else:
            self.__old_values.pop(name, None)
            self.__new_values.pop(name, None)

        self.__dirty.discard(name)
        for dependent in self.__attribute_map[name].recursive_dependents:
            self.__dirty.add(dependent.name)
            try:
                if self.__structure is None:
                    raise KeyError()
                old_value = self.__structure[dependent.name]
            except KeyError:
                self.__new_values.pop(dependent.name, None)
                self.__old_values.pop(dependent.name, None)
            else:
                self.__old_values[dependent.name] = old_value
                self.__new_values[dependent.name] = DELETED

    def __get_attribute(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        :raises AttributeError: Has no such attribute.
        """
        try:
            return self.__attribute_map[name]
        except KeyError:
            pass
        error = "no attribute named {!r}".format(name)
        raise AttributeError(error)

    def get_results(self):
        # type: () -> tuple[dict[str, Any], dict[str, Any]]
        """
        Get results.

        :return: New values, old values.
        """
        sorted_dirty = sorted(
            self.__dirty,
            key=lambda n: len(self.__attribute_map[n].recursive_dependencies),
        )
        failed = set()
        success = set()
        for name in sorted_dirty:
            try:
                self.get_value(name)
            except AttributeError:
                failed.add(name)
            else:
                success.add(name)

        new_values = self.__new_values.copy()
        old_values = self.__old_values.copy()

        return new_values, old_values

    @property
    def delegate_self(self):
        # type: () -> _DelegateSelf | None
        """Delegate self."""
        return self.__delegate_self_ref()

    @property
    def attribute_map(self):
        # type: () -> AttributeMap
        """AttributeMap."""
        return self.__attribute_map

    @property
    def structure(self):
        # type: () -> Structure | None
        """Structure that owns attributes."""
        return self.__structure

    @property
    def in_getter(self):
        # type: () -> Attribute | None
        """Whether running in an attribute's getter delegate."""
        return self.__in_getter

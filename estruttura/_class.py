import abc
import collections

import six
from basicco import custom_repr, runtime_final, recursive_repr, fabricate_value
from tippo import Any, Callable, TypeVar, Iterable, Generic, TypeAlias, Type, Tuple, overload, cast

from ._constants import SupportsKeysAndGetItem, MissingType, MISSING, DELETED, DEFAULT
from ._dict import BaseDict
from ._bases import BaseMeta, Base, BaseHashable, Relationship
from ._make import make_method, generate_unique_filename


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias

_attribute_counter = 0


class Attribute(BaseHashable, Generic[T_co]):
    """Attribute descriptor."""

    __slots__ = (
        "_owner",
        "_name",
        "_default",
        "_factory",
        "_init",
        "_required",
        "_repr",
        "_eq",
        "_hash",
        "_relationship",
        "_metadata",
        "_extra_paths",
        "_builtin_paths",
        "_order",
    )

    def __init__(
        self,
        default=MISSING,  # type: Any
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        init=True,  # type: bool
        required=True,  # type: bool
        repr=True,  # type: bool
        eq=True,  # type: bool
        hash=None,  # type: bool | None
        relationship=None,  # type: Relationship | None
        metadata=None,  # type: Any
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        global _attribute_counter

        # Ensure single default source.
        if default is not MISSING and factory is not MISSING:
            error = "can't declare both 'default' and 'factory'"
            raise ValueError(error)

        # Ensure safe hash.
        if hash is None:
            hash = eq
        if hash and not eq:
            error = "can't contribute to the hash if it's not contributing to the eq"
            raise ValueError(error)

        # Set attributes.
        self._owner = None  # type: Type[BaseClass] | None
        self._name = None  # type: str | None
        self._default = default
        self._factory = factory
        self._init = bool(init)
        self._required = bool(required)
        self._repr = bool(repr)
        self._eq = bool(eq)
        self._hash = bool(hash)
        self._relationship = relationship
        self._metadata = metadata
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

        # Increment order counter.
        _attribute_counter += 1
        self._order = _attribute_counter

    def __hash__(self):
        return hash(self.to_items())

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.to_items() == other.to_items()

    @recursive_repr.recursive_repr
    def __repr__(self):
        items = self.to_items()
        return custom_repr.mapping_repr(
            mapping=dict(items),
            prefix="{}(".format(type(self).__fullname__),
            template="{key}={value}",
            separator=", ",
            suffix=")",
            sorting=True,
            sort_key=lambda i, _s=self, _i=items: next(iter(zip(*_i))).index(i[0]),
            key_repr=str,
        )

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, None) -> A
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, Type[BaseClass]) -> A
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseClass, Type[BaseClass]) -> T_co
        pass

    def __get__(self, instance, owner):
        if instance is not None:
            if self.name is None:
                assert self.owner is None
                error = "attribute not named/owned"
                raise RuntimeError(error)
            return instance[self.name]
        return self

    def __set_name__(self, owner, name):
        # type: (Type[BaseClass], str) -> None
        if self._name is not None and self._name != name:
            error = "attribute already named {!r}, can't rename it to {!r}".format(self._name, name)
            raise TypeError(error)
        if self._owner is not None and self._owner is not owner:
            error = "attribute already owned by {!r}, can't be owned by {!r} as well".format(
                self._owner.__name__, owner.__name__
            )
            raise TypeError(error)
        self._owner = owner
        self._name = name

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("name", self.name),
            ("default", self.default),
            ("factory", self.factory),
            ("init", self.init),
            ("required", self.required),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("relationship", self.relationship),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        )

    def to_dict(self):
        # type: () -> dict[str, Any]
        return dict(self.to_items())

    @overload
    def update(self, __m, **kwargs):
        # type: (A, SupportsKeysAndGetItem[str, Any], **Any) -> A
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (A, Iterable[Item], **Any) -> A
        pass

    @overload
    def update(self, **kwargs):
        # type: (A, **Any) -> A
        pass

    def update(self, *args, **kwargs):
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(A, type(self)(**updated_kwargs))

    def get_default_value(self, process=True):
        # type: (bool) -> T_co

        # Get/fabricate default value.
        if self.default is not MISSING:
            default_value = self.default
        elif self.factory is not MISSING:
            default_value = fabricate_value.fabricate_value(
                self.factory,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        else:
            error = "no valid default/factory"
            raise RuntimeError(error)

        # Process value.
        if process:
            default_value = self.process(default_value)

        return default_value

    def process(self, value):
        # type: (Any) -> T
        if self.relationship is not None:
            return self.relationship.process(value)
        return value

    @property
    def name(self):
        # type: () -> str | None
        return self._name

    @property
    def owner(self):
        # type: () -> Type[BaseClass] | None
        return self._owner

    @property
    def default(self):
        # type: () -> Any
        return self._default

    @property
    def factory(self):
        # type: () -> Callable[..., T_co] | str | MissingType
        return self._factory

    @property
    def init(self):
        # type: () -> bool
        """Whether to include in the `__init__` method."""
        return self._init

    @property
    def required(self):
        # type: () -> bool
        return self._init

    @property
    def repr(self):
        # type: () -> bool
        """Whether to include in the `__repr__` method."""
        return self._repr

    @property
    def eq(self):
        # type: () -> bool
        """Whether to include in the `__eq__` method."""
        return self._eq

    @property
    def hash(self):
        # type: () -> bool
        """Whether to include in the `__hash__` method."""
        return self._hash

    @property
    def relationship(self):
        # type: () -> Relationship | None
        return self._relationship

    @property
    def metadata(self):
        # type: () -> Any
        """User metadata."""
        return self._metadata

    @property
    def extra_paths(self):
        # type: () -> tuple[str, ...]
        """Extra module paths in fallback order."""
        return self._extra_paths

    @property
    def builtin_paths(self):
        # type: () -> tuple[str, ...] | None
        """Builtin module paths in fallback order."""
        return self._builtin_paths

    @property
    @runtime_final.final
    def order(self):
        # type: () -> int
        return self._order

    @property
    def has_default(self):
        # type: () -> bool
        return self._default is not MISSING or self._factory is not MISSING


A = TypeVar("A", bound=Attribute)  # attribute type
AT_co = TypeVar("AT_co", bound=Attribute, covariant=True)  # covariant attribute type


class MutableAttribute(Attribute[T]):
    """Mutable attribute descriptor."""

    __slots__ = ()

    def __set__(self, instance, value):
        # type: (BaseMutableClass, T) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        instance[self.name] = value

    def __delete__(self, instance):
        # type: (BaseMutableClass) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        del instance[self.name]


@runtime_final.final
class AttributeMap(BaseDict[str, AT_co]):
    """Maps attributes by name."""

    __slots__ = ("__attribute_dict",)

    def __init__(self, attribute_items=()):
        # type: (Iterable[tuple[str, AT_co]]) -> None
        """
        :param attribute_items: Attribute items (name, attribute).
        """
        self.__attribute_dict = collections.OrderedDict()  # type: collections.OrderedDict[str, AT_co]
        for name, attribute in attribute_items:
            self.__attribute_dict[name] = attribute

    def __repr__(self):
        return "{}({})".format(type(self).__fullname__, custom_repr.iterable_repr(self.items()))

    def __hash__(self):
        return hash(tuple(self.__attribute_dict.items()))

    def __eq__(self, other):
        return isinstance(other, AttributeMap) and self.__attribute_dict == other.__attribute_dict

    def __getitem__(self, name):
        return self.__attribute_dict[name]

    def __contains__(self, name):
        return name in self.__attribute_dict

    def get(self, name, fallback=None):
        return self.__attribute_dict.get(name, fallback)

    def iteritems(self):
        for name, attribute in six.iteritems(self.__attribute_dict):
            yield (name, attribute)

    def iterkeys(self):
        for name in six.iterkeys(self.__attribute_dict):
            yield name

    def itervalues(self):
        for attribute in six.itervalues(self.__attribute_dict):
            yield attribute

    def __len__(self):
        return len(self.__attribute_dict)

    def __iter__(self):
        for name in six.iterkeys(self.__attribute_dict):
            yield name


class AttributeManager(Base, Generic[AT_co]):
    """Manages attribute values."""

    __slots__ = ("__attribute_map",)

    def __init__(self, attribute_map):
        # type: (AttributeMap[AT_co]) -> None
        """
        :param attribute_map: Attributes.
        """
        self.__attribute_map = attribute_map

    def get_initial_values(self, *args, **kwargs):
        # type: (*Any, **Any) -> dict[str, Any]
        """
        Get initial attribute values.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Initial attribute values.
        """

        # Go through each attribute.
        i = 0
        reached_kwargs = False
        internal_attribute_names = set()
        initial_values = {}
        for attribute_name, attribute in six.iteritems(self.attribute_map):

            # Skip non-init attributes.
            if not attribute.init:

                # Can't get its value from the init.
                if attribute_name in kwargs:
                    error = "attribute {!r} can't be set externally".format(attribute_name)
                    raise TypeError(error)

                if attribute.has_default:

                    # Has a default value.
                    value = attribute.get_default_value()
                    initial_values[attribute_name] = value
                    continue

                elif attribute.required:

                    # Keep track of non-init, required attribute names (internal attributes).
                    internal_attribute_names.add(attribute_name)

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
                            value = attribute.get_default_value(process=False)
                        else:
                            error = "attribute {!r} has no default value".format(attribute_name)
                            raise ValueError(error)
                    i += 1
                    initial_values[attribute_name] = attribute.process(value)
                    continue

            # Get value for keyword argument.
            try:
                value = kwargs[attribute_name]
                if value is DEFAULT:
                    raise KeyError()
            except KeyError:
                if attribute.has_default:
                    value = attribute.get_default_value(process=False)
                elif attribute.required:
                    error = "missing value for required attribute {!r}".format(attribute_name)
                    exc = TypeError(error)
                    six.raise_from(exc, None)
                    raise exc
                else:
                    continue

            # Set attribute value.
            initial_values[attribute_name] = attribute.process(value)

        # Invalid kwargs.
        invalid_kwargs = set(kwargs).difference(self.attribute_map)
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

        return initial_values

    @property
    def attribute_map(self):
        # type: () -> AttributeMap[AT_co]
        """Attribute map."""
        return self.__attribute_map


class BaseClassMeta(BaseMeta, type):
    """Metaclass for :class:`BaseClass`."""

    __attribute_type__ = Attribute  # type: Type[Attribute]
    __relationship_type__ = Relationship  # type: Type[Relationship]
    __kw_only__ = False  # type: bool
    __gen_init__ = False  # type: bool

    __attributes = AttributeMap()  # type: AttributeMap

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):

        # Scrape bases.
        attributes = {}  # type: dict[str, Attribute]
        attribute_orders = {}  # type: dict[str, int]
        for base in reversed(bases):

            # Prevent overriding attributes with non-attributes.
            for attribute_name in attributes:
                if (isinstance(base, BaseClassMeta) and attribute_name not in base.__attributes__) or (
                    hasattr(base, attribute_name)
                    and not isinstance(getattr(base, attribute_name), mcs.__attribute_type__)
                ):
                    error = "{!r} overrides {!r} attribute with non attribute {!r} object".format(
                        base.__name__,
                        attribute_name,
                        type(getattr(base, attribute_name)).__name__,
                    )
                    raise TypeError(error)

            # Collect base's attributes.
            if isinstance(base, BaseClassMeta):
                for attribute_name, attribute in six.iteritems(base.__attributes__):

                    # Attribute type changed and it's not compatible anymore.
                    if not isinstance(attribute, mcs.__attribute_type__):
                        error = (
                            "metaclass {!r} for class {!r} defines '__attribute_type__' as {!r}, "
                            "but base {!r} utilizes {!r}"
                        ).format(
                            mcs.__name__,
                            name,
                            mcs.__attribute_type__.__name__,
                            base.__fullname__,
                            base.__attribute_type__,
                        )
                        raise TypeError(error)

                    assert attribute.name == attribute_name

                    # Collect attribute and remember order only if not seen before.
                    attributes[attribute_name] = attribute
                    if attribute_name not in attribute_orders:
                        attribute_orders[attribute_name] = attribute.order

        # Collect attributes for this class.
        this_attributes = {}  # type: dict[str, Attribute]
        for member_name, member in six.iteritems(dct):
            if isinstance(member, mcs.__attribute_type__):

                # Collect attribute.
                attributes[member_name] = this_attributes[member_name] = member
                if member_name not in attribute_orders:
                    attribute_orders[member_name] = member.order

        # Build ordered attribute map.
        attribute_items = sorted(six.iteritems(attributes), key=lambda i: attribute_orders[i[0]])
        attribute_map = AttributeMap(attribute_items)

        this_attribute_items = [(n, a) for n, a in attribute_items if n in this_attributes]
        this_attribute_map = AttributeMap(this_attribute_items)

        # Hook to edit dct.
        dct_copy = dict(dct)
        edited_dct = mcs.__edit_dct__(this_attribute_map, attribute_map, name, bases, dct_copy, **kwargs)
        if edited_dct is not dct_copy:
            dct_copy = edited_dct

        # Build class.
        cls = super(BaseClassMeta, mcs).__new__(mcs, name, bases, dct_copy, **kwargs)

        # Name attributes.
        for attribute_name, attribute in six.iteritems(this_attributes):
            attribute.__set_name__(cls, attribute_name)
            assert attribute.name == attribute_name

        # Store attribute map.
        cls.__attributes = attribute_map

        # Check for non-default attributes declared after default ones.
        if not cls.__kw_only__:
            seen_default = None
            for attribute_name, attribute in six.iteritems(attribute_map):
                if not attribute.init:
                    continue
                if attribute.has_default:
                    seen_default = attribute_name
                elif seen_default is not None:
                    error = "non-default attribute {!r} declared after default attribute {!r}".format(
                        attribute_name, seen_default
                    )
                    raise TypeError(error)

        # Generate init method.
        if cls.__gen_init__:
            if "__init__" in dct:
                error = "can't manually define __init__"
                raise TypeError(error)
            init_method = cls.__gen_init()
            init_method.__module__ = cls.__module__
            type.__setattr__(cls, "__init__", init_method)

        return cls

    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]
        return dct

    def __gen_init(cls):
        globs = {"AttributeManager": AttributeManager, "DEFAULT": DEFAULT}
        args = []
        lines = []
        for name, attribute in six.iteritems(cls.__attributes__):
            if not attribute.init:
                continue
            if attribute.has_default or cls.__kw_only__:
                args.append("{}=DEFAULT".format(name))
            else:
                args.append(name)

        manager_line = "__initial_values = AttributeManager(type(self).__attributes__).get_initial_values("
        if args:
            manager_line += ", ".join(args)
        manager_line += ")"
        lines.append(manager_line)

        init_line = "self._init(__initial_values)"
        lines.append(init_line)

        init_script = "def __init__(self{}):".format((", " + ", ".join(args)) if args else "")
        init_script += "\n    " + "\n    ".join(lines or ["pass"])

        return make_method("__init__", init_script, generate_unique_filename(cls, "__init__"), globs)

    @property
    @runtime_final.final
    def __attributes__(cls):
        # type: () -> AttributeMap
        return cls.__attributes


class BaseClass(six.with_metaclass(BaseClassMeta, Base)):
    """Base class."""

    __slots__ = ()

    def __init_subclass__(
        cls,
        kw_only=None,  # type: bool | None
        gen_init=None,  # type: bool | None
        **kwargs
    ):
        # type: (...) -> None

        # Keyword argument only.
        if kw_only is not None:
            if cls.__kw_only__ and not kw_only:
                error = "kw_only is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__kw_only__ = bool(kw_only)

        # Generate init method.
        if gen_init is not None:
            if cls.__gen_init__ and not gen_init:
                error = "gen_init is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__gen_init__ = bool(gen_init)

        super(BaseClass, cls).__init_subclass__(**kwargs)  # noqa

    @abc.abstractmethod
    def _init(self, init_values):
        # type: (dict[str, Any]) -> None
        raise NotImplementedError()

    @abc.abstractmethod
    def __getitem__(self, name):
        # type: (str) -> Any
        raise NotImplementedError()


class BasePrivateClass(BaseClass):
    """Base private class."""

    __slots__ = ()

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPC, SupportsKeysAndGetItem[str, Any], **Any) -> BPC
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPC, Iterable[Item], **Any) -> BPC
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BPC, **Any) -> BPC
        pass

    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        raise NotImplementedError()


BPC = TypeVar("BPC", bound=BasePrivateClass)  # base private class type


# noinspection PyAbstractClass
class BaseInteractiveClass(BasePrivateClass):
    """Base interactive class."""

    __slots__ = ()

    @overload
    def update(self, __m, **kwargs):
        # type: (BC, SupportsKeysAndGetItem[str, Any], **Any) -> BC
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BC, Iterable[Item], **Any) -> BC
        pass

    @overload
    def update(self, **kwargs):
        # type: (BC, **Any) -> BC
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        updates = {}
        for name, value in six.iteritems(dict(*args, **kwargs)):
            if value is not DELETED:
                attribute = type(self).__attributes__[name]
                value = attribute.relationship.process(value)
            updates[name] = value
        return self._update(updates)


BC = TypeVar("BC", bound=BaseClass)  # base class type


class BaseMutableClassMeta(BaseClassMeta):
    """Metaclass for :class:`BaseMutableClass`."""

    __attribute_type__ = MutableAttribute  # type: Type[Attribute]


# noinspection PyAbstractClass
class BaseMutableClass(six.with_metaclass(BaseMutableClassMeta, BasePrivateClass)):
    """Base mutable class."""

    __slots__ = ()

    @runtime_final.final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        self._update({name: value})

    @runtime_final.final
    def __delitem__(self, name):
        # type: (str) -> None
        self._update({name: DELETED})

    @overload
    def update(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[Item], **Any) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**Any) -> None
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """Update attribute values."""
        self._update(*args, **kwargs)

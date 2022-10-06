import abc

import six
from basicco import dynamic_code, get_mro, recursive_repr, runtime_final, safe_repr
from tippo import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Literal,
    SupportsKeysAndGetItem,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    overload,
    dataclass_transform,
)

from ._attribute import Attribute, AttributeMap, MutableAttribute, StateReader
from ._bases import CollectionStructure, CollectionStructureMeta
from ._constants import DEFAULT, DELETED, MISSING
from ._relationship import Relationship

T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


@dataclass_transform(field_descriptors=(Attribute,))
class StructureMeta(CollectionStructureMeta):
    """Metaclass for :class:`Structure`."""

    __attribute_type__ = Attribute  # type: Type[Attribute]
    __relationship_type__ = Relationship  # type: Type[Relationship]

    __kw_only__ = False  # type: bool
    __frozen__ = False  # type: bool
    __gen_init__ = False  # type: bool
    __gen_hash__ = False  # type: bool
    __gen_eq__ = False  # type: bool
    __gen_order__ = False  # type: bool
    __gen_repr__ = False  # type: bool

    __attributes = AttributeMap()  # type: AttributeMap

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa

        # Scrape bases.
        base_attributes = {}  # type: dict[str, Attribute]
        attribute_counts = {}  # type: dict[str, int]
        for base in reversed(get_mro.preview_mro(*bases)):
            if base is object:
                continue

            # Prevent overriding attributes with non-attributes.
            for attribute_name in base_attributes:
                if (isinstance(base, StructureMeta) and attribute_name not in base.__attributes__) or (
                    hasattr(base, attribute_name)
                    and not isinstance(getattr(base, attribute_name), mcs.__attribute_type__)
                ):
                    error = "{!r} overrides {!r} attribute with {!r} object, expected {!r}".format(
                        base.__name__,
                        attribute_name,
                        type(getattr(base, attribute_name)).__name__,
                        mcs.__attribute_type__.__name__,
                    )
                    raise TypeError(error)

            # Collect base's attributes.
            if isinstance(base, StructureMeta):
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
                            base.__qualname__,
                            base.__attribute_type__,
                        )
                        raise TypeError(error)

                    assert attribute.name == attribute_name

                    # Collect attribute and remember count only if not seen before.
                    base_attributes[attribute_name] = attribute
                    if attribute_name not in attribute_counts:
                        attribute_counts[attribute_name] = attribute.count

        # Collect attributes for this class.
        this_attributes = {}  # type: dict[str, Attribute]
        for member_name, member in six.iteritems(dct):
            if isinstance(member, mcs.__attribute_type__):

                # Collect attribute.
                base_attributes[member_name] = this_attributes[member_name] = member
                if member_name not in attribute_counts:
                    attribute_counts[member_name] = member.count

        # Build counted attribute map.
        attribute_items = sorted(six.iteritems(base_attributes), key=lambda i: attribute_counts[i[0]])
        attribute_map = AttributeMap(attribute_items)

        this_attribute_items = [(n, a) for n, a in attribute_items if n in this_attributes]
        this_attribute_map = AttributeMap(this_attribute_items)

        # Remove disposable variable "_".
        dct_copy = dict(dct)
        dct_copy.pop("_", None)

        # Hook to edit dct.
        edited_dct = mcs.__edit_dct__(this_attribute_map, attribute_map, name, bases, dct_copy, **kwargs)
        if edited_dct is not dct_copy:
            dct_copy = edited_dct

        # Build class.
        cls = super(StructureMeta, mcs).__new__(mcs, name, bases, dct_copy, **kwargs)

        # Name and claim attributes.
        for attribute_name, attribute in six.iteritems(this_attributes):
            attribute.__set_name__(cls, attribute_name)
            assert attribute.owner is cls
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

        # Generate methods.
        if cls.__frozen__:
            if "__setattr__" in dct:
                error = "can't manually define __setattr__"
                raise TypeError(error)
            type.__setattr__(cls, "__setattr__", _make_frozen_setattr(cls))

            if "__delattr__" in dct:
                error = "can't manually define __delattr__"
                raise TypeError(error)
            type.__setattr__(cls, "__delattr__", _make_frozen_delattr(cls))

        if cls.__gen_init__:
            if "__init__" in dct:
                error = "can't manually define __init__"
                raise TypeError(error)
            type.__setattr__(cls, "__init__", _make_init(cls))

        if cls.__gen_hash__:
            if not cls.__frozen__:
                error = "class {!r} can't be mutable and hashable at the same time"
                raise TypeError(error)

            if not cls.__eq__:
                error = "can't generate __hash__ method if not generating __eq__ as well"
                raise TypeError(error)

            if "__hash__" in dct:
                error = "can't manually define __hash__"
                raise TypeError(error)
            type.__setattr__(cls, "__hash__", _make_hash(cls))

        if cls.__gen_eq__:
            if "__eq__" in dct:
                error = "can't manually define __eq__"
                raise TypeError(error)
            type.__setattr__(cls, "__eq__", _make_eq(cls))

        if cls.__gen_order__:
            if not cls.__gen_eq__:
                error = "'gen_order' is set to True but 'gen_eq' is not"
                raise ValueError(error)
            if "__lt__" in dct:
                error = "can't manually define __lt__"
                raise TypeError(error)
            if "__le__" in dct:
                error = "can't manually define __le__"
                raise TypeError(error)
            if "__gt__" in dct:
                error = "can't manually define __gt__"
                raise TypeError(error)
            if "__ge__" in dct:
                error = "can't manually define __ge__"
                raise TypeError(error)
            type.__setattr__(cls, "__lt__", _make_order(cls, "lt"))
            type.__setattr__(cls, "__le__", _make_order(cls, "le"))
            type.__setattr__(cls, "__gt__", _make_order(cls, "gt"))
            type.__setattr__(cls, "__ge__", _make_order(cls, "ge"))

        if cls.__gen_repr__:
            if "__repr__" in dct:
                error = "can't manually define __repr__"
                raise TypeError(error)
            type.__setattr__(cls, "__repr__", _make_repr(cls))

        return cls

    # noinspection PyUnusedLocal
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]
        return dct

    @property
    @runtime_final.final
    def __attributes__(cls):  # noqa
        # type: () -> AttributeMap
        return cls.__attributes


class Structure(six.with_metaclass(StructureMeta, CollectionStructure[str])):
    """Structure."""

    __slots__ = ()

    def __init_subclass__(
        cls,
        kw_only=None,  # type: bool | None
        frozen=None,  # type: bool | None
        gen_init=None,  # type: bool | None
        gen_hash=None,  # type: bool | None
        gen_eq=None,  # type: bool | None
        gen_order=None,  # type: bool | None
        gen_repr=None,  # type: bool | None
        **kwargs
    ):
        # type: (...) -> None

        # Keyword argument only.
        if kw_only is not None:
            if cls.__kw_only__ and not kw_only:
                error = "kw_only is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__kw_only__ = bool(kw_only)

        # Frozen.
        if frozen is not None:
            if cls.__frozen__ and not frozen:
                error = "frozen is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__frozen__ = bool(frozen)

        # Whether to generate methods.
        if gen_init is not None:
            if cls.__gen_init__ and not gen_init:
                error = "gen_init is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__gen_init__ = bool(gen_init)

        if gen_hash is not None:
            if cls.__gen_hash__ and not gen_hash:
                error = "gen_hash is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__gen_hash__ = bool(gen_hash)

        if gen_eq is not None:
            if cls.__gen_eq__ and not gen_eq:
                error = "gen_eq is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__gen_eq__ = bool(gen_eq)

        if gen_order is not None:
            if cls.__gen_order__ and not gen_order:
                error = "gen_order is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__gen_order__ = bool(gen_order)

        if gen_repr is not None:
            if cls.__gen_repr__ and not gen_repr:
                error = "gen_repr is already on for {!r} base class(es), can't turn it off".format(cls.__name__)
                raise TypeError(error)
            cls.__gen_repr__ = bool(gen_repr)

        super(Structure, cls).__init_subclass__(**kwargs)  # noqa

    # Trick IDEs into thinking that we have these methods defined (they can be auto generated).
    if False:
        # noqa
        def __init__(self, *args, **kwargs):
            pass

        def __hash__(self):
            return 0

        def __eq__(self, other):
            return False

    @abc.abstractmethod
    def __getitem__(self, name):
        # type: (str) -> Any
        raise NotImplementedError()

    @runtime_final.final
    def __iter__(self):
        # type: () -> Iterator[str]
        for name in type(self).__attributes__:
            if hasattr(self, name):
                yield name

    @runtime_final.final
    def __contains__(self, name):
        # type: (object) -> bool
        try:
            if not isinstance(name, six.string_types):
                raise KeyError()
            _ = self[name]
        except KeyError:
            return False
        else:
            return True

    @runtime_final.final
    def __len__(self):
        return len(self.keys())

    @runtime_final.final
    def __getattr__(self, name):
        cls = type(self)
        if name in cls.__attributes__:
            error = "{!r} object has no value for attribute {!r}".format(cls.__qualname__, name)
            raise AttributeError(error)
        return self.__getattribute__(name)

    @abc.abstractmethod
    def __init_state__(self, new_values):
        # type: (dict[str, Any]) -> None
        """
        Initialize state.

        :param new_values: New values.
        """
        raise NotImplementedError()

    @runtime_final.final
    def keys(self):
        # type: () -> tuple[str, ...]
        return tuple(self.__iter__())


class PrivateStructure(Structure):
    """Private structure."""

    __slots__ = ()

    @abc.abstractmethod
    def __update_state__(self, new_values, old_values):
        # type: (PCS, dict[str, Any], dict[str, Any]) -> PCS
        """
        Initialize state.

        :param new_values: New values.
        :param old_values: Old values.
        :return: Transformed.
        """
        raise NotImplementedError()

    @runtime_final.final
    def _discard(self, name):
        # type: (PCS, str) -> PCS
        """
        Discard attribute value if it exists.

        :param name: Attribute name.
        :return: Transformed.
        """
        if name in self:
            return self._remove(name)
        if name not in type(self).__attributes__:
            error = "no attribute named {!r}".format(name)
            raise AttributeError(error)
        if not type(self).__attributes__[name].deletable:
            error = "attribute {!r} is not deletable".format(name)
            raise AttributeError(error)
        return self

    @runtime_final.final
    def _remove(self, name):
        # type: (PCS, str) -> PCS
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises AttributeError: Invalid attribute or no value set.
        """
        return self._update({name: DELETED})

    @runtime_final.final
    def _set(self, name, value):
        # type: (PCS, str, Any) -> PCS
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._update({name: value})

    @overload
    def _update(self, __m, **kwargs):
        # type: (PCS, SupportsKeysAndGetItem[str, Any], **Any) -> PCS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (PCS, Iterable[Item], **Any) -> PCS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (PCS, **Any) -> PCS
        pass

    @runtime_final.final
    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        new_values, old_values = type(self).__attributes__.get_update_values(dict(*args, **kwargs), StateReader(self))
        return self.__update_state__(new_values, old_values)


PCS = TypeVar("PCS", bound=PrivateStructure)


# noinspection PyAbstractClass
class InteractiveStructure(PrivateStructure):
    """Interactive structure."""

    __slots__ = ()

    @runtime_final.final
    def discard(self, name):
        # type: (ICS, str) -> ICS
        """
        Discard attribute value if it exists.

        :param name: Attribute name.
        :return: Transformed.
        """
        return self._discard(name)

    @runtime_final.final
    def remove(self, name):
        # type: (ICS, str) -> ICS
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises AttributeError: Invalid attribute or no value set.
        """
        return self._remove(name)

    @runtime_final.final
    def set(self, name, value):
        # type: (ICS, str, Any) -> ICS
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (ICS, SupportsKeysAndGetItem[str, Any], **Any) -> ICS
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (ICS, Iterable[Item], **Any) -> ICS
        pass

    @overload
    def update(self, **kwargs):
        # type: (ICS, **Any) -> ICS
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


ICS = TypeVar("ICS", bound=InteractiveStructure)


class MutableStructureMeta(StructureMeta):
    """Metaclass for :class:`MutableStructure`."""

    __attribute_type__ = MutableAttribute  # type: Type[Attribute]


# noinspection PyAbstractClass
class MutableStructure(six.with_metaclass(MutableStructureMeta, PrivateStructure)):
    """Mutable structure."""

    __slots__ = ()

    @runtime_final.final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        self._update({name: value})

    @runtime_final.final
    def __delitem__(self, name):
        # type: (str) -> None
        self._update({name: DELETED})

    @runtime_final.final
    def discard(self, name):
        # type: (str) -> None
        """
        Discard attribute value if it exists.

        :param name: Attribute name.
        """
        self._discard(name)

    @runtime_final.final
    def remove(self, name):
        # type: (str) -> None
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :raises AttributeError: Invalid attribute or no value set.
        """
        self._remove(name)

    @runtime_final.final
    def set(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        self._set(name, value)

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


def _make_init(cls):
    # type: (Type[Structure]) -> Callable
    globs = {"DEFAULT": DEFAULT}  # type: dict[str, Any]
    args = []
    arg_names = []
    for name, attribute in six.iteritems(cls.__attributes__):
        if not attribute.init:
            continue
        if attribute.has_default or cls.__kw_only__:
            args.append("{}=DEFAULT".format(name))
            arg_names.append("{name}={name}".format(name=name))
        else:
            args.append(name)
            arg_names.append(name)

    script = "\n".join(
        (
            "def __init__(self{args}):",
            "    self.__init_state__(type(self).__attributes__.get_initial_values({arg_names}))",
        )
    ).format(
        args=(", " + ", ".join(args)) if args else "",
        arg_names=", ".join(arg_names),
    )

    return dynamic_code.make_function(
        "__init__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__init__", cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )


def _make_hash(cls):
    # type: (Type[Structure]) -> Callable
    globs = {}  # type: dict[str, Any]
    args = []
    for name, attribute in six.iteritems(cls.__attributes__):
        if not attribute.hash:
            continue
        args.append(name)

    script = "\n".join(  # TODO: cache hash with special int subclass
        (
            "def __hash__(self):",
            "    hash_values = (self.__class__,) + tuple((n, self[n]) for n in [{args}] if n in self)",
            "    return hash(hash_values)",
        )
    ).format(
        args=(", ".join(repr(a) for a in args)) if args else "",
    )

    return dynamic_code.make_function(
        "__hash__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__hash__", cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )


def _make_eq(cls):
    # type: (Type[Structure]) -> Callable
    globs = {}  # type: dict[str, Any]
    args = []
    for name, attribute in six.iteritems(cls.__attributes__):
        if not attribute.eq:
            continue
        args.append(name)

    script = "\n".join(
        (
            "def __eq__(self, other):",
            "    if self is other:",
            "        return True",
            "    if type(self) is not type(other):",
            "        return False",
            "    eq_values = dict((n, self[n]) for n in [{args}] if n in self)",
            "    other_eq_values = dict((n, other[n]) for n in [{args}] if n in other)",
            "    return eq_values == other_eq_values",
        )
    ).format(
        args=(", ".join(repr(a) for a in args)) if args else "",
    )

    return dynamic_code.make_function(
        "__eq__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__eq__", cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )


def _make_order(cls, method):
    # type: (Type[Structure], Literal["lt", "le", "gt", "ge"]) -> Callable
    globs = {"MISSING": MISSING}  # type: dict[str, Any]
    args = []
    for name, attribute in six.iteritems(cls.__attributes__):
        if not attribute.order:
            continue
        args.append(name)

    operators = {
        "lt": "<",
        "le": "<=",
        "gt": ">",
        "ge": ">=",
    }
    operator = operators[method]

    method_name = "__{}__".format(method)
    script = "\n".join(
        (
            "def {method_name}(self, other):",
            "    if type(self) is not type(other):",
            "        return False",
            "    order_values = tuple(self[n] for n in [{args}])",
            "    other_order_values = tuple(other[n] for n in [{args}])",
            "    return order_values {operator} other_order_values",
        )
    ).format(
        method_name=method_name,
        args=(", ".join(repr(a) for a in args)) if args else "",
        operator=operator,
    )

    return dynamic_code.make_function(
        method_name,
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename(method_name, cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )


def _make_repr(cls):
    # type: (Type[Structure]) -> Callable
    globs = {"six": six, "recursive_repr": recursive_repr, "safe_repr": safe_repr}  # type: dict[str, Any]
    args = []
    kwargs = []
    delegated = []
    for name, attribute in six.iteritems(cls.__attributes__):
        if not attribute.repr:
            continue
        if attribute.has_default:
            kwargs.append(name)
        elif attribute.delegated:
            delegated.append(name)
        else:
            args.append(name)

    script = "\n".join(
        (
            "@safe_repr.safe_repr",
            "@recursive_repr.recursive_repr",
            "def __repr__(self):",
            "    repr_text = '{{}}('.format(type(self).__qualname__)",
            "    parts = []",
            "    for name, value in six.iteritems(dict((n, self[n]) for n in [{args}] if n in self)):",
            "        parts.append(repr(value))",
            "    for name, value in six.iteritems(dict((n, self[n]) for n in [{kwargs}] if n in self)):",
            "        parts.append('{{}}={{}}'.format(name, repr(value)))",
            "    for name, value in six.iteritems(dict((n, self[n]) for n in [{delegated}] if n in self)):",
            "        parts.append('<{{}}={{}}>'.format(name, repr(value)))",
            "    repr_text += ', '.join(parts) + ')'",
            "    return repr_text",
        )
    ).format(
        args=", ".join(repr(a) for a in args) if args else "",
        kwargs=", ".join(repr(a) for a in kwargs) if kwargs else "",
        delegated=", ".join(repr(a) for a in delegated) if delegated else "",
    )
    return dynamic_code.make_function(
        "__repr__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__repr__", cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )


def _make_frozen_setattr(cls):
    # type: (Type[Structure]) -> Callable
    globs = {"cls": cls}  # type: dict[str, Any]
    script = "\n".join(
        (
            "def __setattr__(self, name, value):",
            "    if name in type(self).__attributes__:",
            "        error = '{!r} attributes are read-only'.format(type(self).__qualname__)",
            "        raise AttributeError(error)",
            "    return super(cls, self).__setattr__(name, value)",
        )
    )
    return dynamic_code.make_function(
        "__setattr__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__setattr__", cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )


def _make_frozen_delattr(cls):
    # type: (Type[Structure]) -> Callable
    globs = {"cls": cls}  # type: dict[str, Any]
    script = "\n".join(
        (
            "def __delattr__(self, name):",
            "    if name in type(self).__attributes__:",
            "        error = '{!r} attributes are read-only'.format(type(self).__qualname__)",
            "        raise AttributeError(error)",
            "    return super(cls, self).__delattr__(name)",
        )
    )
    return dynamic_code.make_function(
        "__delattr__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__delattr__", cls.__module__, cls.__qualname__),
        module=cls.__module__,
    )

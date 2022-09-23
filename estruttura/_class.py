import abc

import six
from basicco import custom_repr, runtime_final, recursive_repr, dynamic_code
from tippo import Any, Callable, TypeVar, Iterable, TypeAlias, Type, Tuple, Iterator, overload

from ._constants import SupportsKeysAndGetItem, DELETED, DEFAULT
from ._bases import BaseMeta, BaseIterable, BaseContainer
from ._relationship import Relationship
from ._attribute import Attribute, MutableAttribute, AttributeMap


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


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
        base_attributes = {}  # type: dict[str, Attribute]
        attribute_orders = {}  # type: dict[str, int]
        for base in reversed(bases):

            # Prevent overriding attributes with non-attributes.
            for attribute_name in base_attributes:
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
                    base_attributes[attribute_name] = attribute
                    if attribute_name not in attribute_orders:
                        attribute_orders[attribute_name] = attribute.order

        # Collect attributes for this class.
        this_attributes = {}  # type: dict[str, Attribute]
        for member_name, member in six.iteritems(dct):
            if isinstance(member, mcs.__attribute_type__):

                # Collect attribute.
                base_attributes[member_name] = this_attributes[member_name] = member
                if member_name not in attribute_orders:
                    attribute_orders[member_name] = member.order

        # Build ordered attribute map.
        attribute_items = sorted(six.iteritems(base_attributes), key=lambda i: attribute_orders[i[0]])
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

        # Generate init method.
        if cls.__gen_init__:
            if "__init__" in dct:
                error = "can't manually define __init__"
                raise TypeError(error)
            type.__setattr__(cls, "__init__", _make_init(cls))

        return cls

    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]
        return dct

    @property
    @runtime_final.final
    def __attributes__(cls):
        # type: () -> AttributeMap
        return cls.__attributes


class BaseClass(six.with_metaclass(BaseClassMeta, BaseIterable[Item], BaseContainer[str])):
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

    @recursive_repr.recursive_repr
    def __repr__(self):  # FIXME: generated
        items = tuple(self)
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

    @abc.abstractmethod
    def __getitem__(self, name):
        # type: (str) -> Any
        raise NotImplementedError()

    def __iter__(self):
        # type: () -> Iterator[Item]
        for name, attribute in six.iteritems(type(self).__attributes__):
            try:
                value = self[name]
            except KeyError:
                continue
            yield name, value

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

    def __getattr__(self, name):
        cls = type(self)
        if name in cls.__attributes__:
            error = "{!r} object has no value for attribute {!r}".format(cls.__fullname__, name)
            raise AttributeError(error)
        return self.__getattribute__(name)

    @abc.abstractmethod
    def _init(self, init_values):
        # type: (dict[str, Any]) -> None
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
        return self._update(*args, **kwargs)


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


def _make_init(cls):
    # type: (Type[BaseClass]) -> Callable
    globs = {"DEFAULT": DEFAULT}
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
            "    self._init(type(self).__attributes__.get_initial_values({arg_names}))",
        )
    ).format(
        args=(", " + ", ".join(args)) if args else "",
        arg_names=", ".join(arg_names),
    )

    return dynamic_code.make_function(
        "__init__",
        script,
        globs=globs,
        filename=dynamic_code.generate_unique_filename("__init__", cls.__module__, cls.__fullname__),
        module=cls.__module__,
    )

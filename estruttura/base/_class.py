import six
import collections
import operator

from tippo import Any, Type, TypeVar, Iterator, Iterable, SupportsKeysAndGetItem, Callable, overload
from basicco.explicit_hash import set_to_none
from basicco.safe_repr import safe_repr
from basicco.recursive_repr import recursive_repr
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from basicco.obj_state import get_state, update_state
from basicco.get_mro import preview_mro

from ..constants import DELETED
from ._base import BaseMeta, Base, BaseImmutableMeta, BaseImmutable, BaseMutableMeta, BaseMutable
from ._attribute import BaseAttribute, BaseMutableAttribute, AttributeMap, StateReader


class BaseClassMeta(BaseMeta):
    __attribute_type__ = BaseAttribute

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa

        # Scrape bases.
        base_attributes = {}  # type: dict[str, BaseAttribute]
        counter = collections.Counter()  # type: collections.Counter[str]
        for base in reversed(preview_mro(*bases)):
            if base is object:
                continue

            # Prevent overriding attributes with non-attributes.
            for attribute_name in base_attributes:
                if (isinstance(base, BaseClassMeta) and attribute_name not in base.__attributes__) or (
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
                            base.__qualname__,
                            base.__attribute_type__,
                        )
                        raise TypeError(error)

                    assert attribute.name == attribute_name

                    # Collect attribute and remember count only if not seen before.
                    base_attributes[attribute_name] = attribute
                    if attribute_name not in counter:
                        counter[attribute_name] = attribute.count

        # Collect attributes for this class.
        this_attributes = {}  # type: dict[str, BaseAttribute]
        for member_name, member in six.iteritems(dct):
            if isinstance(member, mcs.__attribute_type__):

                # Collect attribute.
                base_attributes[member_name] = this_attributes[member_name] = member
                if member_name not in counter:
                    counter[member_name] = member.count

        # Build ordered attribute map.
        attribute_items = sorted(six.iteritems(base_attributes), key=lambda i: counter[i[0]])
        attribute_map = AttributeMap(attribute_items)

        this_attribute_items = [(n, a) for n, a in attribute_items if n in this_attributes]
        this_attribute_map = AttributeMap(this_attribute_items)

        # Hook to edit dct.
        dct_copy = dict(dct)
        dct_copy = mcs.__edit_dct__(this_attribute_map, attribute_map, name, bases, dct_copy, **kwargs)

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
        if cls.__kw_only__:
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

        return cls

    # noinspection PyUnusedLocal
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]
        return dct

    @property
    @final
    def __attributes__(cls):  # noqa
        # type: () -> AttributeMap
        return cls.__attributes


AT_co = TypeVar("AT_co", bound=BaseAttribute, covariant=True)  # attribute type
MAT_co = TypeVar("MAT_co", bound=BaseMutableAttribute, covariant=True)  # mutable attribute type


# noinspection PyAbstractClass
class BaseClass(six.with_metaclass(BaseClassMeta, Base)):
    __slots__ = ()
    __attributes__ = AttributeMap()  # type: AttributeMap[BaseAttribute]
    __kw_only__ = False  # type: bool

    def __init_subclass__(cls, kw_only=None, **kwargs):

        # Keyword arguments only.
        if kw_only is not None:
            if not kw_only and cls.__kw_only__:
                error = "class {!r} already set to use keyword arguments only, can't set it to False".format(
                    cls.__qualname__
                )
                raise TypeError(error)
            cls.__kw_only__ = bool(kw_only)

        super(BaseClass, cls).__init_subclass__(**kwargs)  # noqa

    def __init__(self, *args, **kwargs):
        cls = type(self)
        if cls.__kw_only__ and args:
            error = "{}.__init__ accepts keyword arguments only".format(cls.__qualname__)
            raise TypeError(error)
        values = cls.__attributes__.get_initial_values(args, kwargs, init_property="init", init_method="__init__")
        self.__init_state__(values)

    @abstract
    def __getitem__(self, name):
        # type: (str) -> Any
        raise NotImplementedError()

    @final
    def __iter__(self):
        # type: () -> Iterator[str]
        for name in type(self).__attributes__:
            if hasattr(self, name):
                yield name

    @final
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

    @final
    def __len__(self):
        return len(self.keys())

    @final
    def __getattr__(self, name):
        # type: (str) -> Any
        cls = type(self)
        if name in cls.__attributes__:
            error = "{!r} object has no value for attribute {!r}".format(cls.__qualname__, name)
            raise AttributeError(error)
        return self.__getattribute__(name)

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()

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

    def __eq__(self, other):
        # type: (object) -> bool

        # Same object
        if self is object:
            return True

        # Require the exact same type for comparison.
        cls = type(self)
        if cls is not type(other):
            return NotImplemented
        assert isinstance(other, type(self))

        # Get attributes to compare.
        attributes = [n for n, a in six.iteritems(cls.__attributes__) if a.eq]

        # Compare values.
        order_values = dict((n, self[n]) for n in attributes if n in self)
        other_order_values = dict((n, other[n]) for n in attributes if n in other)
        return order_values == other_order_values

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

    @safe_repr
    @recursive_repr
    def __repr__(self):
        cls = type(self)

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
            elif cls.__kw_only__:
                kwargs.append(name)
            else:
                args.append(name)

        parts = []
        for name, value in six.iteritems(dict((n, self[n]) for n in args if n in self)):
            parts.append(repr(value))
        for name, value in six.iteritems(dict((n, self[n]) for n in kwargs if n in self)):
            parts.append("{}={!r}".format(name, value))
        for name, value in six.iteritems(dict((n, self[n]) for n in delegated if n in self)):
            parts.append("<{}={!r}>".format(name, value))

        return "{}({})".format(cls.__qualname__, ", ".join(parts))

    @abstract
    def __init_state__(self, new_values):
        # type: (dict[str, Any]) -> None
        """
        Initialize state.

        :param new_values: New values.
        """
        raise NotImplementedError()

    @abstract
    def __update_state__(self, new_values, old_values):
        # type: (BC, dict[str, Any], dict[str, Any]) -> BC
        """
        Initialize state.

        :param new_values: New values.
        :param old_values: Old values.
        :return: Transformed.
        """
        raise NotImplementedError()

    @final
    def _discard(self, name):
        # type: (BC, str) -> BC
        """
        Discard attribute value if it exists.

        :param name: Attribute name.
        :return: Transformed.
        """
        if name in self:
            return self._delete(name)
        if name not in type(self).__attributes__:
            error = "{!r} object has no attribute named {!r}".format(type(self).__qualname__, name)
            raise AttributeError(error)
        if not type(self).__attributes__[name].deletable:
            error = "attribute {!r} is not deletable".format(name)
            raise AttributeError(error)
        return self

    @final
    def _delete(self, name):
        # type: (BC, str) -> BC
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises AttributeError: Invalid attribute or no value set.
        """
        return self._update({name: DELETED})

    @final
    def _set(self, name, value):
        # type: (BC, str, Any) -> BC
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._update({name: value})

    @overload
    def _update(self, __m, **kwargs):
        # type: (BC, SupportsKeysAndGetItem[str, Any], **Any) -> BC
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BC, Iterable[tuple[str, Any]], **Any) -> BC
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BC, **Any) -> BC
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        new_values, old_values = type(self).__attributes__.get_update_values(dict(*args, **kwargs), StateReader(self))
        return self.__update_state__(new_values, old_values)

    @final
    def keys(self):
        # type: () -> tuple[str, ...]
        return tuple(self.__iter__())


BC = TypeVar("BC", bound=BaseClass)  # base class self type


class BaseImmutableClassMeta(BaseClassMeta, BaseImmutableMeta):
    pass


# noinspection PyAbstractClass
class BaseImmutableClass(six.with_metaclass(BaseImmutableClassMeta, BaseClass, BaseImmutable)):
    __slots__ = ()

    def __copy__(self):
        cls = type(self)
        self_copy = cls.__new__(cls)
        update_state(self_copy, get_state(self))
        return self_copy

    def __hash__(self):
        cls = type(self)
        attributes = [n for n, a in six.iteritems(cls.__attributes__) if a.hash]
        hash_values = (cls,) + tuple((n, self[n]) for n in attributes if n in self)
        return hash(hash_values)

    def __setattr__(self, name, value):
        cls = type(self)
        if name in cls.__attributes__:
            error = "{!r} attributes are read-only".format(cls.__qualname__)
            raise AttributeError(error)
        super(BaseImmutableClass, self).__setattr__(name, value)

    def __delattr__(self, name):
        cls = type(self)
        if name in cls.__attributes__:
            error = "{!r} attributes are read-only".format(cls.__qualname__)
            raise AttributeError(error)
        super(BaseImmutableClass, self).__delattr__(name)

    @final
    def discard(self, name):
        # type: (BIC, str) -> BIC
        """
        Discard attribute value if it exists.

        :param name: Attribute name.
        :return: Transformed.
        """
        return self._discard(name)

    @final
    def delete(self, name):
        # type: (BIC, str) -> BIC
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises AttributeError: Invalid attribute or no value set.
        """
        return self._delete(name)

    @final
    def set(self, name, value):
        # type: (BIC, str, Any) -> BIC
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (BIC, SupportsKeysAndGetItem[str, Any], **Any) -> BIC
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BIC, Iterable[tuple[str, Any]], **Any) -> BIC
        pass

    @overload
    def update(self, **kwargs):
        # type: (BIC, **Any) -> BIC
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


BIC = TypeVar("BIC", bound=BaseImmutableClass)  # base immutable class self type


class BaseMutableClassMeta(BaseClassMeta, BaseMutableMeta):
    __attribute_type__ = BaseMutableAttribute


# noinspection PyAbstractClass
class BaseMutableClass(six.with_metaclass(BaseMutableClassMeta, BaseClass, BaseMutable)):
    __slots__ = ()
    __attributes__ = AttributeMap()  # type: AttributeMap[BaseMutableAttribute]

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    @final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        self._update({name: value})

    @final
    def __delitem__(self, name):
        # type: (str) -> None
        self._update({name: DELETED})

    @final
    def discard(self, name):
        # type: (str) -> None
        """
        Discard attribute value if it exists.

        :param name: Attribute name.
        """
        self._discard(name)

    @final
    def delete(self, name):
        # type: (str) -> None
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :raises AttributeError: Invalid attribute or no value set.
        """
        self._delete(name)

    @final
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
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**Any) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """Update attribute values."""
        self._update(*args, **kwargs)

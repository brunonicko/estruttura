import abc
import collections

import six
from basicco import runtime_final, fabricate_value, custom_repr, recursive_repr
from tippo import Any, Callable, TypeVar, Tuple, Iterable, Generic, Iterator, Type, TypeAlias, overload, cast

from ._constants import MissingType, MISSING, DELETED, SupportsKeysAndGetItem
from ._dict import BaseDict
from ._bases import (
    Base,
    BaseHashable,
    BaseCollectionMeta,
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BasePrivateCollection,
)


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


_attribute_counter = 0


class BaseAttribute(BaseHashable, Generic[T_co]):
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
        relationship=None,  # type: BaseRelationship | None
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
        self._owner = None  # type: Type[BaseObject] | None
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

    @abc.abstractmethod
    def __get__(self, instance, owner):
        # type: (BaseObject, Type[BaseObject]) -> T_co
        raise NotImplementedError()

    def __set_name__(self, owner, name):
        # type: (Type[BaseObject], str) -> None
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
        # type: (BA, SupportsKeysAndGetItem[str, Any], **Any) -> BA
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BA, Iterable[Item], **Any) -> BA
        pass

    @overload
    def update(self, **kwargs):
        # type: (BA, **Any) -> BA
        pass

    def update(self, *args, **kwargs):
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(BA, type(self)(**updated_kwargs))

    def make_default_value(self):
        # type: () -> T_co

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

        # Process using relationship.
        if self.relationship is not None:
            default_value = self.relationship.process(default_value)

        return default_value

    @property
    def name(self):
        # type: () -> str | None
        return self._name

    @property
    def owner(self):
        # type: () -> Type[BaseObject] | None
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
        # type: () -> BaseRelationship | None
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


BA = TypeVar("BA", bound=BaseAttribute)  # base attribute type
BA_co = TypeVar("BA_co", bound=BaseAttribute, covariant=True)  # covariant base attribute type


class BaseMutableAttribute(BaseAttribute[T]):
    __slots__ = ()

    @abc.abstractmethod
    def __get__(self, instance, owner):
        # type: (BaseObject, Type[BaseObject]) -> T
        raise NotImplementedError()

    @abc.abstractmethod
    def __set__(self, instance, value):
        # type: (BaseObject, T) -> None
        raise NotImplementedError()

    @abc.abstractmethod
    def __delete__(self, instance, value):
        # type: (BaseObject, T) -> None
        raise NotImplementedError()


class AttributeMap(BaseDict[str, BA_co]):
    __slots__ = ("__attribute_dict",)

    def __init__(self, attribute_items):
        # type: (Iterable[tuple[str, BA_co]]) -> None
        self.__attribute_dict = collections.OrderedDict()  # type: collections.OrderedDict[str, BA_co]
        for name, attribute in attribute_items:
            self.__attribute_dict[name] = attribute

    def __repr__(self):
        return "{}({})".format(type(self).__fullname__, custom_repr.iterable_repr(self.items()))

    def __eq__(self, other):
        return isinstance(other, AttributeMap) and self.__attribute_dict == other.__attribute_dict

    def __reversed__(self):
        return reversed(self.__attribute_dict)

    def __getitem__(self, name):
        return self.__attribute_dict[name]

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

    def __iter__(self) -> Iterator[str]:
        for name in six.iterkeys(self.__attribute_dict):
            yield name


class BaseAttributeManager(Base, Generic[BA_co]):
    __slots__ = ("_attributes",)

    def __init__(self, attributes):
        # type: (AttributeMap[BA_co]) -> None
        """
        :param attributes: Attributes.
        """
        self._attributes = attributes

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
        for attribute_name, attribute in six.iteritems(self.attributes):

            # Skip non-init attributes.
            if not attribute.init:

                # Can't get its value from the init.
                if attribute_name in kwargs:
                    error = "attribute {!r} can't be set externally".format(attribute_name)
                    raise TypeError(error)

                if attribute.has_default:

                    # Has a default value.
                    value = attribute.make_default()
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
                    i += 1
                    initial_values[attribute_name] = value
                    continue

            # Get value for keyword argument.
            try:
                value = kwargs[attribute_name]
            except KeyError:
                if attribute.has_default:
                    value = attribute.make_default()
                elif attribute.required:
                    error = "missing value for required attribute {!r}".format(attribute_name)
                    exc = TypeError(error)
                    six.raise_from(exc, None)
                    raise exc
                else:
                    continue

            # Set attribute value.
            initial_values[attribute_name] = value

        # Invalid kwargs.
        invalid_kwargs = set(kwargs).difference(self.attributes)
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
    def attributes(self):
        # type: () -> AttributeMap[BA_co]
        """Attributes."""
        return self._attributes


class BaseObjectMeta(BaseCollectionMeta, type):
    def __init__(cls, name, bases, dct, **kwargs):
        super(BaseObjectMeta, cls).__init__(name, bases, dct, **kwargs)

        try:
            attributes = cls.__attributes__
        except NotImplementedError:
            pass
        else:
            # For each declared attribute.
            seen_default = None
            for attribute_name, attribute in six.iteritems(attributes):

                # Set name.
                attribute.name = attribute_name

                # Check for non-default attributes declared after default ones.
                if not cls.__kw_only__:
                    if not attribute.init:
                        continue
                    if attribute.has_default:
                        seen_default = attribute_name
                    elif seen_default is not None:
                        error = "non-default attribute {!r} declared after default attribute {!r}".format(
                            attribute_name, seen_default
                        )
                        raise TypeError(error)

    @property
    @abc.abstractmethod
    def __kw_only__(cls):
        # type: () -> bool
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def __attributes__(cls):  # FIXME: Remove from metaclass.
        # type: () -> AttributeMap[BaseAttribute]
        raise NotImplementedError()


class BaseObject(six.with_metaclass(BaseObjectMeta, BaseCollection[Item])):
    """Base object."""

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: {!r}".format(type(self).__name__)
        raise TypeError(error)

    @abc.abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __getitem__(self, attribute_name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param attribute_name: Attribute name.
        :return: Value/values.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether any of the attributes has value.

        :param value: Value.
        :return: True if has value.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __iter__(self):
        # type: () -> Iterator[Item]
        """
        Iterate over items.

        :return: Item iterator.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __len__(self):
        # type: () -> int
        """
        Number of attributes with values.

        :return: Number of attributes with values.
        """
        raise NotImplementedError()


# noinspection PyCallByClass
type.__setattr__(BaseObject, "__hash__", None)  # force non-hashable


BO = TypeVar("BO", bound=BaseObject)  # base object type


class BasePrivateObject(BaseObject, BasePrivateCollection[Item]):
    """Base private object."""

    __slots__ = ()

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPO, SupportsKeysAndGetItem[str, Any], **Any) -> BPO
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPO, Iterable[Item], **Any) -> BPO
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BPO, **Any) -> BPO
        pass

    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update attribute values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        raise NotImplementedError()


BPO = TypeVar("BPO", bound=BasePrivateObject)  # base private object type


# noinspection PyAbstractClass
class BaseInteractiveObject(BasePrivateObject, BaseInteractiveCollection[Item]):
    """Base interactive object."""

    __slots__ = ()

    @overload
    def update(self, __m, **kwargs):
        # type: (BPO, SupportsKeysAndGetItem[str, Any], **Any) -> BPO
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BPO, Iterable[Item], **Any) -> BPO
        pass

    @overload
    def update(self, **kwargs):
        # type: (BPO, **Any) -> BPO
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update attribute values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


# noinspection PyAbstractClass
class BaseMutableObject(BasePrivateObject, BaseMutableCollection[Item]):
    """Base mutable object."""

    __slots__ = ()

    @runtime_final.final
    def __setitem__(self, attribute_name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param attribute_name: Attribute name.
        :param value: Value.
        """
        self.update({attribute_name: value})

    @runtime_final.final
    def __delitem__(self, attribute_name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param attribute_name: Attribute name.
        """
        self.update({attribute_name: DELETED})

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
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)
